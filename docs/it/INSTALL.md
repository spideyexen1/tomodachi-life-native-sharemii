# Installazione e utilizzo su Windows

[English](../en/INSTALL.md) · [Presentazione del progetto](../../README.it.md)

## Installazione guidata

1. Scarica il `.exe` dalla [release del setup](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.4.0) e aprilo. Il wizard usa .NET Framework di Windows e si apre anche senza Python già presente.
2. Mantieni **Auto · Windows** oppure scegli una lingua (IT, EN, DE, ES, FR, PT; fallback inglese). Seleziona **Nuova installazione / riprendi** per una nuova compilazione oppure **Port già installato** per una build supportata già completata.
3. Indica la cartella. Per una nuova installazione scegli il tuo gioco base, il pacchetto aggiornamento 1.0.4 e `prod.keys`. Sono accettati soltanto file locali, che non vengono caricati online.
4. In **Requisiti**, installa Python/C++ mancanti con i pulsanti oppure seleziona un Python 3.12 completo già presente. Se Microsoft lo richiede, conferma il normale avviso amministratore di Windows. Quando WinGet non è disponibile, il wizard può aprire le pagine ufficiali dei download.
5. Premi **Installa**. Per una nuova installazione vengono scaricati e verificati gli strumenti open source originali, compilato il tuo gioco, preparati gli shader e aggiunto il menu ShareMii con i collegamenti. Per un port già pronto viene eseguita direttamente l'integrazione.
6. Usa **Avvia gioco** oppure il nuovo collegamento. Per riprendere dopo un'interruzione, riapri il setup con la stessa cartella e gli stessi file: download degli strumenti e passaggi di compilazione già completati vengono conservati.

Non scegliere cartelle con file estranei. I salvataggi esistenti vengono conservati. I log restano locali e possono contenere percorsi del PC; non vengono caricati automaticamente. Il setup non firmato e il relativo checksum SHA-256 sono pubblicati insieme ai sorgenti della release. La prima compilazione completa può richiedere un'ora o più.

Il metodo manuale seguente resta disponibile per chi preferisce usare i sorgenti.

## Cosa serve

- Windows 10 o 11 **x86 a 64 bit**. Questa integrazione non dispone di installer per Linux, macOS o ARM64.
- Scheda video con **Vulkan 1.3 oppure OpenGL 4.5**. Selezione del renderer e impostazioni grafiche sono gestite dal port originale.
- Almeno **8 GB di RAM**, preferibilmente **16 GB o più**, e file di paging Windows attivo. Prevedi circa **15 GB liberi per il port**, oltre allo spazio per strumenti di compilazione e backup.
- Il dump della tua copia del gioco base, il tuo **aggiornamento 1.0.4** e il file `prod.keys` della tua console, usati localmente dall'installer originale. Questa repository non offre file del gioco né collegamenti per scaricarli.
- Installazione completata del [port nativo originale 1.0.3](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/releases/tag/v1.0.3), con struttura standard `<port>/build`.
- Installazione completa di **Python 3.12 x64 con Tcl/Tk**, interprete usato nelle verifiche dell'integrazione. Usa le [release ufficiali Python per Windows](https://www.python.org/downloads/windows/); la distribuzione embedded senza Tk non è sufficiente.
- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) con carico di lavoro **Sviluppo di applicazioni desktop con C++**, strumenti MSVC x64 e Windows SDK. Servono per ricompilare il runtime con il nuovo menu, anche se il port originale usava un runtime precompilato.
- Connessione Internet per scaricare dipendenze open source. Git è utile per clonare la repository; è possibile anche scaricarne lo ZIP dei sorgenti.

I numeri di versione sono distinti: **port 1.0.3 / gioco 1.0.4 / ShareMii 3.2.3**.

## 1. Prepara il port originale

Segui le istruzioni del progetto originale e fornisci localmente i tuoi file, aggiornamento e chiavi. Completa compilazione e preparazione degli shader, poi verifica che il gioco originale si avvii. La prima preparazione può essere lunga: questa integrazione non sostituisce la compilazione del gioco base.

Mantieni la struttura interna predefinita. Esempio:

```text
C:\Games\TomodachiLife\
  runtime\menu.cpp
  scripts\run.py
  build\state.json
  build\binaries\1.0.4\main.elf
  build\work\tomodachi_game.dll
  build\userdata\save\
```

Questi file generati vengono creati sul tuo computer. Non copiarli in questa repository e non caricarli su GitHub.

## 2. Installa l'integrazione

Chiudi gioco e finestre di ShareMii. Scarica o clona questa repository in una cartella **separata** dal port:

```powershell
git clone https://github.com/spideyexen1/tomodachi-life-native-sharemii.git
cd tomodachi-life-native-sharemii
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --check-only
```

Sostituisci il percorso di esempio con quello della tua installazione. `--check-only` controlla compatibilità della build locale, Python e compilatore senza scaricare o modificare file. Può essere eseguito con il gioco aperto; l'installazione effettiva richiede che il gioco sia chiuso.

