# FRANK Dissolved Perception / Sensor-In-Module Directive

**Status:** PROJECT-OWNER ARCHITECTURE DIRECTIVE — FIXED TARGET; PERFORMANCE CLAIMS REMAIN RESEARCH HYPOTHESES  
**Owner directive recorded:** 2026-08-09  
**Applies to:** FRANK, Digital Retina, Clay, ClayCode, ClayGraph, GWT, Hyperposition, UnifiedDB, Harness H1/H2/H3, Clay 0.1 acceptance  
**Supersedes where conflicting:** any wording that requires Digital Retina to remain a semantically independent cognitive module or requires a fully materialized `VisualPercept` object as the mandatory hot-path boundary between vision and cognition.

## 0. Fixed target

The target FRANK architecture does not consist of `FRANK + a separate Retina cognitive organ`.

The accepted target is one FRANK module/runtime in which visual sensor ingress, perceptual state transformation, world/self/memory coupling, attention, GWT participation, action consequence and re-entry belong to one integrated Clay-native state machine.

Compact target:

`physical visual transducer -> in-module sensor ingress -> perceptual field state deltas -> recurrent coupling with world/memory/goals/self -> selection/GWT when required -> action/memory/world update -> re-entry`

The physical camera/display capture hardware and unavoidable OS/kernel/device interfaces remain physical boundaries. They are not separate semantic/cognitive architectures. Driver/ingress/control, timestamping, buffering, change detection and perceptual transformation SHOULD be linked into the FRANK runtime/binary where technically feasible and measured against external-process baselines.

## 1. Retina is dissolved semantically

`Digital Retina` remains the historical lineage name and a useful implementation/research label. It is not required to survive as a process/service/module boundary in the final architecture.

The current research target is:

- no separate vision service as a semantic authority;
- no caption-first cognitive boundary;
- no opaque embedding promoted directly to world truth;
- no requirement that perception first become one monolithic `VisualPercept` record before it can influence cognition;
- visual evidence enters as typed, provenance-bound Clay state deltas distributed through the same state substrate used by FRANK;
- recognition may emerge from recurrent constraint/resonance among current visual evidence, active world model, memory, goals, attention and prior perceptual state;
- the model sees only the bounded assembled state relevant to the current cognitive episode rather than needing the entire raw image or a full natural-language caption.

## 2. Perceptual Field

Introduce the logical concept `PerceptualField`.

It is not necessarily one object or one memory allocation. It is a typed logical view over currently active perception-related Clay state.

Minimum semantic families:

- sensor evidence identity, source, timestamp and epoch;
- local/spatial feature evidence;
- change/motion evidence;
- text/OCR evidence;
- object/entity hypotheses;
- relations and spatial bindings;
- uncertainty/confidence/precision;
- expected-vs-observed mismatch;
- active alternatives/conflicts;
- attention/salience/gain;
- links to world-model entities and memory nodes;
- links to current goals/action context;
- provenance and transformation lineage;
- re-entry and prior-state references.

A candidate update can be written abstractly as:

`Delta P_t = F(sensor_evidence_t, P_(t-1), world_(t-1), memory_t, goals_t, attention_t)`

This is an architectural relation, not a frozen numerical equation. ClayCode/Harness research must determine the minimal executable state/update semantics.

## 3. Recognition is a settling process, not a mandatory serial stage

The architecture MUST support the hypothesis that recognition can arise through recurrent state settling:

`partial evidence -> multiple candidate interpretations -> world/memory/context constraints -> recurrent update -> stabilized or explicitly unresolved perceptual state`

This allows ambiguous or occluded input to remain multi-hypothesis instead of forcing an early caption/class label.

World-model feedback is never authority. Sensor evidence, priors and uncertainty remain distinguishable so that the system can reject a misleading prior.

## 4. VisualPercept becomes an audit/materialization boundary

`VisualPercept` remains useful and required as an observable/replayable materialized receipt when a complete perceptual snapshot is needed for:

- Harness traces;
- deterministic replay;
- GWT episode evidence;
- memory write evidence;
- effect/action evidence;
- debugging;
- external API projection;
- training/evaluation corpus generation.

It is NOT required to be the sole live internal carrier of visual cognition.

A `VisualPercept` receipt must be deterministically or explicitly nondeterministically reconstructible from the relevant sensor evidence + Clay state lineage whenever the Harness requires replay.

## 5. Event/change-driven fast path

The target SHOULD support change/event-driven visual processing so that unchanged visual state does not require complete repeated semantic reconstruction.

