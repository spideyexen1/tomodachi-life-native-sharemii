# SPDX-License-Identifier: GPL-3.0-only
"""Install the integration into an existing, supported native-port installation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import venv

from build_runtime import build
from patch_menu import apply_patch, check_source
from shortcuts import create as create_shortcuts
from menu_config import configure as configure_menu
from patch_texture_lifetime import apply_patch as patch_texture_lifetime, check_source as check_texture_source

REPO = Path(__file__).resolve().parents[1]
LOCK = json.loads((Path(__file__).with_name("upstream-lock.json")).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_port(port: Path) -> None:
    if (port / "version.txt").read_text(encoding="utf-8").strip() != LOCK["port"]["version"]:
        raise ValueError("Supported upstream port version: " + LOCK["port"]["version"])
    state = json.loads((port / "build" / "state.json").read_text(encoding="utf-8"))
    if state.get("game_version") != "1.0.4":
        raise ValueError("Build your own game with update 1.0.4 in the upstream installer first.")
    if not {"compile", "link", "prepare"}.issubset(state.get("done", {})):
        raise ValueError("Finish the upstream installation and shader preparation first.")
    for relative in ("build/work/tomodachi_game.dll", "build/work/SDL3.dll", "build/binaries/1.0.4/main.elf"):
        if not (port / relative).is_file():
            raise ValueError("The local installation is incomplete: " + relative)
    for relative, expected in LOCK["port"]["source_sha256"].items():
        text = (port / relative).read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != expected:
            raise ValueError("Unsupported/modified upstream build script: " + relative)
    location = port / "build_location.txt"
    if location.exists() and Path(location.read_text(encoding="utf-8").strip()).resolve() != (port / "build").resolve():
        raise ValueError("This release requires the standard <port>/build layout.")
    check_source(port)
    check_texture_source(port)


def require_python_and_compiler() -> None:
    if platform.system() != "Windows" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise ValueError("Windows x64 is required for this integration.")
    if sys.version_info[:2] != (3, 12) or sys.maxsize <= 2**32:
        raise ValueError("Run this installer with 64-bit Python 3.12 (including Tcl/Tk).")
    import tkinter  # noqa: F401: ensure the full Python install includes Tcl/Tk
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        raise ValueError("Install Microsoft C++ Build Tools with the C++ desktop workload and Windows SDK first.")
    result = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], capture_output=True, text=True, check=True)
    if not result.stdout.strip():
        raise ValueError("The Microsoft C++ x64 tools are missing.")


def refuse_running_game(port: Path) -> None:
    sys.path.insert(0, str(REPO / "payload"))
    import session_lock
    for name in ("game-session.json", "editor-session.json", "save-transfer-session.json"):
        if session_lock.active(port / "integration" / name):
            raise ValueError("Close the game and ShareMii before installing.")
    tasklist = Path(os.environ["SystemRoot"]) / "System32" / "tasklist.exe"
    result = subprocess.run([str(tasklist), "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True)
    names = {"tomodachi_play.exe", "tomodachi_native.exe", "tomodachi_sharemii.exe"}
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) < 2 or row[0].lower() not in names:
            continue
        image = process_image_path(int(row[1]))
        if image is None or image.parent.resolve() == (port / "build" / "work").resolve():
            raise ValueError("Close the native game in this installation before installing. An unidentifiable game process also blocks changes.")


def process_image_path(pid: int) -> Path | None:
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        return Path(buffer.value) if kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)) else None
    finally:
        kernel.CloseHandle(handle)


def prepare_python(port: Path) -> Path:
    folder = port / "deps" / "python-venv"
    if not folder.exists():
        venv.EnvBuilder(with_pip=True).create(folder)
    python = folder / "Scripts" / "python.exe"
    subprocess.run([str(python), "-c", "import sys,tkinter; assert sys.version_info[:2] == (3,12), 'Python 3.12 is required'"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(port / "requirements.txt"), "-r", str(REPO / "requirements-integration.txt")], check=True)
    return python


def fetch_sharemii(port: Path) -> None:
    vendor = port / "integration" / "ShareMii"
    vendor.mkdir(parents=True, exist_ok=True)
    upstream = LOCK["sharemii"]
    base = f'https://raw.githubusercontent.com/{upstream["repository"]}/{upstream["commit"]}/'
    for name, expected in upstream["sha256"].items():
        destination = vendor / name
        if destination.exists():
            if digest(destination) != expected:
                raise ValueError("Existing ShareMii file was modified; keep a copy and resolve it first: " + name)
            continue
        with urllib.request.urlopen(base + name, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("ShareMii source verification failed: " + name)
        destination.write_bytes(data)
    (vendor / "UPSTREAM.txt").write_text(f'Original ShareMii by Star-F0rce, GPL-3.0.\nhttps://github.com/{upstream["repository"]}\nCommit: {upstream["commit"]}\nSources are unmodified.\n', encoding="utf-8")


def fetch_build_dependencies(port: Path, python: Path) -> None:
    # Use the verified upstream tool manifest and its SHA-256 checks.
    code = "import sys;sys.path.insert(0,sys.argv[1]);import install;" + ";".join(f"install.fetch('{name}')" for name in ("llvm", "sdl3", "vulkan-headers", "imgui")) + ";install.fetch_suyu()"
    subprocess.run([str(python), "-c", code, str(port / "scripts")], cwd=port, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-dir", type=Path, required=True, help="Existing upstream v1.0.3 installation, containing build/")
    parser.add_argument("--check-only", action="store_true", help="Validate prerequisites and source without downloads or changes")
    parser.add_argument("--no-shortcuts", action="store_true")
    parser.add_argument("--vulkan-menu", action="store_true", help="Back up graphics settings and enable Vulkan + F1 menu (recommended)")
    parser.add_argument("--menu-renderer", choices=("auto", "opengl", "vulkan"))
    args = parser.parse_args()
    port = args.port_dir.expanduser().resolve()
    try:
        validate_port(port)
        require_python_and_compiler()
        if args.check_only:
            print("Supported local build and prerequisites found. No files changed.")
            return 0
        refuse_running_game(port)
        python = prepare_python(port)
        fetch_sharemii(port)
        fetch_build_dependencies(port, python)
        apply_patch(port, REPO / "payload" / "friday_sharemii.h")
        patch_texture_lifetime(port)
        integration = port / "integration"
        integration.mkdir(exist_ok=True)
        for name in ("bridge.py", "session_lock.py", "play-native.py", "friday_sharemii.h", "save_transfer.py"):
            shutil.copy2(REPO / "payload" / name, integration / name)
        for relative in ("Scambi", "build/saves/sharemii"):
            (port / relative).mkdir(parents=True, exist_ok=True)
        build(port, python)
        if args.vulkan_menu or args.menu_renderer:
            result = configure_menu(port, args.menu_renderer or "vulkan")
            print("Menu compatibility: " + result["renderer"] + ". Graphics settings backup: " + str(result["backup"]))
        if not args.no_shortcuts:
            create_shortcuts(port)
        print("Ready: use the Tomodachi Life - ShareMii shortcut. Create an island and save before opening the editor.")
        print("The first start of the rebuilt host may prepare shaders again. Keep this source repository for future maintenance.")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("Installation stopped: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
