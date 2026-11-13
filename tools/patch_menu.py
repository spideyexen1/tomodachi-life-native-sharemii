# SPDX-License-Identifier: GPL-3.0-only
"""Apply the F1-menu integration to the explicitly supported upstream source."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

MENU_SHA256 = "1ac8884362aec90628b39d7cb0536dca941b4cf5092927b5655666335c856312"
MARKER = '#include "friday_sharemii.h"'
EDITS = (
    ("T_MOUSE, T_SAVE, T_QUIT, T_N", "T_MOUSE, T_SAVE, T_SHARE, T_QUIT, T_N"),
    ('"Mouse controls", "Save now", "Quit to desktop"', '"Mouse controls", "Save now", "ShareMii - Mii e oggetti", "Quit to desktop"'),
    ("static void tc_open(void);", "static void sm_open(void);\nstatic void sm_act(int a);\nstatic void tc_open(void);"),
    ("case T_CTRL: tc_open(); return;", "case T_CTRL: tc_open(); return;\n    case T_SHARE: sm_open(); return;"),
    ("if (g_t_page == 1) { tc_act(a); return; }", "if (g_t_page == 1) { tc_act(a); return; }\n    if (g_t_page == 2) { sm_act(a); return; }"),
    ("g_t_sel != T_CTRL && g_t_sel != T_SAVE", "g_t_sel != T_CTRL && g_t_sel != T_SAVE && g_t_sel != T_SHARE"),
    ("static void draw_tomo(void) {", MARKER + "\n\nstatic void draw_tomo(void) {"),
    ('g_t_page == 1 ? "Controls" : "PC Settings"', 'g_t_page == 2 ? "ShareMii" : g_t_page == 1 ? "Controls" : "PC Settings"'),
    ("g_t_page == 1 ? 10 : shown_rows", "g_t_page == 2 ? 6 : g_t_page == 1 ? 10 : shown_rows"),
    ("    const float fy = by + 1010.0f * u;", "    if (g_t_page == 2) sm_draw(dl, bx, bw, rx, ry0, rw, pitch, rh, u, in, t, m, moved, click);\n    const float fy = by + 1010.0f * u;"),
)


def normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def patched_text(original: str) -> str:
    if hashlib.sha256(original.encode("utf-8")).hexdigest() != MENU_SHA256:
        raise ValueError("Unsupported menu.cpp: use the documented upstream v1.0.3 source.")
    result = original
    for before, after in EDITS:
        count = result.count(before)
        if count != 1:
            raise ValueError(f"Patch context is ambiguous ({count} occurrences): {before}")
        result = result.replace(before, after)
    return result


def check_source(port: Path) -> tuple[Path, Path, str, str]:
    source = port / "runtime" / "menu.cpp"
    backup = source.with_suffix(".upstream.cpp")
    current = normalized(source)
    original = normalized(backup) if MARKER in current else current
    expected = patched_text(original)
    if current not in (original, expected):
        raise ValueError("The menu contains other edits. Merge them manually instead of overwriting them.")
    if backup.exists() and normalized(backup) != original:
        raise ValueError("The upstream source backup differs; it will not be overwritten.")
    return source, backup, original, expected


def apply_patch(port: Path, header: Path) -> None:
    source, backup, original, expected = check_source(port)
    if not (port / "build" / "work").is_dir():
        raise ValueError("A built upstream installation with build/work is required.")
    if not header.is_file():
        raise ValueError("Integration header is missing.")
    queue_header = header.with_name("friday_mii_queue.h")
    types_header = header.with_name("friday_queue_types.h")
    if not queue_header.is_file() or not types_header.is_file():
        raise ValueError("Mii queue header is missing.")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8", newline="\n")
    source.write_text(expected, encoding="utf-8", newline="\n")
    shutil.copy2(header, port / "runtime" / header.name)
    shutil.copy2(queue_header, port / "runtime" / queue_header.name)
    shutil.copy2(types_header, port / "runtime" / types_header.name)
    for name in ("menu.cpp", header.name, queue_header.name, types_header.name):
        shutil.copy2(port / "runtime" / name, port / "build" / "work" / name)
