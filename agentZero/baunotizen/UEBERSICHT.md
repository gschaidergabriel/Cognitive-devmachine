# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T20:32:33Z. **3685 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T02:53:16+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3587 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2185 |
| baunotiz | bauverlauf.jsonl | 1355 |
| baunotiz | github-ereignis | 42 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3685 · Gegenhypothese: 0 von 3685

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: escalate Gen249 paid-lane FREE_ONLY control drift

`baunotiz-bauverlauf-fb1e5535dba2bfd92095` · baunotiz · bauverlauf.jsonl · 2026-08-22T02:53:16+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: escalate Gen249 paid-lane FREE_ONLY control drift

`baunotiz-git-604360022402d356067f8f7b9ebb1132c2a1fe41` · baunotiz · git-commit · 2026-08-22T02:53:16+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: escalate Gen249 paid-lane FREE_ONLY control drift

### claycode supervisor: quarantine paid GLM lanes under FREE_ONLY

`baunotiz-git-00b474f57486c42174dfdbeaf4978117a976b56b` · baunotiz · git-commit · 2026-08-22T01:44:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: quarantine paid GLM lanes under FREE_ONLY

### claycode supervisor: quarantine paid GLM lanes under FREE_ONLY

`baunotiz-bauverlauf-7e379414323ce16ea508` · baunotiz · bauverlauf.jsonl · 2026-08-22T01:44:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen247 read-side schema mutation boundary

`baunotiz-bauverlauf-2f125324ee5a863b79b1` · baunotiz · bauverlauf.jsonl · 2026-08-22T00:48:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen247 read-side schema mutation boundary

`baunotiz-git-fd037c0e43a2d9004073d16041e84a24abdbfad6` · baunotiz · git-commit · 2026-08-22T00:48:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen247 read-side schema mutation boundary

### research: bind Gen247 test source to local EntityOS chronology

`baunotiz-bauverlauf-94c2f1649d6e5cfd5068` · baunotiz · bauverlauf.jsonl · 2026-08-22T00:46:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen247 test source to local EntityOS chronology

`baunotiz-git-c2c6aed7404353b008b1d1f91b511fb574b6fc50` · baunotiz · git-commit · 2026-08-22T00:46:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen247 test source to local EntityOS chronology

### instrument: add paired read-side-effect discriminator

`baunotiz-bauverlauf-4644ac0dd7134ce67de4` · baunotiz · bauverlauf.jsonl · 2026-08-22T00:08:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### instrument: add paired read-side-effect discriminator

`baunotiz-git-73ce06c03766f1895bef52897e5326a7ab11b4d7` · baunotiz · git-commit · 2026-08-22T00:08:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

instrument: add paired read-side-effect discriminator

### instrument: add read-side-effect receipt contract

`baunotiz-bauverlauf-cb8d0d41a24badf8c997` · baunotiz · bauverlauf.jsonl · 2026-08-22T00:07:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### instrument: add read-side-effect receipt contract

`baunotiz-git-777c5457954cd06f194376e12f510165f2baf0e8` · baunotiz · git-commit · 2026-08-22T00:07:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

instrument: add read-side-effect receipt contract

### research: isolate Gen247 read-side schema mutation

`baunotiz-bauverlauf-a86bd94e288b8901b467` · baunotiz · bauverlauf.jsonl · 2026-08-22T00:07:18+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: isolate Gen247 read-side schema mutation

`baunotiz-git-33c6b6c910e945b21b0fede6e64592adedfe4fe7` · baunotiz · git-commit · 2026-08-22T00:07:18+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: isolate Gen247 read-side schema mutation

### research: bind Gen247 generation advance causal neutrality

`baunotiz-bauverlauf-1edccbcc96233eb218b7` · baunotiz · bauverlauf.jsonl · 2026-08-21T23:48:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen247 generation advance causal neutrality

`baunotiz-git-5a04a5de5a1690c095f07207c5323aa9bc5c6985` · baunotiz · git-commit · 2026-08-21T23:48:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen247 generation advance causal neutrality

### research: bind Gen247 bug hypothesis closure provenance

`baunotiz-bauverlauf-a3d1130dd1ef572e93ce` · baunotiz · bauverlauf.jsonl · 2026-08-21T23:45:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen247 bug hypothesis closure provenance

`baunotiz-git-78b7bd4d5d85606fd36c35d730761248ee6ce012` · baunotiz · git-commit · 2026-08-21T23:45:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen247 bug hypothesis closure provenance

### claycode supervisor: bind Gen246 autonomy dispatch provenance boundary

`baunotiz-bauverlauf-edc9aa3fab8de00f9322` · baunotiz · bauverlauf.jsonl · 2026-08-21T22:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen246 autonomy dispatch provenance boundary

`baunotiz-git-042b95303dc1306a062714c61073d6c078f89665` · baunotiz · git-commit · 2026-08-21T22:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen246 autonomy dispatch provenance boundary

### research: fuse tmux autonomy transport fence into go reentry

`baunotiz-bauverlauf-04af697292137f44245a` · baunotiz · bauverlauf.jsonl · 2026-08-21T21:54:46+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: fuse tmux autonomy transport fence into go reentry

`baunotiz-git-8ae4b8ac00be123d4c887c72b646f93d0f26a36a` · baunotiz · git-commit · 2026-08-21T21:54:46+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: fuse tmux autonomy transport fence into go reentry

### research: isolate Gen245 shopping-grounding failure mode

`baunotiz-bauverlauf-e0a9db26b8e96412d75e` · baunotiz · bauverlauf.jsonl · 2026-08-21T21:47:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Bind the first Gen245 negative-rated shopping turn to same-session correction, first-party catalog grounding, causal/retrieval receipts, and the terminal frontend export-gap discriminator. Research-only; agentZero product bytes unchanged.

### research: isolate Gen245 shopping-grounding failure mode

`baunotiz-git-c89af32407ee5ddee2e0404c1e93abd3f40dc887` · baunotiz · git-commit · 2026-08-21T21:47:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: isolate Gen245 shopping-grounding failure mode

Bind the first Gen245 negative-rated shopping turn to same-session correction, first-party catalog grounding, causal/retrieval receipts, and the terminal frontend export-gap discriminator. Research-only; agentZero product bytes unchanged.

### research: route autonomy dispatch provenance counterexample

`baunotiz-bauverlauf-5328fb4fbf2fab2ee8df` · baunotiz · bauverlauf.jsonl · 2026-08-21T21:44:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

