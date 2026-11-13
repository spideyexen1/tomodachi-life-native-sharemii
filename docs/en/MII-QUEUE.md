# Import Miis and items inside the game

From **0.4.0**, all ShareMii import categories use the F1 queue. Select multiple files, mix categories, review destinations and apply the entire queue with **one automatic reload**. The ShareMii editor does not open.

1. Launch **Tomodachi Life - ShareMii**. Create an island and save at least once.
2. Open **F1 → ShareMii - Mii e oggetti**. Choose **Content**, leave **Mode: Import**, then select **Import files in game**. The game confirms a save before opening the queue.
3. Select **Add files...**. The Windows picker filters files for the selected category; use Ctrl/Shift to select several. You can add files repeatedly without restarting.
4. To mix categories, choose **Back**, change **Content**, and open **Import files in game** again. Existing queue entries remain. For example, queue two Miis, three foods and an object before applying.
5. Use left/right on **Review queued creation** to browse entries, showing category and name. **Destination** changes the resident or free item slot for that entry. Choosing a destination already assigned within the same category swaps those two assignments.
6. **Remove selected creation** removes only that queue entry. You can return to the game; the queue stays in memory while this session remains open. Reopening import refreshes destinations from the confirmed save.
7. Select **Apply queue and reload**, check the total count and confirm again. The game saves and exits normally. The importer prepares the complete batch on a private copy and commits it as one operation with a backup. The game restarts automatically; press the usual confirmation button at the title screen to continue.

## Categories and destinations

| Content | File | Destination |
|---|---|---|
| Mii | `.ltd` | Replaces an existing, initialized resident |
| Food | `.ltdf` | New free slot in that category |
| Clothing | `.ltdc` | New free slot in that category |
| Treasure | `.ltdg` | New free slot in that category |
| Interiors | `.ltdi` | New free slot in that category |
| Exteriors | `.ltde` | New free slot in that category |
| Objects | `.ltdo` | New free slot in that category |
| Landscaping | `.ltdl` | New free slot in that category |

These are user creations in ShareMii formats, rather than every built-in game item. Imported items enter the custom-content catalog; the queue does not automatically place them on the island. Use normal game features to use them. Files from other games or renamed formats are not converted.

**Miis** require existing residents, matching the original ShareMii importer. Files do not initialize empty slots. To keep a resident, create a placeholder resident first and check the destination. Original rules for personal data and preferences of established Miis still apply.

**Items** use free slots only in this queue; existing creations are preserved. Categories have up to 99 slots. For clothing, the adapter considers slots 1–256 to respect the original add codec's single-byte slot index. Clothing slots 257–299 are not assigned by this feature. Occupied slots or slots with partial texture files are not reused.

The limit is **70 creations per queue**, subject to available destinations. You can apply more queues later. Closing the session without applying discards its in-memory queue.

Face paint can be embedded in `.ltd` or supplied as both `<file>.ltd.canvas.zs` and `<file>.ltd.ugctex.zs`; keep the pair beside the Mii file. Items use their own `.ltdf/c/g/i/e/o/l` files with embedded textures.

## Backups and recovery

Every input and destination is checked before the first import. Pinned ShareMii 3.2.3 codecs are SHA-256 verified and used without their GUI. The UGC adapter corrects the exterior/object material texture scale write; see [NOTICE](../../NOTICE.md) for details and attribution. Names, attributes and textures are read back before commit. Files exceeding 64 MiB, incomplete compressed textures or incompatible data are rejected.

If any input fails, **none of the batch** replaces the active save. A successful batch keeps the entire previous island at **`build/saves/imports/<timestamp_id>/save`**, with a SHA-256 manifest. Restore through **Setup → Saved games → Import**, choosing that folder. See [save transfer and recovery](SAVE-TRANSFER.md). After an interruption during directory replacement, use **Recover** before launching the game.

The local summary is `integration/last-mii-import.json` (including mixed batches); errors go to `integration/mii-import-error.log`. The original game process ends and starts again, loading changes after the automatic restart. No files are uploaded.

The ShareMii page and queue follow the Windows display language: IT, EN, DE, ES, FR, PT, with English fallback. The game, original PC Settings page and full editor have their own settings. **Export, Export all and List** still use the full editor.

## Verification and Vulkan

Tests without game content exercise all seven UGC categories and a Mii in one commit, one previous-save backup, occupied destinations, the clothing boundary, read-back checks and rollback after a last-item failure. An earlier F1 test on a separate island copy confirmed Mii import, backup and automatic restart. Every combination of item or face paint has not been visually verified in-game. Test saves and imported files are not published.

Experimental Vulkan synchronization and 3D texture changes are not shipped as a definitive selection fix. NVIDIA keeps the previously verified direct-presentation OpenGL profile. This import update does not resolve that Vulkan issue; see [rendering changes and limits](TEXTURE-FIX.md).
