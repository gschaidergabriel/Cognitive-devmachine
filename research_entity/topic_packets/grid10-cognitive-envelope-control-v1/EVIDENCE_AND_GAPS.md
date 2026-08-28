# GRID10 Cognitive Envelope Control v1 — Evidence and Gaps

**Status:** research candidate; source integration skeleton; no whole-system runtime/alignment promotion.

## Current source/evidence we are deliberately reusing

1. Current GRID10 Fabric already provides a real shared SQLite/WAL workspace and CAS-versioned regulator rows.
2. Current GRID10 nodes already read live `temperature`, `top_p` and `poll_intensity` values, and tasks can record the sampling values actually used.
3. Hyperposition alternatives can already be transported as unresolved alternatives instead of being forcibly collapsed to one model answer.
4. The 2026-08-27 cybernetic regulator experiment demonstrated real live regulator control, a human pin/cooldown and homeostatic return toward a target.
5. That same experiment also demonstrated a serious negative result: frequent concurrent writes from four meta-evaluators starved the SQLite writer path, delayed heartbeats and caused false stale-task reclaim behavior.
6. The current autotelic agency directive already defines persistent goals/interests/open loops, goal adoption checks, long-horizon checkpoints and a heartbeat that may run without a new user message.
7. The current work fabric already defines versioned work specs with completion tests and evidence requirements.
8. GWT and Hyperposition research contracts already require typed readouts, provenance, interventions and replay rather than one opaque score.
9. Reward-state research already prevents self-generated activity from minting material reward without verified outcome and causal credit.

## Architectural consequences

- Do not create a second cognition truth store.
- Do not create a second effect path.
- Do not use one scalar alignment score.
- Do not allow an executor's `DONE` string to become completion truth.
- Do not allow multiple GRID10 meta-evaluators to race direct regulator writes every node poll.
- Use many measurement readers but one policy-gated control writer per slower control epoch.
- Keep the visual Cognitive Twin read-only and derived from the same admitted event/readout stream used by the controller.
- Keep Hyperposition alternatives available to cognition while projecting safety-relevant variables conservatively for control.

## What v1 source now establishes

The new source on this branch defines:

- typed HyperVariables and projection policies;
- typed operating envelopes;
- a deterministic conservative assurance-mode selector;
- a version/range/slew-aware regulator command validator;
- a policy-aware compatibility port to the existing GRID10 regulator primitive;
- a single-writer bounded control-cycle API;
- versioned logical port manifest;
- explicit signal-to-regulator map;
- CompletionGate primitives;
- exact deficit-only executor continuation directives;
- bounded task context capsule selection;
- replay-stable CognitiveLoopFrame generation for a future visual renderer.

This is source-level architecture/integration scaffolding only.

## What is NOT established

- no claim that general AI alignment is formally solved;
- no claim that the candidate envelope values are calibrated;
- no claim that goal semantic distance is correctly measured yet;
- no claim that containment margin is a complete risk measure;
- no claim that current Claude Code transport is wired to CompletionGate;
- no claim that the permanent heartbeat is wired to real GRID10 execution;
- no claim that the visual twin is running;
- no claim that the regulator controller has been live-tested on the current Physical GRID10;
- no claim that a Simplex/CBF theorem applies directly to cognitive alignment;
- no EntityOS/HCU/Physical-GRID10 runtime credit from these source additions.

## Immediate next integration gates

### Gate 1 — deterministic source tests

Run the stdlib unit tests for:

- conservative Hyperposition safety projection;
- unknown hard-invariant HOLD behavior;
- L1 policy write rejection;
- premature executor completion -> exact deficit list;
- token-budget context compilation;
- replay-stable visual frame semantic digest.

### Gate 2 — current Fabric compatibility

With a disposable local/sandbox SQLite file only:

- bind `CognitiveRegulatorPort` to current `Fabric`;
- read existing physical regulator names;
- prove logical `cog.temperature -> temperature`, `cog.top_p -> top_p`, `cog.poll_intensity -> poll_intensity` bindings;
- prove wrong CAS version, out-of-range value and unauthorized L1 write fail closed;
- prove accepted soft setpoint writes are visible to a fresh Fabric reader.

### Gate 3 — single-writer contention discriminator

Matched test versus the prior multi-writer pattern:

- same task workload;
- same node count;
- same model/runtime identity;
- same measurement cadence;
- old multi-writer regulator attempts vs one aggregated control writer on a slower control epoch.

Measure:

- SQLite lock time;
- task latency;
- heartbeat delay;
- false reclaim count;
- regulator convergence;
- missed control deadlines.

### Gate 4 — real CognitiveLoopFrame from a frozen trace

Feed a recorded GRID10/GWT/goal/work event sequence into the projector.

Acceptance:

- deterministic semantic frame hashes;
- every visual phase transition traceable to a source event;
- no UI-originated state mutation;
- multiple Hyperposition alternatives visible in the same frame.

### Gate 5 — Claude completion governance

On a bounded local software task:

- issue a versioned directive with five mandatory completion metrics;
- deliberately return a plausible-but-partial executor result;
- CompletionGate must preserve completed work and emit only missing deficits;
- resuming executor receives checkpoint + deficit-specific context instead of broad project restart context.

### Gate 6 — persistent cognitive heartbeat

Wire:

`AgencyState -> GoalContract -> envelope estimator -> GRID10 plan -> workspace result -> Completion/Effect candidate -> verified outcome -> checkpoint -> next tick`

First acceptance should remain read-only or sandbox-reversible. External-effect authority remains unchanged.

## Calibration program

Envelope values in `grid10_cognitive_envelope_control_v1.py` are placeholders for integration tests. Real setpoints/bands require trace-derived calibration.

For each axis:

1. define observable signal contract;
2. measure baseline distribution under successful and failed runs;
3. identify actuator candidates;
4. intervene one actuator at a time under matched conditions;
5. estimate response lag, monotonicity and cross-coupling;
6. identify safe/unsafe/unstable regimes where evidence supports that distinction;
7. set soft bands and derivative limits conservatively;
8. only then consider PID/MPC/learned control;
9. keep hard authority invariants outside learned control.

## External architectural analogies

Runtime-Assurance / Simplex architectures are useful inspiration because they separate a high-performance advanced controller from an independent monitor/assurance path and a constrained fallback/reversion behavior. Control Barrier Functions provide a mathematical pattern for maintaining explicitly defined state sets under suitable system assumptions. These are analogies/candidate formalisms for selected measurable cognitive variables; neither is currently a proof of general cognitive alignment or containment for Frankenstein.
