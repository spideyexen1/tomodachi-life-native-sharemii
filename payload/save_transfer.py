# SPDX-License-Identifier: GPL-3.0-only
"""Local raw-save import/export. No keys, game packages or network are involved."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import uuid
import zipfile

import session_lock

REQUIRED = ("Map.sav", "Mii.sav", "Player.sav")
METADATA = "native-sharemii-export.json"
MAX_FILES, MAX_BYTES = 20000, 2 * 1024**3
BANNED = {".keys", ".nsp", ".nsz", ".xci", ".nca", ".nup", ".tik", ".cert", ".exe", ".dll", ".elf", ".torrent"}
VERSION = "1.0.4"


def digest(file: Path) -> str:
    with file.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def reparse(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def walk_error(error: OSError) -> None:
    raise error


def inventory(root: Path) -> dict[str, str]:
    if reparse(root):
        raise ValueError("Save roots must not be symlinks or reparse points.")
    result, size = {}, 0
    for directory, folders, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in folders + files:
            file = Path(directory) / name
            if reparse(file):
                raise ValueError("Save symlinks and reparse points are not supported.")
        for name in files:
            file = Path(directory) / name
            relative = file.relative_to(root).as_posix()
            if relative == METADATA:
                continue
            if file.suffix.lower() in BANNED:
                raise ValueError("The selected folder contains game packages, keys or programs; select only the raw save folder.")
            size += file.stat().st_size
            if len(result) >= MAX_FILES or size > MAX_BYTES:
                raise ValueError("Save exceeds the supported 20,000 files / 2 GiB limit.")
            result[relative] = digest(file)
    return result


def find_root(folder: Path) -> Path:
    if not folder.is_dir() or reparse(folder):
        raise ValueError("Choose a real raw-save folder without links.")
    folder = folder.resolve()
    candidates, scanned = [], 0
    for directory, folders, files in os.walk(folder, followlinks=False, onerror=walk_error):
        current = Path(directory)
        scanned += 1
        if scanned > 250:
            raise ValueError("Select the specific game/profile save folder, not an entire emulator profile.")
        if any(reparse(current / name) for name in folders + files):
            raise ValueError("Save folders must not contain symlinks or reparse points.")
        if all((current / name).is_file() and (current / name).stat().st_size > 0 for name in REQUIRED):
            candidates.append(current)
            folders[:] = []
        elif len(current.relative_to(folder).parts) >= 3:
            folders[:] = []
    if len(candidates) != 1:
        raise ValueError("Select one raw save containing nonempty Map.sav, Mii.sav and Player.sav; multiple profiles must be selected separately.")
    return candidates[0]


def safe_member(name: str) -> tuple[str, ...]:
    parts = PurePosixPath(name.replace("\\", "/")).parts
    reserved = {"CON", "PRN", "AUX", "NUL"} | {"COM" + str(n) for n in range(1, 10)} | {"LPT" + str(n) for n in range(1, 10)}
    if not parts or name.startswith(("/", "\\")) or any(part in (".", "..") or ":" in part or part.endswith((" ", ".")) or part.split(".")[0].upper() in reserved for part in parts):
        raise ValueError("Unsafe save archive path.")
    return parts


@contextmanager
def source_root(source: Path):
    if source.exists() and reparse(source):
        raise ValueError("Save sources must not be symlinks or reparse points.")
    source = source.expanduser().resolve()
    if source.is_dir():
        yield find_root(source)
        return
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise ValueError("Choose a local raw-save folder or save ZIP archive.")
    with tempfile.TemporaryDirectory(prefix="native-save-read-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_FILES + 1000 or sum(item.file_size for item in entries) > MAX_BYTES:
                raise ValueError("Save archive exceeds the supported size limit.")
            seen = set()
            for item in entries:
                parts = safe_member(item.filename)
                key = "/".join(parts).casefold()
                if key in seen or stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError("Duplicate paths or symlinks in save archive.")
                seen.add(key)
                if Path(parts[-1]).suffix.lower() in BANNED:
                    raise ValueError("A save archive must not contain game packages, keys or programs.")
            for item in entries:
                destination = root.joinpath(*safe_member(item.filename))
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as input_file, destination.open("wb") as output:
                        shutil.copyfileobj(input_file, output)
        yield find_root(root)


def inspect_root(root: Path) -> dict:
    hashes = inventory(root)
    metadata_file = root / METADATA
    version = None
    if metadata_file.is_file():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        if metadata.get("schema") != 1 or metadata.get("sha256") != hashes:
            raise ValueError("Save export manifest does not match the files.")
        version = metadata.get("game_version")
    return {"files": len(hashes), "game_version": version, "has_creations": any(name.startswith("Ugc/") for name in hashes), "sha256": hashes}


def inspect_source(source: Path) -> dict:
    with source_root(source) as root:
        return inspect_root(root)


def port_paths(port: Path) -> tuple[Path, Path, Path]:
    port = port.resolve()
    state = json.loads((port / "build" / "state.json").read_text(encoding="utf-8"))
    if state.get("game_version") != VERSION:
        raise ValueError("This save manager supports native game version 1.0.4 only.")
    userdata = (port / "build" / "userdata").resolve()
    backups = (port / "build" / "saves" / "imports").resolve()
    if not userdata.is_relative_to(port) or not backups.is_relative_to(port):
        raise ValueError("Use the standard local port layout without redirected save directories.")
    return port, userdata, backups


def guard(port: Path, userdata: Path) -> None:
    for name in ("game-session.json", "editor-session.json"):
        if session_lock.active(port / "integration" / name):
            raise ValueError("Close the native game and ShareMii before transferring saves.")
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        import csv
        import subprocess
        tasklist = Path(os.environ["SystemRoot"]) / "System32" / "tasklist.exe"
        try:
            rows = subprocess.run([str(tasklist), "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as error:
            raise RuntimeError("Cannot check running games. Run setup in a normal Windows session before transferring saves.") from error
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        for row in csv.reader(rows.splitlines()):
            if len(row) < 2 or row[0].lower() not in {"tomodachi_play.exe", "tomodachi_native.exe", "tomodachi_sharemii.exe"}:
                continue
            handle = kernel.OpenProcess(0x1000, False, int(row[1]))
            if not handle:
                raise ValueError("Cannot identify a running game process. Close it before transferring saves.")
            try:
                buffer, size = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
                if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)) or Path(buffer.value).parent.resolve() == (port / "build" / "work").resolve():
                    raise ValueError("Close the native game before transferring saves.")
            finally:
                kernel.CloseHandle(handle)
    if (userdata / "save.commit").exists():
        raise ValueError("The native game has an interrupted commit. Start and close it normally before transferring saves.")


@contextmanager
def transfer_session(port: Path, userdata: Path):
    guard(port, userdata)
    integration = port / "integration"
    integration.mkdir(parents=True, exist_ok=True)
    lock = integration / "save-transfer-session.json"
    session_lock.acquire(lock)
    try:
        guard(port, userdata)
        yield
    finally:
        session_lock.release(lock)


def checked_paths(userdata: Path, backups: Path, record: dict) -> tuple[Path, Path]:
    token, backup_id = record.get("token", ""), record.get("backup_id", "")
    if not re.fullmatch(r"[a-f0-9]{32}", token) or not re.fullmatch(r"\d{8}_\d{6}_[a-f0-9]{8}", backup_id):
        raise ValueError("Invalid pending import record; no files were changed.")
    stage, backup = userdata / (".save-import-" + token), backups / backup_id
    for path, parent in ((stage, userdata), (backup, backups)):
        if path.resolve().parent != parent.resolve() or (path.exists() and reparse(path)):
            raise ValueError("Unsafe pending import location.")
    return stage, backup


def recover_pending(userdata: Path, backups: Path) -> dict:
    marker = userdata / ".save-import.pending.json"
    if not marker.exists():
        return {"recovered": False}
    record = json.loads(marker.read_text(encoding="utf-8"))
    stage, backup = checked_paths(userdata, backups, record)
    current = userdata / "save"
    if current.exists() and reparse(current):
        raise ValueError("Redirected native saves are not supported.")
    if not current.exists() and (backup / "save").is_dir():
        (backup / "save").rename(current)
        outcome = "previous-restored"
    elif current.is_dir():
        outcome = "current-preserved"
    elif not record.get("previous_exists"):
        outcome = "empty-previous-state"
    else:
        raise ValueError("Pending import needs manual recovery from its backup; the game must remain closed.")
    if stage.exists():
        # Only this tool's UUID-named, contained staging directory is removed.
        shutil.rmtree(stage)
    marker.unlink()
    return {"recovered": True, "outcome": outcome, "backup": str(backup)}


def copy_snapshot(source: Path, destination: Path, expected: dict[str, str]) -> None:
    for relative in expected:
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, output)
    if inventory(destination) != expected or inventory(source) != expected:
        raise ValueError("The source save changed during the copy. Close the emulator and try again.")


def replace_snapshot(userdata: Path, backups: Path, root: Path, info: dict) -> dict:
    """Commit a prepared snapshot. Caller must own transfer_session and validate it."""
    token = uuid.uuid4().hex
    backup_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + token[:8]
    stage, backup = checked_paths(userdata, backups, {"token": token, "backup_id": backup_id})
    current, marker = userdata / "save", userdata / ".save-import.pending.json"
    if current.exists() and not current.is_dir():
        raise ValueError("The native save location is not a directory. No files were changed.")
    if root == current.resolve() or root.is_relative_to(userdata):
        raise ValueError("Choose a separate emulator save or exported archive, not the current native save.")
    stage.mkdir()
    try:
        copy_snapshot(root, stage, info["sha256"])
        previous = inventory(current) if current.is_dir() else {}
        backup.mkdir(parents=True)
        atomic_json(backup / "manifest.json", {"schema": 1, "game_version": VERSION, "previous_exists": current.exists(), "sha256": previous})
        record = {"schema": 1, "token": token, "backup_id": backup_id, "previous_exists": current.exists()}
        atomic_json(marker, record)
        if current.exists():
            current.rename(backup / "save")
        stage.rename(current)
        marker.unlink()
        return {"backup": str(backup), "files": info["files"], "target": str(current)}
    except BaseException:
        if marker.exists():
            recover_pending(userdata, backups)
        raise
    finally:
        if stage.exists() and not marker.exists():
            shutil.rmtree(stage)


def import_save(port: Path, source: Path, allow_unknown_version: bool = False) -> dict:
    port, userdata, backups = port_paths(port)
    with transfer_session(port, userdata):
        userdata.mkdir(parents=True, exist_ok=True)
        recover_pending(userdata, backups)
        with source_root(source) as root:
            info = inspect_root(root)
            if info["game_version"] not in (None, VERSION):
                raise ValueError("The save's recorded game version does not match 1.0.4.")
            if info["game_version"] is None and not allow_unknown_version:
                raise ValueError("Raw emulator saves do not identify their game version. Confirm that this save belongs to game 1.0.4.")
            return replace_snapshot(userdata, backups, root, info)


def export_save(port: Path, output: Path) -> dict:
    port, userdata, backups = port_paths(port)
    output = output.expanduser().resolve()
    if output.suffix.lower() != ".zip" or output.exists() or output.is_relative_to(userdata):
        raise ValueError("Choose a new ZIP file outside the native save directory.")
    with transfer_session(port, userdata):
        recover_pending(userdata, backups)
        root = find_root(userdata / "save")
        info = inspect_root(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="native-save-export-", dir=output.parent) as temporary:
            snapshot = Path(temporary) / "save"
            snapshot.mkdir()
            copy_snapshot(root, snapshot, info["sha256"])
            partial = Path(temporary) / "export.zip"
            with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
                for relative in sorted(info["sha256"]):
                    archive.write(snapshot / relative, relative)
                archive.writestr(METADATA, json.dumps({"schema": 1, "game_version": VERSION, "sha256": info["sha256"]}, indent=2))
            partial.rename(output)
        return {"archive": str(output), "files": info["files"], "sha256": digest(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inspect", "import", "export", "recover"))
    parser.add_argument("--port-dir", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-unknown-version", action="store_true")
    args = parser.parse_args()
    try:
        if args.operation == "inspect":
            if args.source is None:
                raise ValueError("Choose a save folder or ZIP archive.")
            result = inspect_source(args.source)
            result.pop("sha256", None)
        elif args.port_dir is None:
            raise ValueError("Choose the installed native port folder.")
        elif args.operation == "import":
            if args.source is None:
                raise ValueError("Choose a save folder or ZIP archive.")
            result = import_save(args.port_dir, args.source, args.allow_unknown_version)
        elif args.operation == "export":
            if args.output is None:
                raise ValueError("Choose an output ZIP file.")
            result = export_save(args.port_dir, args.output)
        else:
            port, userdata, backups = port_paths(args.port_dir)
            with transfer_session(port, userdata):
                result = recover_pending(userdata, backups)
        print(json.dumps({"ok": True, "operation": args.operation, "result": result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
