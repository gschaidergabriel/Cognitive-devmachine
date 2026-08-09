# FRANK Thalamus — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: historical archaeology + current target synthesis; no canonical promotion

## T-0 — precursor problem: binary context inclusion

Historical design problem explicitly stated by the Thalamus implementation:
- earlier FRANK used a binary `slim/full` context choice;
- this could only include or suppress broad state blocks;
- it did not express modality-specific gain, novelty, habituation or breakthrough.

Thalamus was invented as a fast pre-model gate so the system could decide **how strongly each state channel should influence the next cognitive projection before the LLM sees it**.

---

## T-1 — first explicit Thalamus implementation

Creation commit: `ccebdc78f3c08013e08758c7386984cc5e70386f`, 2026-03-03.
File: `services/thalamus.py`.

Architecture at creation:
- in-process singleton, no service/port;
- design target `<3 ms` per `gate()`;
- nine channels:
  - `hardware`;
  - `mood`;
  - `user_presence`;
  - `aura`;
  - `qr_coherence`;
  - `perception_events`;
  - `service_health`;
  - `amygdala`;
  - `acc_conflict`.

Initial base gain / habituation time constants:
```text
hardware          0.5 / 120 s
mood              0.7 / 300 s
user_presence     0.9 /  60 s
aura              0.4 / 180 s
qr_coherence      0.4 / 180 s
perception_events 0.6 /  30 s
service_health    0.5 / 300 s
amygdala          0.8 /  60 s
acc_conflict      0.6 / 120 s
```

Global constants:
- relay threshold: `0.25`;
- warmup: first 5 gates relay all channels at gain 1.0;
- sampled logging every 20 calls unless burst/override;
- overload candidate: >=6 channels above gain 0.7;
- deprivation candidate: relay fraction <0.2 for >=5 calls;
- E-PQ overload cooldown 300 s, deprivation cooldown 600 s.

Initial cognitive-mode profiles:
- chat_active;
- idle_focus;
- idle_diffuse;
- consolidation;
- reflecting;
- gaming;
- entity_session.

The mode profile is top-down control: each channel receives a multiplicative attention weight based on current cognitive mode.

---

## T-2 — seven-stage gate algorithm

### Stage 1 — typed channel snapshots
Each modality is reduced into:
```text
ChannelSnapshot {
  name,
  raw_text,
  value_hash,
  numeric_value
}
```

The design already separates a semantic text projection from a numeric state used for gating.

### Stage 2 — novelty
For changed content:
- numeric delta compares current value with last relayed value;
- time since change and time since relay contribute;
- a burst is generated when a previously stable channel changes abruptly.

Representative historical condition:
```text
burst = time_since_change < 2 s
        AND time_since_relay > 120 s
        AND abs(delta) > 0.15
```

Historical novelty form:
```text
novelty = min(1, 2*delta + 0.3*time_factor)
```

### Stage 3 — habituation
If content stays unchanged, habituation rises exponentially toward 1 using a channel-specific time constant.

If content changes:
```text
habituation <- 0.5 * previous_habituation
```
This is a partial spontaneous-recovery rule rather than a full reset.

### Stage 4 — attention allocation
Top-down mode -> per-channel weights.

Examples from the early design:
- chat boosts user presence/mood/amygdala and suppresses AURA/QR/hardware;
- idle/diffuse increases broader environmental/interoceptive channels;
- gaming emphasizes hardware and suppresses low-relevance inner channels;
- reflection boosts mood/amygdala/conflict relative to hardware.

### Stage 5 — salience breakthrough
Historical bypasses:
- recent Amygdala urgency > 0.5 -> threat bypass;
- >=2 failed services -> organ failure bypass;
- ACC conflict >1.0 -> conflict surge bypass;
- user return after long absence -> user-presence bypass.

A breakthrough forces the channel to gain 1.0 for that gate.

### Stage 6 — final gain
Early form:
```text
gain = base_gain
     * (1 - 0.8*habituation)
     * attention_weight
     * vigilance_modifier
     * novelty_or_burst_boost
```
with clamping to [0,1].

E-PQ vigilance changes global gain approximately over 0.7..1.3.

### Stage 7 — relay / PROPRIO projection
Only non-empty channels above the relay threshold appear in `[PROPRIO]`.
Burst channels are marked for emphasis.

The original semantic objective was not merely filtering telemetry; it was to create a pre-model *accessibility field* whose state also fed personality/homeostasis through overload/deprivation events.

---

## T-3 — persistent adaptation and observability

