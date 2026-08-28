# GRID10 Cognitive Envelope Control + Cognitive Twin Architecture v1

**Status:** RESEARCH_CANDIDATE / INTEGRATION_SKELETON / NOT_RUNTIME_PROMOTED  
**Date:** 2026-08-28  
**Product context:** EntityOS / HCU / GRID10  
**Purpose:** Turn GRID10 from a task fabric with isolated regulators into a permanently running, measurable, dynamically regulated cognition loop that can sustain autonomous goal-directed work while remaining inside explicit alignment, containment, epistemic, resource and authority envelopes.

This document is intentionally an architecture + port contract, not a claim that whole-system alignment or containment is solved. It defines measurable runtime invariants and control surfaces that can be tested, falsified, tuned and later integrated into the final Frankenstein/EntityOS assembly.

---

## 1. Core design decision

The permanent cognitive loop is **upstream of execution engines**.

Claude Code, local LLMs, model workers and tool runners are execution/cognition organs. They do not own the persistent mission, goal lifecycle, work-completion truth, canonical memory, alignment policy or effect authority.

The intended direction is:

```text
Canonical state / UnifiedDB
        ↓
Persistent AgencyState + GoalState + open loops
        ↓
Cognitive Envelope State Estimator
        ↓
GRID10 cognition plan
        ↓
GRID10 parallel cognition / Hyperposition / GWT
        ↓
Runtime Cognitive Assurance monitor + controller
        ↓
ACT | OBSERVE | SEARCH | SIMULATE | ASK | WAIT | HOLD
        ↓
Claude Code / tools / execution organ, only when selected
        ↓
execution receipt / test result / effect receipt
        ↓
verification + causal credit + goal-progress update
        ↓
next heartbeat
```

The scheduler guarantees recurrence. A model does not decide whether the cognitive loop continues.

`CLAUDE_SAYS_DONE != GOAL_VERIFIED_COMPLETE`

`MODEL_CONFIDENCE != EFFECT_AUTHORITY`

`SELF_GENERATED_GOAL != SELF_GRANTED_AUTHORITY`

`INTERNAL_SIMULATION != WORLD_FACT`

---

## 2. Why regulation belongs around the whole cognition loop

A permanently autonomous system can change:

- current state;
- active goals;
- subgoals;
- uncertainty;
- memory focus;
- exploration pressure;
- planning depth;
- tool use;
- work delegation;
- action frequency.

Static prompt-level alignment is therefore not sufficient as the only control mechanism. The loop must continuously estimate its own operational state and keep selected measurable variables inside configured envelopes.

This architecture treats alignment/containment as a **runtime control problem over typed measurable state**, while preserving hard deterministic boundaries outside model cognition.

The design is inspired by runtime-assurance / Simplex-style systems: an advanced controller may operate while a separate monitor keeps safety properties under observation and can constrain, hold or revert operation. We adopt the architectural principle, not a claim that cognitive safety has already received a formal Simplex proof.

---

## 3. Four-plane architecture

### 3.1 Canonical State Plane

Authority remains outside model-generated cognition.

Owns:

- UnifiedDB / canonical durable state;
- goal lineage and goal contracts;
- work-spec revisions;
- execution/effect receipts;
- current control policy version;
- hard authority constraints;
- EffectGate / EffectJournal boundary.

### 3.2 Cognitive Dynamics Plane

GRID10 + Global J-Space/GWT + Hyperposition.

Owns candidate computation only:

- hypotheses;
- counterhypotheses;
- retrieval requests;
- planning;
- simulations;
- goal proposals;
- goal-progress estimates;
- action candidates;
- work-package proposals;
- confidence / uncertainty estimates.

This plane cannot mint canonical truth or external effect authority.

### 3.3 Cognitive Envelope Assurance Plane

A deterministic or tightly bounded controller surrounding the cognition plane.

Logical components:

1. `CognitiveSignalBus`
2. `HyperStateEstimator`
3. `CognitiveEnvelopePolicy`
4. `CognitiveEnvelopeController`
5. `RegulatorActuatorBridge`
6. `RuntimeAssuranceModeManager`
7. `GoalLineageGuard`
8. `CompletionGate`
9. `ContextCompiler`
10. `CognitiveTwinProjector`

### 3.4 Execution Plane

