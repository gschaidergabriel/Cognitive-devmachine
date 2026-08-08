# Retina Deep Foundry Run — From Stateless Vision API to Persistent Clay-Native Perception

**Run ID:** `retina-20260809T0615p0700-deep-foundry`  
**Actor:** `chatgpt-secondary`  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Date:** 2026-08-09  
**Program stage:** `L0_ARCHIVE_ASSIMILATION`  
**Depth target:** Clay-foundry depth plus Retina-specific archaeology, current literature, executable mechanism sanity checks, 66 first-generation hypotheses, 20 counterhypotheses, Fusion 2 and 24 transformed second-generation hypotheses.  
**Canonical promotion:** none; research artifacts committed, canonical RAE revision unchanged.

---

## 1. Executive synthesis

The run changes the conceptual center of Digital Retina.

The historical system asks approximately:

`What is in this image, and how do I summarize it for an LLM?`

The new research target asks:

`What visual evidence changed; what hypotheses does it support or contradict; what world state should remain stable or reopen; what uncertainty matters globally; and what additional sensing is worth paying for?`

That is a different architecture class.

The strongest candidate is **not** a larger collection of image models and not a disguised VLM. It is a persistent, partially observed, recurrent state-estimation system whose visual evidence is dissolved into FRANK's Clay-native cognitive state while preserving strict provenance and epistemic separation.

The key architecture is:

`physical sensor`
`-> timestamped Evidence Plane`
`-> sparse temporal/perceptual hypotheses`
`<-> bounded world/memory/context recurrence`
`-> persistent World Plane`
`-> local resolution OR GWT projection`
`-> active sensing/action when uncertainty matters`
`-> outcome + visual re-entry`

A full `VisualPercept` remains available as an audit/replay materialization but is no longer the mandatory hot-path carrier.

The deeper insight from Fusion 2 is that Retina should become a **visual information-allocation system**. Uncertainty, conflict, novelty, task value, risk and expected information gain decide which visual computation happens next. The expensive visual stack stops being a fixed sequence that runs on every frame.

---

## 2. What the historical Retina actually is

Direct source inspection of `gschaidergabriel/digital-retina` confirms a real, sizable CPU-oriented implementation.

### Current public contract

`retina/core.py` describes the API as stateless:

`bytes/path/URL -> structured dict`

The output contains description, concepts, objects, OCR, faces, logos, image metadata and timing. Models are lazy-loaded/singleton-cached. Current comments and README describe different latency regimes, including a roughly 900-ms p50 full path on 4-vCPU and faster specialized/light paths. This configuration drift is itself an E0 benchmark requirement.

### Current implementation style

`retina/vision/frank_eye.py` combines many heterogeneous kernels and heuristics:

- CNN Retina lineage;
- CLIP semantic scoring;
- YOLO detection;
- DINO visual features;
- OCR;
- faces/emotion;
- logos;
- scene vocabularies;
- captioner;
- colour;
- Places365;
- fine objects;
- regional CLIP;
- composition;
- GoL pattern features;
- hand-authored spatial/scene/narrative rules.

The code is already a kind of ensemble cortex in the loose engineering sense, but its architectural output is still fundamentally **one-image analysis**. Temporal continuity and persistent world identity are not first-class in the public contract.

### Current semantic bottleneck

The implementation spends substantial effort translating heterogeneous internal signals into human-language narrative and `[VISION-FACTS]` JSON. That was rational for a downstream LLM consumer, but it creates three costs for the new FRANK:

1. repeated surface reconstruction;
2. loss of causal dependency granularity;
3. pressure to convert uncertain component outputs into declarative phrases too early.

The new architecture therefore reuses the kernels but changes their semantic role.

---

## 3. Archaeology: what the old measurements really teach

### 3.1 Useful positive result

The historical working paper provides evidence that a cooperating CPU-only stack can extract a broad range of useful visual semantics with low hardware requirements. Its original multi-round protocol reports 82.4% held-out phrase coverage over 47 unseen images / 1,196 phrases, with approximately 1.5–2.0 s/image on a 4-vCPU machine in that historical configuration.

