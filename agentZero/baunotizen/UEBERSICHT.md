# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T22:11:17Z. **3161 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T02:46:42+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3063 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1922 |
| baunotiz | bauverlauf.jsonl | 1096 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3161 · Gegenhypothese: 0 von 3161

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-bauverlauf-c694e3593ecb2bafe5e6` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-git-f7e1f58cb929e31275e53913dc65e437cb14f105` · baunotiz · git-commit · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 PTY recovery without fix credit

### claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

`baunotiz-bauverlauf-6241a69263ed23f95d75` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:43:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

`baunotiz-git-0ab454ac948d50acb808607b51540ac327bbb504` · baunotiz · git-commit · 2026-08-21T02:43:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

### research: bind Gen211 system-prompt last-writer alias

`baunotiz-bauverlauf-e153cd74f380e90ff037` · baunotiz · bauverlauf.jsonl · 2026-08-21T01:47:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 system-prompt last-writer alias

`baunotiz-git-539a6c1cf4f9051be12333398bb68359bdd39eb1` · baunotiz · git-commit · 2026-08-21T01:47:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 system-prompt last-writer alias

### claycode supervisor: bind Gen211 identity isolation and work-debt frontier

`baunotiz-bauverlauf-e5140e6f9e8ea22585f5` · baunotiz · bauverlauf.jsonl · 2026-08-21T01:42:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen211 identity isolation and work-debt frontier

`baunotiz-git-18f5a8a446bc194c38b70414bd19a44dcd977db6` · baunotiz · git-commit · 2026-08-21T01:42:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen211 identity isolation and work-debt frontier

### research: route Gen211 null-evidence and isolation falsifiers

`baunotiz-bauverlauf-36c22de40724f275abfc` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:49:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen211 null-evidence and isolation falsifiers

`baunotiz-git-5da37ecd70e2025d60f0ec852d53548657201413` · baunotiz · git-commit · 2026-08-21T00:49:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen211 null-evidence and isolation falsifiers

### research: bind Gen211 warm-pool session prompt race

`baunotiz-bauverlauf-92716302c9b3475c490f` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:46:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 warm-pool session prompt race

`baunotiz-git-0a7fabfe8ee00b70b9e7be9b2b4f9e3aeb3c636b` · baunotiz · git-commit · 2026-08-21T00:46:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 warm-pool session prompt race

### claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

`baunotiz-bauverlauf-ff4b794053d58fe180c0` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:43:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

`baunotiz-git-de63cefc0ae08baa548df8b175d5d7b01baa4255` · baunotiz · git-commit · 2026-08-21T00:43:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

### research: route Gen206 availability and atomicity falsifiers

`baunotiz-bauverlauf-678e0fc68abfe8e872fd` · baunotiz · bauverlauf.jsonl · 2026-08-20T23:55:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen206 availability and atomicity falsifiers

`baunotiz-git-1dabd57d9561653de40c668caa066867b6153e39` · baunotiz · git-commit · 2026-08-20T23:55:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen206 availability and atomicity falsifiers

### claycode supervisor: bind Gen204 candidate identity aliasing frontier

`baunotiz-bauverlauf-11c30fe3183dc83380d9` · baunotiz · bauverlauf.jsonl · 2026-08-20T22:49:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen204 candidate identity aliasing frontier

`baunotiz-git-a829699e440f03ea258c56e3cd6748a6f0ed3ba9` · baunotiz · git-commit · 2026-08-20T22:49:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen204 candidate identity aliasing frontier

### research: preserve Gen204 lease-test flip and route flake matrix

`baunotiz-bauverlauf-c51d8a37a4b09890fed1` · baunotiz · bauverlauf.jsonl · 2026-08-20T22:48:26+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: preserve Gen204 lease-test flip and route flake matrix

`baunotiz-git-5507b05e1bfa2846e9cd329e9587be127e3d76ce` · baunotiz · git-commit · 2026-08-20T22:48:26+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: preserve Gen204 lease-test flip and route flake matrix

### research: route Gen204 identity and provenance falsifiers

`baunotiz-bauverlauf-693cf4e26304cf64f62e` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:50:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen204 identity and provenance falsifiers

`baunotiz-git-8946d67b1320928ed8199adf5680da64a581b2d7` · baunotiz · git-commit · 2026-08-20T21:50:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen204 identity and provenance falsifiers

### research: bind Gen204 content-prefix identity aliasing falsifier

`baunotiz-bauverlauf-3509e57d32798e2ebce8` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:47:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen204 content-prefix identity aliasing falsifier

`baunotiz-git-6a5f143931db33e56aaec57f3af89fb99e829d83` · baunotiz · git-commit · 2026-08-20T21:47:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen204 content-prefix identity aliasing falsifier

### claycode supervisor: bind Gen204 persistent GWT bypass and 664/1 frontier

`baunotiz-bauverlauf-7ee1858581e05adbcc47` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:44:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