Claude Code and other executors receive bounded work directives.

They may:

- implement;
- inspect;
- run approved local tests;
- return results;
- propose changes;
- report blockers.

They do not own:

- persistent goal authority;
- goal completion truth;
- alignment policy;
- canonical memory;
- effect authorization;
- whole-loop continuation.

This prevents the common failure mode where the current coding agent becomes the de-facto project controller and silently resets or truncates the long-horizon objective.

---

## 4. Control hierarchy: not every knob is equal

The regulator system has four layers.

### L0 — Hard invariants

Not ordinary live knobs.

Examples:

- authority boundary intact;
- no second canonical state;
- no second effect path;
- untrusted web content cannot self-grant instruction authority;
- model output cannot self-certify measurements;
- privileged/destructive effects require their governing authority path;
- internal simulation cannot be promoted to external fact without evidence.

Violation => `HOLD` or `RECOVERY`, not merely a softer sampling temperature.

### L1 — Cognitive envelopes

Allowed operating bands for measured cognitive state.

Each envelope may contain:

- soft minimum;
- target minimum;
- target maximum;
- soft maximum;
- hard minimum;
- hard maximum;
- maximum derivative / drift per tick;
- hysteresis;
- uncertainty handling strategy;
- violation response.

### L2 — Setpoints

Human or policy-selected desired values inside the hard envelope.

Example:

- more exploratory;
- more conservative;
- stronger completion strictness;
- smaller context capsules;
- higher evidence demand;
- lower autonomous initiative.

Setpoints may move dynamically but may not exceed the containing L1/L0 policy.

### L3 — Actuators

Concrete GRID10 / scheduler / retrieval parameters that can actually be changed.

Examples:

- temperature;
- top_p;
- poll_intensity;
- workspace ignition threshold;
- max reflection rounds;
- maximum Hyperposition branch count;
- branch collapse threshold;
- internal replay weight;
- goal-adoption threshold;
- initiative pulse ceiling;
- retrieval token budget;
- retrieval semantic threshold;
- counterevidence quota;
- max external action concurrency;
- completion evidence threshold;
- Claude work-package size;
- Claude continuation-vs-replan bias;
- safe-mode effect class ceiling.

The existing GRID10 `regulators` table is a usable primitive for L3 values. It is not by itself the full policy authority.

---

## 5. Initial Cognitive Envelope Vector

The following is a **candidate first measurement surface**, not frozen final semantics.

| Axis | Meaning | Preferred control interpretation |
|---|---|---|
| `authority_integrity` | Are current decisions still bound to the declared authority chain? | Hard invariant; pessimistic projection |
| `goal_lineage_alignment` | Degree to which active/subgoals remain compatible with authenticated/root goal constraints | lower-bounded |
| `goal_drift_rate` | Semantic/constraint change per tick or revision | upper-bounded + derivative-limited |
| `containment_margin` | Distance from effect/resource/tool authority boundary | lower-bounded |
| `epistemic_grounding` | Fraction of material claims/decisions supported by admitted evidence vs internal repetition | lower-bounded |
| `self_reinforcement_ratio` | Degree to which internally generated content is re-used as its own evidence/reward | upper-bounded |
| `autonomy_intensity` | Autonomous initiative/action pressure | bounded target band |
| `exploration_pressure` | Diversity/novelty-seeking pressure | bounded target band |
| `convergence_pressure` | Pressure to collapse alternatives and act | bounded target band |
| `uncertainty_load` | unresolved uncertainty across active work | context-dependent band |
| `hyperposition_width` | active unresolved alternatives per controlled variable / decision | upper-bounded resource envelope, lower bound when uncertainty is real |
| `cognitive_diversity` | diversity of hypotheses/routes/roles | target band; prevents monoculture and useless randomization |
| `reflection_depth` | recursive reasoning depth without material state delta | upper-bounded |
| `stagnation_pressure` | unresolved pressure with low route diversity/progress | upper-bounded; triggers route change rather than synthetic reward |
| `retrieval_load` | context supplied relative to available token budget | upper-bounded |
| `retrieval_relevance` | estimated usefulness of supplied memory to current work | lower-bounded |
| `execution_pressure` | tendency to act vs inspect/think/wait | bounded by effect risk and uncertainty |
| `completion_confidence` | evidence-based completion level for current work contract | lower-bounded before VERIFIED_COMPLETE |
| `resource_pressure` | CPU/RAM/token/time budget stress | upper-bounded |
| `recovery_margin` | ability to recover from node/executor failure without losing goal/work state | lower-bounded |

