# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T08:06:43Z. **4097 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T14:34:29+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3999 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2391 |
| baunotiz | bauverlauf.jsonl | 1560 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4097 · Gegenhypothese: 0 von 4097

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### cognition: add eval-only compositional OOD lesion (#814)

`baunotiz-bauverlauf-a4032a3fddd7448d7eef` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:34:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Preserve canonical leakage-free SFT v2 and exact-omega OOD scoring while adding an evaluation-only 320-case compositional operation-vocabulary lesion, paid-create safety CI coverage, and a bounded go receipt. No Together/model/runtime acceptance claim.

### cognition: add eval-only compositional OOD lesion (#814)

`baunotiz-git-292edfd547d49cb512de7a4bed2c290c71e05674` · baunotiz · git-commit · 2026-08-22T14:34:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: add eval-only compositional OOD lesion (#814)

Preserve canonical leakage-free SFT v2 and exact-omega OOD scoring while adding an evaluation-only 320-case compositional operation-vocabulary lesion, paid-create safety CI coverage, and a bounded go receipt. No Together/model/runtime acceptance claim.

### fix(cognition): fuse exact HF revision with Together catalog fence (#818)

`baunotiz-bauverlauf-2d27d542b4403149fa08` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:33:27+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Preserve SFT-v2, exact HF revision binding, fingerprint/ledger ambiguity handling and zero-retry billed create while removing the invalid guessed Together template path. Require an explicit architecture-compatible full-FT base and use the current Together SDK-v2 limit/file/price contract. Bounded no-network regressions: 17/17 pass; no provider call or billed training.

### fix(cognition): fuse exact HF revision with Together catalog fence (#818)

`baunotiz-git-734f234eaf65f2d8cbfb8453e8db8c7176264afb` · baunotiz · git-commit · 2026-08-22T14:33:27+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fix(cognition): fuse exact HF revision with Together catalog fence (#818)

Preserve SFT-v2, exact HF revision binding, fingerprint/ledger ambiguity handling and zero-retry billed create while removing the invalid guessed Together template path. Require an explicit architecture-compatible full-FT base and use the current Together SDK-v2 limit/file/price contract. Bounded no-network regressions: 17/17 pass; no provider call or billed training.

### state: bind exact omega gate and remaining 0.5B paid-launch blockers (#815)

`baunotiz-bauverlauf-d81b4114d4d34578177c` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:32:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

* state: bind exact omega gate and remaining paid-launch blockers

* evidence: record extra-long cognition convergence cycle

### state: bind exact omega gate and remaining 0.5B paid-launch blockers (#815)

`baunotiz-git-4b052109729329e5b81040b406cf7c07d4c38f93` · baunotiz · git-commit · 2026-08-22T14:32:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

state: bind exact omega gate and remaining 0.5B paid-launch blockers (#815)

* state: bind exact omega gate and remaining paid-launch blockers

* evidence: record extra-long cognition convergence cycle

### ci(cognition): admit exact omega OOD regression (#812)

`baunotiz-bauverlauf-fd20a1928f7e79054eda` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:31:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Wire the canonical #802 exact-omega attack/oracle/ID regression into the existing ClayCog PR admission workflow while preserving v1/v2 validator and corpus gates. Also bind corpus_manifest_v2 reproducibility. GitHub-hosted jobs still fail before any step executes, so this merge claims source/test-coverage improvement only, not Actions runtime PASS.

### ci(cognition): admit exact omega OOD regression (#812)

`baunotiz-git-fc9f4ec86c137491ffc244596e49a9701ef0bdc0` · baunotiz · git-commit · 2026-08-22T14:31:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ci(cognition): admit exact omega OOD regression (#812)

Wire the canonical #802 exact-omega attack/oracle/ID regression into the existing ClayCog PR admission workflow while preserving v1/v2 validator and corpus gates. Also bind corpus_manifest_v2 reproducibility. GitHub-hosted jobs still fail before any step executes, so this merge claims source/test-coverage improvement only, not Actions runtime PASS.

### state(program): bind current native falsifiers + BYOM contract

`baunotiz-bauverlauf-9695cb0caa704950509a` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:30:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### state(program): bind current native falsifiers + BYOM contract

`baunotiz-git-717b772035c51c916d15b75aa0d859cd566a2c3e` · baunotiz · git-commit · 2026-08-22T14:30:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

state(program): bind current native falsifiers + BYOM contract

### cognition: bind SFT v2 paid campaign to exact HF revision (#800)

`baunotiz-bauverlauf-bfb77b2f04cd44b4787f` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:29:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse exact Qwen2.5 source revision into the canonical SFT-v2 fingerprint, local CREATE intent ledger, Together create request and safety regressions while preserving #780 ambiguity handling. Together runtime admission remains open.

### cognition: bind SFT v2 paid campaign to exact HF revision (#800)

`baunotiz-git-cc8449642a76ff74467e02da78ecd38853d6dd76` · baunotiz · git-commit · 2026-08-22T14:29:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: bind SFT v2 paid campaign to exact HF revision (#800)

Fuse exact Qwen2.5 source revision into the canonical SFT-v2 fingerprint, local CREATE intent ledger, Together create request and safety regressions while preserving #780 ambiguity handling. Together runtime admission remains open.

### state: sync canonical cognition state to corpus v2

`baunotiz-bauverlauf-1a1e87fc5c2d76e85ac8` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:29:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Align BOOTSTRAP_MINIMAL and PROGRAM_STATE with merged leakage-free SFT v2, exact hashes/uniqueness evidence, current BYOM architecture gate, and existing fail-closed create safety. No runtime implementation change.

### state: sync canonical cognition state to corpus v2

`baunotiz-git-57cbf37c2939813644b0e2c0993db568e62387a5` · baunotiz · git-commit · 2026-08-22T14:29:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

state: sync canonical cognition state to corpus v2

Align BOOTSTRAP_MINIMAL and PROGRAM_STATE with merged leakage-free SFT v2, exact hashes/uniqueness evidence, current BYOM architecture gate, and existing fail-closed create safety. No runtime implementation change.

### test(cognition): bind PR admission to canonical corpus v2 (#797)

`baunotiz-bauverlauf-5863b3681692e339c190` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:29:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Extend the existing exact-checkout ClayCog admission entry point so it regenerates and validates canonical SFT v2, including exact bound digests and zero train/validation prompt/message leakage. Preserve the existing runtime-binding adversarial tests. GitHub runner admission still fails before visible steps, so this is a source/test-coverage improvement only; no runtime PASS is claimed.

### test(cognition): bind PR admission to canonical corpus v2 (#797)

`baunotiz-git-6512e0d8a6cead21022711f87898b7400b7e50d6` · baunotiz · git-commit · 2026-08-22T14:29:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(cognition): bind PR admission to canonical corpus v2 (#797)

Extend the existing exact-checkout ClayCog admission entry point so it regenerates and validates canonical SFT v2, including exact bound digests and zero train/validation prompt/message leakage. Preserve the existing runtime-binding adversarial tests. GitHub runner admission still fails before visible steps, so this is a source/test-coverage improvement only; no runtime PASS is claimed.

### docs(artefact): align root workspace with Mini Entity + 0.5B target

`baunotiz-bauverlauf-59237fb932a8a1a2ced0` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:29:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### docs(artefact): align root workspace with Mini Entity + 0.5B target

`baunotiz-git-d1f1947ee8d6570fa7fd702b9e51e22ef1e8924e` · baunotiz · git-commit · 2026-08-22T14:29:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

docs(artefact): align root workspace with Mini Entity + 0.5B target

### cognition: close exact-omega OOD promotion bypass (#802)

`baunotiz-bauverlauf-03c30d61120361027026` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:27:57+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Bind valid OOD omega cases to exact typed action vectors, reject duplicate/unknown evaluation IDs, and preserve the empirically falsified Goodhart attack as a regression. Exact isolated regression passes; GitHub PR runner failed before any visible step, so no runner code-failure claim is made.

### cognition: close exact-omega OOD promotion bypass (#802)

`baunotiz-git-afbca677205ad54e5080afe0443e3092773615e2` · baunotiz · git-commit · 2026-08-22T14:27:57+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: close exact-omega OOD promotion bypass (#802)

Bind valid OOD omega cases to exact typed action vectors, reject duplicate/unknown evaluation IDs, and preserve the empirically falsified Goodhart attack as a regression. Exact isolated regression passes; GitHub PR runner failed before any visible step, so no runner code-failure claim is made.

### evidence(cognition): correct Together BYOM template contract

`baunotiz-bauverlauf-d649da7392dd036f00c1` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:26:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence(cognition): correct Together BYOM template contract

`baunotiz-git-6a0eb97661133cc688ba321b2e4d23003c5eada7` · baunotiz · git-commit · 2026-08-22T14:26:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence(cognition): correct Together BYOM template contract

### cognition: fuse SFT v2 with canonical runtime-binding validator (#796)

`baunotiz-bauverlauf-8cda06dd5e314cc13345` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:26:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Converge leakage-free ClayCog SFT v2 onto the single canonical ClayCode/runtime-binding validator and preserve exact uniqueness/cross-split leakage checks. Includes focused isolated v2 regression evidence; no Together training claim.

### cognition: fuse SFT v2 with canonical runtime-binding validator (#796)

`baunotiz-git-3edb31e824404eb7c42f8cb721af27cc83c98794` · baunotiz · git-commit · 2026-08-22T14:26:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: fuse SFT v2 with canonical runtime-binding validator (#796)

Converge leakage-free ClayCog SFT v2 onto the single canonical ClayCode/runtime-binding validator and preserve exact uniqueness/cross-split leakage checks. Includes focused isolated v2 regression evidence; no Together training claim.

### evidence(native): add source-bound 0.7 wrapper execution

`baunotiz-bauverlauf-030cf0b11417f4a9e39e` · baunotiz · bauverlauf.jsonl · 2026-08-22T14:22:50+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

