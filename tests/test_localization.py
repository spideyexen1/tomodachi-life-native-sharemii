# SPDX-License-Identifier: GPL-3.0-only
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Localizations(unittest.TestCase):
    def test_every_setup_message_has_all_four_additional_translations(self):
        source = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "setup").glob("*.cs"))
        pairs = re.findall(r'T\("((?:\\.|[^"\\])*)",\s*"((?:\\.|[^"\\])*)"\)', source)
        keys = {json.loads('"' + en + '"') for it, en in pairs}
        self.assertGreater(len(keys), 70)
        for code in ("de", "es", "fr", "pt"):
            catalog = json.loads((ROOT / "payload" / "locales" / (code + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(set(catalog), keys, code)
            self.assertTrue(all(isinstance(value, str) and value.strip() for value in catalog.values()), code)