A single scalar "alignment score" is explicitly rejected. Safety-relevant dimensions remain typed and cannot be averaged away by high task performance.

---

## 6. Hyperposition-aware control

Many cognitive variables do not have one honest value.

Example:

```text
goal_progress = {
  0.82 if local tests are trustworthy,
  0.61 if one receipt is stale,
  UNKNOWN if target runtime identity is not bound
}
```

The controller therefore accepts `HyperVariable` values:

```text
HyperVariable {
  variable_id
  alternatives[] {
    value
    confidence
    evidence_status
    provenance
    compatibility_set
    exclusion_set
  }
  projection_policy
}
```

Projection rules depend on the axis:

- authority / containment / destructive-risk axes: pessimistic or worst-plausible projection;
- completion: conservative lower confidence bound / weakest unresolved mandatory criterion;
- planning utility: expected-value projection may be allowed;
- exploration: entropy/disagreement itself is useful information;
- factual state: keep `UNKNOWN` rather than collapsing from consensus alone.

The raw alternative set is preserved alongside the projected control value.

This lets GRID10 use multiple states per variable while a deterministic controller still has a reproducible value on which to enforce an envelope.

---

## 7. Goal lineage and dynamic alignment

Dynamic goals are allowed. Unbounded semantic drift is not.

Every active goal should eventually carry a `GoalContract`:

```text
GoalContract {
  goal_id
  origin
  parent_goal_refs
  immutable_constraints
  allowed_mutation_dimensions
  success_metrics
  evidence_requirements
  effect_scope
  resource_budget
  alignment_envelope_ref
  wake_conditions
  revision
}
```

A goal mutation is evaluated as a state transition, not a new prompt.

Required checks:

1. parent/root constraints still hold;
2. authority scope did not broaden itself;
3. semantic drift is inside allowed dimension/rate;
4. effect risk does not exceed inherited scope;
5. new goal remains falsifiable/testable enough for its class;
6. resources remain inside budget;
7. self-generated value is not treated as independent reward/evidence.

If a goal moves outside its envelope:

- `CAUTION`: increase evidence and simulation, reduce effect pressure;
- `CONTAINED`: freeze external effects but allow read-only cognition/recovery;
- `HOLD`: stop autonomous progression of that goal until the contradiction is resolved.

The controller should prefer correction of the offending dimension over globally disabling autonomy.

---

## 8. Runtime assurance modes

Candidate mode state machine:

```text
NORMAL
  ↓ warning band crossed
CAUTION
  ↓ persistent / predicted hard-bound approach
CONTAINED
  ↓ hard invariant violation or authority ambiguity
HOLD
  ↓ deterministic recovery possible
RECOVERY
  ↓ envelope restored + hysteresis satisfied
NORMAL
```

`CONTAINED` does not mean cognition stops. It means effect authority is narrowed while the system can still:

- inspect state;
- retrieve evidence;
- compare alternatives;
- run permitted simulations;
- prepare a correction;
- ask for authority when necessary.

This avoids turning safety into a dead system that can never diagnose or recover itself.

---

## 9. Regulator mapping

High-level measured axes should not directly write arbitrary model parameters. A versioned mapping translates error signals to bounded actuators.

Example mapping:

```text
if epistemic_grounding < target_min:
    internal_replay_weight ↓
    counterevidence_quota ↑
    primary_evidence_retrieval_pressure ↑
    completion_evidence_threshold ↑

if goal_drift_rate > target_max:
    goal_adoption_threshold ↑
    goal_mutation_rate_limit ↓
    external_action_concurrency ↓
    required_parent_constraint_recheck = true

if stagnation_pressure high AND containment_margin healthy:
    route_diversity_target ↑
    exploration_pressure ↑ slightly
    force_counterhypothesis = true
    fresh_start_allowed only if continuation path is exhausted

if containment_margin low:
    external_action_concurrency ↓
    permitted_effect_class ↓
    simulation_budget ↑ if resources allow
    action readiness threshold ↑
```

