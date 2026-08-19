# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-19T10:11:10Z. **2689 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T15:43:36+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2591 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1686 |
| baunotiz | bauverlauf.jsonl | 861 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2689 · Gegenhypothese: 0 von 2689

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

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

### agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-60a15b05f86d2929e14c7ac2bcb2bebbe098c43e` · baunotiz · git-commit · 2026-08-19T09:26:30+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T09:25:47Z (Generation 149, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-c676d4a5c5c718320fdf` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:26:30+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T09:11:09Z (Generation 147, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-8381ead84a8992ab9861b4737351bd21300189bb` · baunotiz · git-commit · 2026-08-19T09:11:50+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T09:11:09Z (Generation 147, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T09:11:09Z (Generation 147, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-668b21f1e52cfad880ae` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:11:50+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T08:41:08Z (Generation 145, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-87df407413c3920a20d9333c47e3bb46182ca4de` · baunotiz · git-commit · 2026-08-19T08:43:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T08:41:08Z (Generation 145, 59 Dateien, 1 geschwaerzt)

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-bauverlauf-75383d1b7c91931e4422` · baunotiz · bauverlauf.jsonl · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-git-56802f61263e4cda9795618a9e6a3f7d65c12542` · baunotiz · git-commit · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 PTY red-green nondeterminism

### agentZero-Export 2026-08-19T08:25:05Z (Generation 145, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-edb529076342e38c816d0e518a6158fe90766659` · baunotiz · git-commit · 2026-08-19T08:25:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T08:25:05Z (Generation 145, 59 Dateien, 1 geschwaerzt)

