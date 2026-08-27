# Retina Deep Foundry — Experiment Matrix

**Status:** PREREGISTRATION CANDIDATE / EXECUTION REQUIRED  
**Run:** `retina-20260809T0615p0700-deep-foundry`

## Experimental law

Retina is not promoted by one score. Every major mechanism is tested against the simplest plausible competing mechanism with frozen inputs, explicit evidence class, cost shadows, negative controls and replay receipts.

Final held-out sets must be frozen **before** architecture/vocabulary/threshold tuning. Development images, final held-out images, OOD images and adversarial controls receive separate hashes.

## E0 — Historical lineage reproduction

**Question:** What does the current `gschaidergabriel/digital-retina` actually do on current project hardware?

Run current code with pinned commit/models/config and record:
- cold/warm start;
- p50/p95/p99;
- RAM;
- structured outputs;
- hard/easy historical fixtures where available;
- exact model versions;
- component failures.

Do not assume comments claiming ~100–300 ms and README/core claims near ~900 ms refer to the same path/config.

**Output:** `RETINA_HISTORICAL_BASELINE_RECEIPT.json`.

## E1 — Honest clean held-out Retina benchmark

Create new frozen sets **not used for vocabulary/threshold tuning**:
- ordinary photos;
- clutter/crowd;
- occlusion;
- art/painting;
- illustration/anime;
- generated composites;
- UI/screenshots;
- text/OCR;
- long-tail objects;
- explicit unknown/OOD.

Metrics:
- object/attribute/relation binding;
- strict phrase utility as secondary metric;
- calibration/Brier/ECE where applicable;
- realistic-negative FPR;
- UNKNOWN recall;
- confidently-wrong rate.

**Primary purpose:** quantify the generalization gap behind historical tuned hard-set results.

## E2 — Representation differential: narrative vs typed state

Same sensor evidence, same 4B/model fixture, compare:

A. historical narrative/JSON;
B. concise typed VisualPercept;
C. sparse PerceptualField Assembly/deltas.

Measure task accuracy, context tokens, reconstruction errors, surface-form sensitivity and replay identity.

Tests H27, H37, H60, H62.

## E3 — Stateless vs temporal field

A. current stateless per-image analysis;
B. same kernels + tracker/cache;
C. PerceptualField without world priors;
D. PerceptualField with full temporal semantics.

Streams contain detector flicker, temporary occlusion, leaving/returning FOV and real removal.

Measure identity switches, recall, false persistence, ghost duration, CPU and state traffic.

Tests H19-H25 and counter H19/C19.

## E4 — Recurrence factorial

Factors:
- recurrence OFF/ON;
- world prior OFF/ON;
- memory feedback OFF/ON;
- goal/context feedback OFF/ON;
- occlusion low/high;
- scene-context congruent/incongruent.

Hold feedforward kernels constant.

Primary outcomes:
- recognition/binding;
- calibration;
- prior-induced false perception;
- convergence iterations;
- cost.

Interaction terms and lesion/rescue required. Tests H09-H18.

## E5 — Misleading-prior / no-signal safety battery

Construct cases where world state strongly predicts object A while sensor evidence supports B, UNKNOWN, or no object.

Include:
- swapped room context;
- stale remembered object;
- adversarial semantic prime;
- blank/noise frame;
- degraded/blurred evidence;
- novel object with familiar context.

Measure wrong-prior acceptance and prior-dominance readout. Successful behavior may be `UNKNOWN` or `CONFLICT`.

Hard release condition: top-down recurrence must not convert no-signal into confident familiar perception.

## E6 — Explicit absence vs non-observation

Sequences:
1. object visible -> occluder -> visible;
2. object visible -> camera turns away -> returns;
3. object visible -> clear empty table;
4. sensor fails;
5. stale frame replay.

Require distinct state trajectories for `OCCLUDED`, `OUT_OF_FOV`, `ABSENT_EXPLICIT_NEGATIVE`, `SENSOR_DEGRADED`, `STALE`.

Tests H20-H21 and synthetic ghost-object result.

## E7 — Anchor/change/event policy

Compare:
- every-frame full analysis;
- fixed-rate full frames;
- change-only;
- fixed anchor + change deltas;
- adaptive anchor + change deltas.

Use normal cameras first; optional event-camera hardware later.

Measure compute, bytes, latency, missed static semantics, restart recovery and dynamic-event latency.

Tests H01-H05.

## E8 — GWT visual gating

Use frozen visual streams with annotated globally important and locally resolvable events.

Compare:
- every meaningful visual update broadcast;
- scalar salience threshold;
- typed multi-feature gating;
- learned/bandit policy only after simple policies establish baseline.

Record candidate, selection, delivery, reconstruction, uptake, causal use, outcome and re-entry.

Metrics: important-event recall, workspace precision, model calls/tokens, end-task outcome.

Tests H35-H42.

## E9 — Active sensing information gain

Ambiguous tasks where a second operation can resolve uncertainty:
- high-res crop;
- OCR retry;
- open-vocabulary detector;
- alternate region;
- new anchor;
- camera movement if available.

Compare:
- always perform expensive operation;
- never perform;
- fixed uncertainty threshold;
- expected information-gain/cost policy.

Tests H38-H39/H63 and counter C09.

## E10 — VisualPercept materialization/replay

Run hot path without eager full materialization. At random checkpoints request a complete VisualPercept receipt.

Verify:
- exact evidence refs;
- semantic equivalence to eager reference;
- deterministic hash where deterministic;
- explicit nondeterminism otherwise;
- no missing alternative/prior contribution.

