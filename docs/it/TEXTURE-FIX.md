# Correzioni del rendering

Dal setup **0.3.3**, OpenGL disabilita le scritture verso gli attachment per cui il fragment shader non dichiara output. Il gioco può associare la stessa texture a due attachment: il secondo output non scritto poteva sovrascrivere l’ombra con valori indefiniti. La maschera deriva dallo stesso header shader usato dal traduttore del port; le maschere dei clear restano separate. Il codice è verificato con un test C senza dati del gioco e con la partita sul PC interessato, dove il giocatore ha confermato stabilità.

La [segnalazione upstream](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/issues/34) descrive lo stesso tipo di scrittura; la [documentazione Khronos](https://wikis.khronos.org/opengl/Fragment_Shader) spiega i valori indefiniti degli output non scritti. Distribuiamo una patch sorgente propria, senza eseguibili sperimentali. Per aggiornare completa **Port già installato** nel setup 0.3.3. La sola riparazione F1 non ricompila il runtime.

La selezione degli edifici non funzionava su Vulkan sul PC verificato. Il profilo automatico torna a OpenGL su NVIDIA e usa la presentazione diretta per mantenere F1 visibile. Sono stati verificati fontana, editor Mii e menu. Vedi la [guida al profilo](MENU-REPAIR.md). Altri difetti del port o di un driver possono comunque rimanere.

## Correzione texture Vulkan della versione 0.3.2


[English](../en/TEXTURE-FIX.md) · [Menu F1](MENU-REPAIR.md) · [Installazione](INSTALL.md)

Il setup **0.3.2** aggiunge una correzione al runtime open source per le texture Vulkan rilasciate dal gioco mentre i comandi già registrati ne usano ancora il descrittore. Prima il percorso Vulkan poteva sostituirle con una texture vuota: oggetti o parti dello scenario apparivano neri per un fotogramma o si caricavano a intermittenza.

La modifica riprende la politica già presente nel backend OpenGL del port supportato: conserva l'immagine GPU già esistente finché il descrittore è ancora referenziato e usato di recente. Non ricrea la texture dalla memoria del gioco dopo il suo rilascio. La conservazione ha limiti di tempo; la distruzione successiva continua a usare le normali fence Vulkan.

La [segnalazione originale sullo sfarfallio](https://github.com/josiahg2502-glitch/TomodachiLife-recomp/issues/34) descrive anche texture rilasciate che diventano vuote su Vulkan. Questa repository distribuisce la propria modifica ai sorgenti fissati della versione 1.0.3; non incorpora gli eseguibili sperimentali allegati a quella discussione.

## Applicare la correzione

1. Salva e chiudi gioco ed editor.
2. Apri il [setup 0.3.3](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.3).
3. Seleziona **Port già installato**, indica la cartella che contiene `build` e completa l'installazione dell'integrazione. Non occorre ricompilare il codice del gioco: viene ricostruito il runtime open source.
4. Riavvia dal collegamento ShareMii e riprova le scene problematiche.

La sola scheda **Ripara menu F1** cambia le impostazioni grafiche: per applicare questa modifica al runtime serve il percorso **Port già installato**. Le nuove installazioni ricevono automaticamente anche la correzione delle texture.

Rimangono supportati port originale **1.0.3**, gioco **1.0.4** e struttura standard. Per ricompilare il runtime servono i prerequisiti C++ documentati. La patch non cambia i salvataggi né imposta il volume. Per F1 e selezione usa il [profilo GPU aggiornato](MENU-REPAIR.md).

## Verifiche e limiti

- Il runtime modificato è stato compilato e avviato sul PC NVIDIA RTX 3060 Ti interessato. Menu F1 e volume al 50% sono stati verificati; il giocatore ha riferito stabilità nelle scene riprovate. Il log ha confermato l'utilizzo di texture trattenute che prima sarebbero state scartate.
- Una prova C compila le funzioni effettivamente modificate e verifica risoluzione dei descrittori, conservazione, rilascio, compattazione della lista e limiti di durata senza dati del gioco.
- I controlli sui sorgenti fissati verificano hash, ripetibilità della patch, sincronizzazione con la copia compilata e rifiuto di modifiche estranee.
- Questa prova non certifica ogni isola, GPU o driver. Altri difetti di rendering o schermate nere possono avere cause diverse. Non è una correzione generale di tutti i problemi grafici del port originale.

Il sorgente originale è conservato in `<port>/runtime/nvn_gl.upstream.c`; la copia usata dal compilatore è `<port>/build/work/nvn_gl.c`. Non sostituire manualmente l'eseguibile con una vecchia build mentre il gioco è aperto. Per un ritorno alla versione precedente, conserva i salvataggi e ripristina insieme sorgente e runtime da una copia precedente con gioco ed editor chiusi.

## Sviluppatori

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --menu-renderer auto
py -3.12 tools/check_upstream.py
py -3.12 tools/check_texture_lifetime.py
```

L'ultima prova richiede GCC e scarica solo il sorgente open source fissato se non si passa `--source`. I file del gioco, le chiavi e i salvataggi personali non vengono distribuiti o caricati online.
