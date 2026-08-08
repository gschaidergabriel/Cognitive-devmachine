# Retina Negative Results and Anti-Goodhart Ledger

**Status:** ACTIVE NEGATIVE-RESULT MEMORY  
**Purpose:** Preserve historical failures and measurement traps so the deep Retina branch cannot rediscover or optimize into them.

## NR-RET-001 — Phrase coverage is not compositional visual correctness

Historical Retina evaluation shows that a system can contain many words/phrases associated with an image while still getting object identity, attribute binding, relation binding or scene composition wrong.

Examples in the historical honest report include correct high-level subject hints with missing colour/detail relations, and components that recognize `rabbit` and `woman` without correctly representing the relation/binding between them.

**Constraint:** Final visual evaluation must contain structured compositional tasks, relation/binding checks and causal downstream tasks in addition to phrase coverage.

## NR-RET-002 — Low CLIP thresholds can create severe realistic-negative false positives

The historical working-paper calibration reports realistic-negative FPR of approximately 43.3% at CLIP threshold 0.20, versus 13.6% at 0.22 in its measured calibration set.

A later report advertises 94.6% CLIP-lenient coverage at 0.20. These two observations must be read together: high lenient coverage at a permissive threshold is not equivalent to high truth accuracy.

**Constraint:** No CLIP similarity threshold is promoted without frozen positive + realistic-negative calibration, uncertainty metrics and downstream error measurement.

## NR-RET-003 — Hard-set post-tuning result is not clean held-out generalization

The later 87.8% strict hard-set result was achieved after adding a large Tier-5 vocabulary containing `LAST_MILE` gap-closer phrases derived from per-image miss analysis and widening top-k/threshold behavior on the same development surface.

This is useful evidence that semantic information can be surfaced by vocabulary/projection changes, but it does not independently establish 87.8% generalization to unseen hard images.

**Constraint:** Freeze image set, annotations, vocabulary and evaluation before tuning; keep development and final held-out sets isolated by hashes.

## NR-RET-004 — Wrong detector boxes can amplify into semantic hallucinations

The May-26 audit records cases such as a Kandinsky image receiving a false YOLO `bed` detection followed by a region-caption attribution hallucination. A wrong upstream primitive created additional downstream narrative error.

**Constraint:** Every derived hypothesis must retain dependency provenance. If an upstream box/identity is invalidated, all dependent semantic claims become invalidated/quarantined automatically.

## NR-RET-005 — Fixed-class detection is structurally incomplete

Historical YOLO 80-class coverage missed long-tail categories such as specific artifacts, stylized objects and scene details; several art/AI hard-set images produced no useful detections.

**Constraint:** Closed-set YOLO remains a baseline, not the universal object ontology. Benchmark open-vocabulary/open-world alternatives and UNKNOWN semantics.

## NR-RET-006 — Art/AI distribution shift breaks ordinary-photo assumptions

Historical Retina exhibited false classes and missing detections on paintings, anime and generated composite scenes.

**Constraint:** Distribution/source class must be part of sensor evidence; evaluation must include photo, UI/screenshot, painting, illustration, generated image, low-light, blur and adversarial composite classes.

## NR-RET-007 — OCR on stylized/painted text is unreliable

Historical examples missed important text in paintings and stylized imagery even when text was semantically visible.

**Constraint:** OCR evidence carries uncertainty and source/layout provenance. `no OCR result` is not evidence of `no text` unless a calibrated negative detector supports it.

## NR-RET-008 — Region captioning is not monotonically beneficial

In the May-26 hard-set, region captioning fired only on a subset of images and sometimes added useful detail, sometimes no value and at least one actively harmful confabulation.

**Constraint:** Caption/VQA/expensive semantic generators must be conditional, dependency-aware and measured for marginal information gain rather than assumed beneficial.

## NR-RET-009 — Surface vocabulary expansion has diminishing returns and can hide architecture limits

Before the aggressive final gap-close, repeated vocabulary/heuristic additions produced small incremental strict-coverage gains while compositional failures persisted.