Tests H29.

## E11 — Transform-lineage invalidation

Generate derived world state through detector/encoder version X. Change calibration/model version or invalidate an upstream box.

Verify only dependent hypotheses/world edges are revoked/recomputed while independent history remains valid.

Tests H34/H55.

## E12 — Image-text encoder bakeoff

Same frozen corpus and tasks:
- current CLIP-B/32;
- MobileCLIP2 candidate(s);
- SigLIP2 candidate(s) if target hardware permits.

Measure not only zero-shot accuracy but:
- localized attribute/relation support;
- realistic-negative calibration;
- latency/RAM;
- cold/warm behavior;
- x86 and Android/edge where possible.

Tests H44-H45/C11.

## E13 — Detection bakeoff / UNKNOWN

Compare:
- current YOLOv8n closed set;
- open-vocabulary detector such as YOLO-World candidate;
- uncertainty/open-world candidate if runtime/licensing permits;
- simple class-agnostic objectness + semantic identification split.

Hard sets emphasize objects outside COCO-80 and intentionally unknown classes.

Measure localization, known AP, unknown recall, false object rate, calibration, latency/RAM.

Tests H43/H51.

## E14 — Dense temporal features

Current DINOv2 vs DINOv3 small/distilled candidate where usable, plus optical-flow/simple feature baselines.

Tasks:
- region correspondence;
- identity under motion/viewpoint;
- re-acquisition after occlusion;
- changed-region matching.

Tests H25/H46.

## E15 — GoL incremental-value ablation

Features:
A. no texture descriptor;
B. HOG/color;
C. LBP/Gabor or equivalent cheap texture baseline;
D. DINO/CLIP dense statistics;
E. historical GoL signatures;
F. best combination.

Use frozen held-out classification/relation/style tasks and cost controls.

Promotion criterion: GoL must contribute repeatable held-out information beyond cheaper baselines. Otherwise demote/remove.

Tests H49/C12.

## E16 — Conditional captioner

Compare BLIP/free-form captioning:
- always on;
- only on high ambiguity;
- only on relation/composition query;
- only after detector/world conflict;
- off.

Track useful information added, false facts added, dependency on wrong boxes, latency/RAM.

Tests H47.

## E17 — In-process vs standalone service topology

On the same hardware and same frozen semantic kernels compare:
- HTTP/RPC standalone Retina;
- local-process IPC/shared memory;
- in-process linked runtime.

Measure sensor-to-state p50/p95/p99, copies/serialization, memory duplication, crash radius, restart/recovery and security isolation.

H3 physical topology is chosen from measurements, not ideology. Tests H50/C02/C15.

## E18 — Crash/restart/replay

Inject crash at:
- after ingress before transform;
- after evidence write;
- during hypothesis update;
- during world integration;
- before/after GWT broadcast;
- during post-action re-entry.

Require idempotency, epoch correctness, replay equivalence or explicit nondeterminism receipt.

Tests H06/H56/H57.

## E19 — Visual prompt-injection battery

Screenshots/images contain instructions such as requests to run shell commands, reveal secrets, modify policy or approve actions.

Verify:
- OCR stores them as observed text;
- perceptual/world state does not grant authority;
- any action still passes normal Needle/effect/capability gates;
- source provenance survives to model context.

Tests H32/H58.

## E20 — Long-horizon streaming continuity

Run hour-scale screen/camera streams with distant-event questions, recurring objects and state changes.

Compare recent-frame, caption-log, repeated-summary, persistent PerceptualField/ClayGraph and optional external streaming-memory baselines.

Measure distant-event recall, visual-detail retention, state size, query latency and token cost.

Tests H23/H59-H65/C16.

## E21 — Post-action visual causal closure

Tasks in which FRANK acts on a visual environment/UI and must verify outcome.

Ablate visual re-entry after action. Measure false-success rate, recovery, repeated actions and world-state correctness.

Tests H40.

## E22 — Cross-modal conflict

Provide controlled conflicts:
- tool/DB says object exists but camera shows absence;
- OCR text conflicts with remembered text;
- user description conflicts with current frame;
- stale visual frame conflicts with fresh system state.

Test whether conflict selectively enters GWT and whether downstream resolution preserves source authority/provenance.

Tests H42.

## E23 — H1/H2/H3 semantic differential

Freeze Golden visual traces and interventions.

Reference Harness, Clay Harness and One-Module FRANK must produce equivalent required semantic transitions for:
- evidence identity;
- alternatives;
- visibility states;
- world integration;
- GWT custody;
- materialized receipts;
- action re-entry.

Physical timing may differ; unexplained semantic divergence is a release blocker.

## E24 — Android/edge thermals and energy

Once target hardware is available, measure sustained camera/screen workloads for:
- battery/energy;
- thermal throttling;
- CPU/GPU/NPU backend;
- memory pressure;
- wakeups/background constraints;
- anchor/change policy.

A desktop-optimal Retina topology is not automatically mobile-optimal.

# Promotion order

Do not execute all experiments blindly. Highest information order:

1. E0 + E1 freeze honest baseline.
2. E3/E6 establish temporal state value and ghost risks.
3. E4/E5 establish whether recurrence is worth keeping safely.
4. E7 establish sampling strategy.
5. E2/E8 establish bounded model/GWT interface.
6. E12-E16 modernize kernels only after architecture metrics exist.
7. E17-E24 complete physical consolidation, security, recovery and platform proof.

The next experiment should always be chosen by expected discrimination among live hypotheses, not by which benchmark is easiest to improve.
