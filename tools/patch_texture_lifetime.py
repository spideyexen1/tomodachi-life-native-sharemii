# SPDX-License-Identifier: GPL-3.0-only
"""Retain finalized Vulkan textures still referenced by queued descriptors.

Matches the supported upstream OpenGL backend's bounded lifetime policy.
No game code or assets are patched.
"""
import hashlib
from pathlib import Path
import shutil

SOURCE_SHA256 = "4cea39a44c617fad77ce4a1cff19fa0a858d0e5b2333ce38ff039e649d8917de"
MARKER = "Local Vulkan texture-lifetime fix, matching handle_make/gl_housekeeping:"

LIFETIME_EDITS = (('int nvn_front_tex_changed(Tex *t) {\n    Fmt f;',
  'int nvn_front_tex_changed(Tex *t) {\n'
  '    /* Retired Vulkan images retain their last texels; guest memory may be reused. */\n'
  '    if (t->dead) return 0;\n'
  '    Fmt f;'),
 ('    if (*t && !(*t)->dead) r |= 1; else *t = NULL;',
  '    /* Local Vulkan texture-lifetime fix, matching handle_make/gl_housekeeping:\n'
  '     * descriptors can still name finalized textures. Reuse only an existing GPU\n'
  '     * image; never recreate it from guest memory after finalization. */\n'
  '    if (*t && (!(*t)->dead || (*t)->vk)) {\n'
  '        (*t)->last_bind = g_st.frames;\n'
  '        r |= 1;\n'
  '        if ((*t)->dead) {\n'
  '            static unsigned retained_samples;\n'
  '            if (retained_samples++ < 6) {\n'
  '                printf("sharemii: retained Vulkan texture sampled: %dx%d, retired %lld frames '
  'ago\\n", (*t)->b.width, (*t)->b.height, (long long)(g_st.frames - (*t)->dead_frame));\n'
  '                fflush(stdout);\n'
  '            }\n'
  '        }\n'
  '    } else *t = NULL;'),
 ('void nvn_front_take_dead(void (*drop)(int kind, void *host)) {\n'
  '    if (!g_dead_n) return;\n'
  '    EnterCriticalSection(&g_dead_lock);\n'
  '    for (int i = 0; i < g_dead_n; i++) {\n'
  '        drop(g_dead[i].kind, g_dead[i].p);',
  'void nvn_front_take_dead(void (*drop)(int kind, void *host)) {\n'
  '    if (!g_dead_n) return;\n'
  '    EnterCriticalSection(&g_dead_lock);\n'
  '    int kept = 0;\n'
  '    for (int i = 0; i < g_dead_n; i++) {\n'
  '        /* Same bounded retention as the GL backend. vk_drop still performs its\n'
  '         * existing GPU-fence retirement once pool references/draws expire. */\n'
  '        if (g_dead[i].kind == K_TEX) {\n'
  '            Tex *dt = g_dead[i].p;\n'
  '            if (dt->vk && dt->pool_refs > 0 && dt->last_bind >= g_st.frames - 2 && g_st.frames '
  '- dt->dead_frame < 300) {\n'
  '                g_dead[kept++] = g_dead[i];\n'
  '                continue;\n'
  '            }\n'
  '        }\n'
  '        drop(g_dead[i].kind, g_dead[i].p);'),
 ('    g_dead_n = 0;\n    LeaveCriticalSection(&g_dead_lock);\n}\nvoid nvn_front_count',
  '    g_dead_n = kept;\n    LeaveCriticalSection(&g_dead_lock);\n}\nvoid nvn_front_count'))

GL_MASK = '''/* Local OpenGL output-mask fix: a bound attachment without a fragment
 * output must not receive undefined values, especially when two attachments
 * alias the same shadow texture. The same header drives mx_translate.c. */
static uint32_t shader_chanmask(uint32_t channels, const Stage *fs, int depth_only) {
    if (depth_only) return 0;
    if (!fs || !fs->code || fs->code_len < 0x50) return channels;
    uint32_t outputs;
    memcpy(&outputs, fs->code + 0x48, sizeof outputs);
    for (unsigned i = 0; i < 8; i++)
        if (!((outputs >> (i * 4)) & 15)) channels &= ~(15u << (i * 4));
    return channels;
}
static void apply_draw_chanmask(void) {
    uint32_t channels = shader_chanmask(S.chanmask, S.prog[1] ? &S.prog[1]->st[1] : NULL, S.prog[0] && !S.prog[1]);
    for (unsigned i = 0; i < 8; i++) {
        unsigned m = channels >> (i * 4);
        glColorMaski(i, m & 1, (m >> 1) & 1, (m >> 2) & 1, (m >> 3) & 1);
    }
}

'''
GL_EDITS = (
    ('/* Feedback guard: a draw that samples,', GL_MASK + '/* Feedback guard: a draw that samples,'),
    ('    apply_stencil();\n    if (g_ncrange)', '    apply_stencil();\n    apply_draw_chanmask();\n    if (g_ncrange)'),
)
EDITS = LIFETIME_EDITS + GL_EDITS

def normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def patched_text(original: str, *, lifetime_only: bool = False) -> str:
    if hashlib.sha256(original.encode("utf-8")).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unsupported nvn_gl.c: use upstream port v1.0.3 source.")
    result = original
    for before, after in LIFETIME_EDITS if lifetime_only else EDITS:
        if result.count(before) != 1:
            raise ValueError("Texture-lifetime patch context is ambiguous.")
        result = result.replace(before, after)
    return result


def check_source(port: Path) -> tuple[Path, Path, Path, str, str]:
    source = port / "runtime" / "nvn_gl.c"
    backup = source.with_name("nvn_gl.upstream.c")
    # Accept the exact, previously verified local candidate without losing its backup.
    legacy = source.with_name("nvn_gl.before-texture-lifetime-fix.c")
    original_file = backup if backup.exists() else legacy if legacy.exists() else source
    current = normalized(source)
    original = normalized(original_file) if MARKER in current else current
    expected = patched_text(original)
    legacy_expected = patched_text(original, lifetime_only=True)
    if current not in (original, legacy_expected, expected):
        raise ValueError("The renderer has unrelated edits; refusing to overwrite them.")
    if backup.exists() and normalized(backup) != original:
        raise ValueError("The original renderer backup differs; it will not be overwritten.")
    return source, backup, original_file, original, expected


def apply_patch(port: Path) -> None:
    source, backup, original_file, original, expected = check_source(port)
    work = port / "build" / "work" / "nvn_gl.c"
    if not work.parent.is_dir():
        raise ValueError("Build the standard port before applying the renderer patch.")
    if work.exists() and normalized(work) not in (original, patched_text(original, lifetime_only=True), expected):
        raise ValueError("The compiled renderer source has unrelated edits; no files changed.")
    if not backup.exists():
        shutil.copy2(original_file, backup)
    if normalized(source) != expected:
        source.write_text(expected, encoding="utf-8", newline="\n")
    shutil.copy2(source, work)