The first implementation persisted:
- channel habituation;
- last relayed hash/value/time;
- last change time;
- relay/suppress counters;
- sampled gate logs with cognitive mode, vigilance, relay fraction, gains, bursts, overrides and gate duration.

Important architectural principle retained:
- long-lived sensory adaptation state survives individual model calls;
- logging can be sampled, but causal transitions used by later behavior need exact receipts in the current target.

---

## T-4 — early reliability correction: singleton shutdown race

Commit `8ddb1bf16117f957d0d8c21082e3fb6e1267bdb4`, 2026-03-04:
- fixed a Thalamus singleton shutdown race condition.

Current reusable rule:
- organ singleton lifetime is a physical implementation detail, but shutdown/restart state must be deterministic and replayable;
- H1/H2/H3 require restart/crash/idempotency fixtures around fast-state organs.

---

## T-5 — Global Workspace feedback coupling

Commit `f1ea0b47ef74cad16a3aadb9e63f633fd97a4e5d`, 2026-03-07.

Added:
```text
subscribe("thalamus", self._on_gws_event)
```

Callback behavior:
- when `event.salience >= 0.7`, update `_last_gws_event_ts` and `_last_burst_ts`;
- this is a cross-system **sensitization cue**, not a complete GWT->Thalamus semantic feedback contract.

Important distinction:
- `services/global_workspace.py` was process-local and its publish path did not implement candidate competition itself;
- therefore this coupling proves a bus callback, not full global-workspace causal closure.

Current reuse:
- keep feedback from globally selected/useful events into perceptual gating as a candidate mechanism;
- bind it to exact WorkspaceEpisode/source/outcome identity rather than a bare timestamp.

---

## T-6 — predictive-coding extension

By commit `3a264068e5000d7d6212336048b3bf6e8e5e28eb`, 2026-03-10, channel state included:
```text
predicted_value
prediction_error
ema_alpha = 0.3
```

Behavior:
- expected next numeric value is an EMA;
- current prediction error is `abs(actual - predicted)`;
- large unexpected deviations increase gain;
- later final-gain logic capped prediction-error boost at about +40%.

This was a major semantic development:
- novelty was no longer only "different from last relayed";
- expectation itself became part of attention allocation.

Current reuse:
- preserve expected-vs-observed mismatch as a typed first-class signal;
- current Retina/PerceptualField integration generalizes this beyond scalar channels;
- prediction error may increase attention/GWT candidacy but cannot by itself establish truth or causal novelty.

---

## T-7 — bug: missing burst state initialization

Commit `1d44389056cdd889e436f8b0a2dffcc49a95272b`, 2026-03-11:
- fixed missing `_last_burst_ts` initialization.

Why it matters now:
- a cross-organ feedback callback referenced state that organ construction had not guaranteed;
- current architecture requires schema-complete state construction and typed completeness checks before a transition can be called valid.

Harness regression:
- every state field read on callback/re-entry paths must have deterministic initialization/migration behavior.

---

## T-8 — major negative result: gain/relay decoupling

Deep audit commit `07f8e26a296cf5bdcd4add14ee42ab501d09422b`, 2026-03-13 reports:
- **Thalamus gain/relay decoupled**;
- consequence reported: **91% Amygdala suppressed**.

This is one of the strongest historical Thalamus constraints.

Interpretation:
- calculating a sensible gain is not sufficient;
- the downstream projection/relay path must demonstrably use that gain;
- a safety-critical/high-salience channel can appear mathematically favored while being practically absent downstream.

Current law:
`gate score != relay != model-visible reconstruction != causal use`.

Mandatory Harness family:
- force known Amygdala/perception/service-health inputs;
- compare expected gate result, actual candidate membership, emitted Assembly/projection, receiver reconstruction and downstream use;
- inject mutations that decouple any adjacent stage and require detection.

---

## T-9 — entity mode/schema evolution

Historical mechanism-index and source comments preserve two compatibility failures:
1. missing `is_entity_active` field once caused a `TypeError` that killed the Thalamus path;
2. an `entity_session` cognitive mode was documented without a matching profile in a historical revision.

Later source explicitly carries fixes/comments for both.

Then the legacy entity system was removed/replaced by Rooms in the 2026-03-13 deep audit, making entity-specific routing itself superseded.

Reusable rule:
- cognitive modes are versioned schema, not free strings;
- removal/rename of a mode requires migration/default/fallback tests;
- no mode can silently select a generic profile if semantics differ materially.

---

## T-10 — top-down model feedback closes the sensory loop

