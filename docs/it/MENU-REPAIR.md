# Riparare il menu F1 invisibile

[English](../en/MENU-REPAIR.md) · [Installazione](INSTALL.md)

## Il problema e la correzione disponibile

Su un PC verificato con NVIDIA RTX 3060 Ti, il renderer OpenGL riceveva F1 e apriva internamente il menu, bloccando gli input del gioco, ma il pannello restava invisibile. I log registravano `menu: opened` anche quando a schermo si vedeva ancora l'isola. Il passaggio a **Vulkan**, seguito dal riavvio, ha reso visibili sia **PC Settings** sia **ShareMii - Mii e oggetti**; entrambe le pagine sono state verificate a schermo.

Il setup **0.3.1** distribuisce questa correzione di configurazione. È un aggiramento del problema del renderer OpenGL: non modifica il codice OpenGL originale e non garantisce lo stesso risultato su ogni GPU o driver. Richiede una **GPU e un driver con Vulkan 1.3**.

## Riparare un port esistente

1. Salva la partita, chiudi il gioco ed esci da ShareMii. Non usare una chiusura forzata per applicare la correzione.
2. Apri il [setup 0.3.1](https://github.com/spideyexen1/tomodachi-life-native-sharemii/releases/tag/v0.3.1).
3. Nella prima scheda seleziona la cartella del port che contiene `build`. Non serve selezionare nuovamente gioco base, aggiornamento o chiavi per la sola riparazione.
4. Apri **Ripara menu F1 → Ripara menu F1 con Vulkan**. La funzione valida il port supportato e rifiuta modifiche mentre il gioco o una sessione di ShareMii/trasferimento è attiva.
5. Attendi la conferma. Il percorso di `graphics.ini` e l'eventuale backup vengono mostrati nel risultato.
6. Riavvia dal collegamento **Tomodachi Life - ShareMii**. Premi **F1** per mostrare **PC Settings**, poi seleziona **ShareMii - Mii e oggetti**. F1 apre e chiude il pannello; alcuni portatili richiedono Fn + F1.

La sola riparazione funziona offline con Python 3.12 già presente, compreso quello privato del port. Non richiede Microsoft C++, download o ricompilazioni. Rimangono supportati il port originale **1.0.3**, gioco **1.0.4** e struttura standard documentata.

## Nuove installazioni e aggiornamenti

Nella prima scheda è preselezionata **Usa Vulkan per il menu F1**. Al termine dell'installazione il setup applica la stessa configurazione e conserva una copia delle preferenze precedenti. Puoi deselezionarla se desideri mantenere il renderer scelto: in quel caso non viene applicata questa correzione. Non abilitarla su una GPU priva di Vulkan 1.3.

Il passaggio da OpenGL a Vulkan può richiedere una nuova preparazione degli shader. Durante questo passaggio la finestra può restare nera e mostrare l'avanzamento nel titolo. Sul PC verificato la preparazione Vulkan è terminata in circa due minuti e mezzo; il tempo varia in base a hardware, driver e cache. Attendi il completamento prima di verificare F1.

## Impostazioni modificate e ripristino

La correzione aggiorna solo queste due opzioni in `<port>/build/config/graphics.ini`:

```ini
renderer = always_vulkan
menu = on
```

`always_vulkan` è intenzionale: nel runtime supportato il valore `vulkan` da solo viene trattato come selezione automatica e può scegliere nuovamente OpenGL su NVIDIA.

Lingua, risoluzione, volume e altre opzioni restano conservati. Prima della prima modifica viene creata una copia esatta `graphics.ini.menu-backup-<data_ora_id>` nella stessa cartella. Una seconda esecuzione con la configurazione già corretta non crea ulteriori copie. I salvataggi dell'isola e i file del gioco non vengono modificati.

Per annullare la correzione, chiudi gioco ed editor, conserva separatamente l'attuale `graphics.ini` e copia al suo posto il backup indicato dal setup. Il ritorno alla vecchia configurazione può far ricomparire il menu invisibile. Puoi applicare nuovamente **Ripara menu F1** in seguito.

## Terminale (facoltativo)

Dal clone della repository, con gioco ed editor chiusi:

```powershell
py -3.12 tools/repair_menu.py --port-dir "C:\Games\TomodachiLife"
```

Per applicare la configurazione durante l'installazione dell'integrazione:

```powershell
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --vulkan-menu
```

Il flag è esplicito per gli utenti CLI; nel setup grafico corrisponde alla casella preselezionata. La riparazione conserva le altre opzioni, crea un backup e pubblica solo un risultato locale. Questa repository e il setup non contengono ROM, aggiornamenti del gioco, chiavi o salvataggi personali.
