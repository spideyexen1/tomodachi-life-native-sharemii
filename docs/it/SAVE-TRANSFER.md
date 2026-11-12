# Importare, esportare e ripristinare un'isola

[English](../en/SAVE-TRANSFER.md) · [Installazione](INSTALL.md)

Il setup **0.3.0** aggiunge la scheda **Salvataggi**. Trasferisce l'intera isola, compresa la cartella `Ugc` con le creazioni; non unisce due partite. Per singoli Mii o oggetti usa invece il menu F1 di ShareMii.

## Prima di iniziare

- Port originale 1.0.3 con gioco **1.0.4**, struttura standard `<port>/build`, Python 3.12. Per i soli trasferimenti non serve ricompilare il gioco o installare C++.
- Chiudi completamente gioco nativo, ShareMii ed emulatore. Non avviarli durante il trasferimento.
- Il salvataggio deve provenire dallo stesso gioco, versione **1.0.4**. Non sono previste conversioni tra versioni. Da una cartella raw non è possibile accertare automaticamente la versione: il setup richiede una conferma esplicita.
- Sono accettati cartelle raw o ZIP di salvataggi, non savestate dell'emulatore, immagini NAND o cartelle dell'intero profilo. Limiti: 20.000 file, 2 GiB non compressi. File mancanti, archivi ambigui, collegamenti e percorsi non sicuri vengono rifiutati.

Il controllo cerca `Map.sav`, `Mii.sav` e `Player.sav` non vuoti e conserva tutti gli altri file del salvataggio. Non è una verifica completa della validità interna dell'isola. I trasferimenti e il ripristino sono testati con dati sintetici; il caricamento di un'isola reale importata non è stato verificato da inizio a fine.

## Dall'emulatore al port nativo

1. Nell'emulatore salva la partita e interrompi l'emulazione. Apri la cartella del salvataggio del gioco e dell'utente corretto dal suo menu contestuale. In Eden la voce è **Open Save Data Location**: vedi la [guida ufficiale](https://github.com/eden-emulator/mirror/blob/master/docs/user/ImportingSaves.md). In altri emulatori può chiamarsi **Open User Save Directory** o avere un nome tradotto.
2. Chiudi l'emulatore. Conserva una copia separata di quella cartella, inclusa `Ugc` e tutte le sottocartelle. Non selezionare una directory con più utenti o più giochi.
3. Apri il setup. Nella prima scheda scegli la **cartella del port** che contiene `build`. Per aggiornare un'integrazione precedente scegli **Port già installato** e completa l'installazione una volta: anche il launcher riceverà il blocco dei trasferimenti attivi.
4. Apri **Salvataggi → Cartella...** oppure **ZIP...**. Seleziona il salvataggio; premi **Verifica sorgente**. Un ZIP esportato da questo setup ha anche un manifesto SHA-256, verificato prima dell'importazione.
5. Per cartelle o ZIP senza metadati, spunta la conferma di provenienza dal gioco 1.0.4 solo dopo averla controllata nell'emulatore.
6. Premi **Importa ora** e conferma la sostituzione. Il setup lascia intatta l'origine, prepara una copia verificata e conserva l'isola precedente in `<port>/build/saves/imports/<data_ora_id>/save`. Il percorso esatto appare nel risultato. Non eliminare il backup prima di aver verificato la partita.
7. Attendi **Operazione completata**, poi avvia il gioco dal collegamento ShareMii e controlla l'isola.

Per una nuova installazione puoi scegliere prima il salvataggio e spuntare **Importa il salvataggio selezionato al termine dell'installazione**. Torna alla prima scheda e prosegui: il controllo della sorgente precede la compilazione, il trasferimento avviene dopo l'installazione del port e dell'integrazione. Se l'installazione riesce ma l'importazione fallisce, correggi il problema e usa **Importa ora** senza ricompilare.

## Esportare dal port

