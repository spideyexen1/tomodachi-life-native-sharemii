# SPDX-License-Identifier: GPL-3.0-only
"""Smoke-test the patch against pinned public upstream source, without a game dump."""
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

from patch_menu import apply_patch, check_source, MARKER
import patch_texture_lifetime as textures
import patch_activity_title as activity

ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = json.loads((ROOT / "tools" / "upstream-lock.json").read_text())
    port = lock["port"]
    base = f'https://raw.githubusercontent.com/{port["repository"]}/{port["commit"]}/'
    with urllib.request.urlopen(base + "runtime/menu.cpp", timeout=60) as response:
        menu = response.read()
    with urllib.request.urlopen(base + "runtime/nvn_gl.c", timeout=60) as response:
        renderer = response.read()
    with urllib.request.urlopen(base + "runtime/display.c", timeout=60) as response:
        display = response.read()
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        (target / "runtime").mkdir()
        (target / "build" / "work").mkdir(parents=True)
        source = target / "runtime" / "menu.cpp"
        source.write_bytes(menu)
        check_source(target)
        apply_patch(target, ROOT / "payload" / "friday_sharemii.h")
        first = source.read_bytes()
        assert first.count(MARKER.encode()) == 1
        assert b"case T_SHARE: sm_open();" in first
        assert b"sm_draw(dl," in first
        apply_patch(target, ROOT / "payload" / "friday_sharemii.h")
        assert source.read_bytes() == first, "Patch is not idempotent"
        assert (target / "runtime" / "menu.upstream.cpp").read_bytes() == menu
        source.write_text(source.read_text() + "\n// unrelated custom edit\n")
        before = source.read_bytes()
        try:
            apply_patch(target, ROOT / "payload" / "friday_sharemii.h")
        except ValueError:
            assert source.read_bytes() == before, "Refused patch changed the source"
        else:
            raise AssertionError("Unrelated edits were overwritten")
        renderer_source = target / "runtime" / "nvn_gl.c"
        renderer_source.write_bytes(renderer)
        textures.apply_patch(target)
        first = renderer_source.read_bytes()
        assert first.count(textures.MARKER.encode()) == 1
        assert (target / "build" / "work" / "nvn_gl.c").read_bytes() == first
        assert (target / "runtime" / "nvn_gl.upstream.c").read_bytes() == renderer
        textures.apply_patch(target)
        assert renderer_source.read_bytes() == first, "Renderer patch is not idempotent"
        # Upgrade an existing 0.3.2 patch without accepting arbitrary edits.
        legacy = textures.patched_text(renderer.decode("utf-8").replace("\r\n", "\n"), lifetime_only=True)
        renderer_source.write_text(legacy, encoding="utf-8")
        (target / "build" / "work" / "nvn_gl.c").write_text(legacy, encoding="utf-8")
        textures.apply_patch(target)
        assert renderer_source.read_bytes() == first, "Legacy renderer upgrade differs"
        renderer_source.write_bytes(first + b"\n// unrelated renderer edit\n")
        before = renderer_source.read_bytes()
        try:
            textures.apply_patch(target)
        except ValueError:
            assert renderer_source.read_bytes() == before
        else:
            raise AssertionError("Unrelated renderer edits were overwritten")
        display_source = target / "runtime/display.c"
        display_source.write_bytes(display)
        activity.apply_patch(target)
        title_patch = display_source.read_text(encoding="utf-8")
        assert title_patch.count(activity.MARKER) == 1
        assert title_patch.count("friday_activity_title(title)") == 2
        assert title_patch.count("friday_activity_title(t)") == 1
        assert (target / "runtime/display.upstream.c").read_bytes() == display
        assert (target / "build/work/display.c").read_text(encoding="utf-8") == title_patch
        assert (target / "build/work/friday_activity_title.h").read_bytes() == activity.HEADER.read_bytes()
        activity.apply_patch(target)
        assert display_source.read_text(encoding="utf-8") == title_patch
        display_source.write_text(title_patch + "\n// unrelated display edit\n", encoding="utf-8")
        before = display_source.read_bytes()
        try:
            activity.apply_patch(target)
        except ValueError:
            assert display_source.read_bytes() == before
        else:
            raise AssertionError("Unrelated display edits were overwritten")
        display_source.write_text(title_patch, encoding="utf-8")
        work_display = target / "build/work/display.c"
        work_display.write_text(title_patch + "\n// unrelated compiled display edit\n", encoding="utf-8")
        try:
            activity.apply_patch(target)
        except ValueError:
            assert display_source.read_text(encoding="utf-8") == title_patch
            assert "unrelated compiled display edit" in work_display.read_text(encoding="utf-8")
        else:
            raise AssertionError("Unrelated work display edits were overwritten")
    for relative, expected in port["source_sha256"].items():
        with urllib.request.urlopen(base + relative, timeout=60) as response:
            data = response.read().decode("utf-8").replace("\r\n", "\n").encode()
        assert hashlib.sha256(data).hexdigest() == expected, relative
    share = lock["sharemii"]
    share_base = f'https://raw.githubusercontent.com/{share["repository"]}/{share["commit"]}/'
    for name, expected in share["sha256"].items():
        with urllib.request.urlopen(share_base + name, timeout=60) as response:
            data = response.read()
        assert hashlib.sha256(data).hexdigest() == expected, name
    print("PASS: pinned upstream sources match; menu/renderer/activity-title patches apply, are idempotent and refuse other edits.")


if __name__ == "__main__":
    main()
