# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-19T08:25:06Z. **2678 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T14:41:02+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2580 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1680 |
| baunotiz | bauverlauf.jsonl | 856 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2678 · Gegenhypothese: 0 von 2678

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: classify Gen143 intermittent receipt failure

`baunotiz-bauverlauf-05167ef6e8d1eeb75f7a` · baunotiz · bauverlauf.jsonl · 2026-08-19T14:41:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: classify Gen143 intermittent receipt failure

`baunotiz-git-2653e7c6c8ffa037bd9e1429f291db084c57461f` · baunotiz · git-commit · 2026-08-19T14:41:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: classify Gen143 intermittent receipt failure

### claycode supervisor: escalate Gen137 repeated incomplete receipts

`baunotiz-bauverlauf-c1aa2705e946177f420e` · baunotiz · bauverlauf.jsonl · 2026-08-19T13:53:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: escalate Gen137 repeated incomplete receipts

`baunotiz-git-efe6ef7f5d0d74ea2cf8cabbd6f2edc664baa95a` · baunotiz · git-commit · 2026-08-19T13:53:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: escalate Gen137 repeated incomplete receipts

### claycode supervisor: block Gen130 null test receipt and bind warm-zero evidence

`baunotiz-bauverlauf-149b5825ec3e9860e2a5` · baunotiz · bauverlauf.jsonl · 2026-08-19T12:44:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: block Gen130 null test receipt and bind warm-zero evidence

`baunotiz-git-32bbd085ec583a6db14ce13499eed88b529b8d2b` · baunotiz · git-commit · 2026-08-19T12:44:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: block Gen130 null test receipt and bind warm-zero evidence

### claycode supervisor: bind Gen123 preprocessor security frontier

`baunotiz-git-9b7f5d0dc984dd0dd0fa69d7d907d8711d81539f` · baunotiz · git-commit · 2026-08-19T11:54:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen123 preprocessor security frontier

### claycode supervisor: bind Gen123 preprocessor security frontier

`baunotiz-bauverlauf-1dfa24bb5f7ec4504a05` · baunotiz · bauverlauf.jsonl · 2026-08-19T11:54:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: bind Gen123 preprocessor security and adapter frontier

`baunotiz-git-e24aef9f0619689ebb1630d1434c6885d0e642c8` · baunotiz · git-commit · 2026-08-19T11:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen123 preprocessor security and adapter frontier

### agentzeroforschung: bind Gen123 preprocessor security and adapter frontier

`baunotiz-bauverlauf-10bd939d265fd7983a2a` · baunotiz · bauverlauf.jsonl · 2026-08-19T11:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

`baunotiz-git-9ab0fcf3405d4dee92fa3b8804ecd351054e50a0` · baunotiz · git-commit · 2026-08-19T10:44:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

### agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

`baunotiz-bauverlauf-ebf28f9445b1d173e720` · baunotiz · bauverlauf.jsonl · 2026-08-19T10:44:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

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

### agentZero-Export 2026-08-19T08:11:08Z (Generation 145, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-e00ff4a6f2b0e58026857d2978c39e36fea76b0c` · baunotiz · git-commit · 2026-08-19T08:11:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T08:11:08Z (Generation 145, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T08:05:57Z (Generation 145, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-597f531e5636c7b4ce21` · baunotiz · bauverlauf.jsonl · 2026-08-19T08:06:38+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T08:05:57Z (Generation 145, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-25093a3a200eab62fd2be59c445edceea77ada2b` · baunotiz · git-commit · 2026-08-19T08:06:38+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T08:05:57Z (Generation 145, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T07:41:08Z (Generation 143, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-3f95c5841f247d0754afceb2cfece138f396f537` · baunotiz · git-commit · 2026-08-19T07:41:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T07:41:08Z (Generation 143, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T07:41:08Z (Generation 143, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-cf3eacf75f2f1c7ab4f3` · baunotiz · bauverlauf.jsonl · 2026-08-19T07:41:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-bauverlauf-400aaca708050a6b42bf` · baunotiz · bauverlauf.jsonl · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-git-66a6c46f5918ffeaa36f432de369c34b21877e6c` · baunotiz · git-commit · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 recurring PTY lease red

### agentZero-Export 2026-08-19T07:32:04Z (Generation 143, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-2c02a90391c990d866a7` · baunotiz · bauverlauf.jsonl · 2026-08-19T07:32:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T07:32:04Z (Generation 143, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-24d3c324bbb13d0a4055e8129a2f77a36447f470` · baunotiz · git-commit · 2026-08-19T07:32:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T07:32:04Z (Generation 143, 59 Dateien, 1 geschwaerzt)

