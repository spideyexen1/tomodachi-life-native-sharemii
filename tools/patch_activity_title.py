# SPDX-License-Identifier: GPL-3.0-only
"""Keep the native game title stable for normal Discord game registration."""
import hashlib
from pathlib import Path
import shutil

SOURCE_SHA256 = "3a7285291dd1f7251a98657aff754e115256a24c46dc1d0f58565d0fe93fbd10"
HEADER = Path(__file__).resolve().parents[1] / "payload/friday_activity_title.h"
MARKER = '#include "friday_activity_title.h"'


def patched_text(original):
    if hashlib.sha256(original.encode("utf-8")).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unsupported display.c: use the documented upstream v1.0.3 source.")
    if original.count('#include "gfx_options.h"') != 1 or original.count('SetWindowTextA(g_hwnd, title);') != 2 or original.count('SetWindowTextA(g_hwnd, t);') != 1:
        raise ValueError("Ambiguous display title patch context.")
    return (original.replace('#include "gfx_options.h"', '#include "gfx_options.h"\n' + MARKER)
            .replace('SetWindowTextA(g_hwnd, title);', 'SetWindowTextA(g_hwnd, friday_activity_title(title));')
            .replace('SetWindowTextA(g_hwnd, t);', 'SetWindowTextA(g_hwnd, friday_activity_title(t));'))


def check_source(port):
    source = port / "runtime/display.c"
    backup = source.with_name("display.upstream.c")
    current = source.read_text(encoding="utf-8")
    original = backup.read_text(encoding="utf-8") if MARKER in current and backup.exists() else current
    expected = patched_text(original)
    if current not in (original, expected):
        raise ValueError("The display source has unrelated edits; no files were changed.")
    if backup.exists() and backup.read_text(encoding="utf-8") != original:
        raise ValueError("The original display source backup differs; it will not be overwritten.")
    return source, backup, original, expected


def apply_patch(port):
    source, backup, original, expected = check_source(port)
    work = port / "build/work"
    if not work.is_dir():
        raise ValueError("Finish the standard upstream build before updating its window title.")
    compiled_source = work / "display.c"
    if compiled_source.exists() and compiled_source.read_text(encoding="utf-8") not in (original, expected):
        raise ValueError("The compiled display source has unrelated edits; no files were changed.")
    if not HEADER.is_file():
        raise ValueError("The activity title header is missing.")
    if not backup.exists():
        shutil.copy2(source, backup)
    source.write_text(expected, encoding="utf-8", newline="\n")
    shutil.copy2(source, compiled_source)
    shutil.copy2(HEADER, port / "runtime" / HEADER.name)
    shutil.copy2(HEADER, work / HEADER.name)