Frozen public-head Thalamus adds `_feedback_bias` and `receive_feedback(referenced_channels)`.

Representative parameters:
- referenced channel boost: `+0.15`;
- ignored channel suppression: `-0.05`;
- decay per gate: `0.87` (~5-call half-life as documented).

Later final gain includes:
```text
feedback_mod = 1 + feedback_bias
pred_boost   = 1 + min(0.5*prediction_error, 0.4)
```

Conceptual advance:
- attention becomes recurrent: model output can influence what is easier to relay on subsequent calls.

Risk:
- naive "model mentioned it -> boost it" can create self-confirming attractors;
- ignored channels can become progressively less visible even when later evidence matters.

Current fusion correction:
- feedback credit must be scoped to exact causal/use/outcome receipts;
- utility may alter non-authoritative salience/routing only;
- novelty/diversity reserve and anti-attractor controls are mandatory;
- untrusted self-reference cannot become sensor truth or learning truth.

---

## T-11 — AURA -> Swarm rename and prompt-truth failure

Commit `62149151ba704479f46265a5b8b5865fd38ba99d`, 2026-04-03.

Root cause explicitly reported:
- Core had a hard-coded `ARCHITECTURE FACT` containing the old `aura` channel;
- it was injected into every Thalamus-related prompt;
- this runtime literal overrode newer training behavior.

Migration:
- `aura` -> `swarm` across 15 Thalamus references;
- `ThalamicInputState` fields renamed;
- consciousness-daemon cache renamed;
- tests/docs updated.

Frozen public-head differences include:
- channel list uses `swarm`;
- Swarm base gain reduced to ~0.05 and is near-silent in most attention profiles;
- QR uses real numeric coherence metric;
- current implementation retains predictive coding and recurrent feedback.

Critical current rule:
- architecture truth cannot be duplicated in uncontrolled prompt literals;
- channel identity must come from versioned semantic schema/current state;
- stale lexical aliases are provenance/migration information, not current facts.

---

## T-12 — measured August-2026 live role

The 2026-08-05 measured architecture report describes Thalamus as layer-1 preconscious gating:
```text
user/event
 -> Amygdala (<0.5 ms)
 -> Thalamus gate (<3 ms)
 -> NAcc (<0.1 ms)
 -> Global Workspace competition/ignition
```

Measured/current channel set in that report:
```text
hardware
mood
user_presence
swarm
qr_coherence
perception_events
service_health
amygdala
acc_conflict
```

Four central mechanisms retained in the measured architecture:
- continuous per-channel gain;
- exponential habituation;
- burst for novel/unexpected change;
- salience breakthrough;
plus E-PQ vigilance modulation.

This means the Thalamus survived multiple architectural generations because it solved a real role: **fast state-dependent access control before limited global/model resources are spent**.

---

## T-13 — C4-C9 abstraction of the Thalamic role

### C4
- Amygdala/Thalamus/NAcc preserved as distinct fast state machines in a Reflex Kernel;
- their outputs feed an exact CognitiveFrame before GWT competition.

### C5
- reflex outputs become part of a sealed causal basis with semantic memory epoch/Assembly;
- gate state no longer has to be serialized as prose to remain causally represented.

### C6
- cross-module Thalamic values gain Clay-native types/ranges/basis/provenance;
- physical values remain numeric, with semantic labels at boundaries.

### C7
- Thalamus is a semantic organ, not necessarily a process/service;
- semantic organ boundary is independent of process/storage/authority boundary.

### C8
- salience becomes explicitly non-authoritative;
- a Salience Governor is separated from canonical memory truth;
- resource allocation and active Assembly selection become downstream typed stages.

### C9
- route/salience/admissibility/selection/authority are explicitly orthogonal;
- a high-gain item may still be inadmissible or quarantined for a consequential use;
- required context can force candidate availability without forcing a winner.

---

## T-14 — Digital Retina / PerceptualField fusion

Current owner-fixed target dissolves Retina as a mandatory independent cognitive process boundary while preserving visual semantics.

New Thalamic role:
- receive typed PerceptualField evidence/state deltas rather than merely a flat `perception_events` text channel;
- preserve separate support from:
  - bottom-up sensor evidence;
  - world/memory prior;
  - current goal/context bias;
  - learned familiarity/readout support;
- gate/select scarce deeper perception/GWT resources based on novelty, conflict, prediction error, risk, goal relevance and action consequence.

