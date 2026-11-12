# Build the Windows setup

The wizard is a C# Windows Forms application built with Windows' .NET Framework compiler. Python builds its embedded source ZIP; no game installation is used when packaging.

From a Git checkout with the intended source files tracked:

```powershell
py -3.12 tools/build_setup.py --out dist
```

The build first runs the publication audit. Its bundle is an explicit subset of Git-tracked source, documentation and license files. Generated game files, keys, saves and the local installation are never read by the packager. The output contains the setup executable and its `.sha256` checksum.

To test the executable without installing anything:

```powershell
$qa = Join-Path $PWD 'dist\qa'
$image = Join-Path $PWD 'dist\preview.png'
$process = Start-Process -FilePath '.\dist\Tomodachi-Life-Native-ShareMii-Setup.exe' -ArgumentList @('--self-test','--work-dir',('"' + $qa + '"'),'--snapshot',('"' + $image + '"')) -WindowStyle Hidden -PassThru -Wait
Get-Content (Join-Path $qa 'self-test.txt')
if ($process.ExitCode -ne 0) { throw 'Setup self-test failed' }
```

The self-test extracts only the embedded source bundle, checks Windows argument quoting and control states, switches languages and renders the wizard's own controls off-screen. It does not capture the desktop, install prerequisites or start a game build.

GitHub Actions runs this build and self-test and uploads a `Windows-Setup` artifact. Published release binaries are unsigned; their checksums accompany them. The complete source, including `setup/SetupWizard.cs`, is available in the tagged source release under GPL-3.0.
