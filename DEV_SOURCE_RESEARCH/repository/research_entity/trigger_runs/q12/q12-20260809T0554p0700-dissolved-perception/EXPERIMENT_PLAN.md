# Experiment Plan — Dissolved Perception / Sensor-In-Module

Run: `q12-20260809T0554p0700-dissolved-perception`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol

## Goal

Determine whether FRANK should realize visual perception as an in-module distributed `PerceptualField` with bounded recurrent world/memory/goal coupling, while keeping `VisualPercept` primarily as an audit/materialization receipt.

## Baselines

### A — Explicit Retina boundary
`sensor -> historical/current Retina feature extraction -> fully materialized VisualPercept -> attention/GWT/cognition`

### B — Dissolved feedforward field
`sensor ingress -> typed perceptual state deltas -> attention/GWT/cognition`

No world/memory/goal feedback into perceptual settling.

### C — Dissolved recurrent field
`sensor ingress -> typed perceptual deltas <-> bounded world/memory/goal/context feedback -> attention/GWT/cognition`

### D — Hybrid fast path
C plus change/event-driven updates and periodic/conditional full anchor evidence.

## E0 — Historical baseline reproduction

Inputs:
- existing Digital Retina implementation/fixtures;
- current project hardware where available.

Measure:
- cold/warm p50/p95/p99 latency;
- CPU/RAM;
- structured field accuracy;
- false positives;
- missing model/weight failure behavior.

Purpose: stop using historical 1.5–2.0 s/image figures as current truth; create a reproducible baseline.

## E1 — Boundary-dissolution A/B

Hold constant:
- sensor input;
- feature extractors;
- semantic content;
- model fixture;
- downstream task.

Compare A vs B.

Measure:
- sensor->semantic-state latency;
- bytes copied/serialized;
- allocations/state writes;
- CPU/RAM;
- task accuracy/calibration;
- deterministic replay;
- provenance completeness.

DP-H1 provisional pass criterion:
- B improves p95 latency or state movement by at least 20% on at least two representative workloads;
- task accuracy loss <=2 percentage points;
- provenance/replay validation = 100% for required receipts.

If this criterion fails, keep the explicit boundary or use a hybrid.

## E2 — Recurrence and world-model factorial

Factors:
- recurrence OFF/ON;
- world-model feedback OFF/ON;
- memory feedback OFF/ON;
- goal/context feedback OFF/ON.

Datasets/fixtures:
- unoccluded easy objects;
- 25/50/75% occlusion;
- clutter/figure-ground scenes;
- ambiguous/bistable scenes;
- context-congruent scenes;
- context-incongruent scenes;
- novel/unknown objects.

Outputs:
- recognition accuracy;
- calibration/Brier or equivalent;
- correction latency;
- wrong-attractor persistence/hysteresis;
- compute iterations/cost.

Key discriminator:
- compare recurrent world-model coupling against a simpler late contextual reranker using matched information and compute.

## E3 — Prior-induced false perception stress test

Factorial:
- sensor quality: high / degraded / absent;
- prior: correct / misleading / neutral;
- feedback precision: low / adaptive / high.

Mandatory conditions:
- no-signal;
- blank/static scene;
- unknown object;
- adversarially misleading context;
- stale world state;
- context swap after partial settling.

Fail condition:
- top-down feedback produces materially more high-confidence false entities/relations than explicit or precision-bounded baselines.

Required architecture response:
- explicit `UNKNOWN`, `CONFLICT`, evidence-vs-prior precision and ability to reopen a settled interpretation.

## E4 — Change/event fast-path benchmark

Compare:
1. fixed-rate full frames;
2. frame-derived change regions only;
3. event-camera stream if hardware becomes available;
4. hybrid change/events + anchor frames.

Workloads:
- static UI;
- slowly changing page/text;
- fast cursor/object motion;
- sudden object appearance;
- camera/viewpoint motion;
- lighting changes;
- long idle interval.

Measure:
- salient-event recall;
- false event rate;
- state update bandwidth;
- CPU/power proxy;
- latency;
- static-semantic retention.

Expected risk:
- change-only misses static/slow semantics; hybrid should rescue with anchors.

## E5 — GWT escalation policy

Compare:
- every-frame/full-percept candidacy;
- low-level novelty threshold;
- high-level prediction-error threshold;
- goal-conditioned threshold;
- combined policy.

Measure:
- GWT ignition frequency;
- meaningful downstream causal-use rate;
- missed task-relevant events;
- model invocations/tokens;
- action latency;
- false alarm/attention churn.

Do not score broadcast existence as success; require receiver uptake/causal use/outcome/re-entry receipts.

## E6 — Materialized receipt vs hot-path object

Test whether `VisualPercept` can be generated on demand from the event/state lineage.

Requirements:
- exact source/frame/event identity;
- timestamp/epoch;
- feature/object/relation evidence;
- uncertainty;
- transformation lineage;
- world/memory/context contributions;
- selected interpretation and alternatives;
- GWT/action/memory causal links.

Pass:
- required trace can be regenerated/replayed with identical deterministic fields or explicit nondeterminism receipts.

Failure:
- debugging/replay becomes weaker than explicit VisualPercept baseline.

## E7 — 4B boundary/context-efficiency test

Conditions:
- raw image/VLM-style heavy input where feasible;
- caption baseline;
- explicit full VisualPercept;
- bounded PerceptualField assembly.

Matched tasks:
- identify relevant visual change;
- answer state-dependent question;
- detect conflict with world model;
- choose action;
- preserve object continuity across turns.

Measure:
- model-visible tokens/bytes;
- inference latency;
- task accuracy;
- unsupported assertion rate;
- calibration;
- world-state consistency.

## E8 — H3 sensor topology differential

Topology 1: external Retina process/service.  
Topology 2: in-process linked sensor ingress and perceptual fast path.  
Topology 3: one binary with isolated threads/rings/capabilities.

Measure:
- sensor->state and sensor->action p50/p95/p99;
- IPC/serialization;
- queueing/buffer latency;
- failure containment;
- restart/recovery;
- memory contention;
- dropped/stale frames/events.

The physical device/OS driver may remain external; do not count unavoidable kernel/device boundaries as cognitive modules.

## Required Harness instrumentation

Every trial emits:
- sensor evidence hash/identity;
- capture/arrival/ingress timestamps;
- perceptual state-delta hashes;
- prior/world/memory/goal inputs and precision weights;
- settling iterations/state transitions;
- alternative interpretations;
- GWT candidate/selection/delivery/uptake/causal-use/outcome/re-entry;
- optional materialized VisualPercept receipt;
- action/outcome;
- latency/cost/resource receipts.

## Promotion rule

Architecture target is owner-fixed, but individual mechanisms are selected by evidence. A failed hypothesis produces a negative result and may justify retaining a localized boundary, periodic anchor, weaker recurrence or explicit materialization on specific platforms/workloads.
