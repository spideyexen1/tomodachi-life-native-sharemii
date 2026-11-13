# Rendering fixes

Since setup **0.3.3**, OpenGL disables writes to attachments for which the fragment shader declares no output. The game may bind the same texture as two attachments: the unwritten second output could overwrite the shadow with undefined values. The mask comes from the same shader header used by the port's translator; clear masks remain separate. A game-free native C check and a live game run verify the change; the player confirmed a stable image on the affected PC.

The [upstream report](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/issues/34) describes this kind of write; [Khronos documentation](https://wikis.khronos.org/opengl/Fragment_Shader) explains undefined unwritten outputs. We distribute our own source patch, without experimental executables. Complete **Existing port** in setup 0.3.3 to update. F1 repair alone does not rebuild the host.

Building selection failed under Vulkan on the tested PC. The automatic profile returns NVIDIA to OpenGL and uses direct presentation to keep F1 visible. Fountain entry, Mii editing and the menu were checked. See the [profile guide](MENU-REPAIR.md). Other port or driver defects may remain.

## Vulkan texture fix from 0.3.2


[Italiano](../it/TEXTURE-FIX.md) · [F1 menu](MENU-REPAIR.md) · [Installation](INSTALL.md)

Setup **0.3.2** adds an open-source runtime fix for Vulkan textures finalized by the game while recorded commands still reference their descriptors. Previously the Vulkan path could replace them with a blank texture, making objects or parts of the scene dark for a frame or intermittently missing.

The change follows the bounded lifetime policy already used by the supported port's OpenGL backend: keep an existing GPU image while its descriptor remains referenced and recently used. Do not recreate the texture from guest memory after finalization. Retention is time-bounded; eventual destruction still uses the existing Vulkan fence mechanism.

The [upstream flicker report](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/issues/34) also describes released textures being drawn blank on Vulkan. This repository supplies its own source change against pinned version 1.0.3; it does not embed experimental executables attached to that discussion.

## Apply the fix

1. Save and close the game and editor.
2. Open [setup 0.3.3](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.3).
3. Choose **Existing port**, select the folder containing `build`, and complete integration installation. Only the open-source host is rebuilt; game code does not need recompilation.
4. Restart through the ShareMii shortcut and revisit affected scenes.

The standalone **Repair F1 menu** tab changes graphics settings only. Apply this runtime change through **Existing port** installation. New installations automatically receive the texture fix too.

Supported versions remain upstream port **1.0.3**, game **1.0.4** and standard layout. Rebuilding the host needs the documented C++ prerequisites. The patch does not alter saves or set volume. For F1 and selection, use the [updated GPU profile](MENU-REPAIR.md).

## Validation and limits

- The modified runtime was compiled and launched on the affected NVIDIA RTX 3060 Ti PC. F1 and 50% volume were checked; the player reported stability in the revisited scenes. Logs confirmed retained textures were sampled instead of being discarded.
- A C regression check compiles the actual modified functions and exercises descriptor resolution, retention, release, list compaction and lifetime bounds without game data.
- Pinned-source checks cover hashes, idempotence, synchronization to the compiled source copy and refusal of unrelated edits.
- This does not certify every island, GPU or driver. Other rendering faults and black screens may have different causes. It is not a general fix for every upstream graphical issue.

Original source is retained as `<port>/runtime/nvn_gl.upstream.c`; the compiler uses `<port>/build/work/nvn_gl.c`. Do not replace a running game's executable with an older build. To roll back, preserve saves and restore both source and host from a previous backup with the game and editor closed.

## Developers

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --menu-renderer auto
py -3.12 tools/check_upstream.py
py -3.12 tools/check_texture_lifetime.py
```

The last check requires GCC and fetches only pinned open-source code unless `--source` is supplied. Game files, keys and personal saves are not distributed or uploaded.
