# FRANK Digital Retina Multimodal Contract

**Status:** PROJECT-OWNER ARCHITECTURE DIRECTIVE — NOT A RESEARCH HYPOTHESIS  
**Owner directive recorded:** 2026-08-09  
**Dissolved-perception update:** 2026-08-09  
**Adaptive visual learning update:** 2026-08-09  
**Applies to:** FRANK, Clay, ClayCode, ClayGraph, GWT, Hyperposition, UnifiedDB, Harness H1/H2/H3 and Clay 0.1 acceptance  
**Controlling extensions:** `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`; `research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md`

## Fixed target

Visual perception through the historical Digital Retina lineage is mandatory in the target FRANK module. It is not an optional plugin or post-release add-on.

However, **Digital Retina is no longer required to survive as a semantically independent cognitive subsystem/process boundary**. The project-owner target is a one-module FRANK in which the visual sensor ingress and perceptual state dynamics dissolve into the integrated Clay-native runtime as far down the physical/software stack as feasible.

The accepted Clay 0.1 FRANK must therefore be multimodal at minimum across language/text and visual perception. Existing voice/audio and other sensor paths may extend multimodality.

FRANK 0.1 additionally MUST contain the adaptive visual learning mechanism defined by `FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md`: a tiny user-specific learned familiarity/routing layer over reusable visual features, with calibrated confidence/open-set handling and bounded autonomous cyclic updates. This is part of the visual architecture, not an optional later personalization feature.

## Required perception architecture

The target path is now:

`physical visual transducer -> in-module sensor ingress -> typed evidence/state deltas -> PerceptualField <-> world/memory/goals/self/context -> adaptive familiarity/readout -> thalamic/attention selection -> GWT when required -> memory/world/action -> re-entry`

`VisualPercept` remains a required **audit/materialization contract**, but it is not a mandatory serial hot-path boundary through which all visual cognition must first pass.

Visual sources may include screen frames, camera frames, images, rendered UI state and other explicitly authorized visual inputs.

The physical perception machinery may use conventional code/models and representations including image tensors, embeddings, OCR, detectors, segmentation, feature extractors, temporal/change detection and numerical vision models. These remain physical backing representations rather than a second semantic architecture.

Whenever visual information changes FRANK's semantic/cognitive state, the changed state MUST remain Clay-native, typed and provenance-bound.

## PerceptualField

The integrated runtime MUST support the logical `PerceptualField` concept defined in `FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`.

The field may be physically distributed across optimized state structures. It must be able to preserve or reference at least:

- source identity/class;
- capture/event time and epoch;
- local/spatial evidence;
- motion/change evidence;
- OCR/text evidence;
- extracted features/entities and unresolved hypotheses;
- relations/spatial bindings;
- confidence/uncertainty/precision;
- expected-vs-observed mismatch;
- active alternative interpretations/conflicts;
- salience/attention metadata;
- links into world model and ClayGraph memory;
- goal/action-context relevance;
- transformation/model lineage;
- prior perceptual state/re-entry lineage;
- learned familiarity candidate/state where used, while preserving its distinction from current sensor evidence.

The architecture MUST permit perception to remain `UNKNOWN`, `CONFLICT` or set-valued when evidence does not justify a single interpretation.

## VisualPercept materialization

A materialized `VisualPercept` receipt remains mandatory whenever required for Harness traceability, replay, memory/effect evidence, debugging, external projection or training/evaluation artifacts.

A minimum materialized receipt must preserve, directly or by referenced typed subobjects:

- source identity and source class;
- capture/event time and epoch;
- spatial/frame/event identity;
- extracted entities/features/relations and unresolved alternatives where relevant;
- confidence/uncertainty and prior-vs-evidence contribution where relevant;
- learned familiarity/readout result and classifier/prototype version when causally used;
- provenance to originating visual evidence;
- transformation/model lineage;
- salience/attention metadata when selected;
- links to any GWT episode, memory write, goal update or effect proposal causally using it.

Harness research must test whether required receipts can be reconstructed from sensor evidence + state lineage without forcing full materialization on every hot-path update.

## Clay-native boundary

Digital Retina is NOT an exception to the FRANK Clay-native rule.

Needle remains the sole intentional non-Clay semantic subsystem. Retina implementation machinery may use conventional code and numerical models, but visual semantics in FRANK state are Clay-native. Raw tensors/pixels/embeddings are physical backing representations and must be provenance-bound when projected into Clay semantics.

No untyped natural-language caption, opaque model embedding or Micro Visual Classifier output may silently become architectural truth, memory truth, execution authority or world-state truth.

## Sensor-in-module boundary

The target H3/Clay 0.1 architecture SHOULD contain, where host/device APIs permit, inside the FRANK process/binary identity:

- device ingress/control adapter;
- timestamps/epochs/source binding;
- buffering/ring state;
- fast change/event extraction;
- visual transformation kernels/models;
- adaptive Micro Visual Classifier/prototype readout and bounded update path;
- Clay state projection/update;
- recurrent perceptual coupling;
- GWT/memory/world/action/re-entry interfaces.