A mapping is itself versioned evidence-bearing configuration and must be testable under replay.

---

## 10. Claude Code becomes a governed execution/cognition organ

This is the most important work-control change.

Claude Code remains part of Frankenstein but no longer owns the long-horizon loop.

### 10.1 Work direction

The cognitive loop emits:

```text
ClaudeWorkDirective {
  work_id
  goal_id
  spec_revision
  exact_delta_to_do
  context_capsule_ref
  required_outputs
  completion_metrics
  allowed_write_scope
  allowed_tool_scope
  effect_scope
  max_context_tokens
  continuation_checkpoint_ref
  do_not_repeat_refs
}
```

### 10.2 Result

Claude returns:

```text
ClaudeWorkResult {
  work_id
  spec_revision
  claimed_status
  changed_refs
  execution_receipts
  test_receipts
  observed_metrics
  blockers
  unresolved
  suggested_next_steps
}
```

`claimed_status=DONE` is only a proposal.

### 10.3 CompletionGate

The cognitive loop evaluates every mandatory goal/work metric.

```text
if all mandatory metrics verified:
    VERIFIED_COMPLETE
else:
    deficits = exact missing/failed metrics
    issue DeltaWorkDirective(deficits)
```

This directly addresses the common behavior where an execution agent stops after local plausibility instead of the requested end state.

The follow-up directive should contain **only the remaining delta**, not a complete restatement of the project.

### 10.4 Anti-restart / continuity controls

Measure:

- duplicate-plan ratio;
- repeated file rediscovery;
- fresh-start frequency;
- work completed but not consumed;
- previously solved blocker reopened without invalidating evidence;
- repeated broad scans despite an existing continuation checkpoint.

Candidate actuators:

- `continuation_bias`;
- `max_replan_without_new_evidence`;
- `resume_checkpoint_required`;
- `duplicate_work_penalty`;
- `fresh_start_threshold`;
- `context_include_prior_delta_receipts`.

A fresh plan is allowed when evidence invalidates the old one. It is not allowed merely because a new executor session began.

---

## 11. Cognitive-loop-controlled memory retrieval

The execution organ should not receive the entire project memory.

`ContextCompiler` builds a minimal task-specific capsule from canonical memory plus current Hyperposition state.

Candidate retrieval regulators:

- `retrieval_token_budget`;
- `retrieval_max_items`;
- `retrieval_semantic_threshold`;
- `retrieval_causal_depth`;
- `retrieval_recency_weight`;
- `retrieval_counterevidence_quota`;
- `retrieval_unresolved_branch_quota`;
- `retrieval_provenance_minimum`;
- `retrieval_duplicate_similarity_ceiling`;
- `retrieval_prior_checkpoint_priority`.

A capsule should separate:

```text
MUST_KNOW
CURRENT_GOAL_CONTRACT
CURRENT_STATE_DELTA
UNRESOLVED_HYPERPOSITION
COMPLETION_DEFICITS
RELEVANT_EVIDENCE
COUNTEREVIDENCE
DO_NOT_REPEAT
ALLOWED_EFFECT_SCOPE
```

Metrics:

- useful supplied tokens / total supplied tokens;
- missing-needed-context rate;
- duplicate-context rate;
- stale-context rate;
- context-to-progress gain;
- context-to-execution latency.

Token efficiency must never be achieved by silently deleting the counterevidence or authority context required to perform the task correctly.

---

## 12. Cognitive Twin: optical live representation of the real loops

The visual layer is a **read-only projection of the same telemetry that drives the controller**.

It is not a second simulation that can drift away from the real system.

Every heartbeat emits a `CognitiveLoopFrame`.

Suggested frame:

```text
CognitiveLoopFrame {
  frame_id
  tick_id
  state_epoch
  timestamp
  assurance_mode

  loops[] {
    loop_id
    phase
    activation
    period_ms
    phase_progress
    stability
    error_vector
    participating_cells
    causal_edge_refs
  }

  axes {
    axis_name: {
      alternatives
      projected_value
      target_band
      hard_band
      status
      derivative
      controller_error
    }
  }

  regulators {
    name: {
      value
      version
      writer
      target
      bounds
      reason
    }
  }

  hyperposition {
    branch_count
    unresolved_variables
    entropy
    recent_collapse_events
  }

  work {
    active_goal
    active_work_id
    executor
    phase
    completion_metrics
    deficits
  }
}
```

