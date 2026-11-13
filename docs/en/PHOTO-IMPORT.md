# Import JPG and PNG photos inside the game

From **0.5.0**, select `.jpg`, `.jpeg` and `.png` images directly in F1. The MIT converter from [PICKLERICK2005/TL-UGC-Editor](https://github.com/PICKLERICK2005/TL-UGC-Editor) is integrated without its editor window. You do not need to prepare or select ShareMii files.

## Prepare a model

Create and save at least one item in **Palette House** in the desired category, choosing its shape and properties. That model is preserved and copied into a free slot for every photo. If Palette House is not unlocked yet, progress normally until you can create a model. An existing, saved ShareMii import can also serve as a model.

A photo supplies **the drawing or texture**. It does not automatically generate a 3D shape, a new Mii, pet behavior or food properties: these come from the model. All seven UGC categories are supported: food, clothing, treasures, interiors, exteriors, objects and landscaping. The model must belong to the new creation's category.

## Import

1. Launch the normal **Tomodachi Life - Nativo + ShareMii** or **Tomodachi Life - ShareMii** shortcut and open **F1 → ShareMii**.
2. Choose **Content**, for example **Food**.
3. Choose **Mode: Photo: contain**, **Photo: crop**, or **Photo: stretch**. Contain preserves the full image with transparent padding; Crop fills the surface and crops edges; Stretch fills it by changing proportions.
4. Select **Import files in game**. The game saves and checks models and free slots. If no model is available, return to the game, create and save one, then try again.
5. Use left/right on **Photo model** to choose the initial model. Select **Add JPG / PNG...** and pick one or more photos using Ctrl/Shift.
6. Browse entries with **Review queued creation**. **Photo model** changes the model of the displayed entry; `→ #N` identifies its automatically assigned new slot. The creation uses the photo's filename within game limits. Existing creations and models are preserved.
7. Go back to change category or fit and add more photos. Fit is captured when a file is added; to change an entry's fit, remove it and add it again in the desired mode. Photos, Mii files and item files can share one queue.
8. Select **Apply queue and reload**, check the total and confirm again. The game saves and exits normally; an automatic window shows conversion progress. Drawing, main texture and thumbnail are converted, then the batch commits with one previous-save backup and the game restarts automatically. Use the normal confirmation button at the title screen.

If a queue already has entries, the displayed model belongs to the selected entry. New photos use their category's default model; review each entry to select another model.

Photos stay on your PC and are not uploaded. Source files are unchanged. Complex layouts, seams or multiple surfaces may need additional work in the game's regular editor. The thumbnail is updated with the photo; it is not a newly rendered 3D view.

## Limits and recovery

Still JPEG/PNG images are accepted up to 64 MiB, 32 megapixels and a 16,384-pixel edge. EXIF orientation is applied. PNG transparency is preserved within game-format limits (canvas and BC1 main textures use binary transparency). Other formats and incomplete files are rejected.

Only texture layouts supported by the converter are accepted; model dimensions are checked before writing. Choose another model if the layout is unsupported. Lighting and material affect colors in-game. Every model/material combination has not been visually verified.

The **70-creation queue** limit, free destinations and clothing slot range 1–256 still apply; see [the import queue guide](MII-QUEUE.md). A failed entry prevents the batch from replacing the active save. A successful batch backs up the previous island at `build/saves/imports/<timestamp_id>/save`. Restore through **Setup → Saved games → Import**, or use **Recover** after an interruption. See [save transfer and recovery](SAVE-TRANSFER.md).

## Provenance and validation

The MIT TL-UGC-Editor codec is extracted unchanged from `a4b3c45dabd8b145de3adae7e4af1fe226f6847f`; its license and attribution are included. The integration adds bounded image decoding, fitting, model cloning, queueing, backups and restart. Tests compare the included codec against SHA-256-verified source and exercise JPEG/PNG, all three fits, all seven categories in synthetic saves, converted-pixel read-back, unchanged models and invalid-second-photo rollback. No photos, models, saves or game resources are distributed.

Graphics settings and the previous OpenGL profile remain unchanged. This feature does not fix the outstanding Vulkan issue.
