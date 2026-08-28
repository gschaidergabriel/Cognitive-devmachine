# TRIGGERWORT 4 — Agent Zero × Project Frankenstein Consciousness × GRID10 Fusion

Status: CURRENT ARCHITECTURE ADDENDUM
Date: 2026-08-28
Scope: Frankenstein 2.0 persistent cognition runtime and GRID10 placement

## 0. Core decision

Frankenstein 2.0 must not copy either Agent Zero or Project Frankenstein's `consciousness_daemon.py` wholesale.

They solve complementary halves:

- **Agent Zero** contributes a strong task-local agent loop: iterative monologue/tool use, superior→subordinate delegation, isolated child contexts, report return, projects/memory, and unattended scheduled executions.
- **Project Frankenstein Consciousness Daemon** contributes a persistent off-chat state organism: workspace snapshots, attention competition, prediction outcomes, persistent goals, experience vectors, idle/deep/recursive reflection, consolidation, rumination detection, and continuous event/state updates outside the LLM.
- **Frankenstein 2.0 / GRID10** must fuse these into a new architecture: a cheap persistent pulse kernel outside the model, with bounded event-triggered GRID cognition bursts and native child-agent execution beneath it.

Canonical statement:

```text
AGENT_ZERO_TASK_LOOP
+
FRANK_PERSISTENT_STATE/PREDICTION_LOOP
+
GRID10_GWT/HYPERPOSITION/RESEARCH_SUBSTRATE
=
FRANKENSTEIN_2_PERSISTENT_PULSE_COGNITION
```

This is a successor architecture, not Agent Zero with extra modules.

---

# 1. What Agent Zero contributes

## 1.1 Task-local monologue loop

Agent Zero's main cognitive execution is an iterative loop that repeatedly:

```text
prepare prompt/context
-> call model
-> inspect tool/result request
-> execute tool/subordinate action
-> feed result back
-> repeat
-> stop on final-response condition
```

This is valuable as the **local execution cognition pattern** for an admitted task or workpackage.

Frankenstein 2.0 should preserve the useful property that a worker can locally perform:

```text
inspect -> plan -> act -> observe -> revise -> act -> finish candidate
```

without forcing the global coordinator to micromanage every step.

## 1.2 Native subordinate agents

Agent Zero's superior/subordinate pattern confirms the architectural value of keeping focused child contexts separate from the superior's main context. Frankenstein already has the same owner-originated principle with native Claude/Caveman workpackages.

Therefore:

```text
GRID != implementation worker
GRID -> WorkPackage -> native child harness -> evidence/result -> GRID/CompletionGate
```

## 1.3 Scheduler / unattended task execution

Agent Zero supports scheduled/planned/ad-hoc unattended agent executions. Frankenstein 2.0 generalizes this into a stronger persistent Agency/DeferredIntent/HOLD-WAKE runtime where the wake trigger may be time, event, condition, new observation, worker completion or causal state change.

## 1.4 Agent Zero anti-patterns to avoid

Known current Agent Zero architecture issues are useful falsifiers for Frankenstein 2.0:

- context can become long enough that user intervention loses effective priority;
- subordinate depth/call count can be insufficiently bounded;
- repeated prompt/tool reconstruction can waste large amounts of context/compute;
- persistent memory can preserve stale or false assumptions unless curated.

Frankenstein 2.0 therefore requires:

```text
INTERRUPT_EVENT > CURRENT_MODEL_CONTEXT_PRIORITY
RECURSION_DEPTH/BUDGET = EXPLICIT
DURABLE_CONTEXT != FULL_PROMPT_REBUILD
STALE_MEMORY != CURRENT_EVIDENCE
```

---

# 2. What the Project Frankenstein Consciousness Daemon contributes

The old daemon was primitive relative to GRID10 but structurally important because it placed identity/state/cognition timing outside the LLM.

Its useful mechanisms are classified below.

## 2.1 WorkspaceSnapshot -> SituationFrame / GWT input

Old daemon:

```text
body
mood
memory
identity
environment
attention_focus
energy
```

2.0 successor:

```text
SituationFrame
  observed_state
  agency_state
  active_goals
  open_loops
  presence/perception
  relevant_memory_refs
  world_model_refs
  prediction_residuals
  worker/task deltas
  effect/completion deficits
  uncertainty/conflict
  resource/assurance state
```

