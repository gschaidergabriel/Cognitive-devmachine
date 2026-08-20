# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T03:15:09Z. **2893 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-20T08:52:47+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2795 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1790 |
| baunotiz | bauverlauf.jsonl | 960 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2893 · Gegenhypothese: 0 von 2893

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen171 out-of-order export race

`baunotiz-bauverlauf-81f415e89f1cf3cb7158` · baunotiz · bauverlauf.jsonl · 2026-08-20T08:52:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen171 out-of-order export race

`baunotiz-git-2ec43d797819beef5b4ed969ca01a2f3ecbec0f3` · baunotiz · git-commit · 2026-08-20T08:52:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen171 out-of-order export race

### research: bind Gen171 out-of-order export race

`baunotiz-bauverlauf-92c4089505f2ebc7fb62` · baunotiz · bauverlauf.jsonl · 2026-08-20T08:48:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen171 out-of-order export race

`baunotiz-git-ce605ac89686e28d75683caf457852f48716d6d5` · baunotiz · git-commit · 2026-08-20T08:48:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen171 out-of-order export race

### claycode supervisor: steer Gen169 failure-identity swap and DB contention

`baunotiz-bauverlauf-0c7b7b6167a79958f610` · baunotiz · bauverlauf.jsonl · 2026-08-20T07:56:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen169 failure-identity swap and DB contention

`baunotiz-git-c03a4f35229809516dc8a27563bc6bdfa9c65b9b` · baunotiz · git-commit · 2026-08-20T07:56:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen169 failure-identity swap and DB contention

### research: bind Gen169 test drift and DB lock frontier

`baunotiz-bauverlauf-6fe0154a7ab6cc414adc` · baunotiz · bauverlauf.jsonl · 2026-08-20T07:47:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen169 test drift and DB lock frontier

`baunotiz-git-b6c9a9f37eab3f6b8872c8b02de06fa035e7859d` · baunotiz · git-commit · 2026-08-20T07:47:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen169 test drift and DB lock frontier

### claycode supervisor: bind Gen159 export latency recovery

`baunotiz-bauverlauf-e56e2a43c08fc15d78ad` · baunotiz · bauverlauf.jsonl · 2026-08-20T06:48:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen159 export latency recovery

`baunotiz-git-1979774548f16aca32ef54bcc391dad5f5308506` · baunotiz · git-commit · 2026-08-20T06:48:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen159 export latency recovery

### research: bind Gen159 export latency normalization

`baunotiz-bauverlauf-b0840ab6719982bf3a54` · baunotiz · bauverlauf.jsonl · 2026-08-20T06:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen159 export latency normalization

`baunotiz-git-add9866829031a2c3bc0f7b7f94c4506075a15d2` · baunotiz · git-commit · 2026-08-20T06:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen159 export latency normalization

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

### EOS-Chronik 2026-08-20 02:59:28 +0000 — entityos: 1 Aenderungen

`baunotiz-git-2c2d6608f09b9bbf2b8ea0cfbad49a17fa1a197f` · baunotiz · git-commit · 2026-08-20T02:59:29+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-20 02:59:28 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mcp_server.py

Zeit: 2026-08-20T02:59:28+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-20 02:56:59 +0000 — entityos: 1 Aenderungen

`baunotiz-git-f9b65411d7d02454731fbf01febb3cae30e8442f` · baunotiz · git-commit · 2026-08-20T02:56:59+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-20 02:56:59 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/prestage.py

Zeit: 2026-08-20T02:56:59+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-20 02:48:38 +0000 — entityos: 1 Aenderungen

`baunotiz-git-7920cbb235caf2afdfb5c5f3ba013092f89384d8` · baunotiz · git-commit · 2026-08-20T02:48:38+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-20 02:48:38 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/prestage.py

Zeit: 2026-08-20T02:48:38+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

