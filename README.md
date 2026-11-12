# Tomodachi Life Native + ShareMii

[English installation guide](docs/en/INSTALL.md) · [Guida all'installazione in italiano](docs/it/INSTALL.md) · [README italiano](README.it.md)

A source-only ShareMii integration for the **unofficial native Windows port of Tomodachi Life: Living the Dream**.

The original native port is [TomodachiLife-recomp by josiahg2502-glitch](https://github.com/josiahg2502-glitch/TomodachiLife-recomp). This repository adds an **F1 menu, backup workflow and launcher** around [ShareMii by Star-F0rce](https://github.com/Star-F0rce/ShareMii). It does not claim authorship of either upstream project.

**No ROMs, game updates, console keys, firmware, save files, extracted assets or game-derived executables are included or linked here. Bring your own game dump and console keys to the upstream installer.**

## Windows setup wizard

Download [**Native + ShareMii Setup**](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.1). It is a small Windows x64 `.exe` with an **automatic Windows-language interface** (IT, EN, DE, ES, FR, PT; English fallback), local file pickers, prerequisite checks, progress/logs and resume support.

Choose **New installation / resume** to build from your own base game, update and keys, or **Existing port** to add the integration to a completed installation. Missing Python and Microsoft C++ Build Tools can be installed using the wizard's WinGet buttons, with Windows administrator approval when needed. If WinGet is unavailable, the wizard offers the official prerequisite download pages.

The wizard itself needs no Python installation to open. Python is required for the build and editor. A first game build and shader preparation may take an hour or longer. The setup contains only this project's source/tools; it downloads the pinned upstream tools separately. It is not digitally signed.

## F1 menu compatibility fix

Setup **0.3.1** adds **Repair F1 menu**, which enables Vulkan and the menu after backing up graphics settings. New installations and integration updates offer **Use Vulkan for the F1 menu**, enabled by default. A Vulkan 1.3 GPU is required; uncheck the option to keep your renderer.

This configuration workaround fixed a menu that opened internally but stayed invisible under OpenGL on the tested NVIDIA PC. It does not change upstream OpenGL code. F1 and the ShareMii page were verified visually after restarting with Vulkan. Shader preparation may run again on the first Vulkan start. Follow the [repair and settings restoration guide](docs/en/MENU-REPAIR.md). Repair alone needs no C++ compiler, download or rebuild.

## Emulator saves and interface language

**Saved games** can inspect and import a raw emulator save folder or ZIP, export the complete island as ZIP, and recover interrupted imports. Import immediately or after a new installation. The source is untouched and the previous island is backed up. Game **1.0.4** is supported without version conversion.

See the [import, export and recovery guide](docs/en/SAVE-TRANSFER.md), including restoration to an emulator. Transfer tests use synthetic fixtures; loading a real imported island remains unverified.

Setup detects the Windows display language at launch, including when opened on another PC. **Auto · Windows** chooses Italian, English, German, Spanish, French or Portuguese. Regional variants use their base language; unsupported languages fall back to English. Manual selection is available. This applies to setup; the game and original editor have their own settings, and diagnostic logs may remain in English.

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
- The setup's source bundle, argument handling, languages, modes and rendering have a self-test. Backend tests cover archive/hash validation, preservation of unrelated files and interrupted-download resume. Its existing-install backend successfully rebuilt the custom host in an isolated copy of a supported installation. A separate full fresh-game build has not been rerun through the wizard.

## Development

```powershell
py -3.12 -m unittest discover -s tests -v
py -3.12 tools/check_upstream.py
py -3.12 tools/audit_publication.py
```

The source smoke test downloads pinned public source files and ShareMii's own GUI assets into temporary storage. It does not fetch game content. The publication audit checks Git-tracked files, not your local game folder.


Save transfer checks additionally cover full-island round trips, preservation of creation files and source data, previous-island backups, version confirmation, manifest tampering, unsafe ZIPs, interrupted commits and recovery. The packaged CLI and post-install import were also exercised against an isolated local port with synthetic saves.

## Credits and license

GPL-3.0; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Unofficial fan integration, not affiliated with or endorsed by Nintendo. Game names and trademarks belong to their respective owners.