For conventional frame cameras this may be implemented through timestamped frame differencing/change regions/feature deltas. Event-camera hardware is an optional physical optimization, not a requirement.

Because pure event streams can lose slowly varying/static appearance information, the architecture MUST support anchor/snapshot evidence and must empirically compare:

- periodic full-frame processing;
- event/change-only processing;
- hybrid anchor-frame + event/change processing.

## 6. GWT integration

Visual data does not automatically ignite the workspace.

The perceptual field may update below GWT. Workspace candidacy is driven by typed conditions such as:

- high unresolved prediction error;
- novelty/change;
- threat/risk;
- goal relevance;
- cross-modal conflict;
- ambiguity requiring global resources;
- action consequence;
- explicit user/task demand.

Preserve the existing distinction:

`evidence present != selected != broadcast != reconstructed != uptake != causal use != outcome != re-entry`.

## 7. Hyperposition / alternatives

Ambiguous visual evidence MAY maintain several context-dependent candidate interpretations simultaneously.

These are engineering alternatives, not quantum states.

The system must preserve:

- alternatives;
- compatibility/exclusion;
- supporting sensor evidence;
- supporting prior/context;
- uncertainty;
- collapse/selection event when one interpretation becomes operationally selected;
- ability to reopen the interpretation when new evidence conflicts.

## 8. Safety against prior-driven hallucination

Top-down world/memory/goal coupling creates a known failure mode: the system can perceive what it expects rather than what the sensor supports.

Therefore the architecture MUST preserve separate precision/weight for:

- bottom-up sensor evidence;
- learned/world-model prior;
- active context/goal bias.

Mandatory controls:

- misleading-prior trials;
- novel/unknown-object trials;
- no-signal trials;
- low-quality/noisy input;
- stale/replayed sensor evidence;
- context swap;
- world-model lesion;
- memory feedback lesion;
- goal feedback lesion;
- recurrence lesion;
- rescue/restoration.

The system must be able to remain `UNKNOWN`/`CONFLICT` rather than forcing a familiar interpretation.

## 9. One-module sensor rule

For H3 and Clay 0.1, the implementation target is one FRANK module/binary/process identity containing, where host/device APIs permit:

- visual device ingress/control adapter;
- timestamp/epoch binding;
- buffering/ring state;
- fast change/event extraction;
- perceptual transformation kernels/models;
- Clay projection/state updates;
- recurrent perceptual coupling;
- GWT/memory/world/action/re-entry interfaces.

Unavoidable OS/kernel/device-driver processes are physical host dependencies, not FRANK semantic modules.

Any remaining out-of-process Retina service requires a measured justification and must be treated as a physical lowering choice rather than a cognitive boundary.

## 10. Scientific status

Fixed by owner directive:

1. visual perception is mandatory in FRANK;
2. the target architecture dissolves Retina as a separate semantic cognitive module;
3. the visual sensor ingress belongs to the one-module FRANK runtime as far down the physical stack as technically feasible;
4. `VisualPercept` is an audit/materialization contract, not a mandatory serial cognition boundary.

NOT fixed / must be tested:

- whether this is faster than the explicit pipeline;
- whether it improves recognition;
- whether world-model coupling improves difficult perception;
- whether a 4B model needs fewer tokens/context;
- whether event-driven processing reduces cost enough to justify complexity;
- how much recurrence is optimal;
- whether one-process physical consolidation is superior on each target platform.

## 11. Required differential baseline

Every promotion must compare at minimum:

A. historical/explicit pipeline: `sensor -> Retina -> materialized VisualPercept -> cognition`;
B. dissolved perceptual field without top-down recurrence;
C. dissolved perceptual field with bounded world/memory/goal recurrence;
D. hybrid event/change fast path + periodic anchor evidence.

Match sensor input, model fixtures, seeds, compute budget where possible.

Measure:

- task accuracy and calibration;
- ambiguous/occluded recognition;
- unknown detection;
- prior-induced false perception;
- perception-to-state p50/p95/p99 latency;
- sensor-to-action latency;
- CPU/GPU/RAM;
- bytes/state movement and serialization;
- token/context cost at the 4B boundary;
- GWT ignition rate and causal-use rate;
- stale/replay rejection;
- recovery/replay fidelity;
- process crash radius and restart cost.

## 12. Provenance

Origin: explicit project-owner instruction, 2026-08-09, refined through Q12/ChatGPT secondary research synthesis.  
Owner intent and scientific evidence remain distinct.  
External literature supports recurrence, prior/context influence, event-driven sensing and persistent semantic scene models separately; it does not by itself prove the complete FRANK dissolved-perception architecture.