**Constraint:** Stop treating vocabulary growth as the default mechanism. Architecture changes must improve held-out binding, temporal, OOD or action-grounding metrics, not only lexical recall.

## NR-RET-010 — Current Retina is stateless by API design

The public `retina.core.analyze()` contract maps an isolated image to a dict. This makes horizontal scaling easy but discards temporal continuity unless an external caller reconstructs it.

**Constraint:** The current service is the stateless baseline. Persistent perception must be tested explicitly rather than inferred from the existence of many per-image stages.

## NR-RET-011 — Narrative aggregation destroys causal granularity

Current `frank_eye.py` contains many hand-coded sentences/heuristics that combine detector, CLIP, face, mood, OCR and spatial outputs into narrative text plus facts. This is readable but can obscure which upstream source caused a downstream belief.

**Constraint:** Canonical cognition uses typed evidence/hypothesis lineage; narrative is a projection.

## NR-RET-012 — Model confidence values are not automatically commensurate

YOLO confidence, CLIP cosine, OCR confidence, classifier probabilities and heuristic thresholds have different semantics and calibration.

**Constraint:** Never add/compare them as if they were one probability without an explicit calibration/fusion contract.

## NR-RET-013 — Temporal memory can create ghost objects

Synthetic mechanism sanity checks in the deep run show the expected trade-off: temporal persistence can rescue missed detections, but slow decay without explicit negative evidence creates long false persistence after objects disappear.

This is synthetic evidence only, not live Retina evidence.

**Constraint:** `OCCLUDED/OUT_OF_FOV` and `ABSENT_EXPLICIT_NEGATIVE` must be distinct and must drive different decay/update rules.

## NR-RET-014 — Strong priors can dominate weak sensor evidence

Synthetic prior-sweep checks show that as sensory signal is degraded, increasing a correlated prior can raise nominal accuracy while sharply increasing acceptance of deliberately wrong priors.

This is a mechanism sanity check, not proof of the correct FRANK gain law.

**Constraint:** Track prior dominance and require misleading-prior/no-signal controls before promoting recurrent gains.

## NR-RET-015 — Event-only state cannot safely recover all static semantics

External event-camera research and synthetic restart/anchor checks both support the limitation: change streams are efficient but may omit static/slow information and cannot reconstruct lost state without an anchor or other state source.

**Constraint:** event/change mode is hybridized with anchor evidence; event-only is a baseline, not the default target.

## NR-RET-016 — GoL visual dynamics have no privileged evidential status

Current Retina contains a Conway-Game-of-Life-based texture/dynamics feature stage. Cellular automata have precedent as texture descriptors, but no evidence currently establishes this specific GoL transform as a uniquely good or cortex-equivalent visual mechanism.

**Constraint:** GoL must survive held-out incremental-value ablation against cheaper texture/dense-feature baselines. Neuroscience analogy cannot promote it.

## NR-RET-017 — Broadcast is not use

A visual candidate reaching GWT does not establish that any receiver reconstructed it, used it causally, changed behavior or generated valid re-entry.

**Constraint:** reuse the project-wide GWT custody chain for every material visual episode.

## NR-RET-018 — Functional multimodality is not native visual-token multimodality

A text/Clay-token 4B reading structured perceptual state can be functionally multimodal at the system level without the underlying model being a native VLM.

**Constraint:** benchmark behavior and token efficiency, but do not describe the underlying model as literally vision-native unless its model architecture/training actually changes accordingly.

## Permanent anti-Goodhart rules

1. Never optimize a test after reading its final held-out misses.
2. Never report CLIP-lenient coverage without its realistic-negative FPR/calibration.
3. Never promote lexical presence as object-relation binding.
4. Never let a world prior become sensor evidence.
5. Never let an embedding score become canonical truth or authority.
6. Never call recurrence/GWT/persistence consciousness evidence by itself.
7. Never hide OOD/UNKNOWN by forcing known labels.
8. Never count repeated variants of one source/checkpoint as independent replication.
9. Never claim component modernization helps until measured on project hardware/workloads.
10. Preserve every failed perceptual mechanism as a future regression fixture.
