# Retina Deep Foundry — Cross-Branch Handoffs

Run: `retina-20260809T0615p0700-deep-foundry`  
Rule: findings are routed as research requirements/hypotheses; room agreement does not upgrade evidence.

## FRANK

### Required architecture input
- treat the existing standalone Retina as historical implementation/kernel source, not final cognitive boundary;
- integrate Evidence/Perceptual/World/GWT/Active-Sensing logical planes into the current FRANK architecture map;
- keep sensor evidence immutable/provenance-bound;
- preserve `OCCLUDED != OUT_OF_FOV != ABSENT_EXPLICIT_NEGATIVE != UNKNOWN != STALE`;
- make object identity independent of current semantic label;
- provide a deterministic firebreak from provisional perceptual hypotheses to durable world belief;
- post-action visual re-entry becomes a first-class outcome verification path.

### Main falsifier
If optimized stateless Retina + simple tracker/cache is Pareto-superior to the recurrent architecture, simplify aggressively while preserving the fixed dissolved semantic target.

## Clay

### Research feedback
Retina supplies a concrete, high-frequency test case for whether Clay is genuinely useful as a dynamic substrate rather than merely a compact serialization language.

Clay must demonstrate:
- sparse local state propagation;
- activation without full graph/model materialization;
- reversible alternatives/conflicts;
- multi-timescale updates;
- provenance-preserving coupling;
- state-dependent computation scheduling;
- bounded Assemblies.

### High-value Clay question
Can Clay make computation follow semantic change, so unchanged visual state is almost free while relevant conflict automatically activates connected world/memory/GWT structures?

## ClayCode

### Required expressivity
ClayCode BASE must be able to encode:
- `SensorEvidence` with source/time/transform/calibration identity;
- sparse spatial/temporal deltas;
- bottom-up precision vs prior precision vs context gain;
- `UNKNOWN`, `CONFLICT`, `OCCLUDED`, `OUT_OF_FOV`, `ABSENT_EXPLICIT_NEGATIVE`, `STALE`, `REVOKED_DERIVATION`;
- set-valued perceptual hypotheses;
- temporal entity identity and track merge/split;
- dependency invalidation;
- GWT visual candidate/custody receipts;
- active-sensing actions and cost/value;
- on-demand `VisualPercept` materialization;
- counterfactual replay interventions.

### Compiler/runtime implication
A visual program should compile to platform-specific lowerings without changing semantic identity: frame-delta CPU path, Android camera/NPU path or future event-sensor path.

### Language-change rule
Do not change ClayCode spec merely because this document asks for a feature. First produce an executable counterexample showing the existing language cannot express the required Retina transition safely/deterministically.

## ClayGraph

### Required graph semantics
- separate Evidence nodes from Hypothesis nodes from World Entity nodes;
- typed support/contradiction edges;
- temporal validity and visibility states;
- identity continuity despite label revision;
- set-valued alternatives and exclusion constraints;
- spatial/n-ary relations;
- active/latent perceptual Assemblies;
- causal paths from visual evidence to GWT, memory, action and re-entry;
- per-edge dependency invalidation.

### Benchmark
Compare persistent graph-assisted relation/object continuity against per-frame RAG/reconstruction under matched tokens/compute.

## UnifiedDB

### Required logical substrate
A visual query must be able to distinguish:

`what raw evidence arrived?`
`what did the perceptual layer infer?`
`what did FRANK believe about the world?`
`what entered GWT?`
`what was causally used?`
`what changed after action/re-entry?`

Canonical/raw evidence, derived features, current world snapshot and activation indices must not collapse into one authority class.

### Physical design question
High-rate perceptual deltas may justify hot ring buffers/columnar/vector sidecars while semantic identity remains unified. Final physical placement is benchmark-gated.

## GWT

### Required visual episode semantics
Visual data may evolve below workspace. Candidate gating should compare at least:
- novelty;
- prediction error;
- uncertainty;
- goal relevance;
- risk;
- cross-modal conflict;
- action consequence;
- expected information gain.

All visual episodes preserve:
`candidate -> selection -> broadcast -> delivery -> reconstruction -> uptake -> causal_use -> outcome -> reentry`.

### Anti-Goodhart
Reducing workspace rate is not success if important-event recall or causal outcomes fall.

## Hyperposition

Retina provides a concrete non-metaphorical use case for contextual alternatives:
- ambiguous object identity;
- multiple plausible relations;
- occlusion explanations;
- mutually exclusive scene interpretations;
- re-opening after contradictory evidence.

Required comparison: Hyperposition/n-ary representation vs calibrated top-k probabilities + ordinary state machine. If simpler representation is information-equivalent, keep the simpler one.

## Emergenz

Retina/world/GWT coupling is not emergence evidence merely because behavior improves.

Use factorial and intervention designs:
- feedforward only;
- temporal state only;
- world recurrence;
- memory recurrence;
- GWT coupling;
- truthful vs shuffled feedback;
- lesion/rescue.

Measure interaction terms, causal effect, recurrence and cost shadows. Do not infer phenomenal consciousness.

## Harness

Immediate H1 additions:
1. historical current Retina baseline adapter;
2. typed Evidence Plane fixture;
3. object continuity/absence/occlusion state machine;
4. PerceptualField reference implementation;
5. recurrence/prior lesion controls;
6. misleading-prior/no-signal battery;
7. anchor/change scheduler;
8. GWT visual custody chain;
9. active-sensing request simulator;
10. on-demand VisualPercept materializer;
11. stale/replay/crash tests;
12. narrative-vs-typed model projection differential.

Required H2: same semantics in ClayCode.

Required H3: in-process sensor/perception topology benchmark against isolated service, preserving the same Golden semantic traces.

## Android / edge runtime

Benchmark sustained, not one-shot, inference. Required measurements:
- warm/cold latency;
- CPU/GPU/NPU/Vulkan/NNAPI backend;
- RAM;
- thermal throttling;
- battery/energy;
- camera wakeups;
- background/process restrictions;
- MobileCLIP2/SigLIP2/DINO/open-vocab candidate feasibility;
- hybrid anchor/change policy.

Desktop performance may not determine the mobile lowering.
