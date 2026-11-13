# Importare foto JPG e PNG dal gioco

Da **0.5.0** puoi selezionare direttamente immagini `.jpg`, `.jpeg` e `.png` nel menu F1. Il convertitore di [TL-UGC-Editor di PICKLERICK2005](https://github.com/PICKLERICK2005/TL-UGC-Editor), MIT, e integrato senza la sua interfaccia. Non devi preparare o scegliere file ShareMii.

## Preparare un modello

Crea nella **studio di design / Palette House** almeno una creazione della categoria desiderata, scegliendone forma e proprieta, poi salvala. Quel modello viene conservato e copiato in uno slot libero per ogni foto. Se non hai ancora sbloccato lo studio di design, continua normalmente il gioco fino a poter creare il modello. Puoi anche usare come modello una creazione gia importata e salvata con ShareMii.

La foto fornisce **il disegno o la texture**. Non viene riconosciuta automaticamente per generare una forma 3D, un nuovo Mii, il comportamento di un animale o le proprieta di un cibo: queste informazioni provengono dal modello. Sono supportate le sette categorie UGC: cibo, vestiti, tesori, interni, esterni, oggetti e paesaggio. Il modello deve appartenere alla stessa categoria della nuova creazione.

La denominazione italiana della struttura e **studio di design**, come nella [presentazione Nintendo](https://www.nintendo.com/it-it/Giochi/Giochi-scaricabili-per-Nintendo-Switch/Tomodachi-Life-Una-vita-da-sogno-2786386.html).

## Importazione

1. Avvia dal normale collegamento **Tomodachi Life - Nativo + ShareMii** o **Tomodachi Life - ShareMii** e apri **F1 → ShareMii**.
2. Scegli **Contenuto**, per esempio **Cibo**.
3. In **Modalita** scegli **Foto: adatta**, **Foto: ritaglia** o **Foto: allunga**. Adatta mantiene l'intera immagine con eventuali bordi trasparenti; Ritaglia riempie la superficie ritagliando i bordi; Allunga usa l'intera superficie modificando le proporzioni.
4. Premi **Importa dal gioco**. Il gioco salva e controlla modelli e slot liberi. Se non trova un modello, torna al gioco, crealo e salvalo prima di riprovare.
5. In **Modello foto**, usa sinistra/destra per scegliere il modello iniziale. Premi **Aggiungi JPG / PNG...** e seleziona una o piu foto con Ctrl/Shift.
6. Usa **Rivedi creazione in coda** per controllare ciascuna foto. **Modello foto** cambia il modello della singola voce visualizzata; `→ #N` indica il nuovo slot assegnato automaticamente. Il file prende il nome della foto, nei limiti del gioco. Modelli e creazioni esistenti non vengono sostituiti.
7. Torna indietro per cambiare categoria o adattamento e aggiungere altre foto. La scelta di adattamento viene memorizzata quando aggiungi il file; per cambiarla su una voce, rimuovila e aggiungila di nuovo nella modalita desiderata. Puoi mescolare foto, file Mii e file oggetto nella stessa coda.
8. Premi **Applica coda e ricarica**, controlla il totale e conferma ancora. Il gioco salva e si chiude normalmente; una finestra mostra l'avanzamento della conversione. Dopo la conversione di disegno, texture e miniatura il gruppo viene applicato con un solo backup e il gioco riparte automaticamente. Al titolo usa il normale tasto di conferma.

Se una coda contiene gia voci, il modello mostrato e quello della voce selezionata. Le nuove foto usano il modello predefinito della loro categoria; rivedi ogni voce per scegliere un altro modello.

Le foto restano sul PC: non sono inviate a servizi online. Il file sorgente non viene modificato. La coda usa solo il primo modello scelto per la sua forma: adattamenti complessi, cuciture o disegni che coprono piu superfici possono richiedere lavoro nell'editor normale del gioco. La miniatura viene aggiornata con la foto, non e una nuova renderizzazione 3D del modello.

## Limiti e recupero

Sono accettate foto statiche JPEG/PNG fino a 64 MiB, 32 megapixel e 16.384 pixel per lato. L'orientamento EXIF viene applicato e la trasparenza PNG viene conservata nei limiti dei formati del gioco (il disegno e la texture BC1 hanno trasparenza binaria). Formati diversi o file incompleti sono rifiutati.

La funzione accetta soltanto i layout texture supportati dal convertitore e verifica le dimensioni del modello prima di scrivere. Se il layout non e riconosciuto, scegli un altro modello. La resa dei colori dipende anche da illuminazione e materiale del gioco. Non tutte le combinazioni di modelli e materiali sono state verificate visivamente.

Restano validi il massimo di **70 creazioni per coda**, le destinazioni libere e il limite degli slot vestiti 1–256 descritto nella [guida alle importazioni](MII-QUEUE.md). L'importazione e una transazione: se fallisce un elemento, il gruppo non sostituisce la partita attiva. Un gruppo riuscito conserva la partita precedente in `build/saves/imports/<data_ora_id>/save`. Ripristina tramite **Setup → Salvataggi → Importa**; dopo un'interruzione usa **Recupera**. Vedi [salvataggi e recupero](SAVE-TRANSFER.md).

## Provenienza e verifiche

Il codec MIT di TL-UGC-Editor e estratto senza modifiche da `a4b3c45dabd8b145de3adae7e4af1fe226f6847f`. Licenza e attribuzione sono incluse. L'integrazione aggiunge controlli sulle immagini, adattamento, clonazione dei modelli, coda, backup e riavvio. I test confrontano il codec incluso con la sorgente verificata SHA-256 e provano JPEG/PNG, tre adattamenti, tutte e sette le categorie su salvataggi sintetici, lettura dei pixel convertiti, conservazione dei modelli e annullamento con una seconda foto non valida. Non si distribuiscono fotografie, modelli, salvataggi o risorse del gioco.

Le impostazioni grafiche e il profilo OpenGL restano quelli della versione precedente. Questa funzione non costituisce una correzione del problema Vulkan.
