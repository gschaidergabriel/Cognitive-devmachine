# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T12:06:44Z. **4211 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T17:47:42+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 4113 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2449 |
| baunotiz | bauverlauf.jsonl | 1616 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4211 · Gegenhypothese: 0 von 4211

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: classify same-source terminal auth cluster recovery

`baunotiz-bauverlauf-964d59db73655c1ea608` · baunotiz · bauverlauf.jsonl · 2026-08-22T17:47:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: classify same-source terminal auth cluster recovery

`baunotiz-git-9d3f3f734f600966310f0cb29f6b2577d9d0d575` · baunotiz · git-commit · 2026-08-22T17:47:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: classify same-source terminal auth cluster recovery

### claycode supervisor: fence PR880 paid cognition lane under FREE_ONLY

`baunotiz-bauverlauf-27d7a225e0ccd46b9b54` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:52:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: fence PR880 paid cognition lane under FREE_ONLY

`baunotiz-git-594d97a80aa27fe9300f51788449ec66ce8434ac` · baunotiz · git-commit · 2026-08-22T16:52:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: fence PR880 paid cognition lane under FREE_ONLY

### cognition: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane (#880)

`baunotiz-bauverlauf-63044cd059216486a1ba` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:37:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Owner-selected Variant 1: Qwen/Qwen3.5-0.8B direct Together Full Fine-Tuning. Preserve paid-create authorization gate; add exact-vector compositional OOD scoring and focused no-secret CI.

### cognition: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane (#880)

`baunotiz-git-74e01f7b63dca277bd2aa3d79e7397ae2083705c` · baunotiz · git-commit · 2026-08-22T16:37:35+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane (#880)

Owner-selected Variant 1: Qwen/Qwen3.5-0.8B direct Together Full Fine-Tuning. Preserve paid-create authorization gate; add exact-vector compositional OOD scoring and focused no-secret CI.

### ci: call corpus validator with exact train/validation paths

`baunotiz-bauverlauf-e7e9abbc063a07e26ddf` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:37:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### ci: call corpus validator with exact train/validation paths

`baunotiz-git-a7086b6a2cd907cc485f553ad157cc9fc8a2db89` · baunotiz · git-commit · 2026-08-22T16:37:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ci: call corpus validator with exact train/validation paths

### ci: add deterministic no-secret cognition gates for 0.8B lane

`baunotiz-bauverlauf-9d748b0466b773db79bf` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:36:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### ci: add deterministic no-secret cognition gates for 0.8B lane

`baunotiz-git-291d089380b73f4c7c643541c73f0a78c99c6f88` · baunotiz · git-commit · 2026-08-22T16:36:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ci: add deterministic no-secret cognition gates for 0.8B lane

### docs: make Qwen3.5-0.8B the canonical paid cognition lane

`baunotiz-bauverlauf-0bd9c3345867181512b0` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:35:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### docs: make Qwen3.5-0.8B the canonical paid cognition lane

`baunotiz-git-1783e788773f8d5929a11969ac13a3e2e7d7b2b6` · baunotiz · git-commit · 2026-08-22T16:35:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

docs: make Qwen3.5-0.8B the canonical paid cognition lane

### test: reject wrong typed args in compositional OOD omega scoring

`baunotiz-bauverlauf-f43eb9f678ece5ffe573` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:35:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test: reject wrong typed args in compositional OOD omega scoring

`baunotiz-git-ad04b8259bee9687c67e7e6a2276beb5f5ba8b7a` · baunotiz · git-commit · 2026-08-22T16:35:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test: reject wrong typed args in compositional OOD omega scoring

### eval: bind compositional OOD omega cases to exact typed vectors

`baunotiz-bauverlauf-a6c30ad498fac5ffa406` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:34:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### eval: bind compositional OOD omega cases to exact typed vectors

`baunotiz-git-4de97ecf66e24bcb61019f6b18ff9cca38e803b3` · baunotiz · git-commit · 2026-08-22T16:34:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

eval: bind compositional OOD omega cases to exact typed vectors

### cognition: promote Qwen3.5-0.8B lane to owner-selected target

`baunotiz-bauverlauf-87235596ba52c02b2614` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:34:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### cognition: promote Qwen3.5-0.8B lane to owner-selected target

`baunotiz-git-99374b9025ae690c4b5798d007d6eea086de37e0` · baunotiz · git-commit · 2026-08-22T16:34:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: promote Qwen3.5-0.8B lane to owner-selected target

### directive: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane

`baunotiz-bauverlauf-50b12b385ced125dd735` · baunotiz · bauverlauf.jsonl · 2026-08-22T16:34:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### directive: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane

`baunotiz-git-778f66d4e6b865d55e4043b014728bc1f61f215e` · baunotiz · git-commit · 2026-08-22T16:34:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

directive: adopt owner-selected Qwen3.5-0.8B Together Full-FT lane

### claycode supervisor: quarantine merged Together 0.8B lane; bind current source-only repairs

`baunotiz-bauverlauf-ffb7216b369c13bf9e70` · baunotiz · bauverlauf.jsonl · 2026-08-22T15:38:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: quarantine merged Together 0.8B lane; bind current source-only repairs

`baunotiz-git-f9d6bcf613dc0874cb03536714a937b11c20be07` · baunotiz · git-commit · 2026-08-22T15:38:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: quarantine merged Together 0.8B lane; bind current source-only repairs

### evidence(go): re-enter native v2 parity and approx1B frontier

`baunotiz-bauverlauf-141a52e8eef8e90d9e37` · baunotiz · bauverlauf.jsonl · 2026-08-22T15:37:10+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence(go): re-enter native v2 parity and approx1B frontier

`baunotiz-git-a10b019bae18baa2612862ffff92e224ac37ca4a` · baunotiz · git-commit · 2026-08-22T15:37:10+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence(go): re-enter native v2 parity and approx1B frontier

### cognition: unify ClayCode syntax authority and top-level OOD semantics (#876)

`baunotiz-bauverlauf-7e38c1f851d5d2220663` · baunotiz · bauverlauf.jsonl · 2026-08-22T15:36:26+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Converge admission and evaluation on one depth-aware ClayCode syntax authority, repair stale comment-smuggling regression semantics, and require turn-body OOD calls. Bounded exact-core isolated evidence covers 16/16 focused tests and all 1,650 canonical SFT-v2 targets at exact corpus hashes. GitHub Actions remained execution-admission blocked before visible steps; no provider/model acceptance claim.