This is a legitimate measurement foundation.

### 3.2 The honest hard-set is more important than the headline

The May-26 audit measured only 35.3% strict phrase coverage on the adversarial 12-image hard set and documented concrete structural failures:

- YOLO's fixed ontology missed required objects;
- YOLO hallucinations on art/AI could seed wrong downstream captions;
- long-tail attributes and spatial binding were weak;
- OCR failed on stylized/painted text;
- region captioning was conditional on upstream detections and sometimes amplified errors;
- CLIP could contain useful semantic signal without correct localization/binding;
- art/anime/generated composites exposed distribution shift.

This failure corpus is more useful to the deep foundry than a single top-line score because each failure can become a regression test.

### 3.3 The later 87.8% strict number must be scoped correctly

A later report pushed strict hard-set coverage to 87.8% by widening scene phrase emission and adding a large Tier-5 vocabulary that included `LAST_MILE` phrases based on per-image miss analysis.

Engineering interpretation:

- the existing visual encoders often contained semantic information that was not surfaced to the downstream text consumer;
- projection/vocabulary design strongly affected measured usefulness.

Scientific boundary:

- once the hard-set misses influence the vocabulary/projection, that surface is development data;
- the final 87.8% is not independent clean held-out generalization evidence.

### 3.4 The 94.6% lenient result exposes a Goodhart trap

The later report also gives 94.6% CLIP-lenient coverage at threshold 0.20.

The historical calibration table in the working paper reports a realistic-negative FPR around 43.3% at the same 0.20 threshold.

Therefore a permissive similarity threshold can make phrase coverage look excellent while accepting many plausible but wrong phrases. This is a direct anti-Goodhart lesson:

`embedding compatibility != perception truth`.

Future Retina acceptance must pair recall/coverage with realistic negatives, calibration, compositional binding, UNKNOWN/OOD and downstream causal outcome.

---

## 4. External research — mechanism map

The deep run deliberately searched adjacent fields rather than only modern VLM papers.

### 4.1 Recurrent visual processing

Kang et al. 2026 systematically compared recurrent and feedforward convolutional networks on occluded object recognition and report an `explaining-away` computation arising in recurrent variants. Recognizing an occluder can help explain missing object features and recover the underlying object representation.

FRANK implication:

Recurrence is worth testing specifically where evidence is incomplete/ambiguous. It should not be added everywhere as biological decoration.

### 4.2 Object-scene joint inference

The Nature Reviews Psychology synthesis by Peelen et al. describes bidirectional object-scene/object-object interactions and frames perception as joint probabilistic inference.

FRANK implication:

The world/scene model can legitimately participate in perception. But because scene context can also impair object perception, every prior contribution must remain separable from sensor support.

### 4.3 Temporal continuity and memory

Continuity-field and visual-memory work supports the general idea that recent perceptual state can stabilize noisy observations. Robotics independently proves that hierarchical persistent scene state can be maintained online.

FRANK implication:

Do not re-create object identity from scratch every frame. But do not keep it forever either: `OCCLUDED`, `OUT_OF_FOV`, explicit absence and stale state need different update rules.

### 4.4 Event-driven vision

The 2024 Nature hybrid event/frame system is strong evidence for the general value of sparse asynchronous updates: high temporal resolution can coexist with lower bandwidth when dense anchors provide static information.

FRANK implication:

Even with ordinary cameras, the architecture should test change-region processing + periodic/adaptive anchors. Event-camera hardware is an optional lowering, not the cognitive design.

### 4.5 Stateful event models

State-space models for event cameras show a modern computational route where hidden state persists over streams and learned timescales cope with varying event frequency.

FRANK implication:

The visual subsystem should not assume one universal frame clock. Multi-rate state is a first-class candidate.

### 4.6 Persistent scene graphs

Hydra/Kimera demonstrate online multi-layer scene graph construction and maintenance.

