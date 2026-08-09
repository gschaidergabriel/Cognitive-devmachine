# FRANK Vision / FrankEye / Digital Retina / PerceptualField — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current owner-fixed target synthesis

## VR-0 — multiple visual lineages, not one renamed module

FRANK visual history contains at least two related but not automatically identical source families:
1. Project-Frankenstein visual/screenshot pipeline -> Adaptive Vision -> FrankEye;
2. Drive `digital-retina` historical implementation -> current owner-fixed Digital Retina / dissolved PerceptualField target.

Fusion preserves their provenance separately. Similar functionality is not counted as independent replication without ancestry evidence.

## PFV-1 — staged adaptive visual pipeline

Commit `90596662837a75801fd2024069ee9bd547137869` (2026-02-25):
- Stage 1: YOLO + OCR + scene heuristics, reported ~100 ms class;
- Stage 2: VLM only when needed;
- `frank_visual_pipeline.py`;
- `frank_adaptive_vision.py` escalation engine;
- `vcb_bridge.py` integration + legacy fallback;
- crosshair region screenshot selector.

This introduced a central current principle:
**cheap structured visual analysis first, expensive model interpretation only under uncertainty/need**.

It also coupled visual evidence to broader proprioceptive context, making source/context attribution important.

## PFV-2 — consolidation into FrankEye

Commit `0fd27f23e87cd1f0b53ce838347d1cdbcb7bd9bb` (2026-03-19):
- introduced unified `FrankEye` CPU vision module using DINOv2 INT8 ONNX;
- deleted/replaced older `frank_visual_pipeline.py`, `frank_adaptive_vision.py` and VCB bridge path.

Historical architecture later described FrankEye as a multi-component CPU pipeline rather than a full multimodal generative model.

Important lesson:
- deletion/renaming does not mean the old staged-escalation idea lost value;
- module consolidation can preserve mechanisms while changing process/file boundaries.

## PFV-3 — WebUI/image path

`4def0bb...` / `d07792a...` / `205456f...` added:
- image drag/drop and upload;
- screenshot auto-analysis;
- separate Describe vs Transcribe modes;
- OCR-only path via Tesseract;
- full FrankEye analysis + Frank language interpretation.

This cleanly demonstrates multiple visual causal stages:
`image bytes -> visual extraction/OCR -> structured/intermediate output -> LLM interpretation -> chat response`.

Current target keeps these stages typed so LLM interpretation cannot silently overwrite primary visual evidence.

## PFV-4 — screenshot-specialized correction

Commit `279eb175...`:
- app/browser-tab/screenshot-specific analysis;
- improved dark-theme OCR preprocessing with inversion/Otsu;
- recognition of FRANK's own WebUI;
- removed useless CIFAR-10 classification for screenshots;
- cleaned output of CIFAR/DINOv2 garbage.

Current lesson:
- generic classifiers can add noise to a domain-specific visual route;
- remove features that do not improve task-level utility rather than retaining them for architectural richness.

## PFV-5 — architecture/doc state drift

`c22e00c...` temporarily removed FrankEye from one “accurate” README architecture representation, while `fb0e7bb...` shortly after reintroduced a dedicated FrankEye section and senses node.

This is another source-freshness warning:
- documentation presence/absence cannot alone establish current runtime architecture;
- visual subsystem identity must come from executable/source/measurement lineage.

---

## DR-1 — historical Drive Digital Retina implementation

Level-0 Drive assimilation confirmed a substantial historical implementation, not just a concept.

Observed historical tree includes at least:
- `retina`;
- `api`;
- `frontend`;
- `eval`;
- `deploy`;
- `tests`;
- `tools`;
- `docs`;
- nested `retina/vision`.

Historical structured image-analysis API exposed fields including:
- description;
- concepts;
- detected objects;
- OCR text;
- faces;
- logos;
- image metadata;
- elapsed time.

`retina/vision/` includes a large `frank_eye.py` plus CLIP classification, OCR, region/scene/composition, Places365, colour and pattern modules.

This lineage may overlap conceptually/naming-wise with Project-Frankenstein FrankEye, but source ancestry is preserved rather than assumed identical.

## DR-2 — historical working-paper measurements

Owner contract records historical engineering-paper figures:
- 82.4% held-out phrase coverage;
- 47 unseen images / 1,196 phrases;
- ~1.5-2.0 s/image on 4-vCPU CPU-only hardware;
- 13.6% false-positive rate on realistic negatives at threshold 0.22.

The source described itself as non-peer-reviewed, n=1 engineering work with distribution/compositional-binding limitations.

Evidence class:
`HISTORICAL_MEASUREMENT_FOUNDATION`, **not** Clay 0.1 acceptance threshold.

## DR-3 — historical autonomous attention candidate

Digital Retina lineage proposed:
- event-triggered rather than purely periodic visual attention;
- bounded daily/cooldown budgets;
- habituation for repetitive visual/OCR state.

This converges with historical Thalamus and current event/change-driven sensing, but shared project ancestry means no independent-evidence bonus.

---

## DR-4 — current owner-fixed dissolved perception target

Current `FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md` makes visual perception mandatory but removes the requirement that Retina survive as an independent semantic process/module.

Target path:
```text
physical visual transducer
 -> in-module sensor ingress
 -> typed evidence/state deltas
 -> PerceptualField <-> world/memory/goals/self/context
 -> adaptive familiarity/readout
 -> thalamic/attention selection
 -> GWT when required
 -> memory/world/action
 -> re-entry
```

`VisualPercept` remains a mandatory audit/materialization contract when needed for replay, debugging, evidence, training/evaluation or causal traceability, but it is not a mandatory serialization chokepoint for every hot-path update.

