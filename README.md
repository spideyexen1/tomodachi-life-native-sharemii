# Tomodachi Life Native + ShareMii

[English installation guide](docs/en/INSTALL.md) · [Guida all'installazione in italiano](docs/it/INSTALL.md) · [README italiano](README.it.md)

A source-only ShareMii integration for the **unofficial native Windows port of Tomodachi Life: Living the Dream**.

The original native port is [TomodachiLife-recomp by josiahg2502-glitch](https://github.com/josiahg2502-glitch/TomodachiLife-recomp). This repository adds an **F1 menu, backup workflow and launcher** around [ShareMii by Star-F0rce](https://github.com/Star-F0rce/ShareMii). It does not claim authorship of either upstream project.

**No ROMs, game updates, console keys, firmware, save files, extracted assets or game-derived executables are included or linked here. Bring your own game dump and console keys to the upstream installer.**

## Windows setup wizard

Download [**Native + ShareMii Setup**](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.5.0). It is a small Windows x64 `.exe` with an **automatic Windows-language interface** (IT, EN, DE, ES, FR, PT; English fallback), local file pickers, prerequisite checks, progress/logs and resume support.

Choose **New installation / resume** to build from your own base game, update and keys, or **Existing port** to add the integration to a completed installation. Missing Python and Microsoft C++ Build Tools can be installed using the wizard's WinGet buttons, with Windows administrator approval when needed. If WinGet is unavailable, the wizard offers the official prerequisite download pages.

The wizard itself needs no Python installation to open. Python is required for the build and editor. A first game build and shader preparation may take an hour or longer. The setup contains only this project's source/tools; it downloads the pinned upstream tools separately. It is not digitally signed.

## Import JPG and PNG photos

Setup **0.5.0** integrates the MIT [TL-UGC-Editor](https://github.com/PICKLERICK2005/TL-UGC-Editor) converter into F1. Choose an item category, **Mode: Photo: contain / crop / stretch**, then **Import files in game**. Select multiple JPG/PNG images, review each model, and apply with one backup and automatic restart. No external editor or ShareMii file selection is needed.

A saved Palette House model is required for the category. The photo supplies its drawing; shape and properties come from the model, which is preserved. This does not generate 3D objects or Miis from photos. See [photos, models, fits and limits](docs/en/PHOTO-IMPORT.md).

## Import Miis and items inside the game

Setup **0.4.0** adds a queue for every category: **F1 → ShareMii → Content → Import → Import files in game**. Queue multiple Miis, foods, clothing, treasures, interiors, exteriors, objects and landscaping; go back to change category without losing the queue. Select **Apply queue and reload** for one backup and one automatic restart. The ShareMii editor does not open.

Miis replace **existing, initialized residents**; items use **free slots**. Up to 70 creations per queue, subject to available destinations. A failed file prevents the entire batch from replacing the active save. The menu follows Windows display language (IT/EN/DE/ES/FR/PT, English fallback). See the [categories, formats and recovery guide](docs/en/MII-QUEUE.md).

## Selection, F1 and flicker fixes

Setup **0.3.3** uses the automatic GPU profile: OpenGL on NVIDIA, Vulkan on other GPUs. On NVIDIA it selects a window with direct OpenGL presentation so F1 and ShareMii remain visible. This avoids a Vulkan selection failure reproduced on the tested PC: keyboard and controller inputs arrived, but buildings could not be selected. OpenGL restored fountain entry and normal play.

The runtime update also prevents unwritten fragment outputs from corrupting OpenGL render targets, a cause of cycling shadows. The player confirmed working controls and a stable image after the change. Vulkan's bounded texture-lifetime fix from 0.3.2 remains included. These results apply to the tested PC; they do not establish compatibility with every GPU or driver.

Complete **Existing port** installation to rebuild the host with both rendering patches. **Repair F1 menu → Repair F1 menu and selection** applies the profile alone, with a backup and no compiler/download. See [repair, renderer choices and restore](docs/en/MENU-REPAIR.md) and [rendering changes and limits](docs/en/TEXTURE-FIX.md).

## Emulator saves and interface language

**Saved games** can inspect and import a raw emulator save folder or ZIP, export the complete island as ZIP, and recover interrupted imports. Import immediately or after a new installation. The source is untouched and the previous island is backed up. Game **1.0.4** is supported without version conversion.

See the [import, export and recovery guide](docs/en/SAVE-TRANSFER.md), including restoration to an emulator. Transfer tests use synthetic fixtures; loading a real imported island remains unverified.

Setup detects the Windows display language at launch, including when opened on another PC. **Auto · Windows** chooses Italian, English, German, Spanish, French or Portuguese. Regional variants use their base language; unsupported languages fall back to English. Manual selection is available. This applies to setup; the game and original editor have their own settings, and diagnostic logs may remain in English.

## How it works

1. The upstream project statically recompiles your own game code into a native Windows program.
2. This integration rebuilds only the open-source host to add **F1 → ShareMii - Mii e oggetti**.
3. For Mii and item imports, prepare and review a queue inside F1. Select multiple files at once or add them in several passes.
4. Applying the queue waits for a confirmed save, closes the game normally, imports all files into a private copy using the verified ShareMii codecs and UGC adapter, and atomically commits the batch with a backup.
5. The native game restarts automatically to load the modified save. This is a reload, not a live engine-memory patch.
6. Export/list operations retain the original full-editor handoff: save, exit, back up, open ShareMii, then offer to resume.

The integration does not write the active island's files while the game process is running. The queue uses the verified ShareMii codecs without their GUI, with the UGC adapter described in the guide.

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
- Batch rollback, two-file commit, input preflight and read-back verification use synthetic saves. The original codec is also tested privately against a separate island copy. Keep the automatic backups; this does not certify every imported Mii or face-paint file.
- The wrapper uses **Browse** dialogs instead of drag-and-drop and exits the editor process after its synchronous GUI operations complete, addressing Windows/Tk hangs observed during local testing.
- The new queue page detects six Windows display languages. Older integration labels remain Italian; original upstream pages and the game keep their own language settings.
- The setup's source bundle, argument handling, languages, modes and rendering have a self-test. Backend tests cover archive/hash validation, preservation of unrelated files and interrupted-download resume. Its existing-install backend successfully rebuilt the custom host in an isolated copy of a supported installation. A separate full fresh-game build has not been rerun through the wizard.

## Development

```powershell
py -3.12 -m unittest discover -s tests -v
py -3.12 tools/check_upstream.py
py -3.12 tools/check_mii_queue_types.py
py -3.12 tools/audit_publication.py
```

The source smoke test downloads pinned public source files and ShareMii's own GUI assets into temporary storage. It does not fetch game content. The publication audit checks Git-tracked files, not your local game folder.


Save transfer checks additionally cover full-island round trips, preservation of creation files and source data, previous-island backups, version confirmation, manifest tampering, unsafe ZIPs, interrupted commits and recovery. The packaged CLI and post-install import were also exercised against an isolated local port with synthetic saves.

## Credits and license

GPL-3.0; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Unofficial fan integration, not affiliated with or endorsed by Nintendo. Game names and trademarks belong to their respective owners.
