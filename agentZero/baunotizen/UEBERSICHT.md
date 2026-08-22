# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T12:36:44Z. **4375 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T19:03:29+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 4277 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2531 |
| baunotiz | bauverlauf.jsonl | 1698 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4375 · Gegenhypothese: 0 von 4375

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### Merge PR #946: bind FREE_ONLY fallback cost classes to canonical source

`baunotiz-bauverlauf-206fb932504fb8c792ba` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:03:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Architecture/source-authority delta only. Preserve UNKNOWN fail-closed semantics, reuse legacy PR #232 only as a bounded evidence-schema donor, and do not hand-label derived bahnen.json without repository-bound canonical provider source. No runtime/provider PASS implied.

### Merge PR #946: bind FREE_ONLY fallback cost classes to canonical source

`baunotiz-git-ed0d28a22cffbf80e72f697acb77586d060f579b` · baunotiz · git-commit · 2026-08-22T19:03:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #946: bind FREE_ONLY fallback cost classes to canonical source

Architecture/source-authority delta only. Preserve UNKNOWN fail-closed semantics, reuse legacy PR #232 only as a bounded evidence-schema donor, and do not hand-label derived bahnen.json without repository-bound canonical provider source. No runtime/provider PASS implied.

### evidence: record historical zero-cost policy donor

`baunotiz-bauverlauf-3c54d513e2ad2963eec7` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:02:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: record historical zero-cost policy donor

`baunotiz-git-c79924ddd970624f114d7c6a855e7364b31c11cd` · baunotiz · git-commit · 2026-08-22T19:02:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: record historical zero-cost policy donor

### architecture: fuse historical zero-cost policy donor into fallback contract

`baunotiz-bauverlauf-8048fef2d802ac7fa25c` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:02:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### architecture: fuse historical zero-cost policy donor into fallback contract

`baunotiz-git-710183c3024e094781e1f917b9de387b19520c5b` · baunotiz · git-commit · 2026-08-22T19:02:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

architecture: fuse historical zero-cost policy donor into fallback contract

### research: bind Gen276 FREE_ONLY fallback source bypass

`baunotiz-bauverlauf-13c02efb9411f430c454` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:01:49+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Bind exact Gen276 source-mechanism evidence and the canonical FREE_ONLY fallback admission/falsification contract. Research/evidence only; no exported product code or provider execution.

### research: bind Gen276 FREE_ONLY fallback source bypass

`baunotiz-git-4db0ca016943a57d9629e052899f027b181a20d7` · baunotiz · git-commit · 2026-08-22T19:01:49+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen276 FREE_ONLY fallback source bypass

Bind exact Gen276 source-mechanism evidence and the canonical FREE_ONLY fallback admission/falsification contract. Research/evidence only; no exported product code or provider execution.

### research: prove Gen276 FREE_ONLY fallback pre-secret source gap

`baunotiz-bauverlauf-9b502fe11a596ed221b4` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:00:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: prove Gen276 FREE_ONLY fallback pre-secret source gap

`baunotiz-git-41f9936a448c173f6c862eb09e359dabccec48b1` · baunotiz · git-commit · 2026-08-22T19:00:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: prove Gen276 FREE_ONLY fallback pre-secret source gap

### evidence: bind fallback cost-class source-authority blocker

`baunotiz-bauverlauf-ffb81be91062663539b8` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:00:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: bind fallback cost-class source-authority blocker

`baunotiz-git-a89116e23239d1650993f069fb3cc9009b117b97` · baunotiz · git-commit · 2026-08-22T19:00:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: bind fallback cost-class source-authority blocker

### architecture: bind fallback cost classes to canonical source

`baunotiz-bauverlauf-0489ba095083cf428ec5` · baunotiz · bauverlauf.jsonl · 2026-08-22T19:00:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### architecture: bind fallback cost classes to canonical source

`baunotiz-git-8f95ccedac5094896f65dd673f8ddb3104eeb873` · baunotiz · git-commit · 2026-08-22T19:00:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

architecture: bind fallback cost classes to canonical source

### fix(cognition): bind 0.8B SDK contract into create identity

`baunotiz-bauverlauf-ca8883343e8c8346fe90` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:58:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Source-contract fusion only. Binds the canonical SDK-v2 Full-FT CREATE transport into campaign/confirmation v3 and fails closed on installed create-signature drift before uploads. Preserves FREE_ONLY authority and all current seed/job-identity fences. Exact PR Actions failed before visible step execution (steps=null), so no runtime PASS or code-failure credit is claimed.

### fix(cognition): bind 0.8B SDK contract into create identity

`baunotiz-git-dc96c985ceccf44d93de09246181e866dfc687ed` · baunotiz · git-commit · 2026-08-22T18:58:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fix(cognition): bind 0.8B SDK contract into create identity

Source-contract fusion only. Binds the canonical SDK-v2 Full-FT CREATE transport into campaign/confirmation v3 and fails closed on installed create-signature drift before uploads. Preserves FREE_ONLY authority and all current seed/job-identity fences. Exact PR Actions failed before visible step execution (steps=null), so no runtime PASS or code-failure credit is claimed.

### evidence: record #939 surface-invariance merge and zero-step CI

`baunotiz-bauverlauf-c27c63df89d46ea444bc` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:58:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: record #939 surface-invariance merge and zero-step CI

`baunotiz-git-44873d6c3c315ca803dfe4205ae3fd3a13ec968f` · baunotiz · git-commit · 2026-08-22T18:58:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: record #939 surface-invariance merge and zero-step CI

### test(cognition): bind SDK fence into v3 confirmation identity

`baunotiz-bauverlauf-58fc2bb7ebe5460cd4d4` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:57:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(cognition): bind SDK fence into v3 confirmation identity

`baunotiz-git-0b8a5257ea513cc1284b7c9597218b6bc1f523f6` · baunotiz · git-commit · 2026-08-22T18:57:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(cognition): bind SDK fence into v3 confirmation identity

### fix(cognition): fence SDK shape and stale create confirmation

`baunotiz-bauverlauf-8493f68e011171ada2a2` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:57:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### fix(cognition): fence SDK shape and stale create confirmation

`baunotiz-git-78910d9e9a80343991a2eae0a8a753895732dfa1` · baunotiz · git-commit · 2026-08-22T18:57:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fix(cognition): fence SDK shape and stale create confirmation

### Merge PR #939: gate exact-vector OOD against slot-copy shortcuts

`baunotiz-bauverlauf-cee7cc7ec9122f25f4f7` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:57:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Evaluation-only promotion hardening. Preserve existing 320 compositional OOD cases, add 80 surface-invariant exact-vector cases and a literal slot-copy negative baseline. Source-exact GitHub Actions remained execution-admission blocked before steps; merge is source/mechanism fusion only, not runtime or model-quality PASS.

### Merge PR #939: gate exact-vector OOD against slot-copy shortcuts

`baunotiz-git-ddefaa3671c61c26ab2bd701a648d8ac576cf25a` · baunotiz · git-commit · 2026-08-22T18:57:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Merge PR #939: gate exact-vector OOD against slot-copy shortcuts

Evaluation-only promotion hardening. Preserve existing 320 compositional OOD cases, add 80 surface-invariant exact-vector cases and a literal slot-copy negative baseline. Source-exact GitHub Actions remained execution-admission blocked before steps; merge is source/mechanism fusion only, not runtime or model-quality PASS.

### state: credit exact SFT-v2 regeneration and advance native frontier

`baunotiz-bauverlauf-978ca742f083ca3d030d` · baunotiz · bauverlauf.jsonl · 2026-08-22T18:56:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

