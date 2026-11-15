# Attivita Discord per tutti i giocatori

Da **0.5.1**, il setup include la compatibilita con il normale rilevamento dei giochi di Discord. Avviando dal collegamento ShareMii, il titolo della finestra resta **Tomodachi Life: Living the Dream**, anche durante il caricamento: Discord non deve piu ricavare il nome da un suffisso come `60 fps`.

La registrazione e una preferenza personale di Discord. Quella effettuata dall'autore sul proprio account non viene trasferita agli altri giocatori. Ognuno puo registrare la propria copia una volta, senza token, bot, mod del client o strumenti aggiuntivi.

## Prima configurazione

1. Installa o aggiorna con **Setup → Port gia installato**, a gioco chiuso. Per una nuova installazione segui la [guida generale](INSTALL.md). Le installazioni precedenti devono completare l'aggiornamento: la sola riparazione delle impostazioni F1 non ricompila questa patch.
2. Apri **Discord desktop** sul PC e avvia il gioco dal collegamento **Tomodachi Life - ShareMii** o **Tomodachi Life - Nativo + ShareMii**.
3. In Discord apri **Impostazioni utente → Giochi registrati → Aggiungilo!**.
4. Seleziona **Tomodachi Life: Living the Dream** e premi **Aggiungi gioco**. Il processo avviato dal launcher e `tomodachi_play.exe`; se necessario, verifica che sia quello della tua installazione.
5. Se hai una vecchia registrazione chiamata `60 fps`, clicca il nome del gioco corrente e rinominalo **Tomodachi Life: Living the Dream**, poi clicca fuori dal campo per confermare. Non e necessario eliminare la registrazione.
6. Verifica che il rilevamento del gioco sia abilitato nella relativa riga. Per condividerlo con gli altri, anche la tua preferenza **Privacy attivita → Condividi la mia attivita** deve consentirlo; restano valide le impostazioni dei singoli server.
7. Apri la tua scheda profilo: durante il gioco deve apparire **Gioca a Tomodachi Life: Living the Dream**. Quando il processo termina, l'attivita corrente scompare; l'elenco dei giochi registrati puo conservarlo tra quelli usati di recente.

Questa e la procedura di [registrazione manuale documentata da Discord](https://discord.com/blog/how-to-share-what-youre-playing-listening-to-or-watching-as-your-status-on-discord); la visibilita segue i [controlli di condivisione delle attivita](https://support.discord.com/hc/en-us/articles/7931156448919-Activity-Sharing-on-Discord-FAQ). Il browser o l'app mobile da soli non eseguono il rilevamento locale del programma Windows.

## Se non compare

- Tieni aperti sia Discord desktop sia il gioco effettivo; il solo setup o launcher non basta.
- Usa il collegamento ShareMii aggiornato. Un avvio diretto degli strumenti upstream puo mantenere i titoli diagnostici con frame/FPS.
- Controlla le preferenze personali e del server sulla condivisione. Il setup non le cambia al tuo posto.
- Se hai spostato l'installazione e Discord non la rileva piu, ripeti **Aggiungilo!** con la nuova copia aperta.
- Se la selezione propone ancora `60 fps`, completa l'aggiornamento del port e riavvia il gioco; una registrazione esistente puo essere rinominata come sopra.

## Cosa distribuisce il progetto

La modifica riguarda il titolo della finestra del runtime open source e i parametri del launcher. Non legge file o credenziali di Discord, non modifica il suo client, non accede ai messaggi e non imposta automaticamente la condivisione per altri account. L'inclusione nel catalogo ufficiale dei giochi di Discord resta una decisione di Discord: questa compatibilita non promette un riconoscimento globale senza la prima registrazione.

La patch e limitata al runtime supportato v1.0.3, verificato tramite SHA-256, e conserva il sorgente originale come `runtime/display.upstream.c`. Le misure FPS e i log restano disponibili; il titolo dinamico resta per gli avvii diagnostici che non impostano `TOMO_DISCORD_TITLE`. Non cambia salvataggi, input, audio o rendering. Non sono distribuiti file del gioco.