FRANK implication:

Persistent scene state is prior art, so no novelty claim. ClayGraph's research opportunity is not `a graph exists`; it is whether the same typed state can connect perception, memory, GWT, goals and action with lower reconstruction cost and stronger provenance.

### 4.7 Streaming visual agents

StreamArena (Aug 6, 2026) directly targets continuous hour-scale visual agents. Its analysis reports failures of recent-frame-only memory, text conversion and repeated compression.

FRANK implication:

The historical Retina `image -> text` interface is particularly weak for unbounded streams. Persistent visual state is a serious systems requirement, not merely a neuroscience analogy.

### 4.8 Active perception

Next-best-view research formalizes sensing as decision-making under uncertainty/information gain.

FRANK implication:

A camera does not have to move for active perception to be useful. Choosing `crop`, `higher resolution`, `OCR retry`, `open-vocab detector`, `new anchor`, or `ask user` is already active sensing.

### 4.9 Open-set/open-world detection

Open-set work emphasizes unknown-object detection and calibrated uncertainty rather than forcing every object into known classes.

FRANK implication:

`UNKNOWN` is not a missing label; it is a valid epistemic state that can trigger active sensing or GWT.

### 4.10 Modern edge kernels

MobileCLIP2, SigLIP2 and open-vocabulary detectors provide plausible replacements/complements for parts of historical Retina. But published benchmark improvements do not imply project-hardware wins.

FRANK implication:

Freeze architecture interfaces first; then let kernels compete behind them.

---

## 5. Fusion 1 — the six-plane model

The strongest architecture after internal archaeology + external research is separated into six logical planes:

### Evidence Plane E
What sensor transforms actually observed. Immutable/provenance-bound. World belief cannot rewrite it.

### Perceptual Inference Plane P
Competing interpretations of the evidence. Set-valued, provisional, confidence/precision aware, dependency-tracked.

### World Plane W
Persistent entities/relations after temporal/admissibility integration. Can survive non-observation but must react strongly to explicit negative evidence.

### Global Plane G
Bounded Assembly projected to GWT only when global reasoning has expected value.

### Active Sensing Plane A
Select additional evidence acquisition/computation when uncertainty matters.

### Receipt Plane R
Materialize complete `VisualPercept`/trace snapshots on demand for audit/replay/training.

This decomposition is intentionally logical. UnifiedDB/H3 may physically co-locate most of it.

---

## 6. Why this is deeper than predictive coding imitation

A naive implementation could say:

`prediction + sensory error -> update belief`.

That is too vague for FRANK.

The deep run adds explicit engineering invariants:

1. evidence has immutable source/epoch/transform identity;
2. priors never become evidence;
3. goal bias changes compute attention, not truth confidence;
4. conflicting hypotheses may coexist;
5. object identity is independent of current semantic label;
6. non-observation differs from explicit negative evidence;
7. every derived fact can be invalidated by upstream lineage;
8. visual updates need not enter GWT;
9. active sensing is cost/value constrained;
10. post-action visual re-entry closes the action loop;
11. materialized perception is reconstructible even if the hot path is sparse;
12. physical sensor topology can change without changing semantic contracts.

This transforms an analogy into an executable research program.

---

## 7. Synthetic mechanism sanity checks

A deterministic synthetic sandbox was used only to test qualitative failure modes. It is explicitly not live Retina evidence.

### 7.1 Prior dominance

As synthetic sensor signal was progressively degraded, increasing a correlated context prior could improve nominal accuracy while making deliberately wrong priors far more likely to be accepted.

Interpretation:

`context helps when evidence is weak` and `context can hallucinate when evidence is weak` are the same mechanism viewed from opposite sides.

Therefore recurrence cannot be scored only on average accuracy.

### 7.2 Temporal persistence

A persistent belief state improved synthetic recall under detector misses. But slow persistence without explicit negative evidence generated very long ghost-object runs and high false-positive rate.

Interpretation:

