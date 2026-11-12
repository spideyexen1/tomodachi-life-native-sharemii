# Import, export and restore an island

[Italiano](../it/SAVE-TRANSFER.md) · [Installation](INSTALL.md)

Setup **0.3.0** adds **Saved games**. It transfers a complete island, including the `Ugc` creations folder; it does not merge two islands. Use the F1 ShareMii menu for individual Mii or items instead.

## Requirements

- Upstream port 1.0.3, game **1.0.4**, standard `<port>/build` layout and Python 3.12. Save transfers alone need no C++ installation or game recompilation.
- Fully close the native game, ShareMii and the emulator. Keep them closed throughout the transfer.
- Use a save from the same game at **1.0.4**. There is no version conversion. Raw emulator folders do not reliably identify their game version, so setup requires your explicit confirmation.
- Choose a raw save folder or save ZIP, not an emulator savestate, NAND image or entire emulator profile. Limits: 20,000 files and 2 GiB uncompressed. Missing files, ambiguous profiles, links and unsafe archive paths are rejected.

The structural check requires nonempty `Map.sav`, `Mii.sav` and `Player.sav`, and preserves every other save file. It cannot fully validate the island's internal contents. Transfers and recovery are tested with synthetic fixtures; loading a real imported island has not been verified end to end.

## Emulator to native port

1. Save in the emulator and stop emulation. Open the save directory for the correct game and user through its context menu. Eden calls this **Open Save Data Location**; see its [official guide](https://github.com/eden-emulator/mirror/blob/master/docs/user/ImportingSaves.md). Other emulators may call it **Open User Save Directory** or use a translated label.
2. Close the emulator. Keep a separate copy of the entire folder, including `Ugc` and all subfolders. Select one user's game save, not a directory containing several users or games.
3. Open setup and select the **port folder** containing `build` in the first tab. To update an older integration, complete **Existing port** installation once so its launcher also receives the active-transfer guard.
4. Open **Saved games → Folder...** or **ZIP...**, select the save, then click **Inspect source**. ZIP exports from this setup include a SHA-256 manifest that is verified before importing.
5. If the folder or ZIP has no version metadata, check the game 1.0.4 confirmation only after verifying the version in your emulator.
6. Click **Import now** and confirm replacement. Setup keeps the source untouched, prepares a verified copy, and preserves the previous island under `<port>/build/saves/imports/<date_time_id>/save`. The result shows the exact path. Retain this backup until you have checked the imported game.
7. Wait for **Operation complete**, then start the native game using the ShareMii shortcut and check the island.

For a new installation, select your save first and enable **Import the selected save after installation**. Return to the first tab and continue. The source is checked before the build; the transfer takes place after the port and integration are installed. If installation succeeds but save import fails, fix the reported problem and use **Import now** without recompiling.

## Export from the native port

1. Save in game, close it and wait for its process to exit. Close ShareMii too.
2. Select your port folder in setup, then open **Saved games → Export ZIP**.
3. Choose a new ZIP outside the active save directory. Existing archives are never overwritten.
4. Wait for confirmation. The ZIP includes all island files plus `native-sharemii-export.json` recording version and hashes. Reimport it through **ZIP... → Import now**; a valid manifest avoids the unknown-version confirmation.

### Restore an export to an emulator

Use the same game updated to 1.0.4. Open the correct user's save directory from the emulator menu, then close the emulator. Back up its entire current contents separately and move them out of the active directory. Extract the ZIP to a temporary folder, then copy **all raw save files and subfolders**, including `Ugc`, directly into the empty active save directory. Do not copy the ZIP itself, an extra containing folder or `native-sharemii-export.json`. Start the emulator and verify the island; if it fails to load, restore the previous copy with both applications closed.

This transfers raw saves only. It does not configure emulators or transfer keys or other system data.

## Restore and recover

**Restore a previous island:** choose the `save` folder inside a `build/saves/imports` backup using **Folder...**, confirm game version 1.0.4, then **Import now**. The island being replaced is preserved in another backup. Existing ShareMii backups in `build/saves/sharemii` are separate.

**Interrupted import:** do not manually move `.save-import-*` files. With everything closed, select the port and use **Recover interrupted import**. A fully installed new island is preserved; an unfinished replacement restores the previous island. Recovery handles an incomplete transaction, rather than undoing a completed import. The updated launcher blocks startup while an import needs recovery.

**Interrupted game commit:** if setup reports `save.commit`, start and close the native game normally so it can complete its own recovery, then retry. Do not delete the game's journals. If an import is also pending and the launcher blocks startup, retain `build/userdata` and the backups unchanged for manual inspection before proceeding.

## Automatic interface language

Setup detects the **Windows display language at launch**, rather than the country where it was downloaded. Italian, English, German, Spanish, French and Portuguese are available; regional variants use their base language. **Auto · Windows** follows the system, while the language menu also allows a manual choice. Unsupported languages fall back to English. Translation catalogs are bundled and work offline.

This setting applies to setup and Saved games. The game and original editor have their own language settings; upstream tool logs and diagnostic details may remain in English. Full guides are provided in English and Italian.

## Optional command line

From a source checkout with all applications closed:

```powershell
py -3.12 payload/save_transfer.py inspect --source "C:\MySave"
py -3.12 payload/save_transfer.py import --port-dir "C:\Games\TomodachiLife" --source "C:\MySave" --allow-unknown-version
py -3.12 payload/save_transfer.py export --port-dir "C:\Games\TomodachiLife" --output "C:\Backups\island.zip"
py -3.12 payload/save_transfer.py recover --port-dir "C:\Games\TomodachiLife"
```

`--allow-unknown-version` explicitly confirms game 1.0.4. It does not override an incompatible version recorded in an export manifest. Save files remain local and are never uploaded or published.
