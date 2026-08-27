# Retina Deep Research Foundation — Persistent Clay-Native Visual Perception

**Status:** ACTIVE RESEARCH FOUNDATION  
**Created:** 2026-08-09  
**Origin actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
**Owner-fixed architecture boundary:** `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`  
**Historical implementation:** `gschaidergabriel/digital-retina`

## 0. Mission

Research how FRANK can become a genuinely **functionally multimodal persistent agent** without requiring visual cognition to remain a separate caption-producing service or requiring the underlying Qwen-class text/Clay model to become a native pixel-token VLM.

The fixed target is already set by the project owner: Digital Retina dissolves semantically into the one-module FRANK runtime as far down the sensor/software stack as technically feasible. The open scientific task is to discover the smallest, fastest, safest and most causally testable mechanism that realizes that target.

The central research question is therefore not:

> Which image model should produce the best caption?

It is:

> How should visual evidence continuously alter a persistent cognitive state so that recognition, uncertainty, memory, world modelling, attention, action and re-entry form one measurable dynamical system?

## 1. Historical baseline reconstructed

The current standalone Digital Retina repository is a substantial CPU-oriented engineering system, not a paper-only idea. Its public API is explicitly stateless: image bytes/path/URL enter and a structured dictionary leaves. The current implementation loads multiple vision kernels and semantic heuristics, including CLIP, YOLO, DINO, OCR, face/emotion, scene vocabularies, region captioning, composition, colour and Game-of-Life-derived pattern descriptors. The README reports roughly 900 ms p50 on a 4-vCPU EPYC for the current full path, with a shorter screenshot path. Earlier comments in `frank_eye.py` describe lighter subpaths, so current hardware/runtime benchmarking must resolve configuration drift rather than trust either number as universal.

Historical evaluation is unusually valuable because it contains both optimistic and adversarial records.

### Historical positive evidence

The May working paper reports a multi-stage CPU-only system with held-out oracle phrase evaluation. The original five-round protocol reports 82.4% phrase coverage over 47 unseen images / 1,196 phrases and approximately 1.5–2.0 s/image on a 4-vCPU host. The paper also explicitly reports realistic-negative false positives and warns that coverage does not establish compositional correctness.

### Historical negative evidence

The May-26 honest hard-set audit is more diagnostic than the headline coverage number. On 12 adversarial images it initially measured only 35.3% strict phrase coverage and documented recurrent failure families:

- fixed YOLO class vocabulary misses long-tail objects;
- detector mistakes become downstream caption mistakes;
- art/illustration/anime are OOD for multiple components;
- OCR fails on painted/stylized text;
- attribute and spatial binding are weak;
- region captioning sometimes helps but can amplify a wrong upstream box;
- whole-image CLIP vocabulary can contain the concept without producing a correct object-relation binding.

A later hard-set report reached 87.8% strict-substring coverage after widening emission to `top_k=800`, lowering the CLIP threshold and adding a large Tier-5 vocabulary explicitly built from per-image miss analysis. This is useful engineering evidence for surfaceability but it is **not clean held-out generalization evidence** for the final post-tuning hard-set. The same historical source family also shows that a CLIP threshold of 0.20 can produce a very high realistic-negative false-positive rate. Therefore neither 94.6% CLIP-lenient coverage nor the tuned 87.8% strict result may be used as a truth-accuracy acceptance threshold without new frozen held-out evaluation.

This negative-result lineage becomes a permanent Retina research constraint.

## 2. External research synthesis

### 2.1 Recurrent vision

Recent controlled work on occluded object recognition finds computations in recurrent networks that are absent from matched feedforward networks, including an `explaining-away` mechanism where knowledge of an occluder helps recover the occluded object representation. This supports recurrence as a plausible engineering mechanism for ambiguous/occluded perception, but does not establish that FRANK's proposed recurrence is correct.

### 2.2 Joint object-scene inference and predictive processing

A 2024 Nature Reviews Psychology synthesis describes object and scene processing as bidirectionally interacting and interpretable as joint probabilistic inference: scene hypotheses can facilitate or impair object perception and objects constrain scene hypotheses. This strongly supports testing the owner's intuition that world state and current visual evidence should interact **inside perception**, rather than only after a caption is produced.

The safety consequence is equally important: priors can bias perception. FRANK must therefore preserve the contribution and precision of bottom-up evidence separately from world/model prior and task/goal bias.

### 2.3 Temporal continuity

Research on continuity fields and visual memory supports the general principle that recent state can stabilize noisy perception. Robotics and dynamic scene-graph work independently demonstrate real-time incremental persistent scene representations. These are useful analogues for object permanence and world-state maintenance, but FRANK must distinguish biological analogy from engineering mechanism.

