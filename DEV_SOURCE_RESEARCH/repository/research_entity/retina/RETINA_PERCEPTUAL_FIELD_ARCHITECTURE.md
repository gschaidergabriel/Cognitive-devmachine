# Retina PerceptualField Architecture Candidate

**Status:** OPEN ARCHITECTURE CANDIDATE UNDER OWNER-FIXED DISSOLVED-PERCEPTION TARGET  
**Run:** `retina-20260809T0615p0700-deep-foundry`  
**Authority:** research candidate; does not override owner directives or empirical results.

## 1. Architectural thesis

The strongest current candidate is to stop treating vision as a function:

`image -> semantic result`

and instead implement it as a continuously updated partially observed state machine:

`visual evidence -> local state delta -> temporal/perceptual inference -> world integration -> selective global use -> active sensing/action -> new evidence`

The physical sensor and unavoidable kernel/device boundary remain physical. Everything above that boundary should be able to compile into the same FRANK runtime/binary in H3 unless a measured isolation/performance reason justifies a separate physical process.

## 2. Six logical planes

### E — Evidence Plane

Authoritative about **what was observed by a particular sensor transform**, not about what the world ultimately is.

Candidate records:

`SensorEvidence {
  evidence_id
  source_id
  source_epoch
  capture_time
  ingest_time
  spatial_scope
  raw_ref_hash?
  transform_id
  transform_version
  observation_type
  value
  bottom_up_precision
  calibration_ref
  provenance
}`

Examples:
- pixel/frame/crop hash;
- changed region;
- OCR token + coordinates;
- box/mask + detector score;
- dense feature region;
- optical flow/motion vector;
- image-text similarity;
- low-level edge/colour/texture evidence.

Hard invariant: Evidence objects are append-only/immutable under ordinary cognition. A later interpretation may supersede a hypothesis, not rewrite the observation.

### P — Perceptual Inference Plane

Non-authoritative hypotheses that explain current evidence.

`PerceptHypothesis {
  hypothesis_id
  subject_candidate
  type_or_label_alternatives[]
  attribute_alternatives[]
  relation_alternatives[]
  supporting_evidence[]
  contradicting_evidence[]
  temporal_support[]
  world_prior_support[]
  memory_support[]
  goal_context_bias[]
  sensor_precision
  prior_precision
  context_gain
  confidence
  status: PROVISIONAL|STABLE|UNKNOWN|CONFLICT|REOPENED
}`

The key difference from the current Retina stack is that a CLIP/YOLO/BLIP result does not immediately become a fact string. It becomes one piece of evidence or one provisional hypothesis with explicit dependency lineage.

### W — World Integration Plane

Persistent scene/object state. This is where the system decides whether a visual candidate corresponds to an existing world entity, a new entity, an unknown entity, or a transient artefact.

`WorldVisualEntity {
  entity_id
  semantic_identity?
  current_visibility_state
  spatial_state
  attributes_with_evidence[]
  relations_with_evidence[]
  last_positive_evidence_epoch
  last_explicit_negative_epoch?
  uncertainty
  provenance
  predecessor/split/merge refs
}`

Required visibility states:

- `VISIBLE_CONFIRMED`
- `VISIBLE_UNCERTAIN`
- `OCCLUDED`
- `OUT_OF_FOV`
- `ABSENT_EXPLICIT_NEGATIVE`
- `UNKNOWN`
- `CONFLICT`
- `SENSOR_DEGRADED`
- `STALE`
- `REVOKED_DERIVATION`

This prevents a common temporal category error:

`not currently observed != absent`.

### G — Global Workspace Projection Plane

The PerceptualField can change continuously without forcing the 4B or GWT to inspect every change. A visual candidate enters the workspace only if its expected global value exceeds cost and local resolution is insufficient.

Candidate ignition features:

- surprise/prediction error;
- unresolved uncertainty;
- novelty/change;
- goal relevance;
- risk/threat;
- cross-modal conflict;
- action consequence;
- object/world inconsistency;
- explicit user/task query;
- expected information gain from global reasoning.

No single scalar is currently frozen. The Harness must compare vector policies, simple weighted policies and learned/bandit policies.

Existing GWT custody remains mandatory:

`candidate -> selection -> broadcast -> delivery -> reconstruction -> uptake -> causal use -> outcome -> re-entry`.

A visual episode is not successful merely because a visual fact was broadcast.

