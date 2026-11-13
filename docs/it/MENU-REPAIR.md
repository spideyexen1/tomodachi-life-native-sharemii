# F1 invisibile o edifici non selezionabili

Il setup **0.3.3** corregge il profilo usato dalle versioni precedenti. Sul PC NVIDIA verificato, Vulkan rendeva visibile F1 ma non permetteva di selezionare gli edifici, anche se tastiera e DualSense inviavano i comandi. Con OpenGL la selezione funzionava; il menu rimaneva invisibile soltanto con la presentazione DXGI. OpenGL con presentazione diretta ha reso utilizzabili entrambi.

## Procedura

1. Salva e chiudi normalmente gioco e ShareMii.
2. Apri il setup 0.3.3 e seleziona la cartella del port esistente nella prima scheda.
3. Premi **Ripara menu F1 → Ripara menu F1 e selezione**.
4. Riavvia dal collegamento Native + ShareMii e premi **F1**. La voce ShareMii resta nel pannello PC Settings.
5. Per installare anche la correzione dello sfarfallio delle ombre, completa **Port già installato**: la riparazione da sola cambia soltanto le preferenze e non richiede C++ o download.

Il profilo automatico scrive:

```ini
renderer = auto
menu = on
present_api = opengl
window = windowed
```

Il port sceglie OpenGL su NVIDIA e Vulkan sulle altre schede. `present_api` riguarda soltanto OpenGL. La finestra evita anche il vecchio problema di composizione osservato a schermo intero su alcuni driver. Volume, lingua e risoluzione restano quelli scelti. Può essere necessaria una nuova preparazione degli shader; attendine il completamento.

Il menu OpenGL richiede OpenGL 4.6 e le estensioni richieste dal port. Vulkan richiede Vulkan 1.3. Il risultato è stato verificato su una configurazione NVIDIA, non su ogni GPU.

## Configurazione da sorgente

Con Python 3.12:

```powershell
py -3.12 tools/repair_menu.py --port-dir "C:\Games\TomodachiLife"
py -3.12 tools/install_integration.py --port-dir "C:\Games\TomodachiLife" --menu-renderer auto
```

La prima riga configura soltanto; la seconda aggiorna anche il runtime. Le alternative esplicite della prima riga sono `--renderer opengl` e `--renderer vulkan`. Con l’installer usa `--menu-renderer opengl` o `--menu-renderer vulkan`. Il vecchio `--vulkan-menu` resta compatibile ma forza Vulkan; non è il profilo consigliato sul PC con questo blocco della selezione.

## Ripristino

Ogni modifica conserva l’originale in `build/config/graphics.ini.menu-backup-<data>_<id>` e mostra il percorso. A gioco ed editor chiusi, conserva una copia della configurazione attuale e ricopia il backup desiderato su `build/config/graphics.ini`. La funzione rifiuta modifiche con una sessione del gioco, editor o trasferimento attiva. Non modifica i salvataggi.

Se F1 si apre ma non si vede, premi nuovamente F1 per restituire i comandi al gioco prima di salvare e chiudere. Nel gioco, la croce PlayStation corrisponde alla conferma: **✕ / Invio / Spazio**. La lettera X della tastiera è un altro comando.
