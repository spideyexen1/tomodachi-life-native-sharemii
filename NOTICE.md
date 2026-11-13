# Credits and source provenance / Crediti e provenienza

- **Native port / Port nativo:** [josiahg2502-glitch/TomodachiLife-recomp](https://github.com/josiahg2502-glitch/TomodachiLife-recomp), supported release 1.0.3, commit `b7ba15075e7303f79b2f941f09d30003f49aa80c`, GPL-3.0. The menu patch targets its open-source host. The upstream project credits [Denkishi/ssbu-recomp](https://github.com/Denkishi/ssbu-recomp) for its runtime and tools.
- **Content editor / Editor dei contenuti:** [Star-F0rce/ShareMii](https://github.com/Star-F0rce/ShareMii), version 3.2.3, commit `30482ad6354016b8e019b3bf86a2413ad0c24121`, GPL-3.0. Its source and GUI assets are fetched locally at installation time, verified and kept unmodified with their license. They are not bundled here.
- **This repository / Questa repository:** F1-menu integration, process handoff, backups, launcher glue, portable installer, Windows setup wizard, tests and bilingual documentation, maintained under the `spideyexen1` repository account. It is a companion to the original port, not a claim to have authored the native recompilation or ShareMii. The setup executable embeds this project's source bundle, not a compiled copy of the game.

The included GPL-3.0 license applies to this integration. Third-party components retain their original licenses, available in their upstream projects and local installations.

The in-game queue uses the pinned ShareMii functions without their GUI. The verified ShareUGC source file stays unmodified on disk; `payload/ugc_import.py` corrects one assignment in its in-memory copy: the eight-byte material texture scale is written to `v2Offset`, as in the original export path, instead of overwriting `vOffset`. The adapter adds file/schema validation, add-only item destinations and read-back checks. Its format/field handling derives from Star-F0rce's GPL-3.0 ShareUGC.

La coda nel gioco usa le funzioni ShareMii senza GUI. Il file ShareUGC verificato resta invariato su disco; `payload/ugc_import.py` corregge una scrittura nella copia in memoria: la scala della texture a otto byte va in `v2Offset`, come nell'esportazione originale, senza sovrascrivere `vOffset`. L'adattatore aggiunge controlli dei file e dello schema, importazione degli oggetti solo negli slot liberi e verifica dei dati riletti. Formato e campi derivano da ShareUGC di Star-F0rce, GPL-3.0.

La licenza GPL-3.0 inclusa si applica a questa integrazione. I componenti di terze parti conservano le rispettive licenze, disponibili nei progetti originali e nelle installazioni locali.

No Nintendo software, assets, fonts, console keys, firmware, save data or game-derived binaries are distributed in this repository. There is no affiliation with Nintendo.

Questa repository non distribuisce software, risorse o font Nintendo, chiavi della console, firmware, salvataggi o binari derivati dal gioco. Non esiste affiliazione con Nintendo.

## Integrated photo converter / Convertitore foto integrato

The texture codec in `payload/photo_texture_codec.py` is an unchanged, GUI-free extraction of TL-UGC-Editor v0.1.2 by PICKLERICK2005 (copyright 2026 pickle), commit `a4b3c45dabd8b145de3adae7e4af1fe226f6847f`. Source: https://github.com/PICKLERICK2005/TL-UGC-Editor . It is MIT-licensed; the full notice is retained in that module and `payload/PHOTO-TEXTURE-LICENSE.txt`. Pinned upstream source hashes are recorded in `tools/upstream-lock.json`. The original editor is not launched or bundled as an executable.

Il codec texture incluso e estratto senza modifiche e senza GUI da TL-UGC-Editor v0.1.2 di PICKLERICK2005 (copyright 2026 pickle), commit indicato sopra, licenza MIT inclusa. L'integrazione aggiunge limiti alle immagini, adattamento, clonazione dei modelli gia presenti nella partita, coda e riavvio automatico. I modelli e i dati del gioco non sono distribuiti.