### A — Active Sensing Plane

Perception becomes action-capable when FRANK can decide which additional evidence is worth acquiring.

Candidate `SenseAction` types:

- higher-resolution crop;
- alternate crop/region;
- OCR retry with different preprocessing;
- open-vocabulary detector invocation;
- fine attribute classifier;
- temporal accumulation;
- refresh anchor frame;
- use another camera/source;
- move/zoom camera where physically available;
- ask user for viewpoint/clarification;
- invoke a more expensive model only when allowed by policy.

Decision candidate:

`a* = argmax_a E[Delta uncertainty(a) + task_value(a) + safety_value(a) - compute_cost(a) - latency_cost(a) - action_risk(a)]`

This equation is a research scaffold, not frozen semantics.

### R — Receipt/Audit Materialization Plane

`VisualPercept` is generated here when a stable inspectable snapshot is needed.

It must preserve:

- exact sensor evidence refs;
- exact hypothesis/world state refs;
- prior vs sensor contribution;
- unresolved alternatives;
- model/transform versions;
- GWT/use/outcome refs;
- explicit nondeterminism when deterministic reconstruction is impossible.

This plane allows the hot path to stay sparse while the Harness can still produce a complete explanatory trace.

## 3. Multi-timescale execution

The one-module target should not imply one clock.

Candidate rates:

### T0 — sensor ingress
As fast as device/source produces useful deltas. No semantic global work required.

### T1 — local perceptual maintenance
Fast change detection, tracks, local evidence refresh, stale timers, cheap uncertainty update.

### T2 — semantic hypothesis update
Triggered by meaningful change, uncertainty or track events; may call CLIP/detector/OCR/dense encoders on bounded regions.

### T3 — GWT/model reasoning
Only when the visual state has global value or cannot resolve locally.

### T4 — consolidation
Slower reconciliation into persistent ClayGraph/UnifiedDB memory, summaries, long-term statistics and learning/evaluation data.

The Harness must measure whether this asynchronous structure creates unacceptable ordering nondeterminism. Epoch/source identities and deterministic replay contracts are therefore architectural, not optional logging.

## 4. Temporal field update

A minimal candidate update can be represented as:

`E_t = sensor_delta(S_t, S_(t-1), epoch_t)`

`P_t = settle(E_t, P_(t-1), W_(t-1), memory_t, goals_t)`

`W_t = reconcile(W_(t-1), P_t, explicit_negative_t, visibility_t)`

Key rules:

1. positive evidence may create/strengthen a hypothesis;
2. missing evidence alone causes age/uncertainty growth, not immediate absence;
3. explicit negative evidence can rapidly reduce a visibility belief;
4. occlusion/out-of-FOV preserve identity while weakening current visibility;
5. strong contradiction reopens a previously stable interpretation;
6. derived state is invalidated if its upstream evidence/transform is revoked;
7. world prior can change hypothesis probability but cannot mint evidence.

## 5. Precision and prior-dominance control

The candidate must expose at least three independent influence families:

`bottom_up_precision`
`world_or_learned_prior_precision`
`goal_context_gain`

A useful diagnostic candidate is a `prior_dominance` readout, for example a normalized fraction of total decision support supplied by priors/context rather than current evidence. The exact formula is open.

Tripwire behavior:

- high prior dominance + low sensor precision -> maintain alternatives / UNKNOWN or request active sensing;
- high prior dominance + strong contradicting sensor evidence -> force REOPEN/CONFLICT;
- high goal gain must never increase evidence truth score;
- no-signal input must not settle to a familiar object solely because the world model expects it.

## 6. Object continuity and anti-ghost semantics

A persistent visual system must solve detector flicker without creating permanent ghosts.

Candidate rules:

- one or several missed detections do not delete a tracked world entity;
- explicit clear negative evidence decays visibility much faster;
- track identity and semantic label are separate — a dog incorrectly labelled `teddy bear` can remain the same entity while its type hypothesis changes;
- temporal association uses geometry, motion, dense features and world constraints under a merge/split audit trail;
- disappearance after action is a high-value outcome candidate and should receive post-action re-entry;
- stale timers depend on scene/source dynamics rather than one universal TTL.

## 7. Existing Digital Retina decomposition

The current 7k+ LoC Retina code should become a library of independently schedulable evidence transforms rather than one monolithic analysis request.

