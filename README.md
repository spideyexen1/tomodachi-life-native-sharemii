# Tomodachi Life Native + ShareMii

[English installation guide](docs/en/INSTALL.md) · [Guida all'installazione in italiano](docs/it/INSTALL.md) · [README italiano](README.it.md)

A source-only ShareMii integration for the **unofficial native Windows port of Tomodachi Life: Living the Dream**.

The original native port is [TomodachiLife-recomp by josiahg2502-glitch](https://github.com/josiahg2502-glitch/TomodachiLife-recomp). This repository adds an **F1 menu, backup workflow and launcher** around [ShareMii by Star-F0rce](https://github.com/Star-F0rce/ShareMii). It does not claim authorship of either upstream project.

**No ROMs, game updates, console keys, firmware, save files, extracted assets or game-derived executables are included or linked here. Bring your own game dump and console keys to the upstream installer.**

## How it works

1. The upstream project statically recompiles your own game code into a native Windows program.
2. This integration rebuilds only the open-source host to add **F1 → ShareMii - Mii e oggetti**.
3. Choose a content category and Import, Export, Export All or List.
4. The menu requests a save and waits for the game's confirmation. It then closes the game.
5. The bridge waits for that game process to exit, copies the entire committed save and writes a SHA-256 manifest.
6. The original ShareMii editor opens with the save folder, category and mode selected. Closing it offers to restart the native game.

Editing happens in the original editor while the game is closed. The integration does not modify a running island's save files or implement its own Mii/item codecs.

Categories exposed by ShareMii: Mii, food, clothing, treasure, interiors, exteriors, objects and landscaping. Availability depends on your save and the upstream editor.

## Supported setup

| Component | Supported version/layout |
|---|---|
| System | Windows 10/11, x64 |
| Native port | Upstream **1.0.3**, pinned commit in `tools/upstream-lock.json` |
| Game | Your own base game plus **1.0.4** update, already built locally |
| Layout | `<port>/build/work` and `<port>/build/userdata` |
| Integration Python | **3.12 x64**, full installation with Tcl/Tk |
| Host compiler | Microsoft C++ Build Tools, C++ desktop workload and Windows SDK; upstream LLVM 9 |
| ShareMii | **3.2.3**, fetched from a pinned commit with SHA-256 checks |

See the installation guide for graphics, memory and disk requirements. This initial integration release supports the documented versions only; it refuses an unknown or independently modified upstream menu.

## Install the integration

First finish the native port's own installation from your own files, then close the game and editor. Keep this repository separate from the game installation.

```powershell
git clone https://github.com/spideyexen1/tomodachi-life-native-sharemii.git
cd tomodachi-life-native-sharemii
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --check-only
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife"
```

Use **Tomodachi Life - ShareMii** on the desktop or **Tomodachi Life + ShareMii** inside the port folder. Create your island and save at least once before opening the editor. The first start after rebuilding may prepare shaders; let it finish.

## Validation and limits

- The original local integration was compiled and its Italian game startup, F1 menu and category selection were checked visually. The introductory sequence ran around 60 fps on the tested system; this is not a performance guarantee for a complete island.
- Backup, process-exit waiting and active-session checks are tested with synthetic data, without game files.
- A source smoke test checks the patch against the pinned upstream source, repeated application, preservation of the original and refusal of unrelated edits.
- Import/export on an established real island has **not** been validated end to end. Keep the automatic backups.
- The wrapper uses **Browse** dialogs instead of drag-and-drop and exits the editor process after its synchronous GUI operations complete, addressing Windows/Tk hangs observed during local testing.
- The in-game integration labels are currently Italian; the guides explain their English meanings.

## Development

```powershell
py -3.12 -m unittest discover -s tests -v
py -3.12 tools/check_upstream.py
py -3.12 tools/audit_publication.py
```

The source smoke test downloads pinned public source files and ShareMii's own GUI assets into temporary storage. It does not fetch game content. The publication audit checks Git-tracked files, not your local game folder.

## Credits and license

GPL-3.0; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Unofficial fan integration, not affiliated with or endorsed by Nintendo. Game names and trademarks belong to their respective owners.
