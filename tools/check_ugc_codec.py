# SPDX-License-Identifier: GPL-3.0-only
"""Exercise pinned GPL ShareUGC with synthetic saves, never game assets."""
import argparse
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "payload"), str(ROOT / "tests")]
import mii_import as mi
import ugc_import as ugc
import save_transfer as saves
from test_mii_import import fixture, table, mii, synthetic_import


def creation(kind):
    import zstandard
    attrs = bytearray(ugc.COUNTS[kind] * 4)
    # Nonzero values test offsets and packed flags independently.
    for index in range(ugc.COUNTS[kind]):
        attrs[index * 4] = 1 if index == ugc.NIGHT[kind] else index + 2
    if kind == 4:
        attrs[12:16] = attrs[8:12]  # pinned exterior codec uses the same field twice
    name = ("Synthetic " + ugc.TYPES[kind]).encode("utf-16-le").ljust(128, b"\0")
    names = name + name
    if kind == 2:
        names += "Text".encode("utf-16-le").ljust(64, b"\0") + name
    compress = zstandard.ZstdCompressor().compress
    return (bytes((kind, 0, 0, 0)) + attrs + bytes(range(20)) + b"\xa2" * 4 + names +
            b"\xa3" * 4 + compress(b"synthetic canvas") + b"\xa4" * 4 +
            compress(b"synthetic texture") + b"\xa5" * 4 + compress(b"synthetic thumbnail"))


def exercise(source):
    codec = ugc.load_vendor(source)
    # Allocate large, zeroed synthetic arrays for every hash the pinned codec
    # references. These are format fixtures, not extracted save/game data.
    keys = {int(key, 16) for key in re.findall(r'offsetLocator\(playersav,"([0-9A-F]{8})"\)', source.read_text(encoding="utf-8"))}
    with tempfile.TemporaryDirectory(prefix="shareugc-check-") as temporary:
        root = Path(temporary)
        save = fixture(root)
        (save / "Ugc/unrelated.txt").unlink()
        arrays = {key: bytes(299 * 128) for key in keys | set(mi.PAINT) | {0x114EFF89}}
        arrays.update({key: ugc.FREE_FLAGS[1] * 299 for key in ugc.ENABLE})
        original = table(arrays)
        (save / "Player.sav").write_bytes(original)
        entries = []
        for kind in range(7):
            file = root / ("creation" + ugc.EXTENSIONS[kind])
            file.write_bytes(creation(kind))
            # Include the largest safe clothing index: tests packed flags,
            # three-digit filenames and the vendor's one-byte slot limit.
            entries.append({"kind": kind + 1, "slot": 256 if kind == 1 else 1, "file": str(file)})
        incoming = mii(root / "resident.ltd", "Synthetic resident", 11)
        mixed = [{"slot": 1, "file": str(incoming)}] + entries
        before = saves.inventory(save)
        with patch.object(saves, "guard"), patch.object(ugc, "load_vendor", return_value=codec):
            result = mi.apply_batch(root, mixed, synthetic_import)
        assert result["creations"] == 8 and result["miis"] == 1
        assert saves.inventory(Path(result["backup"]) / "save") == before
        assert len(list((root / "build/saves/imports").iterdir())) == 1
        assert len(list((save / "Ugc").glob("*.zs"))) == 21
        for entry in entries:
            ugc.verify(codec, save, entry["slot"], entry["kind"] - 1, Path(entry["file"]).read_bytes())
            try:
                ugc.preflight(codec, save, entry["slot"], entry["kind"] - 1, Path(entry["file"]).read_bytes())
            except ValueError as error:
                assert "occupied" in str(error)
            else:
                raise AssertionError("Occupied creation slot accepted")
        # Start again to exercise the last-file failure after real UGC writes.
        saves_before_failure = saves.inventory(save)
        more = [{**entry, "slot": 2} for entry in entries]
        calls = []
        def failing(*args):
            calls.append(args[5])
            codec(*args)
            if args[5] == 6:
                raise RuntimeError("synthetic last-item failure")
        with patch.object(saves, "guard"), patch.object(ugc, "load_vendor", return_value=failing), patch.object(ugc, "schema", side_effect=lambda _, *args: original_schema(codec, *args)):
            try:
                mi.apply_batch(root, more)
            except RuntimeError as error:
                assert "last-item failure" in str(error)
            else:
                raise AssertionError("Failed batch was committed")
        assert calls == list(range(7))
        assert saves.inventory(save) == saves_before_failure
        assert len(list((root / "build/saves/imports").iterdir())) == 1
    print("PASS: original ShareUGC, all seven categories + Mii in one transaction; read-back, occupied slots, clothing boundary, last-file rollback.")


original_schema = ugc.schema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.source:
        exercise(args.source)
    else:
        import json
        lock = json.loads((ROOT / "tools/upstream-lock.json").read_text(encoding="utf-8"))["sharemii"]
        url = f'https://raw.githubusercontent.com/{lock["repository"]}/{lock["commit"]}/ShareUGC.py'
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "ShareUGC.py"
            with urllib.request.urlopen(url, timeout=60) as response:
                source.write_bytes(response.read())
            exercise(source)


if __name__ == "__main__":
    main()