Poi esegui:

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife"
```

L'installer crea o riutilizza `<port>/deps/python-venv`, installa lì le dipendenze GUI, scarica i sorgenti fissati di ShareMii controllandone gli hash, prepara le dipendenze del runtime originale, conserva una copia di `menu.cpp`, applica la patch F1 e compila `tomodachi_sharemii.exe`. Crea inoltre collegamenti dedicati. Preferenze grafiche e isola esistente non vengono sostituite.

L'eseguibile originale `tomodachi_native.exe` resta separato. Conserva anche questa repository per eventuali reinstallazioni e controlli della patch.

Per evitare la creazione dei collegamenti, aggiungi `--no-shortcuts`. Avvio manuale:

```powershell
& "C:\Games\TomodachiLife\deps\python-venv\Scripts\pythonw.exe" "C:\Games\TomodachiLife\integration\play-native.py"
```

## 3. Gioca e apri ShareMii

Usa **Tomodachi Life - ShareMii** sul desktop/menu Start oppure **Tomodachi Life + ShareMii** nella cartella del port. Il launcher rende esplicitamente visibile la finestra nell'avvio diretto. Dopo una ricompilazione o un aggiornamento del driver grafico, il primo avvio può richiedere una nuova preparazione degli shader.

Crea l'isola e salva almeno una volta. Apri **F1 → ShareMii - Mii e oggetti**. Puoi aprire le impostazioni del port anche con il tasto HOME/Guide del controller.

### Coda per importare Mii e oggetti

Per qualsiasi categoria, scegli **Importa → Importa dal gioco**. Seleziona piu file del formato corretto, controlla le destinazioni e applica la coda con un solo ricaricamento automatico. Puoi tornare indietro e cambiare categoria, mantenendo le voci gia accodate. I Mii sostituiscono abitanti inizializzati; gli oggetti usano slot liberi. Vedi [categorie, formati, limiti e recupero](MII-QUEUE.md).

I comandi dell'editor completo descritti sotto riguardano **Esporta, Esporta tutti ed Elenca**.

| Voce | Funzione |
|---|---|
| Contenuto | Categoria; usa sinistra/destra per cambiarla |
| Modalita | Importa, Esporta, Esporta tutti oppure Elenca |
| Salva e apri ShareMii | Salva, chiude la partita, crea il backup e apre l'editor |
| Cartella import / export | Apre la cartella consigliata per gli scambi |
| Backup automatici | Apre la cartella dei backup |
| Indietro | Torna al menu precedente |

Il passaggio all'editor avviene solo dopo la conferma del salvataggio da parte del gioco. Se non è disponibile, torna sull'isola e riprova. Nell'editor usa **Browse** per scegliere file/cartelle, controlla lo slot e premi **Start!**. Un'importazione può sostituire quello slot. Chiudi l'editor e rispondi alla richiesta di riavvio per rientrare nel gioco nativo.

## Cartelle e ripristino

Percorsi relativi all'installazione del port:

| Percorso | Contenuto |
|---|---|
| `build/saves/imports/<data_ora_id>/save` | Partita completa precedente a una coda di importazioni |
| `build/userdata/save` | Salvataggio attuale confermato |
| `build/saves/sharemii/<data_ora>/save` | Backup completo precedente all'editor, comprese le creazioni |
| `build/saves/sharemii/<data_ora>/manifest.json` | Hash SHA-256 del backup |
| `Scambi` | Cartella consigliata per i contenuti da scambiare |
| `build/logs` | Log del gioco e dell'editor |
| `integration` | Sorgenti installati di bridge e launcher |

I backup non vengono cancellati automaticamente. Per ripristinarne uno, chiudi gioco ed editor, apri **Tomodachi Life Launcher.exe**, scegli **SAVE DATA → IMPORT A SAVE** e seleziona la sottocartella `save` del backup desiderato. Il launcher originale conserva i dati attuali prima dell'importazione. Successivamente avvia dal collegamento dedicato a ShareMii.

## Problemi e aggiornamenti

- **Versione non supportata o menu modificato:** usa la versione originale documentata. La patch rifiuta modifiche estranee anziché sovrascriverle. Una nuova versione del port richiede una verifica di compatibilità.
- **Compilatore/Tk mancanti:** installa i prerequisiti indicati. Il Python embedded del port non sostituisce l'interprete completo richiesto dalla GUI.
- **Editor ancora aperto/sessione attiva:** chiudi l'editor normalmente prima di riavviare. Dopo un crash, i file di sessione obsoleti vengono sostituiti quando il processo registrato non esiste più.
- **Salvataggio o slot mancanti:** completa la configurazione iniziale e salva nel gioco. Le categorie disponibili dipendono anche dalle creazioni esistenti.
- **Finestra del gioco assente:** usa il collegamento ShareMii dedicato, che abilita la visibilità nell'avvio diretto.
- **Errore nell'editor:** controlla `build/logs/sharemii-editor.log` e `integration/editor-*.log`. Un backup fallito impedisce l'apertura dell'editor.
- **Aggiornamento del port:** conserva salvataggi e backup e verifica la compatibilità prima di riapplicare l'integrazione. Non forzare una patch su un menu cambiato.

Installer e test sono controllabili senza distribuire contenuti del gioco. L'import/export su un'isola reale non è stato verificato da inizio a fine in questa versione: conserva i backup e consulta le istruzioni originali di ShareMii per i suoi formati.

## Salvataggi e lingua automatica

Vedi la [guida dedicata a importazione, esportazione e ripristino](SAVE-TRANSFER.md). Il setup 0.3.0 rileva la lingua di Windows e offre IT, EN, DE, ES, FR e PT con fallback inglese.

## Menu F1 invisibile

Il setup 0.3.3 propone il profilo GPU automatico per F1 e selezione: OpenGL in finestra con presentazione diretta su NVIDIA, Vulkan sulle altre GPU. Per la sola configurazione usa **Ripara menu F1**; per la patch delle ombre completa **Port già installato**. Vedi [riparazione](MENU-REPAIR.md) e [correzioni grafiche](TEXTURE-FIX.md).