### Keep/reuse as candidate kernels
- input decoding/source limits;
- CLIP-style image/text encoding;
- object detection;
- DINO/dense visual representation;
- OCR engines;
- face/region/colour/composition transforms where justified;
- screenshot/UI-specific fast routes;
- test fixtures and benchmark images;
- warm-up/model caching infrastructure.

### Change semantic role
- YOLO output: evidence/hypothesis, never truth;
- CLIP top-k: evidence over alternatives, never truth;
- OCR: observed text, never instruction authority;
- region caption: conditional evidence generator with upstream dependency;
- free-form narrative: projection, not canonical perception;
- hand-written relation heuristics: provisional relations with evidence refs;
- GoL descriptors: optional experimental features only.

### Likely remove from default hot path unless proven
- broad `top_k=800` concept emission;
- every-frame full vocabulary scoring;
- always-on free-form captioning;
- repeated semantic work on unchanged regions;
- unproven cortex/GoL analogy as architecture justification.

## 8. Modern-kernel benchmark lane

Do not rewrite everything around newer models. Build a stable adapter benchmark and compare:

### Image-text encoders
- existing OpenAI CLIP-B/32;
- MobileCLIP2 candidates for edge/mobile efficiency;
- SigLIP2 where localization/dense semantics may matter.

### Dense features
- current DINOv2;
- DINOv3 small/distilled candidates where license/runtime permit.

### Detection
- current YOLOv8n closed-set baseline;
- YOLO-World/open-vocabulary candidate;
- open-world/uncertainty-aware candidate where executable and appropriately licensed.

Each candidate must be measured on the **same frozen Retina test corpus** and project hardware for:
accuracy, OOD/unknown, calibration, latency, RAM, cold/warm start, energy where available and derived-state utility. Published benchmark wins do not promote a component.

## 9. ClayCode requirements

ClayCode BASE must be able to represent, without prose escape hatches:

- sensor/source epochs;
- immutable evidence receipts;
- sparse spatial/temporal deltas;
- typed uncertainty/precision;
- alternatives and exclusions;
- visibility states;
- evidence dependency lineage;
- provisional/stable/reopened hypotheses;
- persistent world entities;
- n-ary spatial/action relations;
- GWT visual candidate/readout contracts;
- active sensing requests and cost/value metadata;
- materialized VisualPercept receipts;
- invalidation/revocation cascades;
- counterfactual visual interventions.

If the released ClayCode semantics cannot express these, the Retina Harness must produce a concrete executable language counterexample rather than requesting language churn abstractly.

## 10. ClayGraph / UnifiedDB requirements

ClayGraph:
- persistent entity identity;
- spatial/temporal relation topology;
- active vs latent perceptual assembly;
- evidence/hypothesis/world node distinction;
- temporal relation decay/invalidation;
- alternative hypotheses and conflict edges;
- visual-to-memory causal-use paths.

UnifiedDB:
- exact sensor evidence and event history remain replayable;
- derived embeddings/features may be rebuildable sidecars;
- current world snapshot and historical validity are distinct;
- transaction/snapshot identity spans evidence -> hypothesis -> world -> GWT episode;
- querying `what did FRANK see?` must distinguish raw observation, inferred percept and persistent belief.

## 11. H1/H2/H3 validation

### H1 Reference Harness
Implement old stateless Retina baseline and new PerceptualField reference semantics in normal deterministic host code. Freeze Golden visual traces and interventions.

### H2 Clay Harness
Express the same semantics in ClayCode; differential-test state transitions, not only final labels.

### H3 One-Module FRANK
Fuse sensor ingress/perceptual runtime into one module/binary where host APIs permit. Compare against out-of-process H1/H2 physical topology while preserving semantic equivalence.

A boundary may remain physically separate only if measured safety/performance/platform evidence justifies it. Physical separation never recreates a second semantic architecture.

## 12. Falsification posture

This architecture loses if a simpler design dominates it.

In particular, promotion must fail if any of these baselines is Pareto-superior:

- optimized stateless Retina + cache;
- simple detector + tracker + periodic anchors;
- explicit separate Retina process;
- feedforward typed field without recurrence;
- concise caption projection;
- native VLM reference where system constraints permit it as comparator.

The owner-fixed target of dissolved semantics remains; a negative result may still show that some **physical** separation or simpler recurrence strategy is superior.