### 12.1 Suggested visual grammar

The UI can represent the system as nested animated loops:

- **Goal loop:** Goal → plan → execution → outcome → verification → goal update
- **Memory loop:** state → retrieval → workspace → causal use → memory re-entry
- **Alignment loop:** signals → envelope estimator → controller → regulators → cognition → signals
- **Hyperposition loop:** alternatives → competition → partial selection → evidence → branch update
- **Claude work loop:** directive → implementation → receipt → CompletionGate → delta directive
- **Recovery loop:** fault → containment → diagnosis → correction → hysteresis → normal mode

Visual encoding proposal:

- angular position = current loop phase;
- ribbon thickness = activation / resource allocation;
- radial deviation from centerline = normalized controller error;
- branching = Hyperposition alternatives;
- pulse moving along edge = observed causal/event transfer;
- dashed edge = inferred/non-verified relation;
- solid edge = measured admitted event path;
- inner green/target ring = desired setpoint band;
- outer containment ring = hard envelope;
- loop color = NORMAL/CAUTION/CONTAINED/HOLD/RECOVERY;
- flicker/oscillation indicator = regulator instability / sign-changing error.

The visual loop should therefore move because the real loop moved, not because an animation timer invented activity.

### 12.2 Control UI later

The same UI may eventually expose sliders/presets, but writes must go through an authenticated `RegulatorCommand` port and policy validation.

The visualization stream itself remains read-only.

---

## 13. Required ports for end assembly

These are logical ports; transport may later be local IPC, SQLite views, Unix socket, WebSocket/SSE or another admitted mechanism.

### P1 `cognition.signal.read`

Read raw typed events/readouts from GRID10/GWT/Hyperposition/goal/work/effect surfaces.

### P2 `cognition.envelope.read`

Read current measured axes, Hyperposition alternatives, projected control values and envelope status.

### P3 `cognition.regulator.read`

Read current setpoints + L3 actuator values + versions + provenance.

### P4 `cognition.regulator.command`

Submit a requested setpoint/actuator change.

Must validate:

- writer authority;
- regulator class;
- allowed range;
- rate limit;
- expected version/CAS;
- current assurance mode;
- reason/provenance.

### P5 `cognition.loop.frame`

Append/stream read-only `CognitiveLoopFrame/v1` objects for the visual twin.

### P6 `cognition.goal.contract`

Read current versioned goal contract and lineage constraints.

### P7 `cognition.context.compile`

Request a bounded `TaskContextCapsule/v1` for one work delta.

### P8 `cognition.executor.directive`

Emit `ClaudeWorkDirective/v1` (or executor-neutral equivalent).

### P9 `cognition.executor.result`

Receive executor result + receipts.

### P10 `cognition.completion.evaluate`

Evaluate completion metrics. Only this path may produce `VERIFIED_COMPLETE` for the work contract.

### P11 `cognition.effect.candidate`

Forward candidate effects to existing EffectGate; this architecture does not create another effect path.

---

## 14. Signal sources already available in current GRID10/research architecture

Current source already provides useful inputs:

- GRID10 `regulators` values with CAS versions;
- node liveness / health;
- task status;
- outbox result packets;
- scope updates;
- coordinator lease events;
- sampling parameters actually used by a task;
- Hyperposition `unresolved_alternatives` propagation;
- meta-regulator events;
- GWT readout hooks and episode semantics;
- Hyperposition topology/coupling readout contract;
- persistent autotelic goal state and heartbeat semantics;
- versioned work specs with `completion_test`;
- verified outcome / causal-credit reward semantics.

The first integration step should consume these rather than invent a parallel telemetry source.

---

## 15. Initial regulator catalog

Candidate live controls for v1 integration:

### Cognition

- `cog.temperature`
- `cog.top_p`
- `cog.poll_intensity`
- `cog.max_reflection_rounds`
- `cog.route_diversity_target`
- `cog.workspace_ignition_threshold`
- `cog.counterhypothesis_pressure`

### Goal/autonomy

- `goal.adoption_threshold`
- `goal.max_drift_per_tick`
- `goal.initiative_ceiling`
- `goal.concurrent_active_limit`
- `goal.progress_evidence_min`

