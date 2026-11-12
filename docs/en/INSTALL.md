# Windows installation and usage

[Italiano](../it/INSTALL.md) · [Project overview](../../README.md)

## What you need

- Windows 10 or 11, **64-bit x86**. This integration has no Linux, macOS or ARM64 installer.
- A graphics card supporting **Vulkan 1.3 or OpenGL 4.5**. Renderer selection and graphics settings belong to the original port.
- At least **8 GB RAM**, with **16 GB or more recommended**, and a working Windows page file. Plan for roughly **15 GB free for the native port**, plus room for build tools and your backups.
- Your own base-game dump, your own **1.0.4 update**, and your own console's `prod.keys`, used locally by the upstream installer. This repository provides no game files or links to them.
- A completed [upstream native-port 1.0.3 installation](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/releases/tag/v1.0.3), with its standard `<port>/build` folder.
- Full **Python 3.12 x64 with Tcl/Tk**, the interpreter used for this integration's validation. Use [official Python Windows releases](https://www.python.org/downloads/windows/), rather than an embeddable distribution without Tk.
- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with the **Desktop development with C++** workload, x64 MSVC tools and Windows SDK. These are needed to rebuild this integration's custom host even when the original port used a prebuilt runtime.
- Internet access for open-source dependency downloads. Git is useful for cloning this source repository; downloading its source ZIP also works.

The original port and this integration have separate version numbers: **port 1.0.3 / game 1.0.4 / ShareMii 3.2.3**.

## 1. Build the original native port

Follow the original project's own instructions, supplying your own game files, update and keys locally. Finish its compilation and shader preparation, and confirm that its unmodified game starts. Initial preparation can take a long time; this integration does not replace the base-game build.

Keep the default internal build layout. For example:

```text
C:\Games\TomodachiLife\
  runtime\menu.cpp
  scripts\run.py
  build\state.json
  build\binaries\1.0.4\main.elf
  build\work\tomodachi_game.dll
  build\userdata\save\
```

Those generated files are created on your computer. Do not copy them into this source repository or upload them to GitHub.

## 2. Install this integration

Close the game and any ShareMii editor windows. Download or clone this repository into a **different folder** from the port:

```powershell
git clone https://github.com/spideyexen1/tomodachi-life-native-sharemii.git
cd tomodachi-life-native-sharemii
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --check-only
```

Replace the example port path with your actual installation. `--check-only` verifies the supported local build, Python and compiler prerequisites without downloads or changes. It can run while the game is open; installation itself requires the game to be closed.

Then run:

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife"
```

The installer creates or reuses `<port>/deps/python-venv`, installs GUI dependencies there, obtains pinned ShareMii source with hash checks, obtains the upstream host-build dependencies, backs up `menu.cpp`, applies the F1 patch and builds `tomodachi_sharemii.exe`. It creates dedicated shortcuts. It does not alter your graphics preferences or replace your existing island.

Your original `tomodachi_native.exe` remains separate. Keep the downloaded source repository if you need to reinstall or inspect the patch later.

To omit shortcut creation, append `--no-shortcuts`. Manual launch:

```powershell
& "C:\Games\TomodachiLife\deps\python-venv\Scripts\pythonw.exe" "C:\Games\TomodachiLife\integration\play-native.py"
```

## 3. Play and open ShareMii

Use **Tomodachi Life - ShareMii** on the desktop/Start menu, or **Tomodachi Life + ShareMii** in the port folder. The launcher explicitly enables the visible game window. A first start after rebuilding or changing graphics drivers may prepare shaders again.

Create an island and save at least once. Open **F1 → ShareMii - Mii e oggetti**. The controller's HOME/Guide button can also open the port's settings menu.

| Italian menu label | Meaning |
|---|---|
| Contenuto | Content category; use left/right to change it |
| Modalita | Import, Export, Export All or List |
| Salva e apri ShareMii | Save, close the game, back up and open the editor |
| Cartella import / export | Open the suggested exchange folder |
| Backup automatici | Open the backup folder |
| Indietro | Back |

The game must confirm the save before handoff. If saving is unavailable, return to the island and try again. In the editor, use **Browse** to choose a file/folder, check the selected slot and press **Start!**. Importing may replace that slot. Close the editor and answer the restart prompt to return to the native game.

## Save locations and recovery

Paths below are relative to the port installation:

| Path | Purpose |
|---|---|
| `build/userdata/save` | Committed current save |
| `build/saves/sharemii/<timestamp>/save` | Complete pre-editor backup, including creations |
| `build/saves/sharemii/<timestamp>/manifest.json` | Backup SHA-256 hashes |
| `Scambi` | Suggested folder for imported/exported content |
| `build/logs` | Game and editor logs |
| `integration` | Installed bridge and launcher source |

Backups are not automatically deleted. To restore one, close game and editor, open the original **Tomodachi Life Launcher.exe**, select **SAVE DATA → IMPORT A SAVE**, and choose the backup's inner `save` folder. The original launcher backs up the current data before import. Resume through the dedicated ShareMii shortcut afterward.

## Troubleshooting and updates

- **Unsupported version or modified menu:** use the documented upstream version. The patch deliberately refuses other edits rather than silently replacing them. A newer upstream release needs a compatibility review.
- **Missing compiler/Tk:** install the prerequisites above. The upstream port's embedded Python is not a substitute for the full GUI interpreter used here.
- **Editor still open / session already active:** close the editor normally before relaunching. After a crash, stale session files are replaced when their recorded process no longer exists.
- **No save or no slots:** complete the initial island setup and save in the game first. Category availability also depends on your creations.
- **Game window missing:** use the dedicated ShareMii shortcut; it sets the visibility flag for direct launch.
- **Editor error:** inspect `build/logs/sharemii-editor.log` and `integration/editor-*.log`. A failed backup prevents the editor from opening.
- **Port update:** preserve saves and backups, and check compatibility before reapplying this integration. Do not force a patch onto a changed menu.

The installer and automated tests can be checked without distributing game content. Real-island import/export has not been validated end to end in this release; keep your backups and consult ShareMii's original documentation for its file-format behavior.
