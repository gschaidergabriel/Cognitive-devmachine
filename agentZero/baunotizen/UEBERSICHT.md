# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T16:06:44Z. **4499 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T21:38:08+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 4401 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2594 |
| baunotiz | bauverlauf.jsonl | 1759 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4499 · Gegenhypothese: 0 von 4499

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen276 PTY red recurrence to exact-runtime gate

`baunotiz-bauverlauf-cede76b3d5141dd1a91f` · baunotiz · bauverlauf.jsonl · 2026-08-22T21:38:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen276 PTY red recurrence to exact-runtime gate

`baunotiz-git-b8e47067be9ff843a2a1fe9b4bb910956ed6cd2d` · baunotiz · git-commit · 2026-08-22T21:38:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen276 PTY red recurrence to exact-runtime gate

### claycode supervisor: stop source-only guard accumulation and force exact runtime

`baunotiz-bauverlauf-de310a928cf5d3e44d3e` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:39:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: stop source-only guard accumulation and force exact runtime

`baunotiz-git-ac881de36adc6b1bd9381adc43857654d92f5136` · baunotiz · git-commit · 2026-08-22T20:39:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: stop source-only guard accumulation and force exact runtime

### Merge PR #975: bind one generation/CAS authority invariant

`baunotiz-bauverlauf-1416e8555677411cbc78` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:13:27+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Add the auto-activating one-generation-authority guard on top of current profile/truth guards. Native entity_state.generation remains the sole live CAS authority. Source/acceptance guard only; no runtime PASS, no added unusual experiment.

### Merge PR #975: bind one generation/CAS authority invariant

`baunotiz-git-eb4674cc97a65c908961d55f9759e0a1a67a87ba` · baunotiz · git-commit · 2026-08-22T20:13:27+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #975: bind one generation/CAS authority invariant

Add the auto-activating one-generation-authority guard on top of current profile/truth guards. Native entity_state.generation remains the sole live CAS authority. Source/acceptance guard only; no runtime PASS, no added unusual experiment.

### Merge PR #976: bind claim metrics into canonical hash

`baunotiz-bauverlauf-311063e7ec17de909db6` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:12:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Add an auto-activating truth-boundary guard requiring converged reference runtimes to hash-bind the metrics used for state-claim authorization. Deterministic source contract only; no runtime PASS and no additional unusual experiment.

### Merge PR #976: bind claim metrics into canonical hash

`baunotiz-git-c3ba0d6acb432f3fa45c33e1ce8c453c3e1f35e5` · baunotiz · git-commit · 2026-08-22T20:12:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #976: bind claim metrics into canonical hash

Add an auto-activating truth-boundary guard requiring converged reference runtimes to hash-bind the metrics used for state-claim authorization. Deterministic source contract only; no runtime PASS and no additional unusual experiment.

### test(reference): bind claim metrics into canonical hash

`baunotiz-bauverlauf-ada965684784cec95538` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:12:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(reference): bind claim metrics into canonical hash

`baunotiz-git-ad3ce9e974693e81aa84d6ea9e312b466420e2c3` · baunotiz · git-commit · 2026-08-22T20:12:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(reference): bind claim metrics into canonical hash

### evidence(go): record generation authority fork gate

`baunotiz-bauverlauf-3b6a3774092a59ebdd2c` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:12:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence(go): record generation authority fork gate

`baunotiz-git-35cafe91e0ca0436d78df5425e601d92e935fa96` · baunotiz · git-commit · 2026-08-22T20:12:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence(go): record generation authority fork gate

### contract(reference): bind single generation CAS authority

`baunotiz-bauverlauf-5a789d89a382c5c0a24e` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:11:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### contract(reference): bind single generation CAS authority

`baunotiz-git-bc9cd0923f08ad7120293b77778695a532769553` · baunotiz · git-commit · 2026-08-22T20:11:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

contract(reference): bind single generation CAS authority

### Merge PR #973: fuse one profile authority guard

`baunotiz-bauverlauf-2de7c023f24dfd0a6675` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:09:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Replace the earlier always-active duplicate with the current-main auto-activating one-profile-authority invariant. No runtime PASS and no additional unusual experiment.

### Merge PR #973: fuse one profile authority guard

`baunotiz-git-c56b4f8a5358391dad1897b29d8f5beed929fc0c` · baunotiz · git-commit · 2026-08-22T20:09:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #973: fuse one profile authority guard

Replace the earlier always-active duplicate with the current-main auto-activating one-profile-authority invariant. No runtime PASS and no additional unusual experiment.

### test(reference): remove superseded always-red authority guard

`baunotiz-bauverlauf-14fed92b49f5acf49c80` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:09:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(reference): remove superseded always-red authority guard

`baunotiz-git-460c5c10e05530b5d38b9b4b9647dc26fba4baa3` · baunotiz · git-commit · 2026-08-22T20:09:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(reference): remove superseded always-red authority guard

### test(reference): fuse single profile authority invariant

`baunotiz-bauverlauf-72a8c8ea265b4b79b1cd` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:08:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(reference): fuse single profile authority invariant

`baunotiz-git-b35c8fb4be72cfe147e994cd0641459f520be647` · baunotiz · git-commit · 2026-08-22T20:08:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(reference): fuse single profile authority invariant

### evidence: join this go receipts to shared macrocycle

`baunotiz-bauverlauf-5dfeabdf388bd96dbed1` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:08:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Correct local receipt accounting to the shared 19:49 go macrocycle. The sole unusual slot remains the RFC6901 response-pointer falsifier; local shims/poisons are ordinary regressions.

### evidence: join this go receipts to shared macrocycle

`baunotiz-git-90f8f99bfdd92dd6de9fb73489610b400daa9b97` · baunotiz · git-commit · 2026-08-22T20:08:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: join this go receipts to shared macrocycle

Correct local receipt accounting to the shared 19:49 go macrocycle. The sole unusual slot remains the RFC6901 response-pointer falsifier; local shims/poisons are ordinary regressions.

### Merge PR #969: bind single profile authority gate

`baunotiz-bauverlauf-8d105a506914f4097d17` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:06:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the native MiniUnifiedDB profile-authority convergence guard and joined macrocycle receipt. Source/architecture guard only; no runtime PASS, no additional unusual experiment.

### Merge PR #969: bind single profile authority gate

`baunotiz-git-06799ff2cd6ebffdd56521fc6a7fd0f6b6d67ef0` · baunotiz · git-commit · 2026-08-22T20:06:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #969: bind single profile authority gate

Fuse the native MiniUnifiedDB profile-authority convergence guard and joined macrocycle receipt. Source/architecture guard only; no runtime PASS, no additional unusual experiment.

### contract(reference): bind native profile authority convergence gate

`baunotiz-bauverlauf-d03fbad6d7cf34234492` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:06:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fail closed on a second active-profile authority and on local_exec subprocesses without an explicit child environment. Source contract only; no runtime PASS implied.