The old textual `[INNER_WORLD]` style is not the canonical state. The typed `SituationFrame` is.

## 2.2 Attention competition -> pulse admission + GWT salience

Old Frank continuously scored competing attention sources.

2.0 keeps the principle but splits it into two layers:

1. **Pre-GRID deterministic/event salience** decides whether cognition is worth waking.
2. **Inside GRID/GWT candidate salience** decides what enters the global workspace.

No LLM is allowed to be the sole arbiter of whether cognition wakes.

## 2.3 Prediction engine -> PredictionContract + residual

Old Frank stored predictions and later outcomes/surprise.

2.0 promotes this into a first-class causal object:

```text
PredictionContract
  prediction_id
  hypothesis_id
  predicted_state/range
  confidence
  expected_time/event
  observable_discriminator
  source_model/view
  causal_id
```

Later:

```text
PredictionContract + ObservedOutcome -> PredictionResidual
```

The residual updates Hyperposition, World Substrate, Method Memory and causal credit.

## 2.4 Experience vectors -> StateFingerprint / novelty trajectory

The old 64-d experience vectors and novelty/drift/recurrence detection are useful as a cheap state-change sensor.

2.0 successor:

```text
StateFingerprint_t
compare with recent / episodic / analogous states
-> novelty
-> recurrence
-> drift
-> cycle similarity
-> anomaly
```

This is a preconditioner for retrieval and pulse admission, not a claim of consciousness.

## 2.5 Persistent goals -> Agency Kernel

Old Frank had persistent goals with activation/decay.

2.0 moves authoritative goal state entirely outside GRID into the Persistent Agency Kernel.

GRID may:

- propose GoalCandidates;
- critique goals;
- estimate value/information gain;
- propose activation/retirement/HOLD;

but only the Agency Kernel writes canonical GoalContract state.

## 2.6 Idle/deep/recursive reflection -> bounded REFLECT operation

Old Frank ran free-form idle/deep/recursive reflection on schedules and gates.

2.0 keeps reflection but removes open-ended self-text as the core mechanism.

`REFLECT` must have an explicit target and exit condition, e.g.:

```text
resolve contradiction
compress repeated failure
extract method
identify missing discriminator
re-evaluate stale goal
update causal operator
```

Every reflection must end in one of:

```text
METHOD_UPDATE
HYPOTHESIS_UPDATE
GOAL_PROPOSAL
DEFERRED_INTENT
NO_USEFUL_DELTA
ACTION/OBSERVATION_PROPOSAL
```

No useful delta -> stop.

## 2.7 Rumination detector -> anti-loop regulator

This mechanism should become stronger in 2.0.

Detect:

- repeated hypothesis cluster;
- repeated tool/action request;
- low information gain;
- stagnant state fingerprints;
- repeated failed plan family;
- repeated child-workpackage pattern;

Then force one of:

```text
DISCRIMINATING_OBSERVATION
ALTERNATIVE_HYPOTHESIS
CONTEXT_RESET/RECOMPILE
HOLD
ESCALATE_MODEL/HARNESS only if value-positive
```

## 2.8 Ultradian focus/diffuse/consolidation -> adaptive cognitive modes

Do not copy fixed biological timing literally.

Preserve the functional distinction:

- `FOCUS`: exploit current model/goal;
- `DIFFUSE`: increase hypothesis diversity / lateral retrieval;
- `CONSOLIDATE`: no new broad exploration; compress outcomes/memory/methods.

Mode transitions should be evidence/resource/state driven, not hard-coded 90/20/10 minute biological imitation.

## 2.9 Silence mode -> HOLD

The old daemon's explicit silence concept maps naturally to the stronger 2.0 `HOLD` state.

Difference:

- old silence was experiential/behavioral;
- 2.0 HOLD is a typed causal suspension with persisted wake conditions and exact resume checkpoint.

## 2.10 Consolidation -> Memory Evolution layer

Memory consolidation/aging belongs outside GRID.

GRID supplies utility evidence, contradiction evidence, causal outcome and retrieval-use feedback. A deterministic/micro-neural memory lifecycle service decides promotion, degradation, compression, archive/tombstone or true deletion according to policy.

---

# 3. The new Frankenstein 2.0 pulse architecture

