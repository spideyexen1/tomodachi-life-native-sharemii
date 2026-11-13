# Invisible F1 or buildings that cannot be selected

Setup **0.3.3** corrects the profile used by earlier versions. On the tested NVIDIA PC, Vulkan made F1 visible but prevented building selection although keyboard and DualSense input reached the game. OpenGL restored selection; its menu remained invisible only with DXGI presentation. Direct OpenGL presentation made both usable.

## Procedure

1. Save and normally close the game and ShareMii.
2. Open setup 0.3.3 and select the existing port folder in the first tab.
3. Choose **Repair F1 menu → Repair F1 menu and selection**.
4. Restart through the Native + ShareMii shortcut and press **F1**. ShareMii remains in PC Settings.
5. To install the shadow flicker fix too, complete **Existing port**: repair alone changes preferences and needs no C++ compiler or download.

The automatic profile writes:

```ini
renderer = auto
menu = on
present_api = opengl
window = windowed
```

The port selects OpenGL on NVIDIA and Vulkan on other cards. `present_api` affects OpenGL alone. Windowed mode also avoids an older fullscreen composition problem observed on some drivers. Volume, language and resolution are preserved. Shader preparation may run again; wait for completion.

The OpenGL menu requires OpenGL 4.6 and the extensions required by the port. Vulkan requires Vulkan 1.3. This was checked on one NVIDIA configuration, not every GPU.

## Source tools

With Python 3.12:

```powershell
py -3.12 tools/repair_menu.py --port-dir "C:\Games\TomodachiLife"
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --menu-renderer auto
```

The first line changes configuration only; the second also updates the host. Explicit alternatives for the first line are `--renderer opengl` and `--renderer vulkan`. For installation use `--menu-renderer opengl` or `--menu-renderer vulkan`. Legacy `--vulkan-menu` remains compatible but forces Vulkan; it is not the recommended profile on the PC with this selection failure.

## Restore

Every change keeps the original at `build/config/graphics.ini.menu-backup-<date>_<id>` and displays its path. Close the game and editor, keep a copy of the current configuration, then copy the desired backup over `build/config/graphics.ini`. Changes are refused while a game, editor or save-transfer session is active. Saves are not changed.

If F1 opens invisibly, press F1 again to return input to the game before saving and closing. In the game, PlayStation cross is confirm: **✕ / Enter / Space**. Keyboard letter X is a different command.
