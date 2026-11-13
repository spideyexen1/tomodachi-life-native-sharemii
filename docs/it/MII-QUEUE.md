# Importare Mii e oggetti dal gioco

Da **0.4.0**, tutte le categorie di importazione ShareMii si preparano nel menu F1. Puoi selezionare piu file, mescolare categorie, controllare le destinazioni e applicare l'intera coda con **un solo ricaricamento automatico**. Non si apre l'editor ShareMii.

1. Avvia dal collegamento **Tomodachi Life - ShareMii**. Crea l'isola e salva almeno una volta.
2. Apri **F1 → ShareMii - Mii e oggetti**. Scegli **Contenuto**, lascia **Modalita: Importa** e premi **Importa dal gioco**. Il gioco conferma un salvataggio prima di mostrare la coda.
3. Scegli **Aggiungi file...**. Il selettore Windows filtra i file della categoria scelta; usa Ctrl/Shift per sceglierne diversi insieme. Puoi aggiungere altri file senza riavviare.
4. Per mescolare categorie, scegli **Indietro**, cambia **Contenuto** e riapri **Importa dal gioco**. Le voci gia accodate restano presenti. Per esempio puoi accodare due Mii, tre cibi e un oggetto prima di applicare.
5. Con **Rivedi creazione in coda**, usa sinistra/destra per scorrere i file; sono mostrati categoria e nome. **Destinazione** cambia l'abitante o lo slot libero della creazione visualizzata. Se una destinazione e gia assegnata a un'altra voce della stessa categoria, le assegnazioni vengono scambiate.
6. **Rimuovi creazione selezionata** elimina solo quella voce dalla coda. Puoi tornare al gioco: la coda resta in memoria finche la sessione e aperta. Riaprendo l'importazione, le destinazioni vengono aggiornate dal salvataggio confermato.
7. Scegli **Applica coda e ricarica**, controlla il numero totale e conferma una seconda volta. Il gioco salva, si chiude normalmente e il componente di importazione prepara l'intero gruppo su una copia. Il gruppo viene applicato in un'unica operazione con backup; il gioco si riapre automaticamente. Al titolo premi il normale tasto di conferma per continuare.

## Categorie e destinazioni

| Contenuto | File | Destinazione |
|---|---|---|
| Mii | `.ltd` | Sostituisce un abitante esistente e inizializzato |
| Cibo | `.ltdf` | Nuovo slot libero nella categoria |
| Vestiti | `.ltdc` | Nuovo slot libero nella categoria |
| Tesori | `.ltdg` | Nuovo slot libero nella categoria |
| Interni | `.ltdi` | Nuovo slot libero nella categoria |
| Esterni | `.ltde` | Nuovo slot libero nella categoria |
| Oggetti | `.ltdo` | Nuovo slot libero nella categoria |
| Paesaggio | `.ltdl` | Nuovo slot libero nella categoria |

Sono creazioni personali nel formato ShareMii, non tutti gli oggetti di sistema del gioco. Gli oggetti importati entrano nel catalogo dei contenuti personalizzati; la coda non li colloca automaticamente sull'isola. Usa le normali funzioni del gioco per utilizzarli. Formati di altri giochi o file rinominati non sono convertiti.

Per i **Mii** servono abitanti gia creati, come nell'importazione originale di ShareMii. I file non inizializzano slot vuoti. Se vuoi conservare un abitante, crea prima un altro abitante da sostituire e verifica la destinazione. Restano valide le regole originali sui dati personali e le preferenze dei Mii gia sviluppati.

Per gli **oggetti** questa coda usa solo slot liberi: non sostituisce creazioni esistenti. Le categorie hanno fino a 99 slot; per i vestiti l'adattatore considera gli slot 1–256, per rispettare il limite dell'indice a un byte del codec originale di aggiunta. Gli slot vestiti 257–299 non vengono assegnati da questa funzione. Le voci gia occupate o con file texture parziali non vengono riutilizzate.

Il massimo e **70 creazioni per coda**, nei limiti delle destinazioni disponibili. Puoi applicare altre code in seguito. La coda non viene conservata se chiudi la sessione senza applicarla.

Le pitture del viso possono essere incorporate nel `.ltd` oppure accompagnarlo come `<file>.ltd.canvas.zs` e `<file>.ltd.ugctex.zs`: tieni insieme entrambi i file laterali. Gli oggetti usano i propri file `.ltdf/c/g/i/e/o/l` con le texture incorporate.

## Backup e recupero

Tutti i file e gli abbinamenti sono controllati prima della prima importazione. I codec ShareMii 3.2.3 sono verificati tramite SHA-256 e usati senza GUI. L'adattatore UGC corregge la scrittura della scala della texture di esterni/oggetti; dettagli e attribuzione in [NOTICE](../../NOTICE.md). Nomi, attributi e texture vengono riletti e verificati prima di applicare il gruppo. File grandi oltre 64 MiB, texture compresse incomplete o dati non compatibili vengono rifiutati.

Se un file fallisce, **nessun elemento del gruppo** viene applicato al salvataggio attivo. Un gruppo riuscito conserva l'intera partita precedente in **`build/saves/imports/<data_ora_id>/save`**, con manifesto SHA-256. Ripristina tramite **Setup → Salvataggi → Importa**, scegliendo quella cartella. Vedi la [guida ai salvataggi e al recupero](SAVE-TRANSFER.md). Dopo un'interruzione durante il cambio delle cartelle usa **Recupera** prima di avviare il gioco.

Il riepilogo locale e in `integration/last-mii-import.json` (anche per code miste); gli errori in `integration/mii-import-error.log`. Il processo originale termina e viene avviato di nuovo: le modifiche sono caricate dopo il riavvio automatico. Non vengono caricati file in rete.

La pagina ShareMii e la coda seguono la lingua di visualizzazione di Windows: IT, EN, DE, ES, FR, PT, con inglese per le altre lingue. Gioco, PC Settings originale ed editor completo hanno impostazioni proprie. **Esporta, Esporta tutti ed Elenca** continuano a usare l'editor completo.

## Verifiche e Vulkan

I test senza contenuti del gioco verificano tutte e sette le categorie UGC e un Mii in un unico commit, un solo backup precedente, destinazioni occupate, il limite dei vestiti, lettura dei dati importati e annullamento dopo un errore sull'ultimo oggetto. Una precedente prova F1 su una copia separata della partita ha confermato importazione Mii, backup e riavvio automatico. Non e stata verificata graficamente nel gioco ogni combinazione di oggetti o pitture. Le copie di prova e i file importati non vengono pubblicati.

Le prove sperimentali di sincronizzazione e texture 3D Vulkan non sono incluse come correzione definitiva della selezione. Su NVIDIA resta consigliato il profilo OpenGL gia verificato, con presentazione diretta. L'aggiornamento delle importazioni non risolve quel problema: vedi [correzioni grafiche e limiti](TEXTURE-FIX.md).
