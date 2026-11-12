# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PAYLOAD = Path(__file__).resolve().parents[1] / "payload"
sys.path.insert(0, str(PAYLOAD))
import session_lock

spec = importlib.util.spec_from_file_location("bridge", PAYLOAD / "bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class Backups(unittest.TestCase):
    def test_complete_backup_preserves_nested_creations_and_original_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(bridge, "ROOT", root):
                save = root / "userdata" / "save"
                (save / "Ugc" / "paint").mkdir(parents=True)
                for name in ("Mii.sav", "Map.sav", "Player.sav", "Ugc/paint/example.bin"):
                    (save / name).write_bytes(("synthetic test fixture: " + name).encode())
                backup = bridge.make_backup(save)
                manifest = json.loads((backup / "manifest.json").read_text())
                self.assertEqual(len(manifest), 4)
                for relative in manifest:
                    self.assertEqual((save / relative).read_bytes(), (backup / "save" / relative).read_bytes())
                second = bridge.make_backup(save)
                self.assertNotEqual(backup, second)
                (save / "Mii.sav").write_bytes(b"changed after backup")
                self.assertIn(b"synthetic test fixture", (backup / "save" / "Mii.sav").read_bytes())

    def test_incomplete_save_does_not_create_a_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(bridge, "ROOT", root):
                save = root / "save"
                save.mkdir()
                (save / "Mii.sav").write_bytes(b"synthetic incomplete data")
                with self.assertRaisesRegex(RuntimeError, "Map.sav"):
                    bridge.make_backup(save)
                self.assertFalse((root / "build").exists())


@unittest.skipUnless(sys.platform == "win32", "Windows process APIs")
class Sessions(unittest.TestCase):
    def test_waits_for_the_game_process_to_exit(self):
        process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.3)"])
        try:
            bridge.wait_for_game(process.pid)
            self.assertIsNotNone(process.poll())
        finally:
            process.wait(timeout=5)

    def test_active_session_is_refused_and_stale_session_can_be_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "editor-session.json"
            session_lock.acquire(lock)
            self.assertTrue(session_lock.active(lock))
            with self.assertRaises(RuntimeError):
                session_lock.acquire(lock)
            session_lock.release(lock)
            self.assertFalse(lock.exists())
            lock.write_text(json.dumps({"pid": 2147483647}))
            session_lock.acquire(lock)
            self.assertEqual(json.loads(lock.read_text())["pid"], os.getpid())
            session_lock.release(lock)
