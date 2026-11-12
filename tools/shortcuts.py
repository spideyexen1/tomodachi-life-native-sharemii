# SPDX-License-Identifier: GPL-3.0-only
"""Create normal Windows shortcuts, without an unsigned bootstrap executable."""
import os
from pathlib import Path
import subprocess

SCRIPT = r'''
$ErrorActionPreference = 'Stop'
$port = $env:TOMO_INTEGRATION_PORT
$shell = New-Object -ComObject WScript.Shell
$paths = @(
    (Join-Path $port 'Tomodachi Life + ShareMii.lnk'),
    (Join-Path $shell.SpecialFolders('Desktop') 'Tomodachi Life - ShareMii.lnk'),
    (Join-Path $shell.SpecialFolders('Programs') 'Tomodachi Life - ShareMii.lnk')
)
foreach ($path in $paths) {
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = Join-Path $port 'deps\python-venv\Scripts\pythonw.exe'
    $shortcut.Arguments = '"' + (Join-Path $port 'integration\play-native.py') + '"'
    $shortcut.WorkingDirectory = $port
    $icon = Join-Path $port 'build\work\tomodachi.ico'
    if (Test-Path -LiteralPath $icon) { $shortcut.IconLocation = $icon + ',0' }
    $shortcut.Description = 'Native Tomodachi Life + ShareMii integration'
    $shortcut.Save()
    Write-Output $path
}
'''


def create(port: Path) -> None:
    powershell = Path(os.environ["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    env = dict(os.environ, TOMO_INTEGRATION_PORT=str(port))
    subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-Command", SCRIPT], env=env, check=True)
