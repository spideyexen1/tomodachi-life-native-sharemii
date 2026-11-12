# SPDX-License-Identifier: GPL-3.0-only
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "payload"))
import save_transfer as saves


def island(folder, label):
    folder.mkdir(parents=True, exist_ok=True)
    for name in saves.REQUIRED:
        (folder / name).write_bytes((label + name).encode())
    (folder / "Ugc").mkdir()
    (folder / "Ugc" / "synthetic.canvas.zs").write_bytes(b"synthetic creation, not game data")


class SaveTransfers(unittest.TestCase):
    def setUp(self):
        # Unit tests isolate Windows process enumeration; guard behavior is tested below.
        processes = patch("subprocess.run", return_value=SimpleNamespace(stdout=""))
        processes.start()
        self.addCleanup(processes.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.port = self.root / "port"
        (self.port / "build").mkdir(parents=True)
        (self.port / "build" / "state.json").write_text(json.dumps({"game_version": "1.0.4"}))
        self.current = self.port / "build" / "userdata" / "save"
        self.source = self.root / "emulator"
        island(self.source, "new")
        island(self.current, "old")

    def test_roundtrip_preserves_source_creations_and_old_island(self):
        expected = saves.inventory(self.source)
        old = saves.inventory(self.current)
        imported = saves.import_save(self.port, self.source, True)
        self.assertEqual(saves.inventory(self.source), expected)
        self.assertEqual(saves.inventory(self.current), expected)
        self.assertEqual(saves.inventory(Path(imported["backup"]) / "save"), old)
        archive = self.root / "export.zip"
        saves.export_save(self.port, archive)
        inspected = saves.inspect_source(archive)
        self.assertEqual(inspected["game_version"], "1.0.4")
        self.assertTrue(inspected["has_creations"])
        saves.import_save(self.port, archive)
        self.assertEqual(saves.inventory(self.current), expected)

    def test_unknown_version_requires_confirmation(self):
        old = saves.inventory(self.current)
        with self.assertRaisesRegex(ValueError, "Confirm"):
            saves.import_save(self.port, self.source)
        self.assertEqual(saves.inventory(self.current), old)

    def test_incompatible_manifest_rejected_even_with_confirmation(self):
        saves.atomic_json(self.source / saves.METADATA, {"schema": 1, "game_version": "1.0.3", "sha256": saves.inventory(self.source)})
        with self.assertRaisesRegex(ValueError, "version"):
            saves.import_save(self.port, self.source, True)

    def test_manifest_tampering_rejected(self):
        saves.atomic_json(self.source / saves.METADATA, {"schema": 1, "game_version": "1.0.4", "sha256": saves.inventory(self.source)})
        (self.source / "Mii.sav").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "manifest"):
            saves.inspect_source(self.source)

    def test_unrelated_and_ambiguous_folders_rejected(self):
        with self.assertRaises(ValueError):
            saves.inspect_source(self.root / "missing")
        island(self.root / "profiles" / "one", "one")
        island(self.root / "profiles" / "two", "two")
        with self.assertRaisesRegex(ValueError, "multiple profiles"):
            saves.inspect_source(self.root / "profiles")

    def test_traversal_duplicate_and_game_archive_entries_rejected(self):
        for index, entries in enumerate(({"../outside.txt": "bad"}, {"Map.sav": "a", "map.sav": "b"}, {"base.nsp": "synthetic"}, {"CON.sav": "bad"})):
            archive = self.root / (str(index) + ".zip")
            with zipfile.ZipFile(archive, "w") as stream:
                for name, data in entries.items():
                    stream.writestr(name, data)
            with self.assertRaises(ValueError):
                saves.inspect_source(archive)
        self.assertFalse((self.root / "outside.txt").exists())

    def test_active_game_or_native_commit_blocks_transfer(self):
        with patch.object(saves.session_lock, "active", return_value=True):
            with self.assertRaisesRegex(ValueError, "Close"):
                saves.export_save(self.port, self.root / "out.zip")
        (self.current.parent / "save.commit").write_text("synthetic pending native commit")
        with self.assertRaisesRegex(ValueError, "interrupted commit"):
            saves.import_save(self.port, self.source, True)

    def test_copy_failure_keeps_current_island(self):
        old = saves.inventory(self.current)
        with patch.object(saves, "copy_snapshot", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                saves.import_save(self.port, self.source, True)
        self.assertEqual(saves.inventory(self.current), old)
        self.assertFalse((self.current.parent / ".save-import.pending.json").exists())

    def test_failed_commit_rename_rolls_back(self):
        old = saves.inventory(self.current)
        rename = Path.rename
        def fail_stage(path, target):
            if path.name.startswith(".save-import-"):
                raise OSError("synthetic commit failure")
            return rename(path, target)
        with patch.object(Path, "rename", fail_stage):
            with self.assertRaisesRegex(OSError, "commit failure"):
                saves.import_save(self.port, self.source, True)
        self.assertEqual(saves.inventory(self.current), old)

    def test_crash_recovery_restores_previous_state(self):
        userdata = self.current.parent
        backups = self.port / "build" / "saves" / "imports"
        record = {"token": "a" * 32, "backup_id": "20261112_120000_aaaaaaaa", "previous_exists": True}
        stage, backup = saves.checked_paths(userdata, backups, record)
        backup.mkdir(parents=True)
        old = saves.inventory(self.current)
        self.current.rename(backup / "save")
        stage.mkdir()
        (stage / "partial.txt").write_text("not committed")
        saves.atomic_json(userdata / ".save-import.pending.json", record)
        result = saves.recover_pending(userdata, backups)
        self.assertEqual(result["outcome"], "previous-restored")
        self.assertEqual(saves.inventory(self.current), old)
        self.assertFalse(stage.exists())

    def test_invalid_recovery_marker_cannot_escape_userdata(self):
        saves.atomic_json(self.current.parent / ".save-import.pending.json", {"token": "../../outside", "backup_id": "bad"})
        with self.assertRaisesRegex(ValueError, "Invalid pending"):
            saves.recover_pending(self.current.parent, self.root)

    def test_export_never_overwrites_an_existing_archive(self):
        archive = self.root / "kept.zip"
        archive.write_bytes(b"user file")
        with self.assertRaises(ValueError):
            saves.export_save(self.port, archive)
        self.assertEqual(archive.read_bytes(), b"user file")

    def test_source_change_detected_before_replacing_current(self):
        old = saves.inventory(self.current)
        copy = saves.shutil.copy2
        def changing(source, destination):
            result = copy(source, destination)
            Path(source).write_bytes(b"emulator wrote a new save")
            return result
        with patch.object(saves.shutil, "copy2", changing):
            with self.assertRaisesRegex(ValueError, "changed"):
                saves.import_save(self.port, self.source, True)
        self.assertEqual(saves.inventory(self.current), old)
