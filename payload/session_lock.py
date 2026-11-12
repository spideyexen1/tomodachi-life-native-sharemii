"""Process-scoped local locks used by the native launcher and editor bridge."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path


def alive(pid: int) -> bool:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return ctypes.get_last_error() != 87
    try:
        code = wintypes.DWORD()
        return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
    finally:
        kernel.CloseHandle(handle)


def active(path: Path) -> bool:
    try:
        return alive(int(json.loads(path.read_text())["pid"]))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def acquire(path: Path) -> None:
    if active(path):
        raise RuntimeError("Questa sessione e gia aperta.")
    path.unlink(missing_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid()}, stream)


def release(path: Path) -> None:
    try:
        if json.loads(path.read_text())["pid"] == os.getpid():
            path.unlink()
    except (OSError, ValueError, KeyError):
        pass
