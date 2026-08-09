# 666 Level-0 Run Report — PF ↔ Recovery Cross-Source Reconciliation

## Run identity
- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- program stage: `L0_ARCHIVE_ASSIMILATION`
- release gate: `NOT_PASS`
- worker: `chatgpt-secondary-20260809T1206p0700-666-pf-recovery-reconcile`
- task: `666-l0-pf-recovery-crosssource-20260809T1206p0700`

## Routing / peer pulse
At run start, a live center pulse showed an active Titan-memory pip/vendor audit. During the run, additional non-overlapping peers appeared for PF `ce007` semantic lineage and a new Drive-root Level-0 task. This worker therefore remained on the bounded cross-source recovery-lineage lane and did not duplicate those tasks.

## Inputs cross-read
- `research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_MANIFEST.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1058p0700_drive_frank_rettung_recovery_semantic_closure.json`
- `research_entity/archive_assimilation/manifests/DRIVE_FRANK_RETTUNG_20260731_EXACT_DEDUP_20260809T0931p0700.json`
- Project-Frankenstein frozen head `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Project-Frankenstein older recovery base `2ee91c4479eec549de3bec357af69799fad583ad`
- frozen-head files `services/paper_research.py` and `services/genesis/sandbox.py`
- frozen-head absence check for `services/identity_forge.py`

## Verified lineage results
1. **The two Drive rescue roots collapse to one content family.** `frank-rettung-2026-07-31` was previously proven byte-identical to `frank-rettung` across all 10 leaf files. This run carries that proof into PF cross-source reconciliation: preserve both provenance aliases, but never count the second copy as independent semantic evidence or earned work.
2. **`paper_research.py` is an exact PF-head duplicate.** The frozen-head Git blob is `c1b6156d2a2122b33101faa24af0c759669216e7`, matching the recovery receipt. Disposition remains `EXACT_DUPLICATE_OF_FROZEN_PF_HEAD` with zero new semantic credit.
3. **`identity_forge.py` is recovery-only relative to the frozen head.** A direct frozen-ref fetch of `services/identity_forge.py` returned no file. This supports preservation as a separate recovery lineage node, but does **not** prove the file never existed in unresolved Project-Frankenstein history.
4. **The recovered Genesis sandbox is a superseded precursor, not a restore candidate.** Frozen-head `services/genesis/sandbox.py` resolves to Git blob `9e158072caf6f05362709db7a05e7cdf7a9e8162`, different from the recovery precursor. The historical negative result—timeout/resource-limited subprocess execution is not a complete security isolation boundary—remains useful; the precursor itself must not overwrite current code.
5. **The provenance anchors resolve.** `2ee91c4479eec549de3bec357af69799fad583ad` is a real Project-Frankenstein commit from 2026-03-12; frozen head `abba90a...` is from 2026-04-05. Therefore May-11 uncommitted recovery edits can be chronologically newer while still inheriting an older repository base. File recency alone is not a supersession rule.

## Reconciliation classes
- exact Drive alias: `frank-rettung-2026-07-31` ↔ `frank-rettung`
- exact PF-head duplicates: `paper_research.py`, `self_engineering.py`
- recovery-only relative to frozen head: `identity_forge.py`
- historical precursor superseded at frozen head: `genesis/sandbox.py`
- broken negative fixture: `snake_feel.py`
- divergent May-11 variants requiring feature-level differential/replay: `toolboxd.py`, `consciousness_daemon.py`, `e_pq.py`, `agentic/tools.py`

## Scientific / architecture delta
This run produces a **lineage and provenance delta**, not a new scientific mechanism claim. The previously routed IdentityForge, sandbox and visual-regression findings remain available to `frank`, `gwt`, `harness`, `unifieddb` and `claycode`; this run strengthens their ancestry/dedup semantics and prevents duplicate evidence or earned-work weighting.

## Negative results / guards
- full Project-Frankenstein frozen-head tree denominator: still unresolved in the current manifest;
- full Project-Frankenstein commit-DAG/history denominator: still unresolved;
- therefore `identity_forge.py` is only proven absent at the frozen head path, not from all history;
- no global exact Level-0 percentage is added by this bounded reconciliation while the combined denominator remains open;
- no paid training was initiated.

## Durable outputs
- `research_entity/archive_assimilation/receipts/666_20260809T1208p0700_chatgpt_secondary_pf_recovery_crosssource_reconciliation.json`
- `research_entity/rooms/center_events/20260809T1208p0700_666_pf_recovery_crosssource_delta.json`
- this run report

## Remaining highest-value obligations
1. finish exact Project-Frankenstein frozen-head tree denominator;
2. obtain/validate an exact Project-Frankenstein commit-DAG/history denominator;
3. consume the active PF-ce007 semantic-lineage result without overlap;
4. consume the active new-Drive-root epoch result and update global rest obligations;
5. continue remaining Drive exact disposition/content/hash lanes, including the currently active Titan vendor audit;
6. once both source universes are exact, finish cross-source reconciliation, historical earned-work row deduplication, branch feedback and release audit.

## Completion judgment
This bounded lane is complete and non-overlapping. `666_RELEASE_GATE` remains `NOT_PASS`; no post-Level-0 stochastic field spawning is authorized yet.
