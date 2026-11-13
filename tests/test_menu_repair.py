# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import menu_config
import repair_menu


class MenuRepair(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = Path(self.temp.name)
        self.config = self.port / "build" / "config" / "graphics.ini"
        self.config.parent.mkdir(parents=True)

    def test_backups_exact_original_and_preserves_other_options(self):
        original = b"; GPU settings\r\nrenderer = auto\r\nmenu = off\r\nlanguage = it\r\nwidth = 1600\r\nvolume = 30\r\n"
        self.config.write_bytes(original)
        result = menu_config.configure(self.port)
        self.assertTrue(result["changed"])
        self.assertEqual(Path(result["backup"]).read_bytes(), original)
        self.assertEqual(self.config.read_bytes(), original.replace(b"renderer = auto", b"renderer = always_vulkan").replace(b"menu = off", b"menu = on"))

    def test_second_application_is_idempotent_and_creates_no_extra_backup(self):
        self.config.write_bytes(b"renderer = auto\n")
        menu_config.configure(self.port)
        second = menu_config.configure(self.port)
        self.assertFalse(second["changed"])
        self.assertIsNone(second["backup"])
        self.assertEqual(len(list(self.config.parent.glob("*.menu-backup-*"))), 1)

    def test_opengl_profiles_use_direct_window_presentation(self):
        for renderer in ("auto", "opengl"):
            original = b"renderer=always_vulkan\npresent_api=dxgi\nwindow=fullscreen\nvolume=50\nlanguage=it\n"
            self.config.write_bytes(original)
            result = menu_config.configure(self.port, renderer)
            self.assertEqual(Path(result["backup"]).read_bytes(), original)
            values = dict(line.split(b"=", 1) for line in self.config.read_bytes().splitlines())
            self.assertEqual(values[b"renderer"], renderer.encode())
            self.assertEqual(values[b"present_api"], b"opengl")
            self.assertEqual(values[b"window"], b"windowed")
            self.assertEqual(values[b"volume"], b"50")
            self.assertEqual(values[b"language"], b"it")
            self.assertFalse(menu_config.configure(self.port, renderer)["changed"])

    def test_unknown_profile_cannot_modify_settings(self):
        self.config.write_bytes(b"renderer=auto\n")
        with self.assertRaises(ValueError):
            menu_config.configure(self.port, "unknown")
        self.assertEqual(self.config.read_bytes(), b"renderer=auto\n")

    def test_duplicate_case_insensitive_keys_are_all_replaced(self):
        self.config.write_bytes(b"Renderer=gl\nrenderer=auto\nMENU=off\nmenu=off\n")
        menu_config.configure(self.port)
        self.assertEqual(self.config.read_bytes(), b"Renderer=always_vulkan\nrenderer=always_vulkan\nMENU=on\nmenu=on\n")

    def test_bom_and_inline_comments_do_not_break_upstream_parser(self):
        self.config.write_bytes(b"\xef\xbb\xbfrenderer = gl ; old choice\r\nmenu = off # disabled\r\n; unrelated \xff\r\n")
        menu_config.configure(self.port)
        # Match upstream's parser: it trims whitespace, not BOMs or inline comments.
        values = {}
        for line in self.config.read_bytes().splitlines():
            line = line.strip()
            if b"=" in line and not line.startswith((b";", b"#", b"[")):
                key, value = line.split(b"=", 1)
                values[key.strip()] = value.strip()
        self.assertEqual(values[b"renderer"], b"always_vulkan")
        self.assertEqual(values[b"menu"], b"on")
        self.assertIn(b"; old choice", self.config.read_bytes())
        self.assertIn(b"; unrelated \xff", self.config.read_bytes())
        self.assertFalse(menu_config.configure(self.port)["changed"])

    def test_new_config_contains_complete_runtime_values(self):
        result = menu_config.configure(self.port)
        self.assertIsNone(result["backup"])
        self.assertEqual(self.config.read_bytes(), b"renderer = always_vulkan\nmenu = on\n")

    def test_atomic_replace_failure_leaves_original_and_backup_intact(self):
        original = b"renderer = gl\nmenu = off\n"
        self.config.write_bytes(original)
        with patch.object(Path, "replace", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                menu_config.configure(self.port)
        self.assertEqual(self.config.read_bytes(), original)
        self.assertEqual(next(self.config.parent.glob("*.menu-backup-*")).read_bytes(), original)
        self.assertFalse(list(self.config.parent.glob("*.tmp")))

    def test_running_game_refuses_repair_before_writing(self):
        self.config.write_bytes(b"renderer=auto\n")
        with patch.object(repair_menu.integration, "validate_port"), patch.object(repair_menu.integration, "refuse_running_game", side_effect=ValueError("Close the native game")):
            with self.assertRaisesRegex(ValueError, "Close"):
                repair_menu.repair(self.port)
        self.assertEqual(self.config.read_bytes(), b"renderer=auto\n")

    def test_repair_requires_no_compiler_or_download(self):
        with patch.object(repair_menu.integration, "validate_port"), patch.object(repair_menu.integration, "refuse_running_game"), patch.object(repair_menu.integration, "require_python_and_compiler", side_effect=AssertionError("No compiler needed")), patch.object(repair_menu.integration, "fetch_build_dependencies", side_effect=AssertionError("No downloads needed")):
            self.assertTrue(repair_menu.repair(self.port)["changed"])