Unavoidable device hardware, firmware, OS/kernel drivers and host APIs remain physical dependencies rather than semantic modules.

Any retained out-of-process Retina or adaptive learner service is a physical lowering choice requiring measured justification; it does not define the cognitive architecture and cannot become a separate semantic authority.

## Recurrent world/memory/context coupling

The target MUST support experimentally bounded recurrence from world model, memory, goal/action context and prior perceptual state into visual interpretation.

This is intended to test context-dependent recognition, completion and persistent entity continuity.

Top-down state is not sensor truth. The system must preserve distinguishable precision/weight for:

- bottom-up evidence;
- world/learned prior;
- current goal/context bias;
- learned familiarity/readout support where used.

Mandatory safety/falsification conditions include misleading priors, no-signal input, unknown objects, degraded input, context swaps, stale/replayed evidence, feedback lesions and rescue.

## Adaptive user-specific visual learning

FRANK 0.1 MUST implement adaptive visual learning according to `FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md` and the research foundation `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md`.

The preferred initial implementation reuses frozen Retina visual features and learns only a tiny personal readout/prototype layer. The normal autonomous cycle MUST NOT retrain the full visual backbone.

Required behavior:

- familiar recurring user/workspace visual content can acquire persistent prototype/readout support;
- trusted training examples use GOLD/SILVER/BRONZE provenance tiers;
- BRONZE self-predictions cannot directly become positive training truth;
- output distinguishes calibrated familiar/needs-confirmation/ambiguous/unknown/conflict states;
- only high-confidence familiar states may bypass expensive broad recognition;
- novel, contradictory or weakly supported input escalates into deeper Retina/PerceptualField processing;
- cyclic updates occur only under explicit resource budgets and preserve last-known-good rollback;
- classifier/prototype versions, calibration and feature-backbone compatibility remain replayable/persistable;
- learned familiarity improves routing but cannot rewrite Evidence Plane truth.

Mandatory experiment families are MVC-E1..E7 plus crash/restart/rollback and long-horizon familiar+novel action-loop tests. Exact performance thresholds remain evidence-gated until frozen from project-hardware measurements.

## Event/change-driven fast path

The target SHOULD support event/change-driven state updates so unchanged visual state need not be fully reconstructed continuously.

Conventional cameras may implement this through frame differencing/change regions/feature deltas. Event-camera hardware is an optional optimization.

For the current main-screen candidate, a roughly 19-second anchor screenshot cadence may serve as a default visual heartbeat, with immediate additional screenshots available on demand, before/after actions, under uncertainty/conflict or when active sensing predicts positive information value. The exact 19-second cadence remains tunable unless separately owner-frozen.

Because change-only/event-only sensing can miss static or slowly varying information, Harness must compare:

- periodic full-frame processing;
- event/change-only processing;
- hybrid anchor-frame + event/change processing;
- hybrid anchor/change plus adaptive familiarity fast-path routing.

## GWT and attention integration

Visual evidence participates in the same causal observability contract as other FRANK perception.

Perceptual state may update below the workspace. GWT candidacy/ignition is triggered only when globally useful, including conditions such as:

- unresolved prediction error;
- novelty/change;
- risk/threat;
- goal relevance;
- cross-modal/state conflict;
- ambiguity requiring global resources;
- action consequence;
- explicit task demand.

Familiar visual content may remain local when the learned readout is calibrated, current evidence is compatible and no globally useful change exists. Novelty/unknown/conflict should tend to buy deeper perception or GWT resources rather than being forced into a familiar class.

The system must distinguish at least:

- no visual evidence;
- visual evidence present but locally resolved/gated;
- visual evidence resolved through a calibrated familiar fast path;
- visual evidence selected for workspace;
- delivered/reconstructed/uptaken visual state;
- visual state causally used downstream;
- visual outcome/re-entry;
- stale/replayed/mismatched evidence.

Existing GWT law remains mandatory:

`evidence present != selected != broadcast != reconstruction != uptake != causal use != outcome != re-entry`.

## Harness requirement

H1 Reference Harness MUST include deterministic sensor/Retina fixtures and end-to-end visual-perception traces.

H1 MUST implement both the explicit materialized baseline and the dissolved-perception candidate sufficiently to run differential experiments, and MUST include the mandatory adaptive visual learner from the v0.1 directive.

H2 ClayCode Harness MUST express the same frozen visual semantics, PerceptualField updates, materialized receipt semantics, adaptive learner state/update/promotion/rollback semantics and causal transitions in ClayCode.

H3 One-Module/Binary FRANK MUST contain/bind the sensor ingress, visual runtime and adaptive learner as part of the accepted FRANK module identity according to the dissolved-perception and adaptive-learning directives. A build without the mandatory visual path or adaptive learner cannot PASS H3 or DOOMSDAY.

