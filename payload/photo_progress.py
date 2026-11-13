# SPDX-License-Identifier: GPL-3.0-only
"""Small automatic progress window while the saved game's photos are encoded."""
import ctypes
import tkinter as tk
from tkinter import ttk


class PhotoProgress:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ShareMii - JPG / PNG")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        language = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3ff
        self.message = {
            0x10: "Conversione foto {current}/{total}. Il gioco si riapre automaticamente.",
            0x07: "Fotos umwandeln {current}/{total}. Das Spiel startet automatisch neu.",
            0x0a: "Convirtiendo fotos {current}/{total}. El juego se reabre automaticamente.",
            0x0c: "Conversion photos {current}/{total}. Le jeu redemarre automatiquement.",
            0x16: "Convertendo fotos {current}/{total}. O jogo reabre automaticamente.",
        }.get(language, "Converting photos {current}/{total}. The game restarts automatically.")
        self.label = ttk.Label(self.root, text="ShareMii", padding=16)
        self.label.pack(fill="x")
        self.name = ttk.Label(self.root, text="", padding=(16, 0, 16, 12))
        self.name.pack(fill="x")
        self.bar = ttk.Progressbar(self.root, mode="determinate", length=440)
        self.bar.pack(padx=16, pady=(0, 16))
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.geometry(f"+{max(0, (self.root.winfo_screenwidth()-w)//2)}+{max(0, (self.root.winfo_screenheight()-h)//2)}")
        self.root.update()

    def __call__(self, current, total, name):
        self.label.configure(text=self.message.format(current=current, total=total))
        self.name.configure(text=name[:60])
        self.bar.configure(maximum=total, value=current - 1)
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass  # a completed transaction must stay successful if its UI closed
