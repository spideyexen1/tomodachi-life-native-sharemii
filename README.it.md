# Tomodachi Life Native + ShareMii

[Guida completa in italiano](docs/it/INSTALL.md) · [English installation guide](docs/en/INSTALL.md) · [English README](README.md)

Integrazione ShareMii, distribuita come soli sorgenti, per il **port nativo Windows non ufficiale di Tomodachi Life: Living the Dream**.

Il port originale è [TomodachiLife-recomp di josiahg2502-glitch](https://github.com/josiahg2502-glitch/TomodachiLife-recomp). Questa repository aggiunge **menu F1, backup e avvio** usando [ShareMii di Star-F0rce](https://github.com/Star-F0rce/ShareMii). La paternità dei due progetti originali resta ai rispettivi autori.

**Qui non sono inclusi né collegati ROM, aggiornamenti del gioco, chiavi della console, firmware, salvataggi, risorse estratte o eseguibili derivati dal gioco. L'installer originale richiede i tuoi file del gioco e le tue chiavi.**

## Setup guidato Windows

Scarica [**Native + ShareMii Setup**](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.5.0): un piccolo `.exe` Windows x64 con **lingua automatica da Windows** (IT, EN, DE, ES, FR, PT; inglese per le altre lingue), scelta dei file locali, controllo dei prerequisiti, avanzamento, log e ripresa dell'installazione.

Scegli **Nuova installazione / riprendi** per compilare usando il tuo gioco base, aggiornamento e chiavi, oppure **Port già installato** per aggiungere l'integrazione a una build completata. I pulsanti WinGet permettono di installare Python e Microsoft C++ Build Tools mancanti; Windows può chiedere la conferma amministratore. Se WinGet non è disponibile, vengono proposte le pagine ufficiali dei prerequisiti.

Il setup si apre anche senza Python già installato; Python serve poi alla compilazione e all'editor. La prima compilazione del gioco e degli shader può richiedere un'ora o più. Il pacchetto contiene solo sorgenti/strumenti di questo progetto e scarica separatamente gli strumenti originali fissati. Non è firmato digitalmente.

## Importare foto JPG e PNG

Il setup **0.5.0** integra il convertitore MIT di [TL-UGC-Editor](https://github.com/PICKLERICK2005/TL-UGC-Editor) nel menu F1. Scegli una categoria di oggetti, **Modalita: Foto: adatta / ritaglia / allunga**, poi **Importa dal gioco**. Seleziona piu JPG/PNG, controlla il modello di ogni voce e applica la coda con un solo backup e riavvio automatico. Non si apre un editor esterno e non servono file ShareMii.

Serve un modello gia creato e salvato nello studio di design per la categoria scelta. La foto ne fornisce il disegno; forma e proprieta vengono dal modello, conservato senza modifiche. Non e una generazione 3D da foto e non crea Mii da fotografie. Vedi la [guida a foto, modelli, adattamenti e limiti](docs/it/PHOTO-IMPORT.md).

## Importare Mii e oggetti dal gioco

Il setup **0.4.0** aggiunge la coda per tutte le categorie: **F1 → ShareMii → Contenuto → Importa → Importa dal gioco**. Accoda piu Mii, cibi, vestiti, tesori, interni, esterni, oggetti e paesaggi; cambia categoria tornando indietro, senza perdere la coda. Scegli **Applica coda e ricarica** per un solo backup e un solo riavvio automatico. L'editor ShareMii non si apre.

I Mii sostituiscono **abitanti esistenti e inizializzati**; gli oggetti usano **slot liberi**. Fino a 70 creazioni per coda, nei limiti delle destinazioni disponibili. Un file non valido impedisce l'applicazione dell'intero gruppo. Il menu segue la lingua di Windows (IT/EN/DE/ES/FR/PT, inglese per le altre lingue). Vedi la [guida alle categorie, ai formati e al ripristino](docs/it/MII-QUEUE.md).

## Correzioni a selezione, F1 e sfarfallio

Il setup **0.3.3** usa il profilo GPU automatico: OpenGL su NVIDIA, Vulkan sulle altre GPU. Su NVIDIA imposta una finestra con presentazione OpenGL diretta per rendere visibili F1 e ShareMii. Evita così un blocco della selezione riprodotto sul PC verificato: tastiera e controller inviavano i comandi, ma gli edifici non venivano selezionati. OpenGL ha ripristinato l’ingresso nella fontana e il normale utilizzo del gioco.

L’aggiornamento del runtime impedisce inoltre che output non scritti dagli shader corrompano i render target OpenGL, una causa di ombre intermittenti. Il giocatore ha confermato comandi funzionanti e immagine stabile dopo la modifica. Rimane inclusa la correzione alla durata delle texture Vulkan della versione 0.3.2. Il risultato riguarda il PC verificato e non garantisce compatibilità con ogni GPU o driver.

Completa **Port già installato** per ricompilare il runtime con entrambe le patch grafiche. **Ripara menu F1 → Ripara menu F1 e selezione** applica soltanto il profilo, con backup e senza compilatore o download. Vedi [riparazione, scelta renderer e ripristino](docs/it/MENU-REPAIR.md) e [modifiche al rendering e limiti](docs/it/TEXTURE-FIX.md).

## Salvataggi da emulatore e lingua

La scheda **Salvataggi** permette di verificare e importare una cartella raw o uno ZIP da un emulatore, esportare l'intera isola in ZIP e recuperare importazioni interrotte. Puoi importare subito o al termine di una nuova installazione. La sorgente resta intatta e l'isola precedente viene conservata in un backup. È supportato il gioco **1.0.4**, senza conversioni tra versioni.

Segui la [guida importazione/esportazione e ripristino](docs/it/SAVE-TRANSFER.md), anche per riportare un'esportazione nell'emulatore. Le prove dei trasferimenti usano dati sintetici; il caricamento di un'isola reale importata resta da verificare.

Il setup rileva la lingua di visualizzazione di Windows all'avvio, anche su un PC diverso da quello del download. Il menu **Auto · Windows** sceglie fra italiano, inglese, tedesco, spagnolo, francese e portoghese. Le varianti regionali usano la lingua base; le lingue non supportate usano l'inglese. È possibile cambiare lingua manualmente. Questa scelta riguarda il setup; gioco ed editor originale mantengono le proprie impostazioni, e i log diagnostici possono rimanere in inglese.

## Come funziona

1. Il progetto originale ricompila staticamente il codice della tua copia in un programma Windows nativo.
2. Questa integrazione ricompila solo il runtime open source per aggiungere **F1 → ShareMii - Mii e oggetti**.
3. Per importare Mii e oggetti, prepara e controlla una coda dentro F1. Puoi scegliere piu file insieme oppure aggiungerli in momenti successivi.
4. Applicando la coda, il menu aspetta un salvataggio confermato e chiude normalmente il gioco. I codec ShareMii verificati con l'adattatore UGC modificano una copia privata; il gruppo viene poi applicato insieme con backup della partita precedente.
5. Il gioco nativo si riavvia automaticamente per caricare il salvataggio modificato. E un ricaricamento, non una modifica immediata alla memoria del motore.
6. Le operazioni di esportazione/elenco mantengono il percorso nell'editor completo: salvataggio, chiusura, backup, ShareMii e proposta di riavvio.

L'integrazione non scrive nei file dell'isola mentre il processo del gioco e aperto. La coda usa i codec ShareMii verificati senza GUI, con l'adattatore UGC descritto nella guida.

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