Object permanence requires **negative-evidence semantics**, not just memory decay.

### 7.3 GWT gating

A toy scalar ignition score showed the expected precision/recall tradeoff: high thresholds can make workspace events highly precise while missing most important events.

Interpretation:

Low GWT rate is not success. Visual gating must be evaluated against downstream important-event recall and causal outcomes.

### 7.4 Anchor/event tradeoff

Synthetic state-loss tests showed event-only processing cannot reconstruct lost static state, whereas occasional anchors trade additional cost for recovery.

Interpretation:

Hybrid anchor + change is the default candidate until real evidence says otherwise.

### 7.5 Active sensing

Selective synthetic second-look policies produced a smooth accuracy/cost frontier.

Interpretation:

This supports implementing sensing as a resource decision rather than always invoking every expensive stage.

Full numbers are preserved in `SYNTHETIC_MECHANISM_RECEIPT.json`.

---

## 8. First-generation hypothesis field

The run generated 66 materially distinct first-generation hypotheses across eight families:

1. temporal ingress/sampling;
2. recurrent inference;
3. object/world continuity;
4. Clay semantics;
5. GWT + active perception;
6. visual kernels/performance;
7. safety/OOD/recovery;
8. small-model functional multimodality.

Twenty explicit counterhypotheses were added, including the possibility that:

- simple detector+tracker wins;
- feedforward typed state is enough;
- separate process isolation is better;
- native VLM remains necessary for some target tasks;
- typed state is worse for the 4B;
- open-vocabulary kernels are too expensive;
- one-module consolidation increases crash radius;
- dedicated video memory is better than general ClayGraph.

This matters because the run is not designed to prove the owner's favorite mechanism. It is designed to keep the fixed owner target while letting implementation evidence choose the simplest working realization.

---

## 9. Fusion 2 — transformed hypotheses

External research + counterhypotheses + synthetic failures produced 24 second-generation hypotheses. The most important transformation is from **recognition architecture** to **evidence-computation economics**.

### 9.1 Precision budget scheduler

Instead of running all vision stages, precision/uncertainty becomes an input to compute allocation.

High-certainty local state -> cheap maintenance.

High-value uncertainty -> buy more evidence.

### 9.2 Evidence debt

An unresolved visual hypothesis that persists while influencing world/action state accumulates `evidence debt`. Before high-impact use, the system should refresh or resolve it.

This is analogous to technical debt but machine-verifiable: an entity has age, uncertainty, last positive evidence and action relevance.

### 9.3 Perceptual interrupt

Rare high-risk surprise may need an interrupt-like path into GWT rather than waiting for ordinary scheduling.

This gives the thalamic/GWT architecture a concrete visual role without broadcasting every frame.

### 9.4 Epistemic visual types

A value should be distinguishable as:

`OBSERVED`
`INFERRED`
`REMEMBERED`
`EXPECTED`
`CONFLICT`

The same semantic noun can therefore appear with different epistemic provenance.

### 9.5 Visual information router

The future Retina is less a fixed model stack and more a router/compiler for evidence-producing transformations.

A cheap path may end after change tracking.

A difficult path may invoke open-vocabulary detection, OCR retry, dense regions and global reasoning.

### 9.6 Perceptual sufficiency receipt

If a frame/change does **not** enter GWT, the system can optionally emit a compact receipt explaining why local processing was sufficient. That makes `ignored` perception auditable and enables missed-escalation analysis.

### 9.7 Multimodal agency loop as the real benchmark

The strongest functional-multimodality test is not static image QA. It is:

`perceive -> decide -> act -> visually verify -> update -> recover`

across long horizons.

If FRANK can do that coherently with a 4B reading bounded Clay state, the architecture has achieved a much more meaningful form of functional multimodality than high phrase coverage alone.

---

## 10. Kernel strategy

### Do not rewrite from zero

Current Retina is valuable as:
- source adapters;
- cached models;
- CLIP/YOLO/DINO/OCR kernels;
- UI/screenshot heuristics;
- colour/spatial transforms;
- test fixtures;
- warmup/runtime knowledge;
- historical failure corpus.