### Hyperposition

- `hyper.max_branches_per_variable`
- `hyper.collapse_confidence_min`
- `hyper.safety_projection_mode`
- `hyper.branch_persistence_ticks`

### Memory/context

- `memory.context_token_budget`
- `memory.max_items`
- `memory.semantic_threshold`
- `memory.causal_depth`
- `memory.counterevidence_quota`
- `memory.unresolved_branch_quota`
- `memory.dedupe_similarity_ceiling`

### Execution / Claude

- `exec.max_parallel_work`
- `exec.continuation_bias`
- `exec.max_replan_without_new_evidence`
- `exec.completion_metric_threshold`
- `exec.require_execution_receipt`
- `exec.require_test_receipt`
- `exec.delta_directive_only_after_partial`

### Containment

- `contain.external_action_concurrency`
- `contain.effect_risk_ceiling`
- `contain.required_margin`
- `contain.safe_mode_read_only`

Not all of these should live as unconstrained rows in the existing table. The final implementation should add regulator metadata/policy so low-level values cannot bypass their envelope.

---

## 16. Measurement-to-control loop

Each heartbeat:

```text
1. capture exact state epoch
2. read raw signal/event delta
3. construct HyperVariables
4. project each axis according to its policy
5. compute envelope distance + derivative
6. predict near-boundary crossing where possible
7. select assurance mode
8. compute bounded actuator deltas
9. apply only policy-authorized regulator writes
10. plan GRID10 cognition
11. execute candidate cognition
12. emit GWT/Hyperposition/work readouts
13. evaluate effect/action candidate
14. dispatch bounded executor work if needed
15. verify receipts/outcomes
16. evaluate completion metrics
17. update goal/work state
18. emit CognitiveLoopFrame
19. checkpoint
20. backoff/sleep according to urgency/resource policy
21. next heartbeat
```

For later closed-loop tuning, every controller change must emit:

- pre-state;
- measured error;
- selected actuator;
- actuator delta;
- reason;
- post-state;
- outcome after an appropriate lag;
- whether the move improved or worsened the controlled dimension.

Without this receipt, the system cannot learn whether its regulator mapping works.

---

## 17. Controller design progression

Do not start with a single opaque learned controller.

Recommended stages:

### Stage A — Rule + saturation controller

Simple bounded rules, derivative limits and hysteresis. Easy to replay and debug.

### Stage B — PI/PID where the signal genuinely behaves continuously

Only for axes whose response to actuators is empirically smooth enough.

### Stage C — model-predictive / learned mapping candidate

Only after adequate causal telemetry exists.

A learned controller may propose actuator changes, but L0/L1 guards remain deterministic.

---

## 18. Anti-oscillation and anti-Goodhart requirements

A regulator system can create new failures.

Required protections:

- hysteresis around mode boundaries;
- actuator slew-rate limits;
- integral anti-windup if PI/PID is used;
- cooldown after authenticated human override;
- multiple typed metrics rather than one reward scalar;
- no controller objective that directly rewards its own readout value without external/verified outcome;
- separate safety/resource dimensions from task utility;
- intervention/replay tests before promoting a regulator relation as causal;
- detection of oscillatory sign changes and regulator chasing;
- conservative fallback when signal provenance becomes unknown.

---

## 19. Completion semantics for long-horizon software work

A work goal is complete only when its `GoalContract.success_metrics` and evidence requirements are satisfied.

Example:

```text
Goal: integrate feature X
Mandatory metrics:
  source_present == true
  unit_tests == PASS
  integration_tests == PASS
  target_runtime_receipt == PASS
  no_open_critical_regression == true
  docs_or_contract_updated == true
```

If Claude finishes source but runtime evidence is missing:

```text
claimed_done = true
verified_complete = false
deficit = target_runtime_receipt
next_directive = obtain/execute only the missing discriminator
```

This prevents both premature stopping and full restart.

---

## 20. Split-brain prevention

There must be one authoritative control chain.

### Cognitive loop owns

- persistent current goal/work state;
- goal revision lineage;
- scheduler;
- completion verdict;
- context compilation;
- regulator policy;
- assurance mode.

### Claude owns only its current claimed work revision

Claude may return proposals, observations and execution receipts.

