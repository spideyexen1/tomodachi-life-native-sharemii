"""Local ShareMii handoff. Uses the unmodified upstream editor; no content codecs.

The native menu saves first. This process waits for that game process to exit,
backs up the committed save, configures the editor and offers to resume the game.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import session_lock

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "integration"
ITEMS = ("Mii", "Food", "Clothing", "Treasure", "Interior", "Exterior", "Objects", "Landscaping")
MODES = ("Import", "Export", "Export All", "List")


def wait_for_game(pid: int) -> None:
    if pid <= 0:
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x00100000, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:  # process has already exited
            return
        raise RuntimeError("Non posso verificare la chiusura del gioco. Nessuna modifica effettuata.")
    try:
        if kernel.WaitForSingleObject(handle, 30000) != 0:
            raise RuntimeError("Il gioco non si e chiuso. L'editor non verra aperto.")
    finally:
        kernel.CloseHandle(handle)


def make_backup(save: Path) -> Path:
    for name in ("Mii.sav", "Map.sav", "Player.sav"):
        if not (save / name).is_file():
            raise RuntimeError("Crea prima un'isola e salva la partita: manca " + name)
    destination = ROOT / "build" / "saves" / "sharemii" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(save, destination / "save")
    manifest = {}
    for file in sorted((destination / "save").rglob("*")):
        if file.is_file():
            with file.open("rb") as stream:
                manifest[str(file.relative_to(destination / "save"))] = hashlib.file_digest(stream, "sha256").hexdigest()
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return destination


def editor(save: Path, item: str, mode: str, preview: bool = False) -> int:
    # Configure the original GUI at its normal mainloop entry, without copying
    # or reimplementing any ShareMii import/export algorithm.
    import tkinter as tk
    import faulthandler
    from tkinterdnd2 import TkinterDnD

    # Windows' drag/drop registration can hang on this system. The original
    # Browse dialogs provide the same file operations without that registration.
    original_tk = TkinterDnD.Tk
    original_drop = tk.BaseWidget.drop_target_register
    original_bind = tk.BaseWidget.dnd_bind
    TkinterDnD.Tk = tk.Tk
    tk.BaseWidget.drop_target_register = lambda *args, **kwargs: None
    tk.BaseWidget.dnd_bind = lambda *args, **kwargs: None

    vendor = HERE / "ShareMii"
    source = vendor / "ShareMii.py"
    namespace = {"__name__": "__main__", "__file__": str(source)}
    original_mainloop = tk.Misc.mainloop

    def configured_mainloop(root, *args, **kwargs):
        faulthandler.cancel_dump_traceback_later()
        from tkinter import messagebox
        root.title("ShareMii 3.2.3 | Tomodachi Life PC | backup automatico creato")
        def callback_error(kind, value, tb):
            (HERE / "editor-exceptions.log").write_text("".join(traceback.format_exception(kind, value, tb)), encoding="utf-8")
            root.after_idle(lambda: messagebox.showerror("ShareMii", str(value), parent=root))
        root.report_callback_exception = callback_error
        # Let the original mainloop return without entering the Windows/Tk
        # destruction path that hangs on this PC. The editor process then exits.
        root.protocol("WM_DELETE_WINDOW", root.quit)
        namespace["itemVar"].set(item)
        namespace["modeVar"].set(mode)
        if not preview:
            namespace["folderVar"].set(str(save))
        return original_mainloop(root, *args, **kwargs)

    tk.Misc.mainloop = configured_mainloop
    sys.path.insert(0, str(vendor))
    sys.argv = [str(source)]
    os.chdir(vendor)
    with (HERE / "editor-startup.log").open("w") as diagnostic:
        faulthandler.dump_traceback_later(15, file=diagnostic)
        try:
            exec(compile(source.read_bytes(), str(source), "exec"), namespace)
        finally:
            faulthandler.cancel_dump_traceback_later()
            tk.Misc.mainloop = original_mainloop
            TkinterDnD.Tk = original_tk
            tk.BaseWidget.drop_target_register = original_drop
            tk.BaseWidget.dnd_bind = original_bind
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-pid", type=int, default=0)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--item", choices=ITEMS, default="Mii")
    parser.add_argument("--mode", choices=MODES, default="Import")
    parser.add_argument("--editor", action="store_true")
    parser.add_argument("--preview", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.editor:
        try:
            result = editor(args.save, args.item, args.mode, args.preview)
        except BaseException:
            (HERE / "editor-fatal.log").write_text(traceback.format_exc(), encoding="utf-8")
            result = 1
        # All import/export operations are synchronous GUI callbacks and have
        # completed before Quit returns. Avoid Tk finalizers hanging the bridge.
        os._exit(result)
    import tkinter as tk
    from tkinter import messagebox
    ui = tk.Tk()
    ui.withdraw()
    editor_lock = HERE / "editor-session.json"
    try:
        wait_for_game(args.parent_pid)
        session_lock.acquire(editor_lock)
        backup = make_backup(args.save)
        python = ROOT / "deps" / "python-venv" / "Scripts" / "pythonw.exe"
        logs = ROOT / "build" / "logs"
        logs.mkdir(exist_ok=True)
        with (logs / "sharemii-editor.log").open("ab") as log:
            result = subprocess.run([str(python), str(__file__), "--editor", "--save", str(args.save), "--item", args.item, "--mode", args.mode], stdout=log, stderr=log, cwd=ROOT)
        if result.returncode:
            raise RuntimeError("ShareMii si e chiuso con un errore. Backup: " + str(backup) + "\nDettagli in build\\logs\\sharemii-editor.log")
        if messagebox.askyesno("ShareMii - torna al gioco", "Editor chiuso. Vuoi riprendere Tomodachi Life?\n\nIl backup precedente alle modifiche e in:\n" + str(backup), parent=ui):
            session_lock.release(editor_lock)
            subprocess.Popen([str(python), str(HERE / "play-native.py")], cwd=ROOT)
        return 0
    except Exception as error:
        (HERE / "bridge-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        messagebox.showerror("ShareMii - operazione interrotta", str(error), parent=ui)
        return 1
    finally:
        session_lock.release(editor_lock)
        ui.quit()


if __name__ == "__main__":
    os._exit(main())
