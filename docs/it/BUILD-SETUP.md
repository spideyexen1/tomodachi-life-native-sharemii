# Compilare il setup Windows

Il wizard è un'applicazione C# Windows Forms compilata con il compilatore .NET Framework di Windows. Python prepara lo ZIP dei sorgenti incorporato; il pacchetto non utilizza l'installazione del gioco.

Da un checkout Git con i sorgenti desiderati tracciati:

```powershell
py -3.12 tools/build_setup.py --out dist
```

La compilazione esegue prima il controllo dei file pubblicabili. Il bundle include un insieme esplicito di sorgenti, documentazione e licenza tracciati da Git. Il packager non legge file generati dal gioco, chiavi, salvataggi o l'installazione locale. Produce il setup e il relativo checksum `.sha256`.

Per provare l'eseguibile senza installare nulla:

```powershell
$qa = Join-Path $PWD 'dist\qa'
$image = Join-Path $PWD 'dist\preview.png'
$process = Start-Process -FilePath '.\dist\Tomodachi-Life-Native-ShareMii-Setup.exe' -ArgumentList @('--self-test','--work-dir',('"' + $qa + '"'),'--snapshot',('"' + $image + '"')) -WindowStyle Hidden -PassThru -Wait
Get-Content (Join-Path $qa 'self-test.txt')
if ($process.ExitCode -ne 0) { throw 'Setup self-test failed' }
```

Il self-test estrae solo il bundle dei sorgenti, verifica argomenti Windows e stati dei controlli, cambia lingua e disegna fuori schermo i controlli del wizard. Non cattura il desktop, non installa prerequisiti e non avvia la compilazione del gioco.

GitHub Actions esegue compilazione e self-test e produce l'artefatto `Windows-Setup`. I binari delle release non sono firmati digitalmente; sono accompagnati dai checksum. I sorgenti completi, compreso `setup/SetupWizard.cs`, sono nella release dei sorgenti associata al tag, sotto GPL-3.0.
