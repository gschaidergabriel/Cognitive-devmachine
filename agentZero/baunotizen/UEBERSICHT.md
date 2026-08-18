# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-18T15:11:05Z. **2525 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-18T20:39:11+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2429 |
| vorfall | 96 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1604 |
| baunotiz | bauverlauf.jsonl | 781 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |

## Hypothese: 0 von 2525 · Gegenhypothese: 0 von 2525

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **1** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: steer Gen85 Mistral prestage regression

`baunotiz-bauverlauf-a058ed244d15c3dd5eb7` · baunotiz · bauverlauf.jsonl · 2026-08-18T20:39:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen85 Mistral prestage regression

`baunotiz-git-d67181b6978ac1ae9227ce3d171805995cded428` · baunotiz · git-commit · 2026-08-18T20:39:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen85 Mistral prestage regression

### claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

`baunotiz-bauverlauf-d29252642b0d6565e56a` · baunotiz · bauverlauf.jsonl · 2026-08-18T19:39:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

`baunotiz-git-6f26c6140c09a8783c211be39e6456cd5592cf66` · baunotiz · git-commit · 2026-08-18T19:39:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

### claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

`baunotiz-bauverlauf-ab8f8081d673cd7185e7` · baunotiz · bauverlauf.jsonl · 2026-08-18T18:44:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

`baunotiz-git-9fc1f3ccee7c2dc4f54fd5b7e89c31a8106ed7e0` · baunotiz · git-commit · 2026-08-18T18:44:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

### claycode supervisor: bind Gen62 persistent adapter counterevidence

`baunotiz-bauverlauf-9fc58bc90caa8e7721d7` · baunotiz · bauverlauf.jsonl · 2026-08-18T17:41:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen62 persistent adapter counterevidence

`baunotiz-git-f95beb3101ae357808054c30953241515d585e4b` · baunotiz · git-commit · 2026-08-18T17:41:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen62 persistent adapter counterevidence

### claycode supervisor: steer on Gen39 runtime-adapter regression

`baunotiz-bauverlauf-7c0f7c63d6e00a5cdf9a` · baunotiz · bauverlauf.jsonl · 2026-08-18T16:40:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer on Gen39 runtime-adapter regression

`baunotiz-git-67ce133835faea60689e86eb2e8a6846c5a32c6a` · baunotiz · git-commit · 2026-08-18T16:40:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer on Gen39 runtime-adapter regression

### claycode supervisor: bind Gen36 measurement reconvergence and compression-receipt semantics

`baunotiz-bauverlauf-0683e06a6325fcf05690` · baunotiz · bauverlauf.jsonl · 2026-08-18T15:49:46+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen36 measurement reconvergence and compression-receipt semantics

`baunotiz-git-e84a9a6c789970aaf345c84adb136a6dc4d22be2` · baunotiz · git-commit · 2026-08-18T15:49:46+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen36 measurement reconvergence and compression-receipt semantics

### claycode supervisor: steer on Gen35 test-receipt drift and durable-memory emergence

`baunotiz-bauverlauf-c6bd9afe90dfeb9fdd4d` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:58:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer on Gen35 test-receipt drift and durable-memory emergence

`baunotiz-git-d20a090a25f2b8c65bf7bc4a41aa76ec460e8851` · baunotiz · git-commit · 2026-08-18T14:58:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer on Gen35 test-receipt drift and durable-memory emergence

### agentZero research: combined Claude token savings model

`baunotiz-bauverlauf-90c73358f7b4cd4ec191` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:51:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero research: combined Claude token savings model

`baunotiz-git-d5acb7e26fe478755adf126c6a813845f5777c3e` · baunotiz · git-commit · 2026-08-18T14:51:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero research: combined Claude token savings model

### agentZero research: index Claude-only token savings analysis

`baunotiz-bauverlauf-dc5adb297ed215eaa610` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:47:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero research: index Claude-only token savings analysis

`baunotiz-git-afcc99de62c5b3283870f6a64ee3e6e5612dfa02` · baunotiz · git-commit · 2026-08-18T14:47:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero research: index Claude-only token savings analysis

### agentZero research: quantify Claude token savings architecture

`baunotiz-bauverlauf-ce3b01b6512951083a08` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:47:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero research: quantify Claude token savings architecture

`baunotiz-git-721ce5f340b770b58267f5cd654bafda9d338129` · baunotiz · git-commit · 2026-08-18T14:47:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero research: quantify Claude token savings architecture

### agentZero research: index generation 33 measurement integrity

`baunotiz-bauverlauf-1dd5e84ac09d328713b3` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:46:58+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero research: index generation 33 measurement integrity

`baunotiz-git-37c3d877b1f88185649841a82de0186248e39e45` · baunotiz · git-commit · 2026-08-18T14:46:58+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero research: index generation 33 measurement integrity

### agentZero research: bind generation 33 measurement-integrity frontier

`baunotiz-bauverlauf-8f4f56fbfdcad667b22a` · baunotiz · bauverlauf.jsonl · 2026-08-18T14:46:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero research: bind generation 33 measurement-integrity frontier

`baunotiz-git-98c6926f4692b063ec5b638197ee88a23ce32d4e` · baunotiz · git-commit · 2026-08-18T14:46:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero research: bind generation 33 measurement-integrity frontier

### agentZero-Export 2026-08-18T14:41:02Z (Generation 93, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-402debf1c8b26fa5de1b06036841a4e703ec75ce` · baunotiz · git-commit · 2026-08-18T14:41:42+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T14:41:02Z (Generation 93, 59 Dateien, 1 geschwaerzt)

