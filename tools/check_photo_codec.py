# SPDX-License-Identifier: GPL-3.0-only
"""Verify upstream photo codec provenance and seven-category photo transactions."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "payload"), str(ROOT / "tests")]
from PIL import Image
import zstandard
import mii_import as mi
import photo_import as photos
import photo_texture_codec as texture
import ugc_import as ugc
import save_transfer as saves
from check_ugc_codec import creation
from test_mii_import import fixture, table


def exercise(ugc_source, photo_source, license_path):
    lock = json.loads((ROOT / "tools/upstream-lock.json").read_text(encoding="utf-8"))["photo_texture"]
    for path in (photo_source, license_path):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == lock["sha256"][path.name]
    original = photo_source.read_text(encoding="utf-8")
    core = original[original.index("def div_round_up"):original.index("# ---------------- grouping")].rstrip() + "\n"
    integrated = (ROOT / "payload/photo_texture_codec.py").read_text(encoding="utf-8")
    assert integrated[integrated.index("def div_round_up"):] == core
    assert license_path.read_text(encoding="utf-8") in integrated
    codec = ugc.load_vendor(ugc_source)
    keys = {int(key, 16) for key in re.findall(r'offsetLocator\(playersav,"([0-9A-F]{8})"\)', ugc_source.read_text(encoding="utf-8"))}
    with tempfile.TemporaryDirectory(prefix="photo-codec-check-") as temporary:
        root = Path(temporary)
        save = fixture(root)
        arrays = {key: bytes(299 * 128) for key in keys | set(mi.PAINT) | {0x114EFF89}}
        arrays.update({key: ugc.FREE_FLAGS[1] * 299 for key in ugc.ENABLE})
        (save / "Player.sav").write_bytes(table(arrays))
        models = []
        for kind in range(7):
            seed = creation(kind)
            at = seed.find(b"\xa3" * 4)
            sizes = (262144, 98304 if kind == 0 else 131072, 65536)
            data = seed[:at]
            for marker, size in zip((0xa3, 0xa4, 0xa5), sizes):
                data += bytes((marker,)) * 4 + zstandard.ZstdCompressor().compress(bytes(size))
            path = root / ("model" + ugc.EXTENSIONS[kind])
            path.write_bytes(data)
            models.append({"kind": kind + 1, "slot": 1, "file": str(path)})
        with patch.object(saves, "guard"), patch.object(ugc, "load_vendor", return_value=codec):
            mi.apply_batch(root, models)
        before = saves.inventory(save)
        model_hashes = {key: value for key, value in before.items() if key.startswith("Ugc/")}
        entries = []
        for kind in range(7):
            path = root / (f"photo-{kind}.jpg" if kind % 2 else f"photo-{kind}.png")
            Image.new("RGB", (32, 16), (250, 20, 10)).save(path)
            entries.append({"kind": kind + 1, "slot": 2, "file": str(path), "photo": True, "template": 1, "fit": photos.FITS[kind % 3]})
        progress = []
        with patch.object(saves, "guard"), patch.object(ugc, "load_vendor", return_value=codec):
            result = mi.apply_batch(root, entries, progress=lambda *step: progress.append(step))
        assert result["photos"] == result["creations"] == 7
        assert len(progress) == 7
        assert saves.inventory(Path(result["backup"]) / "save") == before
        after = saves.inventory(save)
        assert all(after[key] == digest for key, digest in model_hashes.items())
        for kind in range(7):
            canvas = ugc.paths(save, 2, kind)[0]
            image, fmt, raw = texture.decode_texture(canvas)
            center = image.getpixel((128, 128))
            assert center[0] > 240 and center[1] < 30 and center[3] == 255
            photos.texture_formats(save, 2, kind)
        stable = saves.inventory(save)
        bad = root / "bad.png"
        bad.write_bytes(b"broken PNG input")
        more = [{**entries[0], "slot": 3}, {**entries[1], "slot": 3, "file": str(bad)}]
        with patch.object(saves, "guard"), patch.object(ugc, "load_vendor", return_value=codec):
            try:
                mi.apply_batch(root, more)
            except Exception:
                assert saves.inventory(save) == stable
            else:
                raise AssertionError("Invalid second photo was committed")
        assert len(list((root / "build/saves/imports").iterdir())) == 2
    print("PASS: MIT codec provenance; JPEG/PNG, three fits, all seven categories, unchanged models, one backup, pixel read-back and invalid-photo rollback.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ugc-source", type=Path)
    parser.add_argument("--photo-source", type=Path)
    args = parser.parse_args()
    if args.ugc_source and args.photo_source:
        exercise(args.ugc_source, args.photo_source, args.photo_source.with_name("LICENSE"))
        return
    lock = json.loads((ROOT / "tools/upstream-lock.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for part, files in (("sharemii", ("ShareUGC.py",)), ("photo_texture", ("tl_ugc_editor.py", "LICENSE"))):
            for name in files:
                url = f'https://raw.githubusercontent.com/{lock[part]["repository"]}/{lock[part]["commit"]}/{name}'
                with urllib.request.urlopen(url, timeout=60) as response:
                    (folder / name).write_bytes(response.read())
        exercise(folder / "ShareUGC.py", folder / "tl_ugc_editor.py", folder / "LICENSE")


if __name__ == "__main__":
    main()
