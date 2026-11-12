# SPDX-License-Identifier: GPL-3.0-only
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import setup_backend as backend


class ToolArchives(unittest.TestCase):
    def archive(self, folder, entries):
        path = folder / "tools.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        return path

    def test_extracts_tools_and_preserves_identical_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            port = root / "port"
            archive = self.archive(root, {"Package/scripts/example.py": "print('tool')", "Package/version.txt": "1.0.3"})
            backend.extract_tools(archive, port, "Package")
            first = (port / "scripts" / "example.py").read_bytes()
            backend.extract_tools(archive, port, "Package")
            self.assertEqual((port / "scripts" / "example.py").read_bytes(), first)

    def test_rejects_traversal_before_writing_any_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.archive(root, {"Package/good.txt": "tool", "Package/../../escaped.txt": "bad"})
            with self.assertRaises(ValueError):
                backend.extract_tools(archive, root / "port", "Package")
            self.assertFalse((root / "port" / "good.txt").exists())
            self.assertFalse((root / "escaped.txt").exists())

    def test_refuses_game_data_in_tools_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.archive(root, {"Package/example.sav": "synthetic fixture"})
            with self.assertRaisesRegex(ValueError, "game data"):
                backend.extract_tools(archive, root / "port", "Package")

    def test_refuses_conflicts_without_overwriting_user_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            port = root / "port"
            port.mkdir()
            (port / "version.txt").write_text("user file")
            archive = self.archive(root, {"Package/new.txt": "tool", "Package/version.txt": "different"})
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                backend.extract_tools(archive, port, "Package")
            self.assertEqual((port / "version.txt").read_text(), "user file")
            self.assertFalse((port / "new.txt").exists())

    def test_download_hash_mismatch_does_not_publish_the_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "verified.zip"
            with patch.object(backend.urllib.request, "urlopen", return_value=io.BytesIO(b"synthetic tool bytes")):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    backend.download_tools("https://example.invalid/tools.zip", target, "0" * 64)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix(".zip.part").exists())

    def test_validated_download_can_be_reused_offline(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "verified.zip"
            data = b"synthetic tool bytes"
            with patch.object(backend.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                backend.download_tools("https://example.invalid/tools.zip", target, hashlib.sha256(data).hexdigest())
            with patch.object(backend.urllib.request, "urlopen", side_effect=AssertionError("network not expected")):
                backend.download_tools("https://example.invalid/tools.zip", target, hashlib.sha256(data).hexdigest())
            self.assertEqual(target.read_bytes(), data)


class SetupPlan(unittest.TestCase):
    def test_running_game_from_another_installation_does_not_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            port = Path(temporary)
            result = SimpleNamespace(stdout='"tomodachi_play.exe","1234"\n')
            with patch.object(backend.integration.subprocess, "run", return_value=result), patch.object(backend.integration, "process_image_path", return_value=port / "other" / "game.exe"), patch("session_lock.active", return_value=False):
                backend.integration.refuse_running_game(port)

    def test_running_game_in_target_installation_blocks_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            port = Path(temporary)
            result = SimpleNamespace(stdout='"tomodachi_play.exe","1234"\n')
            with patch.object(backend.integration.subprocess, "run", return_value=result), patch.object(backend.integration, "process_image_path", return_value=port / "build" / "work" / "tomodachi_play.exe"), patch("session_lock.active", return_value=False):
                with self.assertRaisesRegex(ValueError, "Close the native game"):
                    backend.integration.refuse_running_game(port)

    def test_new_install_refuses_an_unrelated_nonempty_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "keep.txt").write_text("user data")
            with self.assertRaisesRegex(ValueError, "Unrelated files"):
                backend.validate_plan(root, False, None, None, None)
            self.assertEqual((root / "keep.txt").read_text(), "user data")

    def test_new_install_requires_local_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "port"
            with self.assertRaisesRegex(ValueError, "Base game"):
                backend.validate_plan(root, False, None, None, None)

    def test_existing_install_uses_readonly_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(backend.integration, "validate_port") as validate:
                backend.validate_plan(root, True, None, None, None)
            validate.assert_called_once_with(root)
            self.assertEqual(list(root.iterdir()), [])

    def test_interrupted_download_can_resume_in_its_own_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            port = root / "port"
            port.mkdir()
            (port / ".native-sharemii-setup.json").write_text(json.dumps({"archive_sha256": backend.LOCK["port_archive"]["sha256"]}))
            (port / "deps").mkdir()
            files = []
            for name in ("base.nsp", "update.nsp", "prod.keys"):
                file = root / name
                file.write_text("synthetic placeholder, not a game or key")
                files.append(file)
            with patch.object(backend.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024**3)):
                backend.validate_plan(port, False, *files)
