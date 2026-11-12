# Repair an invisible F1 menu

[Italiano](../it/MENU-REPAIR.md) · [Installation](INSTALL.md)

## Observed issue and available fix

On a tested NVIDIA RTX 3060 Ti PC, the OpenGL renderer received F1 and opened the menu internally, blocking game input, but the panel remained invisible. Logs recorded `menu: opened` while the island was still visible. Switching to **Vulkan** and restarting made both **PC Settings** and **ShareMii - Mii e oggetti** visible; both pages were checked on screen.

Setup **0.3.1** distributes this configuration fix. It works around the OpenGL rendering issue rather than changing upstream OpenGL code, and does not guarantee the same outcome on every GPU or driver. It requires a **GPU and driver supporting Vulkan 1.3**.

## Repair an existing installation

1. Save your game, close it and exit ShareMii. Avoid force-quitting the game to apply this fix.
2. Open [setup 0.3.1](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.1).
3. Select the existing port folder containing `build` in the first tab. You do not need to reselect game packages or keys for repair alone.
4. Open **Repair F1 menu → Repair F1 menu with Vulkan**. The action validates the supported port and refuses changes while its game or ShareMii/save-transfer session is running.
5. Wait for confirmation. The result shows `graphics.ini` and its backup path, if a backup was needed.
6. Restart using **Tomodachi Life - ShareMii**. Press **F1** to open **PC Settings**, then select **ShareMii - Mii e oggetti**. F1 opens and closes the panel; some laptops require Fn + F1.

Repair alone runs offline with an existing Python 3.12, including the port's private interpreter. No C++ compiler, download or recompilation is needed. Supported versions remain upstream port **1.0.3**, game **1.0.4** and the standard documented layout.

## New installations and integration updates

**Use Vulkan for the F1 menu** is checked by default in the first tab. At the end of installation, setup applies the same configuration and backs up previous preferences. Uncheck it to keep your selected renderer; doing so skips this fix. Do not enable it on a GPU without Vulkan 1.3 support.

Moving from OpenGL to Vulkan may prepare shaders again. The window can remain black during this step, with progress in its title. Vulkan preparation finished in about two and a half minutes on the tested PC; timing varies with hardware, drivers and cache. Wait for completion before checking F1.

## Changes and restoration

The fix updates only these options in `<port>/build/config/graphics.ini`:

```ini
renderer = always_vulkan
menu = on
```

`always_vulkan` is deliberate: in the supported runtime, plain `vulkan` means automatic selection and may choose OpenGL again on NVIDIA.

Language, resolution, volume and other options are retained. Before changing an existing file, setup keeps an exact `graphics.ini.menu-backup-<date_time_id>` copy alongside it. Repeating repair with an already-correct configuration creates no further backup. Island saves and game files are not modified.

To undo the fix, close the game and editor, retain a separate copy of the current `graphics.ini`, then copy the reported backup over `graphics.ini`. Restoring the old renderer may bring back the invisible panel. You can apply **Repair F1 menu** again later.

## Optional command line

From a source checkout, with the game and editor closed:

```powershell
py -3.12 tools/repair_menu.py --port-dir "C:\Games\TomodachiLife"
```

To apply the configuration while installing the integration:

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --vulkan-menu
```

CLI users opt in with the explicit flag; the GUI exposes the checked-by-default option. Repair preserves unrelated settings, creates a backup and returns a local result only. No ROMs, game updates, keys or personal saves are distributed or linked by this repository or setup.
