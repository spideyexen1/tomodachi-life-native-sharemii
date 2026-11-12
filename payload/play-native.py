"""Start the custom native runtime with the upstream launch configuration."""
import importlib.util
import os
from pathlib import Path
import sys
import traceback
import session_lock

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "integration"


def main():
    game_lock = HERE / "game-session.json"
    try:
        if (ROOT / "build" / "userdata" / ".save-import.pending.json").exists():
            raise RuntimeError("A save import needs recovery. Open Setup > Saved games > Recover before starting the game.")
        if session_lock.active(HERE / "save-transfer-session.json"):
            raise RuntimeError("A save transfer is active. Wait for it to finish before starting the game.")
        if session_lock.active(HERE / "editor-session.json"):
            raise RuntimeError("ShareMii e ancora aperto. Chiudi l'editor prima di riprendere il gioco.")
        session_lock.acquire(game_lock)
        if (ROOT / "build" / "userdata" / ".save-import.pending.json").exists():
            raise RuntimeError("A save import needs recovery. Open Setup > Saved games > Recover before starting the game.")
        if session_lock.active(HERE / "save-transfer-session.json"):
            raise RuntimeError("A save transfer is active. Wait for it to finish before starting the game.")
        scripts = ROOT / "scripts"
        sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location("native_run", scripts / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.EXE = "tomodachi_sharemii.exe"
        sys.argv = [str(scripts / "run.py"), "--direct", "--env", "SSBU_SHOW=1"]
        result = module.main()
        if result:
            raise RuntimeError("Il gioco si e chiuso con codice " + str(result) + ". I dettagli sono in build\\logs.")
        return 0
    except Exception as error:
        import tkinter as tk
        from tkinter import messagebox
        (HERE / "launch-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        ui = tk.Tk()
        ui.withdraw()
        messagebox.showerror("Tomodachi Life nativo", str(error), parent=ui)
        ui.quit()
        return 1
    finally:
        session_lock.release(game_lock)


if __name__ == "__main__":
    os._exit(main())
