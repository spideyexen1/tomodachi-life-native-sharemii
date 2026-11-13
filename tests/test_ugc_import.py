# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "payload"), str(ROOT / "tools")]
import mii_import as mi
import ugc_import as ugc
from check_ugc_codec import creation


class UgcInputs(unittest.TestCase):
    def test_all_seven_headers_and_three_compressed_blocks(self):
        for kind in range(7):
            with self.subTest(kind=kind):
                name, blocks = ugc.parse(creation(kind), kind)
                self.assertEqual(len(blocks), 3)
                self.assertGreater(name, 20)

    def test_wrong_category_and_truncation(self):
        with self.assertRaisesRegex(ValueError, "category"):
            ugc.parse(creation(0), 5)
        for kind in range(7):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                ugc.parse(creation(kind)[:100], kind)

    def test_broken_texture_markers_and_compression(self):
        data = creation(5)
        with self.assertRaisesRegex(ValueError, "textures"):
            ugc.parse(data.replace(b"\xa4" * 4, bytes(4)), 5)
        with self.assertRaises(Exception):
            ugc.parse(data[:-10], 5)
        # A valid compressed prefix followed by truncation must also fail.
        import zstandard
        payload = zstandard.ZstdCompressor().compress(b"a" * 10000)
        with self.assertRaises(ValueError):
            mi.validate_paint(payload[:5])

    def test_mixed_categories_allow_same_slot_but_not_duplicate_category(self):
        entries = [{"kind": kind + 1, "slot": 1, "file": "item" + extension}
                   for kind, extension in enumerate(ugc.EXTENSIONS)]
        mi.check_entries(entries)
        with self.assertRaisesRegex(ValueError, "different destination"):
            mi.check_entries(entries + [entries[0]])
        with self.assertRaisesRegex(ValueError, "matching its category"):
            mi.check_entries([{"kind": 5, "slot": 1, "file": "item.ltdo"}])

    def test_clothing_vendor_byte_limit_and_bad_kind(self):
        mi.check_entries([{"kind": 2, "slot": 256, "file": "clothing.ltdc"}])
        for entry in ({"kind": 2, "slot": 257, "file": "clothing.ltdc"},
                      {"kind": 8, "slot": 1, "file": "item.ltdo"}):
            with self.assertRaises(ValueError):
                mi.check_entries([entry])

    def test_modified_vendor_is_not_executed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ShareUGC.py"
            path.write_text("raise RuntimeError('never execute')")
            with self.assertRaisesRegex(ValueError, "verification failed"):
                ugc.load_vendor(path)


if __name__ == "__main__":
    unittest.main()
