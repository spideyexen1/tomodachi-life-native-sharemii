# SPDX-License-Identifier: GPL-3.0-only
"""Compile and exercise actual patched texture-handle/retirement functions without a game."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

from patch_texture_lifetime import patched_text

URL = "https://raw.githubusercontent.com/josiahg2502-glitch/TomodachiLife-recomp/b7ba15075e7303f79b2f941f09d30003f49aa80c/runtime/nvn_gl.c"


def function(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    # These two pinned functions have no braces inside literals or comments.
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


STUBS = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {int width, height;} TexBuilder;
typedef struct {int dead, pool_refs; void *vk; long long last_bind, dead_frame; TexBuilder b;} Tex;
typedef struct {int value;} View;
typedef struct {int value;} SamplerParams;
typedef struct {Tex *tex; View view;} Entry;
typedef struct {int count; Entry e[2];} TexPool;
typedef struct {int count, used[2]; SamplerParams e[2];} SamplerPool;
typedef struct {char *text; int state;} Stage;
typedef struct {Stage st[6];} Prog;
enum {K_TEX=1, K_PROG=2};
static struct {long long frames;} g_st;
static struct {int kind; void *p;} g_dead[16];
static int g_dead_n, g_pool_lock, g_dead_lock, dropped, released;
static void AcquireSRWLockShared(int *p) {(void)p;}
static void ReleaseSRWLockShared(int *p) {(void)p;}
static void EnterCriticalSection(int *p) {(void)p;}
static void LeaveCriticalSection(int *p) {(void)p;}
static void tex_release_packaged(void *p) {(void)p; released++;}
static void drop(int kind, void *p) {dropped++; if(kind==K_TEX)((Tex*)p)->vk=NULL;}
static void reset(void) {g_dead_n=0;dropped=released=0;g_st.frames=10;}
static void retire(Tex *t) {g_dead[g_dead_n].kind=K_TEX;g_dead[g_dead_n++].p=t;}
'''

CASES = r'''
int main(void) {
    Tex t={1,1,(void*)1,9,9,{256,256}}, other={1,0,(void*)1,9,9,{64,64}};
    TexPool pool={2,{{NULL,{0}},{&t,{7}}}};
    SamplerPool samplers={1,{1,0},{{42},{0}}};
    Tex *out=NULL; View view={0}; SamplerParams sampler={0};
    reset();
    assert(nvn_front_handle(&pool,&samplers,1,&out,&view,&sampler)==3);
    assert(out==&t && t.last_bind==10 && view.value==7 && sampler.value==42);
    /* No GPU image: reject, rather than rebuild from freed guest memory. */
    t.vk=NULL;
    assert(nvn_front_handle(&pool,&samplers,1,&out,&view,&sampler)==2 && out==NULL);
    t.vk=(void*)1;
    retire(&t); nvn_front_take_dead(drop);
    assert(g_dead_n==1 && dropped==0 && released==0 && t.vk);
    /* A pool descriptor is rebound: release both resource and packaged data. */
    t.pool_refs=0; nvn_front_take_dead(drop);
    assert(g_dead_n==0 && dropped==1 && released==1 && !t.vk);
    reset();t.vk=(void*)1;t.pool_refs=1;t.last_bind=7;retire(&t);
    nvn_front_take_dead(drop);assert(dropped==1 && released==1);
    /* Hard age bound prevents an endlessly referenced finalized texture leaking. */
    reset();g_st.frames=310;t.vk=(void*)1;t.dead_frame=10;t.last_bind=310;retire(&t);
    nvn_front_take_dead(drop);assert(dropped==1 && g_dead_n==0);
    /* Mixed retirement list compacts correctly while preserving live descriptors. */
    reset();t.vk=(void*)1;t.dead_frame=9;t.last_bind=10;retire(&other);retire(&t);
    nvn_front_take_dead(drop);
    assert(g_dead_n==1 && g_dead[0].p==&t && dropped==1 && released==1 && t.vk);
    /* Non-texture cleanup still executes and resets program stage ownership. */
    reset();Prog program={{{NULL,0}}};
    for(int i=0;i<6;i++){program.st[i].text=malloc(1);assert(program.st[i].text);program.st[i].state=1;}
    g_dead[0].kind=K_PROG;g_dead[0].p=&program;g_dead_n=1;
    nvn_front_take_dead(drop);assert(g_dead_n==0 && dropped==1 && released==0);
    for(int i=0;i<6;i++)assert(!program.st[i].text && !program.st[i].state);
    puts("PASS: native descriptor lifetime, deferred release, list compaction and bounded cleanup.");
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Optional original pinned source; otherwise fetch public upstream")
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.source:
        original = args.source.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            original = response.read().decode("utf-8").replace("\r\n", "\n")
    patched = patched_text(original)
    compiler = shutil.which("gcc")
    if not compiler:
        raise RuntimeError("GCC is required for this development-only native regression check.")
    work = (args.work_dir or Path(tempfile.gettempdir())).resolve()
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="texture-lifetime-check-", dir=work) as temporary:
        root = Path(temporary).resolve()
        if root.parent != work:
            raise RuntimeError("Unexpected temporary directory.")
        code = STUBS + function(patched, "int nvn_front_handle(") + "\n" + function(patched, "void nvn_front_take_dead(") + CASES
        source = root / "check.c"
        source.write_text(code, encoding="utf-8")
        executable = root / "check.exe"
        subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
