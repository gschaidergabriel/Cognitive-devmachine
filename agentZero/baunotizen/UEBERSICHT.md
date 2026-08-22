# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T13:36:44Z. **4459 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T20:06:35+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 4361 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2573 |
| baunotiz | bauverlauf.jsonl | 1740 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4459 · Gegenhypothese: 0 von 4459

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

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

### contract(reference): bind native profile authority convergence gate

`baunotiz-git-18db1397eb724ac7de10ce2d5b68b4f95a51b686` · baunotiz · git-commit · 2026-08-22T20:06:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

contract(reference): bind native profile authority convergence gate

Fail closed on a second active-profile authority and on local_exec subprocesses without an explicit child environment. Source contract only; no runtime PASS implied.

### contract(reference): bind single profile authority gate

`baunotiz-bauverlauf-6efd23ab024778f20576` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:05:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the deterministic native-profile-authority guard and joined macrocycle receipt onto fresh main. No runtime PASS; no additional unusual experiment.

### contract(reference): bind single profile authority gate

`baunotiz-git-9f825c9f5c09be484ea59fe87fba46e0a2f443c9` · baunotiz · git-commit · 2026-08-22T20:05:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

contract(reference): bind single profile authority gate

Fuse the deterministic native-profile-authority guard and joined macrocycle receipt onto fresh main. No runtime PASS; no additional unusual experiment.

### contract(native): bind donor extraction preservation matrix

`baunotiz-bauverlauf-0c04e66f1e60b5b1ff28` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:05:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the non-duplicate fresh-main donor-only preservation matrix on top of #957/#959 and reference responsibility semantics. Keep native v2 fail closed; no runtime PASS or provider execution claimed.

### contract(native): bind donor extraction preservation matrix

`baunotiz-git-7feca575be3a7ba7be1f9fb70a04a2117b0f2cc2` · baunotiz · git-commit · 2026-08-22T20:05:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

contract(native): bind donor extraction preservation matrix

Fuse the non-duplicate fresh-main donor-only preservation matrix on top of #957/#959 and reference responsibility semantics. Keep native v2 fail closed; no runtime PASS or provider execution claimed.

### Merge PR #964: bind staged cognition single authority path

`baunotiz-bauverlauf-3d6c6ddf31542ae2b5a1` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:04:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the staged-cognition donor contract into one canonical acceptance path, add executable source-coherence/ClayCog role-neutrality guards, and preserve FREE_ONLY plus runtime-evidence boundaries. Source contract only; no staged runtime PASS.

### Merge PR #964: bind staged cognition single authority path

`baunotiz-git-9cb37a3c1e9e9423531375811f47919d253398f2` · baunotiz · git-commit · 2026-08-22T20:04:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #964: bind staged cognition single authority path

Fuse the staged-cognition donor contract into one canonical acceptance path, add executable source-coherence/ClayCog role-neutrality guards, and preserve FREE_ONLY plus runtime-evidence boundaries. Source contract only; no staged runtime PASS.

### cognition: enforce campaign-neutral reusable SFT v2

`baunotiz-bauverlauf-578bf455d5f8c90ac57a` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:04:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the narrow campaign-literal corpus gate on current semantic-slot validation. Reuse donor regressions only; exact GitHub runner had steps=null, so no test PASS or training claim.

### cognition: enforce campaign-neutral reusable SFT v2

`baunotiz-git-2971facc836ce99bdf6918c51e15c67df7c4cf36` · baunotiz · git-commit · 2026-08-22T20:04:07+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

cognition: enforce campaign-neutral reusable SFT v2

Fuse the narrow campaign-literal corpus gate on current semantic-slot validation. Reuse donor regressions only; exact GitHub runner had steps=null, so no test PASS or training claim.

### evidence: bind staged contract fusion and zero-step admission

`baunotiz-bauverlauf-471885f1f4a59e1380df` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:03:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: bind staged contract fusion and zero-step admission

`baunotiz-git-5cd0848829b5d4e2c47a14a937cf93d310adbef1` · baunotiz · git-commit · 2026-08-22T20:03:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: bind staged contract fusion and zero-step admission

### fusion: remove duplicate staged contract path

`baunotiz-bauverlauf-ad24b20ea12168341098` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:02:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### fusion: remove duplicate staged contract path

`baunotiz-git-ad57d750c54403e7c8254239faab1ba2a8b27235` · baunotiz · git-commit · 2026-08-22T20:02:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fusion: remove duplicate staged contract path

### ci: point staged gate at fused acceptance contract

`baunotiz-bauverlauf-703a1c1a4aea95da91bb` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:02:26+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### ci: point staged gate at fused acceptance contract

`baunotiz-git-ab9f10531f98f87c5c0ff078dfe46fa7133b4a14` · baunotiz · git-commit · 2026-08-22T20:02:26+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ci: point staged gate at fused acceptance contract

### evidence: bind exact zero-step run and reference donor blockers

`baunotiz-bauverlauf-ec3aa0e0d685559b2894` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:02:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: bind exact zero-step run and reference donor blockers

`baunotiz-git-0111dd0ee1de9156e8e907f52968e28eb6905c7f` · baunotiz · git-commit · 2026-08-22T20:02:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: bind exact zero-step run and reference donor blockers

### test: point staged guard at fused authority contract

`baunotiz-bauverlauf-ee9ea91eb0ea3ef0ae57` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:02:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test: point staged guard at fused authority contract

`baunotiz-git-cf68a832154d442fdb47f07699807d0ab5e48b9d` · baunotiz · git-commit · 2026-08-22T20:02:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test: point staged guard at fused authority contract

### fusion: adopt staged cognition authority contract

`baunotiz-bauverlauf-180c7812bea0a0653673` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:01:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### fusion: adopt staged cognition authority contract

`baunotiz-git-a607a7e15bfdba1b1f08b821a4f1e048a971b11b` · baunotiz · git-commit · 2026-08-22T20:01:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fusion: adopt staged cognition authority contract

### contract(native): require reference effect semantics, not names

`baunotiz-bauverlauf-d13204898e5a9676ab79` · baunotiz · bauverlauf.jsonl · 2026-08-22T20:01:04+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Fuse the responsibility-level parity guard on top of the AST executable-binding guard. Keep native profile-v2 fail closed; no runtime PASS implied.

