# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "payload"))
import mii_import as mi
import save_transfer as saves


def table(fields):
    heap = 32 + len(fields) * 8
    out = bytearray(heap)
    struct.pack_into("<III", out, 0, 0x01020304, 1, heap)
    for index, (key, payload) in enumerate(fields.items()):
        struct.pack_into("<II", out, 32 + index * 8, key, len(out))
        out += struct.pack("<I", len(payload)) + payload
    return out


def fixture(root):
    (root / "build/userdata/save").mkdir(parents=True)
    (root / "integration").mkdir()
    (root / "build/state.json").write_text(json.dumps({"game_version": "1.0.4"}))
    raw = bytearray()
    for index in range(70):
        record = bytearray(struct.pack("<I", 152) + bytes(152))
        if index < 2:
            record[8] = index + 1
        raw += record
    fields = {0x881CA27A: raw, 0x2499BFDA: bytes(70 * 64), 0x3A5EDA05: bytes(70 * 128),
              0x5E32ADF4: b"\xff" * (70 * 4), 0xDFC82223: bytes(27), 0x9999B7D9: bytes(70 * 4)}
    fields.update({key: bytes(70 * 4) for key in mi.PERSONAL})
    save = root / "build/userdata/save"
    (save / "Mii.sav").write_bytes(table(fields))
    (save / "Player.sav").write_bytes(table({**{key: bytes(71 * 4) for key in mi.PAINT}, 0x114EFF89: bytes(152)}))
    (save / "Map.sav").write_bytes(b"synthetic island map - no game content")
    (save / "Ugc").mkdir()
    (save / "Ugc/unrelated.txt").write_bytes(b"existing user creation")
    return save


def mii(path, name, marker):
    data = bytearray(436)
    data[0] = 3
    struct.pack_into("<I", data, 4, 152)
    data[12] = marker
    data[232:296] = name.encode("utf-16-le").ljust(64, b"\0")
    data[296:424] = name.encode("utf-16-le").ljust(128, b"\0")
    data[428:432], data[432:436] = b"\xa3" * 4, b"\xa4" * 4
    path.write_bytes(data)
    return path


def synthetic_import(mode, slot, save, source, backup):
    assert mode == "Import" and backup is False
    target = Path(save) / "Mii.sav"
    data, incoming = bytearray(target.read_bytes()), Path(source).read_bytes()
    fields = mi.fields(data)
    raw = fields[0x881CA27A] + 4 + (slot - 1) * 156
    name = fields[0x2499BFDA] + 4 + (slot - 1) * 64
    data[raw:raw + 156], data[name:name + 64] = incoming[4:160], incoming[232:296]
    target.write_bytes(data)


class MiiBatch(unittest.TestCase):
    def setUp(self):
        # Process exclusion is tested separately in the save-transfer suite.
        guard = patch.object(saves, "guard")
        guard.start()
        self.addCleanup(guard.stop)

    def test_two_miis_commit_together_with_one_exact_previous_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = fixture(root)
            before = saves.inventory(save)
            one, two = mii(root / "one.ltd", "One", 11), mii(root / "two.ltd", "Two", 22)
            result = mi.apply_batch(root, [{"slot": 1, "file": str(one)}, {"slot": 2, "file": str(two)}], synthetic_import)
            self.assertEqual(result["miis"], 2)
            self.assertEqual(saves.inventory(Path(result["backup"]) / "save"), before)
            self.assertEqual(len(list((root / "build/saves/imports").iterdir())), 1)
            self.assertEqual((save / "Ugc/unrelated.txt").read_bytes(), b"existing user creation")
            data = (save / "Mii.sav").read_bytes()
            start = mi.fields(data)[0x2499BFDA] + 4
            self.assertEqual(data[start:start + 64].decode("utf-16-le").split("\0")[0], "One")
            self.assertEqual(data[start + 64:start + 128].decode("utf-16-le").split("\0")[0], "Two")

    def test_failure_on_second_mii_never_changes_the_active_save(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = fixture(root)
            before = saves.inventory(save)
            one, two = mii(root / "one.ltd", "One", 11), mii(root / "two.ltd", "Two", 22)
            def failing(mode, slot, folder, source, backup):
                synthetic_import(mode, slot, folder, source, backup)
                if slot == 2:
                    raise RuntimeError("simulated second-file failure")
            with self.assertRaisesRegex(RuntimeError, "second-file"):
                mi.apply_batch(root, [{"slot": 1, "file": str(one)}, {"slot": 2, "file": str(two)}], failing)
            self.assertEqual(saves.inventory(save), before)
            self.assertFalse((root / "build/userdata/.save-import.pending.json").exists())

    def test_all_inputs_are_checked_before_the_first_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = fixture(root)
            before = saves.inventory(save)
            one = mii(root / "one.ltd", "One", 11)
            bad = root / "bad.ltd"
            bad.write_bytes(b"\x03broken")
            calls = []
            with self.assertRaisesRegex(ValueError, "truncated"):
                mi.apply_batch(root, [{"slot": 1, "file": str(one)}, {"slot": 2, "file": str(bad)}], lambda *args: calls.append(args))
            self.assertEqual(calls, [])
            self.assertEqual(saves.inventory(save), before)

    def test_duplicate_destination_and_empty_resident_are_refused(self):
        with self.assertRaisesRegex(ValueError, "different destination"):
            mi.check_entries([{"slot": 1, "file": "one.ltd"}, {"slot": 1, "file": "two.ltd"}])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = fixture(root)
            with self.assertRaisesRegex(ValueError, "empty"):
                mi.validate_save(save, [3])

    def test_no_op_or_wrong_slot_import_fails_read_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = fixture(root)
            before = saves.inventory(save)
            source = mii(root / "one.ltd", "One", 11)
            with self.assertRaisesRegex(ValueError, "read-back"):
                mi.apply_batch(root, [{"slot": 1, "file": str(source)}], lambda *args: None)
            self.assertEqual(saves.inventory(save), before)

    def test_truncated_legacy_and_incomplete_paint_are_rejected(self):
        for data in (b"\x01", b"\x02" + bytes(100), b"\x03" + bytes(100)):
            with self.assertRaisesRegex(ValueError, "truncated"):
                mi.validate_mii(data, {})
        with tempfile.TemporaryDirectory() as temp:
            source = mii(Path(temp) / "one.ltd", "One", 11)
            data = bytearray(source.read_bytes())
            data[1:3] = b"\1\1"
            with self.assertRaisesRegex(ValueError, "paint is truncated"):
                mi.validate_mii(data, {})

    def test_modified_vendor_source_is_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "ShareMii.py"
            source.write_text("raise RuntimeError('must not execute')")
            with self.assertRaisesRegex(ValueError, "verification failed"):
                mi.load_vendor(source)


if __name__ == "__main__":
    unittest.main()
