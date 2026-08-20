# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T00:11:14Z. **2812 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-20T05:49:38+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2714 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1749 |
| baunotiz | bauverlauf.jsonl | 920 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2812 · Gegenhypothese: 0 von 2812

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: index Gen159 export latency spike

`baunotiz-bauverlauf-a755e03141cbd4fecb54` · baunotiz · bauverlauf.jsonl · 2026-08-20T05:49:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: index Gen159 export latency spike

`baunotiz-git-1aac4373ef6e8ea7a407d7f8fcfe93e00158df15` · baunotiz · git-commit · 2026-08-20T05:49:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: index Gen159 export latency spike

### research: bind Gen159 export latency spike

`baunotiz-bauverlauf-840622232a72cee278f0` · baunotiz · bauverlauf.jsonl · 2026-08-20T05:49:10+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen159 export latency spike

`baunotiz-git-236d001250786f05a88ceef23cfcc162008afa21` · baunotiz · git-commit · 2026-08-20T05:49:10+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen159 export latency spike

### claycode supervisor: bind Gen159 PTY recovery and hierarchy verdict gap

`baunotiz-bauverlauf-86142a0ae8e8e399f962` · baunotiz · bauverlauf.jsonl · 2026-08-20T04:54:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen159 PTY recovery and hierarchy verdict gap

`baunotiz-git-2a0e598ea685b9c3e7d9716954e5eaae7c7ba48d` · baunotiz · git-commit · 2026-08-20T04:54:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen159 PTY recovery and hierarchy verdict gap

### research: bind Gen159 PTY recovery and hierarchy verdict frontier

`baunotiz-bauverlauf-138c24efe37f9373b635` · baunotiz · bauverlauf.jsonl · 2026-08-20T04:49:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen159 PTY recovery and hierarchy verdict frontier

`baunotiz-git-63564da926f0c0671ebed27b214fae99d1189aa8` · baunotiz · git-commit · 2026-08-20T04:49:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen159 PTY recovery and hierarchy verdict frontier

### claycode supervisor: bind Gen159 recurrent PTY post-attach red and receipt drift

`baunotiz-bauverlauf-c8ffabd8aa8a3ea7b76f` · baunotiz · bauverlauf.jsonl · 2026-08-20T03:44:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen159 recurrent PTY post-attach red and receipt drift

`baunotiz-git-feb4a33a5c466334a20dea8a1cb535691d4820a1` · baunotiz · git-commit · 2026-08-20T03:44:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen159 recurrent PTY post-attach red and receipt drift

### claycode supervisor: bind Gen159 test-surface drift and hierarchy localization

`baunotiz-bauverlauf-f44ae55281da6a704eac` · baunotiz · bauverlauf.jsonl · 2026-08-20T01:39:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen159 test-surface drift and hierarchy localization

`baunotiz-git-7483cc20833c1c85c8602b67ead52faf785cd3c3` · baunotiz · git-commit · 2026-08-20T01:39:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen159 test-surface drift and hierarchy localization

### agentzeroforschung: index Gen159 hierarchy aggregation analysis

`baunotiz-bauverlauf-64c144d80a900b268e14` · baunotiz · bauverlauf.jsonl · 2026-08-20T00:50:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: index Gen159 hierarchy aggregation analysis

`baunotiz-git-935ead2577a91b33b222a39d0e1b0eb128355a51` · baunotiz · git-commit · 2026-08-20T00:50:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: index Gen159 hierarchy aggregation analysis

### agentzeroforschung: localize Gen159 hierarchy aggregation defect

`baunotiz-bauverlauf-e9fde7d979848c6b3c8c` · baunotiz · bauverlauf.jsonl · 2026-08-20T00:49:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: localize Gen159 hierarchy aggregation defect

`baunotiz-git-f40e4b77004e24d138d52593b6470425f56d23b8` · baunotiz · git-commit · 2026-08-20T00:49:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: localize Gen159 hierarchy aggregation defect

### EOS-Chronik 2026-08-20 00:00:04 +0000 — clayverse: 1 Aenderungen

`baunotiz-git-5221a340b570646f0e9beace428b806114ae2f42` · baunotiz · git-commit · 2026-08-20T00:00:04+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-20 00:00:04 +0000 — clayverse: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  werkzeug/schluesselwacht.py

Zeit: 2026-08-20T00:00:04+00:00
Wirt: frank-api
Instanz: zero
Baum: clayverse (/opt/clayverse)
Dateien: 1
Fern: origin -> /srv/git/clayverse.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-19 23:58:03 +0000 — clayverse: 1 Aenderungen

`baunotiz-git-8c3fc4427f2f7e50336a67ce114ed568e08146e0` · baunotiz · git-commit · 2026-08-19T23:58:04+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-19 23:58:03 +0000 — clayverse: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  werkzeug/schluesselwacht.py

Zeit: 2026-08-19T23:58:03+00:00
Wirt: frank-api
Instanz: zero
Baum: clayverse (/opt/clayverse)
Dateien: 1
Fern: origin -> /srv/git/clayverse.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-19 23:56:03 +0000 — unifieddb: 1 Aenderungen

`baunotiz-git-9a7e102a07e2d0a23b6c85bf3bcb57088fd89430` · baunotiz · git-commit · 2026-08-19T23:56:03+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-19 23:56:03 +0000 — unifieddb: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  udb/abruf/paket.py

Zeit: 2026-08-19T23:56:03+00:00
Wirt: frank-api
Instanz: zero
Baum: unifieddb (/opt/unifieddb)
Dateien: 1
Fern: origin -> /srv/git/unifieddb.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-19 23:53:02 +0000 — entityos: 3 Aenderungen

`baunotiz-git-1754d631f0387f5d08a3a69bb5d47ca548a4c543` · baunotiz · git-commit · 2026-08-19T23:53:02+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-19 23:53:02 +0000 — entityos: 3 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/clayverse/mistral_prestage/transport.py
  udb-backup/udb_backup.py

Zeit: 2026-08-19T23:53:02+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### claycode supervisor: bind Gen159 prestage negative-count metrology defect

`baunotiz-bauverlauf-c69d9c92696d02a5b516` · baunotiz · bauverlauf.jsonl · 2026-08-19T23:45:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen159 prestage negative-count metrology defect

`baunotiz-git-ae860a013dec689b3ef41e5de929d03a5ceadcbc` · baunotiz · git-commit · 2026-08-19T23:45:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen159 prestage negative-count metrology defect

### agentZero-Export 2026-08-19T23:41:12Z (Generation 159, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-abe9855e0ebb4b7bc4ae6dc98ad65190429fdcb7` · baunotiz · git-commit · 2026-08-19T23:41:54+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T23:41:12Z (Generation 159, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T23:11:12Z (Generation 159, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-fd9ad8ab49b0180e5a493589786c63c6c5ac164c` · baunotiz · git-commit · 2026-08-19T23:11:58+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T23:11:12Z (Generation 159, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T23:11:12Z (Generation 159, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-fd9e4c77cddfbfa08136` · baunotiz · bauverlauf.jsonl · 2026-08-19T23:11:58+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