### 2.4 Event/change-driven sensing

Event-camera research establishes a real latency-bandwidth advantage for asynchronous change sensing. A 2024 Nature system combined 20-fps RGB with event sensing and achieved the latency of a much higher-rate camera while retaining low bandwidth in its automotive task. Event streams are not sufficient for all static/slow information, so the strongest current FRANK candidate is hybrid `anchor evidence + change/event deltas`, not event-only vision.

State-space models for event cameras further support carrying state across asynchronous events and multiple timescales rather than reconstructing independent dense frames at every step.

### 2.5 Long-horizon streaming agents

The August-6-2026 StreamArena work is directly relevant to FRANK: recent-frame-only systems cannot recover distant events; text-only conversion loses visual evidence; repeated compression erodes fine detail. Its two-tier persistent approach supports the broader idea that streaming agents need stateful visual memory rather than an endless sequence of isolated descriptions. It does not prove ClayGraph or PerceptualField specifically.

### 2.6 Active perception

Next-best-view and active-perception research treats perception as an action-selection problem: the system can choose a view or sensing operation that is expected to reduce uncertainty. FRANK can generalize this beyond camera movement to cheap vs expensive visual actions: crop/zoom, region re-encode, OCR, open-vocabulary detection, higher-resolution anchor, alternate camera, or a model call.

### 2.7 Open-world recognition

Open-set and open-world detection research reinforces that real systems must represent `unknown`, not only distribute confidence over known classes. Uncertainty-aware open-set detectors improve unknown recall in published benchmarks. FRANK therefore treats UNKNOWN/CONFLICT as successful epistemic states, not failures to force a label.

### 2.8 Efficient visual kernels

The historical Retina components are no longer the only plausible edge-friendly kernels. MobileCLIP2 provides modern small image-text encoders with strong mobile latency claims; SigLIP2 provides improved dense/localized vision-language features; YOLO-World and later open-world detectors directly address fixed-class object detection; newer DINO families provide dense self-supervised features. These are **benchmark candidates**, not automatic upgrades. All must be tested on the actual x86/Android/device targets, licensing constraints and Retina workloads.

## 3. Research object: PerceptualField

The proposed PerceptualField is not a database table, tensor, graph or monolithic object. It is a logical view across typed, provenance-bound state whose physical lowering may be optimized by ClayCode/UnifiedDB.

The strongest current decomposition is:

### Plane E — Evidence

Immutable or append-only observations tied to source identity, time/epoch, coordinates, transformation lineage and bottom-up precision. Examples: frame/crop hash, OCR tokens, detector box, embedding score, optical flow/change region, low-level feature receipt.

**Hard law:** world state may interpret evidence but may not rewrite evidence history.

### Plane P — Perceptual inference

Set-valued hypotheses derived from current evidence + temporal state + priors. Objects, attributes, relations, alternatives, contradictions and uncertainty live here. A hypothesis records which part came from sensor evidence, prior/world state and goal/context bias.

### Plane W — World integration

Persistent entities and relations that have passed admissibility/temporal consistency rules. These may live in ClayGraph/UnifiedDB and remain connected to their evidence/provisional predecessors. World state can outlive a frame, but it must encode whether an entity is visible, occluded, out-of-view, stale, explicitly absent or uncertain.

### Plane G — Global projection

Only a bounded Assembly enters GWT/model-visible cognition. Local visual processing may update E/P/W without igniting the workspace. GWT receives novelty, unresolved contradiction, goal relevance, risk, action consequence, cross-modal conflict or explicit demand.

### Plane A — Active sensing

When the current evidence is insufficient and the uncertainty matters, FRANK can select the next sensing computation/action by expected information gain and task value relative to cost/risk.

### Plane R — Audit materialization

`VisualPercept` remains an on-demand deterministic or explicitly nondeterministic receipt reconstructed from the relevant evidence/state lineage for Harness replay, training, debugging, external projection or causal episode custody.

## 4. Essential state distinctions

The following must never collapse into one Boolean `seen` state:

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

The semantic reason is simple: no observation is not negative evidence. If FRANK sees a cup, then turns away, the cup is not thereby absent. If the camera returns to the table and the cup is clearly not there, that is materially different evidence. This distinction is central to object permanence without ghost-object hallucination.

## 5. Candidate dynamics

No final equation is promoted. The research candidate can be expressed abstractly as a partially observed recurrent state estimator:

`E_t = observe(sensor_t, source_epoch)`