Reference-vs-Clay-vs-One-Module differential tests must verify representation-invariant equivalence for sensor evidence identity, state lineage, materialized VisualPercept receipts when requested, learned familiarity state when used, attention/GWT use, memory/world updates and downstream effects.

Required additional differential families:

- explicit Retina->VisualPercept boundary vs dissolved PerceptualField;
- feedforward vs recurrent perceptual field;
- world/memory/goal feedback lesions and rescue;
- misleading-prior/no-signal/unknown-object controls;
- fixed full-frame vs change-only vs hybrid anchor/change;
- adaptive familiar fast path vs full Retina on matched familiar/novel data;
- prototype vs tiny learned readout under frozen resource/retention/open-set tests;
- pseudo-label poisoning and sequential forgetting;
- out-of-process vs in-process H3 sensor/learner topology;
- model-visible context/token cost of caption/full-percept/bounded Assembly projections.

Primary experiment plan: `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/EXPERIMENT_PLAN.md`.
Adaptive visual learning experiments: `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md` MVC-E1..E7.

## Historical reuse requirement

Level-0 assimilation must ingest the existing Drive `digital-retina` lineage before replacing or reusing mechanisms. The observed historical tree includes at least `retina`, `api`, `frontend`, `eval`, `deploy`, `tests`, `tools` and `docs`, with a nested `retina/vision` branch.

Historical code is evidence and reusable foundation, not automatic current truth. Reuse must be classified as directly reusable, reusable with adaptation, measurement foundation, negative-result value, superseded/informative or not reusable.

Historical dictionary/pattern/familiarity mechanisms must be explicitly considered as possible reusable/negative-result foundations for the v0.1 adaptive learner rather than rediscovered blindly.

## Historical implementation and measurement baseline

Level-0 Drive assimilation has confirmed a substantial historical implementation rather than a paper-only concept:

- `retina/core.py` exposes a structured image-analysis API rather than only free-text captioning;
- the historical structured result includes description, concepts, detected objects, OCR text, faces, logos, image metadata and elapsed time;
- `retina/vision/` contains a large `frank_eye.py` implementation plus CLIP classification, OCR, region/scene/composition, Places365, colour and pattern-oriented modules;
- `tests/test_smoke.py` expects real structured output fields and actual model weights/sample image.

A historical working paper reports, for its own limited engineering test regime, 82.4% held-out phrase coverage over 47 unseen images / 1,196 phrases, about 1.5-2.0 seconds per image on 4-vCPU CPU-only hardware, and 13.6% false-positive rate on a realistic-negative set at threshold 0.22. The paper explicitly describes itself as non-peer-reviewed, n=1 engineering work and notes distribution/compositional-binding limitations.

These figures are **measurement foundations, not frozen Clay 0.1 acceptance thresholds**. H1/H2/H3 must reproduce or falsify the historical baseline on current project hardware and under the current dissolved multimodal contract before performance claims are promoted.

The historical autonomous-vision design also proposes event-triggered rather than periodic visual attention, bounded daily/cooldown budgets and habituation for repetitive visual/OCR state. This is a candidate policy to test, not proof that the historical design was deployed or optimal.

Primary Level-0 receipt: `research_entity/archive_assimilation/receipts/666_20260809T0441p0700_chatgpt_secondary_drive_g8_g9_retina_code_shard.json`.

## Research status of the dissolved design

External research synthesized in:

`research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/REPORT.md`

supports the separate ingredients of recurrent perception, prior/context influence, event-driven low-latency sensing and persistent semantic scene state.

It does NOT independently prove that FRANK's complete dissolved architecture is superior. Performance/cognitive benefits remain OPEN and must be tested by the differential Harness.

The existence of the adaptive learner is owner-fixed for v0.1; its exact algorithm and performance benefits remain research-gated.

## Acceptance rule

Visual perception and adaptive user-specific visual learning are mandatory architecture completeness. Clay 0.1 cannot reach chief-developer first-test acceptance if:

- the visual perception path is absent;
- the adaptive Micro Visual Classifier/cyclic learner is absent or disabled;
- sensor/perceptual semantic state bypasses Clay typing/provenance;
- H1/H2/H3 disagree on frozen required visual or adaptive-learning semantics;
- materialized audit receipts cannot be produced/replayed when required;
- visual evidence cannot be traced through selection/broadcast/causal use/re-entry when it enters GWT;
- stale/replayed evidence is accepted as current without detection;
- world/memory priors or learned familiarity cannot be distinguished from sensor evidence;
- visual model or Micro Visual Classifier output can mint execution authority directly;
- adaptive learning can promote untrusted self-labels to training truth without the required trust gate;
- learner state cannot be versioned, rolled back, replayed and recovered;
- project-hardware resource use and MVC-E1..E7/frozen successor thresholds have not been run;
- H3 retains an unexplained semantic Retina or adaptive-learner service boundary contrary to the one-module target.
