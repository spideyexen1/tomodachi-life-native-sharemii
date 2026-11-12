# Tomodachi Life Native + ShareMii

[Guida completa in italiano](docs/it/INSTALL.md) · [English installation guide](docs/en/INSTALL.md) · [English README](README.md)

Integrazione ShareMii, distribuita come soli sorgenti, per il **port nativo Windows non ufficiale di Tomodachi Life: Living the Dream**.

Il port originale è [TomodachiLife-recomp di josiahg2502-glitch](https://github.com/josiahg2502-glitch/TomodachiLife-recomp). Questa repository aggiunge **menu F1, backup e avvio** usando [ShareMii di Star-F0rce](https://github.com/Star-F0rce/ShareMii). La paternità dei due progetti originali resta ai rispettivi autori.

**Qui non sono inclusi né collegati ROM, aggiornamenti del gioco, chiavi della console, firmware, salvataggi, risorse estratte o eseguibili derivati dal gioco. L'installer originale richiede i tuoi file del gioco e le tue chiavi.**

## Setup guidato Windows

Scarica [**Native + ShareMii Setup**](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.1): un piccolo `.exe` Windows x64 con **lingua automatica da Windows** (IT, EN, DE, ES, FR, PT; inglese per le altre lingue), scelta dei file locali, controllo dei prerequisiti, avanzamento, log e ripresa dell'installazione.

Scegli **Nuova installazione / riprendi** per compilare usando il tuo gioco base, aggiornamento e chiavi, oppure **Port già installato** per aggiungere l'integrazione a una build completata. I pulsanti WinGet permettono di installare Python e Microsoft C++ Build Tools mancanti; Windows può chiedere la conferma amministratore. Se WinGet non è disponibile, vengono proposte le pagine ufficiali dei prerequisiti.

Il setup si apre anche senza Python già installato; Python serve poi alla compilazione e all'editor. La prima compilazione del gioco e degli shader può richiedere un'ora o più. Il pacchetto contiene solo sorgenti/strumenti di questo progetto e scarica separatamente gli strumenti originali fissati. Non è firmato digitalmente.

## Correzione compatibilità menu F1

Il setup **0.3.1** aggiunge **Ripara menu F1**, che abilita Vulkan e il menu dopo aver conservato una copia delle impostazioni grafiche. Per installazioni e aggiornamenti è disponibile **Usa Vulkan per il menu F1**, preselezionato. Serve una GPU Vulkan 1.3; deseleziona l'opzione per mantenere il renderer scelto.

Questa correzione di configurazione ha risolto il menu che si apriva internamente ma rimaneva invisibile con OpenGL sul PC NVIDIA verificato. Non modifica il codice OpenGL originale. F1 e la pagina ShareMii sono stati verificati a schermo dopo il riavvio con Vulkan. Al primo avvio Vulkan può essere necessaria una nuova preparazione degli shader. Segui la [guida alla riparazione e al ripristino delle preferenze](docs/it/MENU-REPAIR.md). La sola riparazione non richiede C++, download o ricompilazioni.

## Salvataggi da emulatore e lingua

La scheda **Salvataggi** permette di verificare e importare una cartella raw o uno ZIP da un emulatore, esportare l'intera isola in ZIP e recuperare importazioni interrotte. Puoi importare subito o al termine di una nuova installazione. La sorgente resta intatta e l'isola precedente viene conservata in un backup. È supportato il gioco **1.0.4**, senza conversioni tra versioni.

Segui la [guida importazione/esportazione e ripristino](docs/it/SAVE-TRANSFER.md), anche per riportare un'esportazione nell'emulatore. Le prove dei trasferimenti usano dati sintetici; il caricamento di un'isola reale importata resta da verificare.

Il setup rileva la lingua di visualizzazione di Windows all'avvio, anche su un PC diverso da quello del download. Il menu **Auto · Windows** sceglie fra italiano, inglese, tedesco, spagnolo, francese e portoghese. Le varianti regionali usano la lingua base; le lingue non supportate usano l'inglese. È possibile cambiare lingua manualmente. Questa scelta riguarda il setup; gioco ed editor originale mantengono le proprie impostazioni, e i log diagnostici possono rimanere in inglese.

## Come funziona

1. Il progetto originale ricompila staticamente il codice della tua copia in un programma Windows nativo.
2. Questa integrazione ricompila solo il runtime open source per aggiungere **F1 → ShareMii - Mii e oggetti**.
3. Scegli categoria e modalità: Importa, Esporta, Esporta tutti oppure Elenca.
4. Il menu richiede un salvataggio, aspetta la conferma del gioco e chiude la partita.
5. Il bridge attende la fine del processo, copia l'intero salvataggio confermato e crea un manifesto SHA-256.
6. Si apre l'editor originale ShareMii con cartella, categoria e modalità già selezionate. Alla chiusura puoi riavviare il gioco nativo.

La modifica avviene nell'editor originale con il gioco chiuso. L'integrazione non implementa nuovi codec per Mii/oggetti e non scrive nei file dell'isola mentre la partita è aperta.

ShareMii espone Mii, cibo, vestiti, tesori, interni, esterni, oggetti e paesaggio. Le operazioni disponibili dipendono dal salvataggio e dall'editor originale.

## Configurazione supportata

Windows 10/11 x64, port originale **1.0.3**, gioco locale aggiornato alla **1.0.4**, struttura standard `<port>/build`, **Python 3.12 x64 con Tcl/Tk**, Microsoft C++ Build Tools con strumenti desktop C++ e Windows SDK. ShareMii **3.2.3** viene scaricato da un commit fissato e controllato tramite SHA-256.

Questa prima versione dell'integrazione accetta solo le versioni documentate. Un menu originale sconosciuto o modificato separatamente viene rifiutato.

## Installazione rapida

Completa prima l'installazione del port originale usando i tuoi file, poi chiudi gioco ed editor. Mantieni questa repository separata dalla cartella del gioco.

```powershell
git clone https://github.com/spideyexen1/tomodachi-life-native-sharemii.git
cd tomodachi-life-native-sharemii
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --check-only
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife"
```

Avvia **Tomodachi Life - ShareMii** dal desktop oppure **Tomodachi Life + ShareMii** nella cartella del port. Crea l'isola e salva almeno una volta prima di usare l'editor. Al primo avvio dopo la ricompilazione può essere necessaria una preparazione degli shader: attendine la conclusione.

## Verifiche e limiti

- L'integrazione locale originale è stata compilata e verificata a schermo: avvio in italiano, menu F1 e selezione delle categorie. Nella sequenza introduttiva sono stati osservati circa 60 fps; non è una garanzia sulle prestazioni di un'isola completa.
- Backup, attesa della chiusura del processo e controllo delle sessioni attive sono testati con dati sintetici, senza file del gioco.
- Un controllo sui sorgenti originali fissati verifica applicazione della patch, ripetibilità, conservazione dell'originale e rifiuto di modifiche estranee.
- L'import/export su un'isola reale già sviluppata **non è stato verificato da inizio a fine**. Conserva i backup automatici.
- Il wrapper usa **Browse** al posto del trascinamento e termina il processo dell'editor dopo le operazioni sincrone della GUI, per evitare blocchi Windows/Tk riscontrati nelle prove locali.
- Il setup dispone di un self-test per pacchetto sorgenti, argomenti, lingue, modalità e rendering. I test del backend coprono archivi/hash, protezione dei file estranei e ripresa dei download. Il backend per port già installati ha ricompilato correttamente il runtime in una copia isolata di un'installazione supportata. Non è stata ripetuta una compilazione completa del gioco da zero attraverso il wizard.

Requisiti completi, ripristino e risoluzione dei problemi sono nella [guida italiana](docs/it/INSTALL.md).


I controlli sui salvataggi coprono inoltre andata/ritorno dell'isola intera, conservazione di creazioni e sorgente, backup dell'isola precedente, conferma della versione, manifesti alterati, ZIP non sicuri, commit interrotti e recupero. Il CLI incorporato e l'importazione dopo il setup sono stati provati anche su un port locale isolato con salvataggi sintetici.

## Crediti e licenza

GPL-3.0: [LICENSE](LICENSE) e [NOTICE.md](NOTICE.md). Integrazione amatoriale non ufficiale, non affiliata né approvata da Nintendo. Nomi e marchi appartengono ai rispettivi titolari.