The permanent runtime should be cheap. GRID/model cognition is a burst, not a permanently decoding process.

```text
                  WORLD / SYSTEM / USER / WORKERS
                              |
                              v
                    EVENT + STATE INGEST
                              |
                              v
                 PERSISTENT PULSE KERNEL
        (deterministic + tiny local vector/micro-model logic)
                              |
        +---------------------+--------------------+
        |                     |                    |
  StateFingerprint      Prediction residual    Goal/Open-loop
        |                     |                    |
        +---------------------+--------------------+
                              |
                    PulseAdmissionScore
                              |
                 low value --> WAIT/HOLD
                              |
                 high value / wake condition
                              v
                       COGNITIVE PULSE
                              |
                              v
                       SituationFrame
                              |
                              v
                           GRID10
                 + Hyperposition + GWT
                              |
                ACT | ASK | OBSERVE | SPEAK
                DELEGATE | REFLECT | WAIT | HOLD
                              |
        +---------------------+---------------------+
        |                     |                     |
      Voice              MicroLab/Retina      Native Child
                                                   |
                                            local monologue loop
                                                   |
        +---------------------+---------------------+
                              |
                        Outcome/Evidence
                              |
                 EffectGate / CompletionGate
                              |
                              v
       UnifiedDB + MethodMemory + WorldModel + GoalState
                              |
                              v
                         next pulse
```

---

# 4. CognitivePulse contract

A pulse is not “run the model again”. It is a typed reason to spend cognition.

Suggested fields:

```text
pulse_id
trigger_type
trigger_event_ids[]
created_at
state_generation
agency_generation
salience
uncertainty
expected_information_gain
expected_goal_value
consequence_if_ignored
novelty
prediction_error
user_interrupt_priority
resource_budget
assurance_mode
recommended_topology
resume_checkpoint_id?
```

Pulse sources may include:

- user input/interruption;
- salient Retina PerceptEvent;
- prediction residual;
- worker completion/failure;
- goal wake condition;
- unresolved completion deficit;
- material world-model anomaly;
- scheduled maintenance/research opportunity;
- contradiction/conflict;
- persistent idle opportunity with positive expected value.

---

# 5. What belongs inside GRID10

GRID10 is a cognitive burst workspace. It should not own persistence, clocks, sensors or execution processes.

The baseline 10 slots are **logical functions, not fixed personalities**. They may collapse, duplicate or expand dynamically.

A strong default decomposition is:

## G1 — Orientation / Situation Model

Build the minimal current problem frame:

```text
what changed?
what is controlled?
what is observed vs inferred?
what state matters now?
```

Inputs: SituationFrame, Retina/PerceptualField, StateFingerprint.

## G2 — Goal / Value / Priority

Read active GoalContracts/open loops and evaluate current pressure/value.

Produces candidate next target, not canonical goal mutation.

## G3 — Epistemic Gap / Information Gain

Identify UNKNOWN/CONFLICT/NOT_COMPUTED and ask:

```text
what missing observation would most reduce decision uncertainty?
```

This is the explicit ARC-AGI-3 exploration organ.

## G4 — Hypothesis + Counterhypothesis

Generate materially different explanatory branches and preserve them in Hyperposition.

## G5 — World Projection / Prediction

Request/fuse vector, QUBO, physics or causal views as needed; emit predictions/discriminators.

## G6 — Planning / Prospection

Construct bounded action sequences and estimate likely end states, reversibility and cost.

## G7 — Retrieval / Method Transfer

Select relevant factual memory, causal episodes, Method Memory, negative results and analogies; test transfer conditions before applying old methods.

## G8 — Simulation / Cognitive Micro-Lab

When useful, reduce the question to primitive variables and run deterministic/QUBO/NeRD/other micro-simulations. Simulation output remains hypothesis evidence.

## G9 — Delegation / Harness Routing

Choose the cheapest adequate compute unit:

```text
DIRECT_SMALL
R0 deterministic code/SQL
R1 model recursion
R2 native child harness/workpackage
specialist model
no delegation
```

It specifies the WorkPackage/expected evidence, not the child's implementation steps.

## G10 — Critic / Completion / Stop-HOLD Discriminator

Challenge the current winner:

- enough evidence?
- premature convergence?
- repeated loop?
- effect actually permitted?
- completion evidence sufficient?
- should we WAIT/HOLD instead?

