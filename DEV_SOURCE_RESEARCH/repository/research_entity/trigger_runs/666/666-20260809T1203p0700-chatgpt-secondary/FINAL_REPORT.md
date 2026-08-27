# 666 Level-0 Run — Historical Retina Adaptive-Learning Lineage

- **Run:** `666-20260809T1203p0700-chatgpt-secondary`
- **Actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- **Canonical parent:** r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **Stage:** `L0_ARCHIVE_ASSIMILATION`
- **Gate:** `666_RELEASE_GATE = NOT_PASS`
- **Exact coverage credit:** `0.0%`

## Why this shard

The current Level-0 denominator is still unfrozen, so the highest-value work is not another broad architecture hypothesis but source accounting plus non-overlapping historical assimilation. The Drive root currently exposes newer/separate source trees including `needle`, `digital-retina`, `digital-retina-e2e`, `titan-memory`, recovery trees, `xeno`, `synteq-umbau`, `frank-projects`, `aicore`, `frank-werkzeuge`, `frank-demo`, `frank-library`, and the 663,552,000-byte archive. The existing frozen semantic concept index therefore cannot be treated as the complete Drive denominator.

This run selected the historical `digital-retina` learning/pattern/dictionary/familiarity lane because the current FRANK v0.1 adaptive visual learning directive explicitly requires Level 0 to recover that lineage.

## Core recovered mechanism

Historical Retina already implemented an ancestor of the modern Micro Visual Classifier concept:

`image -> shallow/frozen visual features -> GoL dynamical signature -> learned centroid dictionary -> cosine nearest-centroid readout -> phrases/familiarity-like output`

The learned library was not merely conceptual. Historical code builds multi-channel 50-D signatures over real images, L2-normalizes them, fits deterministic K-means (`k=32`), traces cluster membership back to source images and associates cluster centers with cached external-oracle phrases. Runtime then performs nearest-center cosine matching above a high similarity gate.

A separate offline iteration loop reused cached oracle labels, measured current Retina coverage, ranked misses and re-evaluated changes without re-querying the teacher. This provides an ancestral cycle:

`teacher reference -> frozen replay -> misses -> representation/vocabulary/threshold update -> re-evaluate`

The historical implementation is nevertheless **not** the current required learner: it was predominantly global/offline, lacked per-user evidence tiers, candidate-vs-current atomic promotion, rollback/version migration and a sufficiently strong open-set contract.

## Measurements and negative results preserved

Historical reports contain useful contradictions and anti-Goodhart evidence that must remain alive:

- An early honest hard-set evaluation reported **35.3%** strict phrase coverage on 12 adversarial images and **47.5%** on 10 easy images, explicitly rejecting an unsupported earlier `55->95%` memory claim.
- A later dictionary experiment reported **82.4% aggregate held-out phrase coverage** across 47 images / 1,196 phrases, with the learned dictionary moving one fixed-set architecture progression from **78.9% to 87.5% (+8.6pp)**.
- Realistic negative controls showed severe threshold sensitivity: a CLIP similarity threshold of **0.20** was reported with roughly **43.3% realistic FPR**, while **0.22** reduced realistic FPR to about **13.6%** at lower recall.
- Later hard-set reporting reached **94.6% CLIP-lenient** at 0.20 and **87.8% strict-substring after broad phrase emission**, but the same sweep yielded only **66.3% at 0.22**. These figures measure different things and must not be collapsed into one accuracy claim.
- Documented failure modes include YOLO class-boundary misses, YOLO hallucinations on art/AI propagating into region-caption confabulation, painted-text OCR failures, weak fine compositional binding and metric inflation through broad vocabulary surfacing.

## Current FRANK/Clay implication

The safe inheritance path is:

1. retain a cheap prototype/nearest-centroid `MVC-0` baseline;
2. reuse frozen CLIP/DINO-class features before inventing a heavier learner;
3. preserve deterministic, versioned prototype state and frozen replay;
4. calibrate unknown/familiar gates on realistic near-neighbor and OOD negatives;
5. preserve `familiarity != sensor truth` and `confidence != authority`;
6. admit only provenance-qualified examples to autonomous updates;
7. retain candidate/current shadow evaluation and rollback;
8. benchmark whether historical GoL-signature centroids add anything beyond modern reusable features rather than assuming they do.

Recommended H1 discriminating experiment: compare a CLIP/DINO centroid baseline to the historical GoL-signature centroid family on recurring user-specific classes plus realistic unknown/near-neighbor negatives. Preregister known-class accuracy, open-set AUROC/FPR at target recall, calibration, sequential retention, poisoning resistance, CPU/RAM/update overhead and real routing savings.

## Earned-work interpretation

This run records historical Retina as **REUSABLE_WITH_ADAPTATION**, **MEASUREMENT_FOUNDATION**, and **NEGATIVE_RESULT_VALUE** for the adaptive visual learner. It does **not** assign avoided/reused hours yet because the final row-level Level-0 earned-work map still needs duplicate and lineage reconciliation.

## Branch feedback

See `BRANCH_FEEDBACK_MANIFEST.json`. Material deltas were routed to `frank`, `harness`, `claycode`, `claygraph`, `unifieddb`, `emergenz`, `clay`, and `q12_index`; `gwt` and `hyperposition` receive explicit `NO_CHANGE` for this shard.

## Remaining Level-0 obligations

The release gate remains open. Required next work includes recursive Drive denominator freeze, `digital-retina` ↔ `digital-retina-e2e`/recovery lineage reconciliation, disposition of stored Retina evaluation artifacts, complete Project-Frankenstein history/tree accounting, cross-source reconciliation and row-level earned-work deduplication.

No canonical scientific claim was promoted by this run. Historical measurements remain historical evidence and current implementation hypotheses remain falsifiable.
