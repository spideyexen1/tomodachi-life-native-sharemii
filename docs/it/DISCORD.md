# Attività Discord automatica

Il setup **0.6.0** aggiunge Discord Rich Presence tramite connessione locale per tutte le installazioni. Ai giocatori non serve creare un'app sviluppatore, inserire un ID, accedere tramite questa integrazione o usare **Giochi registrati → Aggiungilo!**.

## Come usarla

1. Chiudi il gioco e installa la versione 0.6.0 o successiva. Per un'installazione esistente scegli **Port già installato** nel setup.
2. Apri **Discord desktop** sullo stesso PC e avvia dal collegamento **Tomodachi Life - ShareMii** o **Tomodachi Life - Nativo + ShareMii**.
3. Quando parte il gioco nativo, nel profilo compare l'app **Tomodachi Life Native + ShareMii**, con **Tomodachi Life: Living the Dream**, **Native Windows + ShareMii** e il tempo trascorso.
4. Chiudendo il gioco nativo la Rich Presence scompare. Un riavvio automatico per le importazioni chiude la sessione precedente e ne avvia una nuova.

Puoi aprire Discord anche dopo il gioco: il launcher continua a ritentare durante la partita. Dopo un riavvio di Discord il collegamento può richiedere circa 30–40 secondi. Il solo browser o client mobile non riceve la connessione IPC locale di Windows. Il solo setup o la finestra del launcher non pubblicano attività.

La visibilità segue le tue [preferenze di condivisione attività di Discord](https://support.discord.com/hc/en-us/articles/7931156448919-Activity-Sharing-on-Discord-FAQ). L'integrazione non modifica queste impostazioni.

## Se non compare

- Usa il collegamento ShareMii, tieni aperto Discord desktop e attendi il ricollegamento.
- Controlla `integration/discord-presence-status.json` nell'installazione. `connected` indica che Discord ha confermato l'attività; la visibilità resta gestita da Discord. `waiting_for_discord` indica che il client locale non è disponibile. Con `missing_dependency` riesegui il setup. Con `invalid_application_id` o `invalid_configuration` reinstalla la configurazione predefinita del progetto. Il diagnostico può restare obsoleto se il launcher viene terminato bruscamente.
- Discord assente, chiuso o non rispondente non impedisce l'avvio o la chiusura del gioco. Altre attività possono influire su ciò che appare nel profilo.
- Rimane il titolo stabile della finestra introdotto in 0.5.1 per il rilevamento standard, ma la registrazione manuale non serve alla Rich Presence.

## Disattivarla localmente

Crea `integration/discord-presence.local.json` con:

```json
{"enabled": false}
```

Riavvia il gioco. L'opzione locale viene conservata dagli aggiornamenti dell'integrazione. Imposta `true` per riattivarla. Puoi anche specificare un diverso `application_id` pubblico nello stesso file; non inserire mai token bot, client secret o password.

## Funzionamento e privacy

L'Application ID pubblico condiviso è `1571541052223918080`, in `integration/discord-presence.json`. Il setup installa `pypresence==4.6.2` nell'ambiente Python privato del port. Il launcher usa il protocollo IPC locale di Discord e il PID effettivo del gioco nativo, con tentativi limitati nel tempo e ricollegamento in background. Pubblica solo le etichette fisse del gioco/progetto e l'orario di avvio della sessione. Non legge isole, salvataggi, nomi dei Mii, messaggi, file degli account Discord o credenziali. Il diagnostico locale contiene solo stato e ID dei processi; le risposte IPC complete non vengono registrate.

L'implementazione segue la documentazione Discord per [Rich Presence senza autenticazione](https://docs.discord.com/developers/discord-social-sdk/development-guides/setting-rich-presence) e [RPC SET_ACTIVITY](https://docs.discord.com/developers/topics/rpc#commands-setactivity). Non inserisce il gioco nel catalogo ufficiale di rilevamento Discord. La prova locale ha verificato comparsa e rimozione dell'attività usando un'isola separata; i test con client simulato coprono collegamento tardivo, errori opzionali e pulizia dei processi.
