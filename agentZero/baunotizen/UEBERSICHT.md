# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-19T10:41:10Z. **2695 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T16:55:25+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2597 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1689 |
| baunotiz | bauverlauf.jsonl | 864 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2695 · Gegenhypothese: 0 von 2695

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen149 retrieval ACTIVE and reauth regression

`baunotiz-bauverlauf-580bfc23deecd637ea83` · baunotiz · bauverlauf.jsonl · 2026-08-19T16:55:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen149 retrieval ACTIVE and reauth regression

`baunotiz-git-d9a13bbbf87047f29100aeb6eb88ac5b5c8aea82` · baunotiz · git-commit · 2026-08-19T16:55:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen149 retrieval ACTIVE and reauth regression

### claycode supervisor: bind Gen145 metrology and adapter-scope distinction

`baunotiz-bauverlauf-08b748bd883d038b21cd` · baunotiz · bauverlauf.jsonl · 2026-08-19T15:43:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen145 metrology and adapter-scope distinction

`baunotiz-git-878fed4c367186fb993b4c33f2ccffd6878bc599` · baunotiz · git-commit · 2026-08-19T15:43:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen145 metrology and adapter-scope distinction

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

### agentZero-Export 2026-08-19T10:20:42Z (Generation 153, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-cff97ba3d46a368b870e830949f9de539df3386d` · baunotiz · git-commit · 2026-08-19T10:22:30+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T10:20:42Z (Generation 153, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T10:11:09Z (Generation 151, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-41f953c516be4f28ed14cce39bbafc5bc227fd93` · baunotiz · git-commit · 2026-08-19T10:11:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T10:11:09Z (Generation 151, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T10:11:09Z (Generation 151, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-b540cc9809df8bb41117` · baunotiz · bauverlauf.jsonl · 2026-08-19T10:11:49+00:00 · agentZero

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

### agentZero-Export 2026-08-19T09:41:10Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-8e4f78f6dbb595ae5dcc82fbc37a0f80345be3fa` · baunotiz · git-commit · 2026-08-19T09:42:56+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T09:41:10Z (Generation 149, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T09:41:10Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-ab8889e43fc1621e7ac0` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:42:56+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-60a15b05f86d2929e14c7ac2bcb2bebbe098c43e` · baunotiz · git-commit · 2026-08-19T09:26:30+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-c676d4a5c5c718320fdf` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:26:30+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

