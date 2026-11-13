# SPDX-License-Identifier: GPL-3.0-only
"""Exercise the actual owning queue buffers without a game or Windows UI."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <new>
static int allocations;
static void *allocate(size_t n) { void *p=malloc(n); assert(p); ++allocations; return p; }
static void release(void *p) { if(p) --allocations; free(p); }
#define IM_ALLOC allocate
#define IM_FREE release
#define IM_ASSERT assert
#define IM_PLACEMENT_NEW(p) new(p)
#include "friday_queue_types.h"
struct Entry { int slot=0; SmWString path; SmString name; };
int main() {
    {
        SmString text="hello"; text+=text; assert(!strcmp(text.c_str(),"hellohello"));
        text=text; assert(text.size()==10);
        assert(!strcmp(("prefix-"+text.substr(5)+"-"+sm_number(70)).c_str(),"prefix-hello-70"));
        SmWString path=L"folder\\file.ltd";
        assert(path.find_last_of(L"\\/")==6);
        assert(!wcscmp(path.substr(7).c_str(),L"file.ltd"));
        SmVector<Entry> queue;
        for(int i=0;i<70;++i) queue.push_back({i+1,L"local folder\\file.ltd",sm_number(i+1)});
        assert(queue.size()==70 && queue[69].slot==70);
        queue.erase(queue.begin()+20); assert(queue.size()==69 && queue[20].slot==22);
        SmVector<Entry> extra; extra.push_back({71,L"other.ltd","extra"});
        queue.insert(queue.end(),extra.begin(),extra.end());
        extra[0].name="changed"; assert(!strcmp(queue[69].name.c_str(),"extra"));
        SmVector<Entry> swapped; queue.swap(swapped);
        assert(queue.empty() && swapped.size()==70);
        swapped.clear(); assert(swapped.empty());
        SmVector<SmString> values;
        for(int i=0;i<8;++i) values.push_back(sm_number(i));
        values.push_back(values[0]); assert(!strcmp(values[8].c_str(),"0"));
        SmVector<unsigned char> bytes(4096,0);
        bytes[4095]=123; bytes.resize(8192);
        assert(bytes[4095]==123 && bytes[8191]==0);
    }
    assert(allocations==0);
    puts("PASS: queue growth, independent copies, aliasing, removal, review and cleanup.");
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    compiler = shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        raise RuntimeError("G++ or Clang++ is required for this development check.")
    work = (args.work_dir or Path(tempfile.gettempdir())).resolve()
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mii-queue-check-", dir=work) as temp:
        source, executable = Path(temp) / "check.cpp", Path(temp) / "check.exe"
        source.write_text(HARNESS, encoding="utf-8")
        subprocess.run([compiler, "-std=c++14", "-Wall", "-Wextra", "-Wno-misleading-indentation", "-fno-exceptions", "-fno-rtti", "-I", str(ROOT / "payload"), str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