`P_t = infer(E_t, P_(t-1), W_(t-1), M_t, G_t, action_t)`

`W_t = integrate(P_t, W_(t-1), admissibility, temporal_rules)`

`I_t = ignition_value(P_t, W_t, goals, risk, uncertainty, cost)`

`A*_t = argmax_a E[information_gain(a) + task_value(a) - compute_cost(a) - action_risk(a)]`

The key scientific variable is not whether these exact functions are used; it is whether maintaining the **separable causal contributions** yields better accuracy, calibration, latency, persistence and downstream action than simpler baselines.

## 6. Architecture anti-patterns

Retina research must actively reject or test against:

1. `image -> one caption -> LLM` as the only semantic path;
2. treating embedding similarity as truth;
3. forcing top-1 known classification under OOD;
4. using current world belief as if it were sensor evidence;
5. rebuilding the whole scene every frame when nothing changed;
6. keeping stale world objects forever because they were once seen;
7. deleting objects merely because they left the field of view;
8. letting OCR/visual text become instruction authority;
9. allowing one wrong detector box to mint many untracked derived facts;
10. optimizing phrase coverage after looking at the test misses;
11. treating workspace broadcast as proof of downstream causal use;
12. treating recurrence, complexity or integration as evidence of phenomenal consciousness.

## 7. Current component strategy

The existing Digital Retina code is not discarded. It becomes a **kernel library and historical oracle baseline**.

Likely reusable kernels include:

- image/source normalization;
- CLIP-style semantic scoring;
- object detection;
- DINO/dense features;
- OCR;
- colour/spatial feature extraction;
- screenshot/UI specialization;
- selected relation and region transforms;
- benchmark/evaluation scaffolding;
- deterministic warm-up/runtime instrumentation.

Likely demoted from hot-path semantic truth:

- free-form narrative concatenation;
- broad top-k vocabulary emission as truth;
- downstream facts that do not preserve dependency provenance;
- always-on caption generation;
- any threshold whose only support is tuned phrase coverage.

The Game-of-Life stage receives no privileged status. Cellular automata have precedent as texture descriptors, but current evidence does not justify Conway GoL as a special general vision mechanism. It remains a falsifiable feature family and must compete against cheaper/more conventional texture and dense-feature baselines.

## 8. Scientific acceptance dimensions

No single Retina score is allowed. Every architecture candidate is evaluated on a vector:

### Perception correctness
- object/entity accuracy;
- attribute and spatial binding;
- relation correctness;
- OCR/text correctness;
- compositional tasks;
- occlusion/ambiguity completion;
- calibration and abstention;
- unknown/OOD detection.

### Temporal correctness
- track continuity;
- object permanence;
- explicit absence detection;
- stale/ghost duration;
- scene-change detection;
- post-action outcome attribution.

### Causal/GWT correctness
- candidate creation;
- ignition selection;
- receiver delivery/reconstruction/uptake;
- causal use;
- outcome;
- re-entry;
- lesion/rescue.

### Performance
- sensor-to-state p50/p95/p99;
- sensor-to-action latency;
- CPU/GPU/NPU utilization;
- RAM/VRAM;
- bytes copied/serialized;
- energy/thermal on edge/mobile;
- 4B token/context cost;
- state/write amplification.

### Recovery/security
- crash/restart fidelity;
- deterministic replay;
- stale/replay rejection;
- prompt-injection resistance;
- authority isolation;
- model/component version invalidation.

## 9. Required baselines

At minimum compare:

A. current historical stateless Retina service + materialized output;
B. same kernels in-process but still feedforward/stateless;
C. PerceptualField with temporal persistence but no top-down world recurrence;
D. bounded recurrence with explicit evidence/prior separation;
E. hybrid anchor/change fast path;
F. simple tracker + periodic detector baseline;
G. where feasible, a native VLM reference as an **evaluation comparator only**, never silently inserted into the target serving architecture.

## 10. Deep-run research status

This foundation opens a dedicated visual-perception domain because the problem can no longer be represented cleanly as only `interfaces_io`, `frank_gwt` or generic `synthetic_clay`. The recurring invariants — evidence vs prior, temporal visibility states, active sensing, persistent object identity, visual GWT custody and streaming cost — require their own shard while remaining bidirectionally connected to every affected FRANK branch.

The first deep foundry run is:

`research_entity/retina/runs/retina-20260809T0615p0700-deep-foundry/REPORT.md`

Its hypotheses remain OPEN unless independently supported or experimentally closed. Historical measurements remain historical evidence, not current Clay 0.1 release evidence.