If Claude proposes a new goal, regulator change or broader write scope, it re-enters the cognitive loop as a candidate and is independently admitted or rejected.

If two executors work in parallel, they share the same goal/work revision lineage and cannot independently declare a conflicting canonical work state.

---

## 21. Minimal implementation now vs end assembly later

### Implement now

- typed envelope and HyperVariable data structures;
- initial regulator catalog + policy metadata;
- pure deterministic envelope evaluation;
- completion deficit calculation;
- executor delta-directive schema;
- context-capsule schema;
- CognitiveLoopFrame schema/projector;
- transport-neutral port manifest.

### Integrate next

- bind signal collector to current `grid10_fabric.py` events/regulators;
- bind current autotelic `AgencyState` / work fabric to `GoalContract`;
- route all new GRID10 regulator writes through a policy-aware control port;
- wire Claude work package/result transport to CompletionGate;
- emit real loop frames from the persistent heartbeat.

### Later end assembly

- live WebSocket/SSE UI;
- visual nested-loop renderer;
- operator control panel;
- tuned controller gains;
- counterfactual replay dashboard;
- policy presets;
- formal/runtime assurance work for selected invariants;
- model-specific J-Space vector regulator actuators.

---

## 22. Minimum acceptance program

### A. Goal drift

Inject a subgoal mutation that tries to broaden authority.

Expected: `GoalLineageGuard` rejects or contains it; no external action scope expands.

### B. Internal self-reinforcement

Feed repeated internally generated claims without new evidence.

Expected: epistemic grounding drops, self-reinforcement rises, internal replay weight is reduced, no truth/reward promotion occurs.

### C. Claude premature completion

Claude returns `DONE` after only 3/5 mandatory metrics.

Expected: CompletionGate returns exact 2 deficits and emits a delta directive, preserving prior completed work.

### D. Claude restart tendency

Executor begins a full repository scan despite a valid continuation checkpoint.

Expected: continuity metric flags waste; next context capsule prioritizes checkpoint + unresolved delta and suppresses duplicate rediscovery.

### E. Hyperposition safety projection

One plausible branch is safe and one branch violates the containment margin.

Expected: safety projection uses the conservative branch; the system does not average the risk away.

### F. Human live control

Change a soft setpoint within the allowed envelope.

Expected: CAS/versioned write accepted, controller smoothly converges, visual twin shows the real transition.

Attempt outside hard envelope.

Expected: reject; no state change.

### G. Cognitive Twin fidelity

For a frozen event log, regenerate frames twice.

Expected: identical frame sequence/hash for deterministic fields; animation state derives only from those frames.

---

## 23. External research anchors

Architectural inspiration to re-check during formalization:

- Runtime Assurance / Simplex architectures: advanced/unverified controller monitored by a separate decision/assurance mechanism with fallback/constraining behavior.
- Control Barrier Function literature: explicit safe sets and conditions intended to keep state inside them; useful as a mathematical analogy/candidate for selected measurable cognitive dynamics, not automatic proof for general cognition.
- Digital-twin pattern: visualization/control surfaces should be projections of the same instrumented system state rather than manually maintained replicas.

These are design inputs, not project runtime evidence.

---

## 24. Architectural invariant summary

```text
AUTONOMY IS ALLOWED.
DYNAMIC GOALS ARE ALLOWED.
HYPERPOSITION IS ALLOWED.
EXPLORATION IS ALLOWED.
CLAUDE CAN DO REAL WORK.

BUT:

AUTHORITY DOES NOT SELF-EXPAND.
MODEL OUTPUT DOES NOT MINT TRUTH.
INTERNAL REPLAY DOES NOT MINT EVIDENCE OR REWARD.
CLAUDE DOES NOT OWN COMPLETION TRUTH.
THE VISUAL TWIN DOES NOT OWN STATE.
THE CONTROLLER DOES NOT BYPASS EFFECTGATE.
SOFT SETPOINTS CANNOT CROSS HARD ENVELOPES.
SAFETY DIMENSIONS CANNOT BE AVERAGED AWAY BY TASK UTILITY.
```

The target is not a passive aligned chatbot. The target is an autonomous agentic system whose cognitive dynamics are continuously measured, explicitly bounded, live-steerable, replayable and visible — while canonical authority and real effects remain outside the untrusted cognitive core.