This slot may recommend, but deterministic EffectGate/CompletionGate remain outside GRID.

---

# 6. What must stay outside GRID10

These are runtime organs, not cognitive cells:

```text
UnifiedDB canonical state
Persistent AgencyState / GoalContracts
Heartbeat / Pulse Scheduler
DeferredIntent / HOLD-WAKE registry
Retina continuous low-level processing
PresenceKernel
Memory lifecycle / degradation / consolidation
World Substrate persistence
Xeno Assimilator/Gardener
EffectGate authority
CompletionGate authority
Native child process runtime
Voice realtime transport
credential/permission policy
DB coordination/leases/generation fencing
```

GRID consumes projections of these states and proposes changes; it does not become their authority.

---

# 7. Agent Zero loop placement in Frankenstein 2.0

The Agent-Zero-like iterative monologue is preserved **below GRID** as one possible execution/harness unit.

```text
GRID selects DELEGATE
 -> WorkPackage
 -> native child agent
 -> child local monologue/tool loop
 -> child candidate result + receipts
 -> WorkExecutionBinding
 -> parent re-entry
 -> CompletionGate
 -> GRID/Agency update
```

The superior global entity does not stay trapped inside the child's context while implementation/debugging proceeds.

This is the key difference from simply making GRID itself a recursive monologue.

---

# 8. Interrupt priority

A new user message, high-consequence perception event or authority change must not merely become another chunk buried in a long model history.

It is a typed interrupt:

```text
INTERRUPT
 -> persist/abort or suspend current local cognition as policy allows
 -> invalidate stale ContextView
 -> recompile SituationFrame
 -> new cognitive pulse
```

This directly addresses the known failure mode where long tool/subagent histories can overwhelm a user's intervention.

---

# 9. Memory-evolution interaction

Memory importance must feed pulse cognition without turning recency into truth.

Useful signals include:

```text
semantic relevance
causal relevance
goal relevance
recent access
successful reuse
prediction support/falsification
novelty/anomaly
provenance quality
age
contradiction status
```

Old low-utility information should normally lose retrieval activation before physical deletion. High-use/high-utility memories may graduate to durable/protected status. Raw episodic detail may compress into sparse summaries/operators while provenance remains recoverable when policy allows.

Hard deletion is a separate retention/policy operation, not the normal meaning of cognitive decay.

---

# 10. Pulse cadence law

Do not copy Project Frankenstein's many fixed daemon intervals as the final architecture.

Use a hybrid scheduler:

```text
EVENT-DRIVEN first
+
cheap heartbeat safety net
+
per-goal wake conditions
+
resource-aware maintenance windows
```

The heartbeat should be cheap enough that “nothing worth thinking about” results in near-zero cognitive work.

---

# 11. Required ablations

The fusion earns architecture credit only if measured.

Compare at minimum:

A. task-local Agent-Zero-style loop only
B. + persistent Agency/HOLD-WAKE
C. + Frank-style pulse/state fingerprints/prediction residuals
D. + GRID10 without MethodMemory/world model
E. + full Research-Entity substrate
F. + World Substrate/MicroLab
G. full Frankenstein 2.0 pulse cognition

Metrics:

- successful long-horizon continuation;
- false wake rate;
- missed important wake events;
- actions per solved unknown environment;
- information gain per external action;
- repeated-error rate;
- premature convergence;
- rumination/repetition rate;
- context tokens per completed goal;
- child delegation usefulness;
- stale-memory admission rate;
- prediction calibration;
- recovery after contradiction/failure;
- HOLD correctness;
- completion correctness.

---

# 12. Final architecture identity

Frankenstein 2.0 cognition is therefore:

```text
Persistent Agency Kernel
+ cheap continuous/event pulse
+ typed SituationFrame
+ GRID10 adaptive cognitive burst
+ GWT/Hyperposition
+ externalized memory/world/context
+ native child-agent monologue execution
+ verified outcome re-entry
```

The old Consciousness Daemon becomes a source of mechanisms, not a process to preserve wholesale.

Agent Zero becomes a source of agent-loop/delegation/scheduler mechanics, not the identity of the new system.

GRID10 becomes the bounded integrator that turns persistent state into high-value cognition only when a pulse justifies it.