## DR-5 — PerceptualField semantics

Current logical field preserves/references:
- source identity/class;
- capture/event time + epoch;
- local/spatial evidence;
- motion/change evidence;
- OCR/text;
- features/entities and unresolved hypotheses;
- spatial/relational bindings;
- confidence/uncertainty/precision;
- expected-vs-observed mismatch;
- active alternatives/conflicts;
- salience/attention;
- world/ClayGraph links;
- goal/action relevance;
- transformation/model lineage;
- prior perceptual/re-entry state;
- learned familiarity state where used.

Required epistemic states include `UNKNOWN`, `CONFLICT` and set-valued alternatives.

## DR-6 — recurrent perception

World model, memory, goals/action context and prior perceptual state may feed back into visual interpretation.

Hard distinction:
- bottom-up evidence;
- world/learned prior;
- current goal/context bias;
- learned familiarity/readout support.

Top-down state is never sensor truth.

Mandatory controls include:
- misleading priors;
- no-signal;
- unknown objects;
- degraded input;
- context swaps;
- stale/replayed evidence;
- feedback lesions/rescue.

This is the current successor to Project-Frankenstein's early recurrent perception and Thalamus predictive-error paths.

## DR-7 — adaptive familiarity learner

FRANK 0.1 owner directive requires tiny user-specific learning over reusable/frozen visual features.

Required behavior:
- recurring user/workspace content may gain persistent prototype/readout support;
- GOLD/SILVER/BRONZE provenance tiers;
- BRONZE self-predictions cannot directly become positive truth;
- output supports calibrated familiar / needs-confirmation / ambiguous / unknown / conflict;
- high-confidence familiar state may bypass expensive broad recognition;
- novel/contradictory/weak evidence escalates;
- cyclic updates are resource-bounded and rollbackable;
- learner/backbone/calibration versions are replayable.

This learns **routing/familiarity**, not canonical visual truth.

## DR-8 — current post-Level0 fusion correction: two gates

Recent whole-mesh research supports keeping two independently testable gates:

### RecognitionValidity
Can this learned state support a fast recognition route **now**?
Checks current:
- feature-backbone compatibility;
- calibration validity;
- source/context coherence;
- open-set/near-confuser evidence;
- contradictions/conflict.

### AdaptiveStatePromotion
May candidate learned state become durable/current?
Checks:
- evidence provenance/trust;
- candidate shadow result;
- poisoning/pseudo-label state;
- version lineage;
- rollback witness;
- atomic publication.

Synthetic prior fusion found a large difference between learning-admission-only and dual-gate behavior, but this remains a proxy until real frozen Retina replay.

## DR-9 — Perceptual Cache Coherence

Fast visual reuse is invalid if perception/calibration/model/source epochs are incoherent. A familiar object label cannot survive silently across incompatible backbone/calibration/context revisions.

Current rule:
`cached percept/familiarity identity = content + source + transform/backbone + calibration + context/basis epoch`, not only semantic class name.

## DR-10 — current GWT/Thalamus coupling

Visual evidence can update locally below GWT.

GWT candidacy increases for:
- unresolved prediction error;
- novelty/change;
- threat/risk;
- goal relevance;
- cross-state conflict;
- ambiguity needing global resources;
- action consequence;
- explicit task demand.

A calibrated familiar unchanged object may stay local.

Mandatory causal ladder:
`visual evidence present != local resolution != familiar fast path != selected != broadcast != reconstructed != uptake != downstream causal use != outcome != re-entry`.

## VR-1 — current fused target

Historical Project-Frankenstein staged escalation + FrankEye screenshot specialization + Drive Retina structured vision are all reused as testable implementation foundations.

Target architecture itself is:
- sensor/device ingress physical layer;
- typed Clay-native perceptual state;
- dissolved recurrent PerceptualField;
- exact provenance/model lineage;
- bounded event/change fast path + periodic anchor/full-frame rescue;
- tiny adaptive familiarity/readout;
- Thalamus/attention/GWT selective escalation;
- Unified Memory world/entity links;
- VisualPercept audit materialization on demand.

## Mandatory regressions

- VR-REG-01 generic classifier adds irrelevant/noisy label and degrades screenshot task;
- VR-REG-02 OCR/VLM interpretation overwrites primary pixel/source evidence role;
- VR-REG-03 visual module present in docs but unreachable at runtime;
- VR-REG-04 image/screenshot processed but result never enters world/GWT/action path;
- VR-REG-05 stale/replayed screenshot accepted as current;
- VR-REG-06 familiar prototype survives incompatible backbone/calibration version;
- VR-REG-07 misleading memory prior overrides contradictory sensor evidence;
- VR-REG-08 no-signal/open-set input forced into familiar class;
- VR-REG-09 BRONZE self-prediction recursively trains itself as truth;
- VR-REG-10 change-only path misses static important state; anchor-frame rescue required;
- VR-REG-11 out-of-process vs in-process lowering changes semantic/percept receipt;
- VR-REG-12 H1/H2/H3 visual state/receipt/GWT/action equivalence.

## Fusion decision

- PF Adaptive Vision/FrankEye: `REUSE_PIPELINE/SCREENSHOT/OCR_MECHANISMS_AS_IMPLEMENTATION_FOUNDATION; RETEST`.
- Drive Digital Retina: `MANDATORY_HISTORICAL_FOUNDATION; REUSE_SELECTED_MODULES_AFTER_DIFFERENTIAL_TESTS`.
- current Digital Retina/PerceptualField: `OWNER_FIXED_TARGET`.
- adaptive Micro Visual Classifier/familiarity: `OWNER_FIXED_EXISTENCE, ALGORITHM/PERFORMANCE_RESEARCH-GATED`.
