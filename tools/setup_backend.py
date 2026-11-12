# SPDX-License-Identifier: GPL-3.0-only
"""Backend for the Windows wizard. Network downloads are open-source tools only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

import install_integration as integration

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "payload"))
import save_transfer
LOCK = json.loads((HERE / "setup-lock.json").read_text(encoding="utf-8"))
GAME_SUFFIXES = {".nsp", ".nsz", ".xci", ".nca", ".nup", ".keys", ".sav", ".elf"}
RANGES = {"precheck": (12, 14), "packages": (14, 16), "inputs": (16, 18), "dump": (18, 23), "tools": (23, 27), "media": (27, 29), "deps": (29, 30), "stage": (30, 31), "convert": (31, 32), "tables": (32, 33), "lift": (33, 35), "sdk": (35, 36), "compile": (36, 72), "link": (72, 74), "prepare": (74, 90), "shortcuts": (90, 91)}


def event(stage: str, percent: int, message: str = "") -> None:
    print("##setup " + json.dumps({"stage": stage, "percent": max(0, min(100, percent)), "message": message}), flush=True)


def recognized_source(port: Path) -> bool:
    script = port / "scripts" / "install.py"
    try:
        data = script.read_text(encoding="utf-8").encode("utf-8")
        return hashlib.sha256(data).hexdigest() == integration.LOCK["port"]["source_sha256"]["scripts/install.py"]
    except OSError:
        return False


def recognized_resume(port: Path) -> bool:
    try:
        marker = json.loads((port / ".native-sharemii-setup.json").read_text(encoding="utf-8"))
        return marker.get("archive_sha256") == LOCK["port_archive"]["sha256"]
    except (OSError, ValueError, AttributeError):
        return False


def validate_plan(port: Path, existing: bool, base: Path | None, update: Path | None, keys: Path | None) -> None:
    if not port.is_absolute():
        raise ValueError("Choose an absolute installation folder.")
    if existing:
        integration.validate_port(port)
        return
    if port.exists() and any(port.iterdir()) and not (recognized_source(port) or recognized_resume(port)):
        raise ValueError("Choose an empty folder or the supported port folder. Unrelated files will not be overwritten.")
    for label, file, suffixes in (("Base game", base, {".nsp", ".nsz", ".xci"}), ("Update 1.0.4", update, {".nsp", ".nsz"}), ("Console keys", keys, {".keys"})):
        if file is None or not file.is_file() or file.suffix.lower() not in suffixes:
            raise ValueError(label + ": choose your own existing local file.")
    parent = port
    while not parent.exists():
        parent = parent.parent
    if shutil.disk_usage(parent).free < 15 * 1024**3:
        raise ValueError("At least 15 GB of free space is required, plus room for tools and backups.")


def download_tools(url: str, destination: Path, expected: str) -> None:
    if destination.is_file() and integration.digest(destination) == expected:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    hasher = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=90) as response, partial.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            hasher.update(chunk)
    if hasher.hexdigest() != expected:
        partial.unlink(missing_ok=True)
        raise ValueError("The tools archive did not match its pinned SHA-256. Download refused.")
    partial.replace(destination)


def extract_tools(archive: Path, port: Path, prefix: str) -> None:
    """Validate every path and conflict before writing anything from the archive."""
    root = port.resolve()
    pending = []
    with zipfile.ZipFile(archive) as package:
        if sum(info.file_size for info in package.infolist()) > 200 * 1024**2:
            raise ValueError("Unexpected tools archive size.")
        for info in package.infolist():
            name = info.filename.replace("\\", "/")
            parts = PurePosixPath(name).parts
            if not parts or parts[0] != prefix or ".." in parts or any(":" in part for part in parts):
                raise ValueError("Unsafe archive path.")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Archive symlinks are not accepted.")
            if len(parts) == 1 or info.is_dir():
                continue
            relative = Path(*parts[1:])
            if relative.suffix.lower() in GAME_SUFFIXES:
                raise ValueError("The tools package must not contain game data, keys or saves.")
            destination = (root / relative).resolve()
            if not destination.is_relative_to(root):
                raise ValueError("Archive path escapes the installation folder.")
            data = package.read(info)
            if destination.exists():
                if not destination.is_file() or destination.read_bytes() != data:
                    raise ValueError("Existing file differs; refusing to overwrite: " + str(relative))
            else:
                pending.append((destination, data))
    for destination, data in pending:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)


def run(command: list[str], port: Path, native: bool = False) -> None:
    # Do not echo command lines: they contain the user's local file paths.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RECOMP_", "SSBU_", "TOMO_"))}
    env.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    process = subprocess.Popen(command, cwd=port, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    assert process.stdout is not None
    for line in process.stdout:
        print(line.rstrip(), flush=True)
        if native and line.startswith("##ssbu "):
            try:
                item = json.loads(line[7:])
                start, end = RANGES.get(item.get("id"), (12, 90))
                if item.get("ev") == "progress" and item.get("total", 0):
                    progress = start + (end - start) * min(1, item["done"] / item["total"])
                else:
                    progress = end if item.get("state") in ("done", "skip") else start
                event("native", int(progress), item.get("msg", ""))
            except (ValueError, KeyError, TypeError):
                pass
    if process.wait():
        raise RuntimeError("A build step stopped. Read the installation log, fix the reported problem and run setup again to resume.")


def perform(port: Path, existing: bool, base: Path | None, update: Path | None, keys: Path | None, no_shortcuts: bool = False, import_source: Path | None = None, allow_unknown_save: bool = False) -> None:
    event("validate", 0)
    validate_plan(port, existing, base, update, keys)
    if import_source is not None:
        save_info = save_transfer.inspect_source(import_source)
        if save_info["game_version"] not in (None, "1.0.4") or (save_info["game_version"] is None and not allow_unknown_save):
            raise ValueError("Confirm that the selected save belongs to game version 1.0.4 before installing.")
    integration.require_python_and_compiler()
    integration.refuse_running_game(port)
    if not existing:
        port.mkdir(parents=True, exist_ok=True)
        (port / ".native-sharemii-setup.json").write_text(json.dumps({"setup_version": LOCK["version"], "archive_sha256": LOCK["port_archive"]["sha256"]}), encoding="utf-8")
        if not recognized_source(port):
            event("download", 3)
            archive = port / "deps" / "setup-downloads" / "native-port-v1.0.3.zip"
            item = LOCK["port_archive"]
            download_tools(item["url"], archive, item["sha256"])
            extract_tools(archive, port, item["prefix"])
        event("python", 7)
        python = integration.prepare_python(port)
        try:
            integration.validate_port(port)
            ready = True
        except (OSError, ValueError):
            ready = False
        if not ready:
            event("native", 12)
            run([str(python), "-u", str(port / "scripts" / "install.py"), "--no-gui", "--no-self-update", "--no-shortcuts", "--progress-json", "--base", str(base), "--update", str(update), "--keys", str(keys)], port, native=True)
        integration.validate_port(port)
    event("integration", 91)
    command = [sys.executable, "-u", str(HERE / "install_integration.py"), "--port-dir", str(port)]
    if no_shortcuts:
        command.append("--no-shortcuts")
    run(command, port)
    if import_source is not None:
        event("save-import", 98)
        result = save_transfer.import_save(port, import_source, allow_unknown_save)
        print("Save import completed. Backup: " + result["backup"], flush=True)
    event("done", 100)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-dir", type=Path, required=True)
    parser.add_argument("--existing", action="store_true")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--update", type=Path)
    parser.add_argument("--keys", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--no-shortcuts", action="store_true", help="Developer/CLI option: omit shortcut creation")
    parser.add_argument("--import-save", type=Path)
    parser.add_argument("--allow-unknown-save-version", action="store_true")
    args = parser.parse_args()
    try:
        port = args.port_dir.expanduser().resolve()
        if args.check_only:
            validate_plan(port, args.existing, args.base, args.update, args.keys)
            integration.require_python_and_compiler()
            event("checked", 100)
        else:
            perform(port, args.existing, args.base, args.update, args.keys, args.no_shortcuts, args.import_save, args.allow_unknown_save_version)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        event("error", 0, str(error))
        print(str(error), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