1. Salva nel gioco, chiudilo e attendi la fine del processo. Chiudi anche ShareMii.
2. Nel setup seleziona la cartella del port nella prima scheda, poi **Salvataggi → Esporta ZIP**.
3. Scegli un nuovo file ZIP fuori dalla cartella del salvataggio. Il setup non sovrascrive archivi esistenti.
4. Attendi la conferma. Lo ZIP contiene tutti i file dell'isola e `native-sharemii-export.json` con versione e hash. Puoi reimportarlo con **ZIP... → Importa ora** senza la conferma della versione sconosciuta, purché il manifesto risulti valido.

### Riportare l'esportazione nell'emulatore

Usa lo stesso gioco aggiornato alla 1.0.4. Apri la cartella di salvataggio del corretto utente dal menu dell'emulatore, poi chiudilo. Copia l'intero contenuto attuale in una cartella di backup separata e spostalo fuori dalla cartella attiva. Estrai lo ZIP in una cartella temporanea e copia **i file del salvataggio e tutte le sue sottocartelle**, compresa `Ugc`, direttamente nella cartella attiva vuota. Non copiare il solo ZIP, una cartella contenitrice aggiuntiva o `native-sharemii-export.json`. Avvia l'emulatore e verifica la partita; se non si carica, ripristina la copia precedente con entrambi i programmi chiusi.

Questa è una copia di salvataggi raw. Non configura emulatori e non trasferisce chiavi o altri dati di sistema.

## Ripristino e interruzioni

**Tornare all'isola precedente:** scegli con **Cartella...** il percorso `save` di uno dei backup in `build/saves/imports`. Conferma la versione 1.0.4 e premi **Importa ora**. Anche l'isola che stai sostituendo viene conservata in un nuovo backup. I backup ShareMii preesistenti in `build/saves/sharemii` restano separati.

**Importazione interrotta:** non spostare manualmente i file `.save-import-*`. Con tutto chiuso, seleziona il port e premi **Recupera interruzione**. Se la nuova isola era già stata installata completamente, viene mantenuta; se la sostituzione non era conclusa, viene ripristinata la precedente. La funzione recupera una transazione incompleta, non annulla un'importazione già conclusa. Il launcher aggiornato blocca l'avvio finché esiste un'importazione da recuperare.

**Commit del gioco interrotto:** se compare un errore relativo a `save.commit`, avvia e chiudi normalmente il gioco nativo per permettergli di completare il proprio recupero; poi riprova. Non cancellare i journal del gioco. Se esiste anche un'importazione in sospeso e il launcher impedisce l'avvio, conserva intatta la cartella `build/userdata` e i backup: serve una verifica manuale prima di procedere.

## Lingua dell'interfaccia

Il setup rileva la **lingua di visualizzazione di Windows al momento dell'avvio**, non il paese del download. Sono disponibili italiano, inglese, tedesco, spagnolo, francese e portoghese; le varianti regionali usano la rispettiva lingua base. Il menu **Auto · Windows** segue il sistema, oppure puoi scegliere manualmente una lingua. Per le altre lingue viene usato l'inglese. Le traduzioni sono incluse e funzionano offline.

Questa impostazione riguarda l'interfaccia del setup e della scheda Salvataggi. La lingua del gioco e dell'editor originale dipende dalle loro impostazioni; i log tecnici degli strumenti originali e i dettagli diagnostici possono restare in inglese. Le guide complete sono disponibili in italiano e inglese.

## Uso da terminale (facoltativo)

Con i programmi chiusi, dal clone sorgente:

```powershell
py -3.12 payload/save_transfer.py inspect --source "C:\MySave"
py -3.12 payload/save_transfer.py import --port-dir "C:\Games\TomodachiLife" --source "C:\MySave" --allow-unknown-version
py -3.12 payload/save_transfer.py export --port-dir "C:\Games\TomodachiLife" --output "C:\Backups\island.zip"
py -3.12 payload/save_transfer.py recover --port-dir "C:\Games\TomodachiLife"
```

Il flag `--allow-unknown-version` è la conferma esplicita della versione 1.0.4; non forza l'importazione di esportazioni che dichiarano una versione incompatibile. I salvataggi rimangono sul PC e non vengono pubblicati o caricati online.