### Do not freeze current kernels either

Run controlled bakeoffs:

- CLIP-B/32 vs MobileCLIP2;
- CLIP/SigLIP2 where dense/local semantics matter;
- DINOv2 vs DINOv3 small/distilled where available;
- YOLOv8n vs open-vocabulary/open-world detectors;
- captioner always-on vs information-gain conditional;
- GoL vs ordinary texture/dense-feature baselines.

The cognitive architecture must survive these swaps.

---

## 11. Game-of-Life result

The GoL stage is retained as a research candidate but loses any privileged explanatory status.

Reason:

- cellular automata can be valid engineered texture descriptors;
- current code extracts measurable density/stability/oscillation features;
- but the deep run found no evidence that Conway GoL is uniquely aligned with visual cortex or necessary for Retina semantics;
- its current phrase mapping can be tested directly against simpler texture/dense-feature descriptors.

Decision:

`ABLATE, DO NOT BELIEVE`.

If it adds robust held-out information at attractive cost, keep it. Otherwise remove it from the default hot path.

---

## 12. Clay/ClayCode meaning

Retina becomes one of the hardest tests of the entire Clay claim.

If Clay is genuinely a dynamic cognitive substrate, it should support:

- sparse high-rate deltas;
- relation activation;
- fast local state without full model calls;
- uncertainty/conflict;
- temporal identity;
- multiple timescales;
- active Assemblies;
- reversible world updates;
- evidence provenance;
- deterministic replay.

If implementing Retina in Clay requires turning every update into verbose object serialization and database queries, then the current Clay design is not yet the substrate the project intends.

ClayCode therefore gets a concrete falsifier: can it compile the PerceptualField semantics into low-overhead runtime code while preserving exact trace semantics?

---

## 13. GWT meaning

Visual perception gives GWT a measurable selection problem.

Bad GWT design:

`new frame -> broadcast vision`.

Research target:

`local evidence/state update -> local resolution if possible -> global ignition only if expected global value justifies it`.

Candidate ignition variables:
- unresolved surprise;
- uncertainty;
- risk;
- goal relevance;
- cross-modal conflict;
- action consequence;
- evidence debt;
- expected information gain.

Every selected visual episode still requires delivery/reconstruction/uptake/causal-use/outcome/re-entry receipts.

---

## 14. ClayGraph/UnifiedDB meaning

Visual memory is no longer just `store the last caption`.

The substrate must answer separately:

- what sensor evidence arrived?
- what hypothesis was inferred?
- what was believed about the persistent world?
- what was visible versus merely remembered?
- which evidence supported a relation?
- what entered GWT?
- what changed after an action?
- which derived state became invalid after a detector/model change?

This is exactly why the Evidence/P/W distinction exists.

Physical unification remains benchmark-gated. High-rate evidence may live in optimized buffers/sidecars while sharing one semantic identity/query plane.

---

## 15. Strongest counterargument after the whole run

The strongest alternative is much simpler:

`optimized Retina kernels + tracker + cache + periodic full frames + concise typed output`.

This could capture most useful continuity without the complexity of recurrent world feedback, active sensing or set-valued PerceptualField dynamics.

This is not a straw man. It becomes a mandatory baseline in E3/E4/E7.

If it wins, FRANK should use it.

The owner-fixed semantic dissolution still stands: even a simpler solution can be in-process and Clay-native without creating a separate cognitive Retina organ.

---

## 16. Second strongest counterargument

A native VLM may simply be much better at compositional vision.

The target architecture intentionally avoids inserting a cloud/external VLM into the serving path, but the research must still use strong VLMs as evaluation comparators where legitimate. If modular kernels + 4B structured reasoning cannot meet the required visual behavior, that is a scientific result; the project should not hide it behind easier metrics.

No automatic paid/model integration is authorized by this run.

---

## 17. Experiment priority