Familiar visual content:
- may remain local when evidence/current-version/calibration/context are coherent;
- familiar fast path is invalidated by stale feature backbone, calibration drift, conflict, near-confuser/open-set evidence or changed context.

Novel/conflicting evidence:
- tends to increase deeper Retina/PerceptualField processing and/or GWT candidacy;
- cannot be forced into a familiar identity by top-down memory.

---

## T-15 — current dual-gate learning correction

The fused adaptive-memory research adds a distinction not explicit in historical Thalamus:

### RecognitionValidity gate
Controls whether learned familiarity may accelerate current recognition/routing.
Checks include:
- current feature/backbone version;
- calibration validity;
- open-set/near-confuser evidence;
- current context/source coherence;
- contradiction/conflict state.

### AdaptiveStatePromotion gate
Controls whether candidate learned state becomes durable/current.
Checks include:
- GOLD/SILVER trusted evidence;
- candidate shadow evaluation;
- poisoning/pseudo-label constraints;
- version lineage;
- rollback witness;
- atomic promotion/publication.

Thalamus/attention may consume outputs from both gates but may not merge them into one confidence scalar without losing falsifiability.

---

## T-16 — lineage-fused current target

Target logical Thalamus is a **fast typed access-control organ**, physically colocatable inside one-module FRANK but semantically/interventionally distinct.

Required inputs:
- exact current state basis/epoch;
- typed sensor/perceptual deltas;
- Amygdala threat/risk;
- service/body state;
- mood/personality vigilance;
- memory/world/goal context as explicitly typed prior/bias, not evidence;
- prediction error;
- GWT/outcome feedback receipts when causally justified;
- resource state/budget.

Required state per channel/field family:
```text
channel_id / semantic_role
source_epoch
value/evidence_ref
base_gain or policy prior
habituation state + time constant
novelty/change state
prediction/expected state + error
mode/context modulation
feedback/utility modulation with causal receipt
breakthrough reason
computed gain
relay/candidate result
suppression reason
version/policy hash
```

Required output is not prose. It is a typed gate/attention decision that can lower into:
- local PerceptualField routing;
- candidate membership/weight;
- required-context escalation;
- GWT Assembly input;
- diagnostic/materialized receipts.

### Core equations are historical candidates, not immutable magic numbers
The historical multiplicative gain structure is reusable, but exact coefficients must be benchmarked against H1/H2/H3 traces.

### Hard invariants
1. current sensor evidence and memory/familiarity prior stay separate;
2. high salience cannot mint truth or authority;
3. missing schema/mode/state field is explicit invalid/UNKNOWN, not crash/silent fallback;
4. calculated gain must be causally traceable to actual relay/candidate membership;
5. safety-critical breakthrough paths have direct completeness tests;
6. feedback adapts salience only with bounded causal credit;
7. stale source/basis/calibration invalidates fast-path reuse;
8. restart preserves or explicitly resets habituation/prediction state according to a versioned policy;
9. one-module physical collapse may not erase the ability to lesion Thalamus independently in Harness experiments.

## Mandatory historical regression suite

- `T-REG-01`: missing `is_entity_active`/mode-equivalent field;
- `T-REG-02`: mode exists but profile missing;
- `T-REG-03`: `_last_burst_ts`/callback state missing initialization;
- `T-REG-04`: singleton shutdown/restart race;
- `T-REG-05`: gain/relay decoupling, including Amygdala high-salience survival;
- `T-REG-06`: stale AURA/Swarm alias injected from uncontrolled runtime prompt literal;
- `T-REG-07`: GWS high-salience callback fires but has no downstream effect;
- `T-REG-08`: recurring unchanged channel habituates while a true change recovers;
- `T-REG-09`: prediction-error boost does not suppress exact low-novelty required context;
- `T-REG-10`: feedback-bias attractor poisoning / repeated self-reference;
- `T-REG-11`: misleading visual prior/familiarity vs strong contradictory sensor evidence;
- `T-REG-12`: stale Retina/readout/calibration version fast-path rejection;
- `T-REG-13`: crash/replay with persistent habituation and prediction state;
- `T-REG-14`: Reference-vs-ClayCode-vs-OneModule differential gate equivalence.

## Fusion decision

`REUSE_SEMANTICS + ADAPT_IMPLEMENTATION + RETEST_PARAMETERS`.

The Thalamus is retained because continuous gain, habituation, burst, breakthrough, predictive error and recurrent modulation are compatible with the current dissolved-perception/GWT architecture. Its exact historical channels and coefficients are not treated as eternal constants. Its failure history is promoted to executable regression requirements.
