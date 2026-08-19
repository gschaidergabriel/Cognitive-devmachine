# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-19T04:11:09Z. **2620 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T10:44:08+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2522 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1652 |
| baunotiz | bauverlauf.jsonl | 826 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2620 · Gegenhypothese: 0 von 2620

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **1** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

`baunotiz-git-9ab0fcf3405d4dee92fa3b8804ecd351054e50a0` · baunotiz · git-commit · 2026-08-19T10:44:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

### agentzeroforschung: classify Gen116 PTY lease oscillation

`baunotiz-bauverlauf-6fca3a9e7dd2507c7521` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:47:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: classify Gen116 PTY lease oscillation

`baunotiz-git-b643704e7245d1e9cb3302c5ef1db2bd5e5d6b52` · baunotiz · git-commit · 2026-08-19T09:47:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: classify Gen116 PTY lease oscillation

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-bauverlauf-75383d1b7c91931e4422` · baunotiz · bauverlauf.jsonl · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-git-56802f61263e4cda9795618a9e6a3f7d65c12542` · baunotiz · git-commit · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 PTY red-green nondeterminism

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-bauverlauf-400aaca708050a6b42bf` · baunotiz · bauverlauf.jsonl · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-git-66a6c46f5918ffeaa36f432de369c34b21877e6c` · baunotiz · git-commit · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 recurring PTY lease red

### agentzeroforschung: bind Gen116 stable 583/1 growth frontier

`baunotiz-bauverlauf-e2951bf2c9cb5bde2ad7` · baunotiz · bauverlauf.jsonl · 2026-08-19T05:48:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: bind Gen116 stable 583/1 growth frontier

`baunotiz-git-c5ef966b728d493295051d2209e7de89fa46d24c` · baunotiz · git-commit · 2026-08-19T05:48:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen116 stable 583/1 growth frontier

### claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

`baunotiz-bauverlauf-d185b210443afa86415e` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:55:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

`baunotiz-git-a9fe30c8803257c8f69c22259473de3be3d07401` · baunotiz · git-commit · 2026-08-19T04:55:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

### agentzeroforschung: index Gen116 adapter evidence correction

`baunotiz-bauverlauf-9bd86f9bfa49d0e9fc39` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: index Gen116 adapter evidence correction

`baunotiz-git-d825c9453cf27d9aefd4fe2f3b813a0f6c4b53b7` · baunotiz · git-commit · 2026-08-19T04:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: index Gen116 adapter evidence correction

### agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

`baunotiz-bauverlauf-37f7d7625e889765ab83` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:46:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

`baunotiz-git-d9371059b2995dfb3c193e277016a01ad644d5ef` · baunotiz · git-commit · 2026-08-19T04:46:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

### agentZero-Export 2026-08-19T03:41:08Z (Generation 117, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-4c7b410f2704367f6179d3c4a62507a9fa262d35` · baunotiz · git-commit · 2026-08-19T03:43:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T03:41:08Z (Generation 117, 59 Dateien, 1 geschwaerzt)

### claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

`baunotiz-git-a591e40e29d9ddb9f4d35dcfe3691f37f9034977` · baunotiz · git-commit · 2026-08-19T03:41:31+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

### claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

`baunotiz-bauverlauf-a769c7cb4251dd7fc691` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:41:31+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-5a2cbb3916235dab9811d0053fde94064cb53dcb` · baunotiz · git-commit · 2026-08-19T03:11:43+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-56f704d6523b91a46161` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:11:43+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen107 583/1 and stale security acceptance

`baunotiz-git-3beb76ffb6f05a43aa192b568956fd4626bead06` · baunotiz · git-commit · 2026-08-19T02:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen107 583/1 and stale security acceptance

### claycode supervisor: bind Gen107 583/1 and stale security acceptance

`baunotiz-bauverlauf-0d84e4a40038c22ed240` · baunotiz · bauverlauf.jsonl · 2026-08-19T02:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T02:41:07Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-68d8c7b1224496ff76acbd8121e9da0d7b74cf7a` · baunotiz · git-commit · 2026-08-19T02:44:42+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T02:41:07Z (Generation 116, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T02:41:07Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-71ad087e8d276960dd97` · baunotiz · bauverlauf.jsonl · 2026-08-19T02:44:42+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T02:11:07Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-a5c68d5e14f70193362c3b0dbbf9fca77a10f1bd` · baunotiz · git-commit · 2026-08-19T02:11:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T02:11:07Z (Generation 116, 59 Dateien, 1 geschwaerzt)