The 25-experiment matrix is staged so architecture questions close before component shopping:

### Wave 0 — truth baseline
E0 current code/hardware reproduction; E1 clean frozen held-out benchmark.

### Wave 1 — state mechanism
E3 temporal field; E6 explicit absence; E4 recurrence; E5 prior safety.

### Wave 2 — compute allocation
E7 anchor/change; E8 GWT gating; E9 active sensing.

### Wave 3 — interface
E2 typed state vs narrative; E10 materialization; E11 lineage invalidation.

### Wave 4 — kernel modernization
E12 image-text encoders; E13 detection/UNKNOWN; E14 dense temporal features; E15 GoL; E16 captioner.

### Wave 5 — system closure
E17 physical topology; E18 recovery; E19 prompt injection; E20 long-horizon memory; E21 action closure; E22 cross-modal conflict; E23 H1/H2/H3 differential; E24 Android/edge.

---

## 18. Fixed decisions vs open research

### Fixed by owner directive

- visual perception is mandatory;
- Retina is not a separate semantic cognitive organ in target FRANK;
- sensor ingress should dissolve into the one-module runtime as far as technically feasible;
- Clay-native semantic state is authoritative above the physical sensor/model backing;
- VisualPercept is an audit/materialization interface, not mandatory serial hot path.

### Strong research candidate, not yet fixed

- Evidence/P/W/G/A/R six-plane logical architecture;
- explicit visibility-state lattice;
- precision-separated recurrence;
- evidence debt;
- perceptual interrupt;
- active sensing by expected information gain;
- adaptive anchor/change scheduling;
- selective GWT visual Assemblies;
- continuous shadow baseline.

### Empirically open

- actual latency gain;
- actual recognition gain;
- optimal recurrence;
- optimal anchor policy;
- best encoder/detector;
- value of GoL;
- whether one process is physically superior on each platform;
- whether the 4B can exploit Clay visual state better than narrative;
- how close the whole architecture can come to native-VLM behavior on required tasks.

---

## 19. Durable outputs

Created/updated in this run:

- `research_entity/retina/RETINA_DOMAIN_INDEX.json`
- `research_entity/retina/RETINA_RESEARCH_FOUNDATION.md`
- `research_entity/retina/RETINA_PERCEPTUAL_FIELD_ARCHITECTURE.md`
- `research_entity/retina/RETINA_HYPOTHESIS_MATRIX.json`
- `research_entity/retina/RETINA_SECOND_GENERATION_HYPOTHESES.json`
- `research_entity/retina/RETINA_EXPERIMENT_MATRIX.md`
- `research_entity/retina/RETINA_NEGATIVE_RESULTS.md`
- `research_entity/retina/RETINA_BRANCH_HANDOFFS.md`
- this report;
- `EXTERNAL_RESEARCH_MANIFEST.md`
- `TOOL_EXECUTION_MANIFEST.json`
- `SYNTHETIC_MECHANISM_RECEIPT.json`
- Topic/Micro-Packets materialized separately.

`DOMAIN_REGISTRY.json` was CAS-updated to add `visual_perception_retina` as a first-class research domain.

---

## 20. Final synthesis

The deepest useful reframing is:

**Retina should stop trying to understand an image completely.**

It should continuously maintain the minimum visual evidence needed to keep FRANK's world state calibrated.

When reality behaves as expected, most perception remains local, sparse and cheap.

When reality violates expectation, uncertainty rises, a relation becomes inconsistent, a risky object appears, an action has an unexpected result, or the current task needs detail, the system spends more computation and can ignite GWT.

That makes the desired architecture closer to a living control loop than a VLM substitute API:

`predict / observe / compare / maintain / question / act / verify / revise`.

The scientific burden now moves to the Harness. If the mechanism is real, it must beat simpler baselines in **held-out perception, calibration, continuity, action grounding, latency, state movement and 4B token cost** while surviving misleading priors, OOD, stale input, crash/restart and prompt-injection tests.

If it cannot, simplify it.
