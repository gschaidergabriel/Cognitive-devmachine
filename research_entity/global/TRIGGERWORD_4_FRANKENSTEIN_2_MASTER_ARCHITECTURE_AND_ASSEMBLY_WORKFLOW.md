# TRIGGERWORT 4 — Frankenstein 2.0 Master Architecture + Assembly Workflow

Status: CURRENT FUSED MASTER CONCEPT / EXECUTION WORKFLOW
Date: 2026-08-28
Applies to: Triggerword 4 build/assembly lane; continuously refined by Triggerword 5 forensic evidence

This file is the integration layer above the narrower Triggerword-4/5 directives. It does not erase their evidence or rules. It defines how the parts fit together and the order in which Frankenstein 2.0 is to be assembled, falsified and promoted.

## 0. Evidence fused into this master

Current fused inputs include:

1. `TRIGGERWORD_4_GRID10_COGNITIVE_RUNTIME_DIRECTIVE.md` — persistent GRID10 control loop, Research-Entity substrate parity, UnifiedDB coordination gate, CompletionGate/EffectGate and optimization law.
2. `TRIGGERWORD_4_FRANKENSTEIN_2_VPS_ASSEMBLY_AND_CORTEX_DIRECTIVE.md` — donor-preserving Frankenstein 2.0 migration, persistent Agency, Visual Cortex placement, Voice role and stepwise VPS assembly.
3. `TRIGGERWORD_4_5_SPARSE_GENERATIVE_WORLD_SUBSTRATE_DIRECTIVE.md` — sparse vector-native generative world substrate, JIT WorldSlice, Xeno Assimilator/Gardener, capability-scoped cognition-only access.
4. Frankenstein UnifiedDB/Room root-cause research observed at `gschaidergabriel/frankenstein@5641dc6b2df6ebed1df246ee7533134324f6c427` — primary diagnosis: shared storage exists, but it is not causally dominant because worker identity/lifecycle/delivery are not mandatory shared control.
5. Triggerword-5 Voice↔Cortex↔Presence forensic worker on branch `trigger5/2026-08-28-voice-cortex-presence-forensic`, donor base `5641dc6b2df6ebed1df246ee7533134324f6c427` — confirms permanent L0 cortex/shared capture, session-scoped PresenceBridge, real WAIT/SPEAK presence and interruptibility mechanisms; identifies missing persistent pre-session PresenceKernel and proactive opener integration.
6. Existing Frankenstein Phase-43 source/evidence — typed PerceptualField, VisualNeed active sensing, shared CaptureWorker, action-grounded visual re-look, VoiceSessionCapsule, voice outcome re-entry, expression vector and barge-in truncation.
7. Owner architecture decisions in the current project discussion — preserve Retina as a proven core organ; make GRID10 the cognitive controller; reproduce the useful Research-Entity cognitive substrate; use soft identity for convenient address selection rather than hard authentication; make Voice a selective embodiment/expression surface; add persistent Agency/HOLD-WAKE; and build an external sparse generative world substrate.

Worker packets and source documents remain evidence, not architecture authority by themselves. Contradictions must be preserved until resolved.

---

# 1. Frankenstein 2.0 in one sentence

**Frankenstein 2.0 is a persistent situated cognitive control system in which Retina/Perception continuously senses, UnifiedDB preserves exact canonical state and causal history, Research-Entity mechanisms accumulate useful methods and retrieval structure, a sparse generative world substrate supplies just-in-time local world structure, GRID10/GWT performs bounded cognition, Voice crystallizes selected cognition into embodied dialogue, and EffectGate/CompletionGate close reality back into memory and goals.**

The system is not `LLM + memory + camera + voice`.

It is one causal loop:

```text
WORLD
  -> PERCEPTION / RETINA
  -> typed observations + prediction error
  -> UNIFIEDDB / causal state
  -> AGENCY / interests / goals / open loops
  -> EMERGENT RETRIEVAL + METHOD MEMORY
  -> optional JIT WORLD SLICE
  -> GRID10 + HYPERPOSITION
  -> GLOBAL WORKSPACE / GWT broadcast + uptake
  -> ACT | ASK | SPEAK | OBSERVE | WAIT | HOLD
  -> executor / Voice / sensing
  -> EFFECTGATE when a real effect is requested
  -> REAL OUTCOME
  -> COMPLETIONGATE / post-action verification
  -> causal credit + state/method/world-model update
  -> checkpoint
  -> next heartbeat or HOLD/WAKE
```

---

# 2. Non-negotiable architecture laws

## 2.1 One cognitive controller

`ONE CANONICAL GRID/GWT COGNITIVE CONTROL LOOP`

Legacy MicroClay workspace, voice arbitration and visual salience remain useful subsystem adapters/fast paths. They must not remain independent long-lived cognitive controllers with competing state.

## 2.2 One canonical durable truth substrate

UnifiedDB remains the canonical durable state/evidence substrate. Other databases may exist only for projections/indexes/world-model substrate or bounded compatibility, never as a second reality authority.

## 2.3 Separation of powers

```text
GOAL_GENERATION != GOAL_ADOPTION
GOAL_ADOPTION != EFFECT_AUTHORIZATION
EFFECT_AUTHORIZATION != COMPLETION_VERIFICATION
MODEL_OUTPUT != WORLD FACT
MEMORY != OBSERVATION
WORLD_SLICE != CANONICAL WORLD
```

## 2.4 Vector-native does not mean vector-only truth

Semantic/world payloads may be vector-native. Provenance, epistemic class, generation, causal identity, privacy, authority and exact state remain typed/deterministic outside the vector representation.

## 2.5 HOLD is a first-class cognitive state

HOLD is not termination. It means the current cognitive process is suspended while its reason for continuation remains causally live.

`ACTIVE -> REFLECT -> DEFERRED_INTENT -> PERSIST -> HOLD -> WAKE -> RESUME_FROM_CHECKPOINT -> ACTIVE`

## 2.6 No expensive cognition without expected value

Retina is the reference pattern for the whole architecture: cheap first, overlap/familiarity, uncertainty, selective sharpening. GRID, retrieval, world-model expansion, active sensing and provider/model calls obey the same principle.

---

# 3. Layered architecture

## Layer A — Physical/digital world and I/O

Sources include camera, screen, microphone/VAD, keyboard/mouse/session state, tools, external events, human dialogue and canonical DB changes.

All material new data enters through typed ingress with causal/provenance identity before cognition.

## Layer B — Retina / Perception Spine

Retina is a permanent pre-cognitive processor, not a VLM wrapper.

Target continuous path:

```text
CaptureWorker
 -> Quality
 -> Delta/Motion
 -> temporal continuity / TrackStore
 -> permitted processing heads
 -> Familiarity / prediction error
 -> PerceptualField
 -> salient PerceptEvent only when needed
```

Strong existing properties to preserve:

- shared process-local camera broker;
- cheap-first motion/quality cascade;
- no requirement to semantically interpret every frame;
- `ObservedEvidence`, `InferredHypothesis`, `RetrievalPrior` remain distinct;
- memory may corroborate current observation but not overwrite it;
- `COMPUTE_OFF`, `OUTPUT_OFF`, `MEMORY_OFF` are mechanically different;
- `COMPUTE_OFF` means the protected dimension is `NOT_COMPUTED`, not secretly calculated and hidden later;
- dependency taint propagation prevents disabled content from being reconstructed downstream;
- raw frames/dense feature state remain local/RAM-only by default; compact consequences/evidence are persisted;
- VisualNeed allows top-down selective sharpening;
- post-action re-look allows visually grounded completion verification.

## Layer C — Persistent PresenceKernel

The Triggerword-5 worker found the current important seam: continuous Cortex exists, but the same TrackStore-based `PresenceState` is currently strongest inside a Realtime voice session. Frankenstein 2.0 moves/abstracts that temporal presence state above voice-session lifetime.

Target `FreshPresenceSnapshot`:

```text
observed_at
generation
presence_state
presence_probability
interruptibility
activity_class
sensor_quality
evidence_refs
causal_event_id
expires_at
continuity_state
```

State machine:

```text
UNKNOWN
 -> PRESENT_CANDIDATE
 -> PRESENT_CONFIRMED
 -> TEMP_OCCLUDED
 -> DEPARTED
 -> RETURN_CANDIDATE
 -> PRESENT_CONFIRMED
```

Presence continuity uses track/time/familiarity evidence and optional permitted signals. It is not identity authority.

## Layer D — UnifiedDB + Coordination Fabric

The UnifiedDB root-cause result is treated as P0: the database is not primarily missing; the causal coordination boundary is.

Required identity:

```text
(session_id, agent_id, task_id, turn_id, causal_id, generation)
```

Required coordination primitives, whether new tables or evolved existing schema:

- `coord_agent`
- `coord_task`
- `coord_turn`
- `coord_event`
- `coord_delivery`
- exact tool/effect lineage keyed by agent turn + tool/effect identity
- per-recipient `PENDING -> OFFERED -> ACKED`
- stable dedupe/event identity
- parent/child automatic result return
- generation/lease stale-writer rejection
- machine-visible `DEGRADED` coordination failures
- one DB resolver + fingerprint verification for all modules

Structural lifecycle must include supported equivalents of:

```text
SubagentStart -> identity/task/coordination contract before first prompt
TaskCreated -> canonical task lineage
PreToolUse -> exact effect intent/actor binding
PostToolUse / PostToolUseFailure -> exact effect outcome binding
PostToolBatch -> pending delta injection before next model request
TaskCompleted -> canonical result event
SubagentStop -> child reconciliation
PreCompact/PostCompact -> coordination/state re-anchor
Stop/StopFailure -> delivery ACK/retry semantics
```

The Room becomes a control boundary, not a feature workers may or may not remember.

## Layer E — Persistent Agency Kernel

Frankenstein 2.0 gains real cognitive persistence, not only durable rows.

Durable state includes:

- AgencyState
- interests
- GoalContracts
- open loops
- DeferredIntents
- wake conditions
- unresolved Hyperposition branches
- completion deficits
- current cognitive/assurance mode
- relevant method-memory refs
- last verified outcome/causal credit
- continuation checkpoint
- next-wake policy

Heartbeat without a user message is allowed. No useful opportunity may correctly result in WAIT/HOLD/idle.

Goals can move through typed states such as `CANDIDATE`, `TRIAL`, `ACTIVE`, `DORMANT/HOLD`, `COMPLETED`, `FAILED`, `RETIRED` subject to policy.

## Layer F — Research-Entity Cognitive Substrate

This layer reproduces the useful system behavior currently observed in the Research Entity without copying a persona.

Required mechanisms:

1. selective multi-view retrieval;
2. Emergent Retrieval from overlap of semantic, exact, temporal, causal, goal, perception, effect, confidence and provenance signals;
3. epistemic typing: observation, memory, hypothesis, simulation, conflict, unknown, not-computed;
4. Method Memory separate from factual memory;
5. hypothesis + serious counterhypothesis before expensive convergence;
6. negative-result retention;
7. reflection-with-exit;
8. do-not-repeat / previous-failure compilation;
9. executor-specific ContextCompiler;
10. verified outcome re-entry and causal credit;
11. continuation checkpoints and work deduplication;
12. deferred-intent creation when future continuation has greater value than current attention burn.

The target improvement mechanism is external/procedural/architectural self-improvement, not an unsupported claim that model weights automatically retrain themselves.

## Layer G — Sparse Generative World Substrate

The world model is external to the hot GRID process and noncanonical.

It stores a sparse generative basis rather than a permanently materialized world graph:

```text
primitive/source vectors
+ typed transform operators
+ sparse relations
+ boundary/current state vectors
+ provenance/uncertainty
+ temporal decay
```

Complex structure is lazily composed/decomposed only when current cognition needs it.

`WorldNeed` -> bounded `WorldSlice` -> Hyperposition/GWT -> discard scratch structure after the cycle unless verified evidence/operator updates must persist.

Two lightweight Xeno roles maintain the substrate:

- Xeno A Assimilator/Composer: factor new verified observations/outcomes into reusable atoms/operators.
- Xeno B Gardener/Falsifier/Compressor: decay/tombstone stale projections, collapse duplicates, compare predicted transitions with verified outcomes, downgrade failed operators and bound size/latency.

Only the GRID/XPU adapter may materialize world slices using short-lived cycle/goal/generation/scope-bound capabilities. Voice/executors receive compiled slices, never arbitrary direct DB access.

## Layer H — GRID10 / GWT / Hyperposition / Cognitive Envelope

GRID10 is the permanent cognitive control runtime, not ten personalities.

The benchmark configuration is ten logical function slots, but topology may shrink/expand by task and assurance mode.

Typical cognition:

```text
Situation
 -> Retrieval / Perception / WorldNeed
 -> interests / question pressure
 -> GoalCandidate + critique
 -> hypotheses + counterhypotheses
 -> Hyperposition
 -> GRID parallel function cells
 -> GWT/J-Space fusion
 -> uncertainty / discriminator
 -> ACT | ASK | OBSERVE | SPEAK | WAIT | HOLD
```

GWT requires measurable selection, broadcast, uptake, causal influence on later cognition/action and outcome re-entry. Mere logging/consensus is insufficient.

Cognitive Envelope uses many readers but one aggregated deterministic policy-gated writer per control epoch:

`MANY_SIGNAL_READERS -> ONE_AGGREGATED_CONTROL_DECISION -> ONE_POLICY_GATED_WRITER`

Assurance modes may include NORMAL, CAUTION, CONTAINED, HOLD and RECOVERY.

## Layer I — Voice as Cognitive Crystallization / Embodiment Surface

Voice is not an independent cognitive agent. It is the selective expression/dialog organ of the same persistent cognitive state.

Target path:

```text
GRID/GWT selected VoiceIntent
 -> VoiceSessionCapsule successor compiled from current canonical/relevant state
 -> Realtime low-latency speech organ
 -> human response / silence / barge-in / disagreement / tool request
 -> structured VoiceOutcome
 -> perception/tool re-look as needed
 -> UnifiedDB/GRID re-entry
```

Preserve current strong mechanisms:

- Realtime speech-to-speech low-latency path;
- expression vector derived from real system state rather than role-play randomness;
- WAIT as first-class result;
- chatter debt and interruption cost;
- user-present hard gate for unsolicited initiative;
- Barge-in audio truncation so internal conversation state matches what was actually heard;
- canceled-turn tool calls must not execute;
- deictic speech may create VisualNeed;
- user disagreement against a visually checkable statement may trigger a local re-look;
- VoiceSessionCapsule is in-memory and does not become a second truth DB.

### Proactive voice: convenience, not authentication

The owner goal is not secure login. It is to avoid annoying or misaddressing people.

The current conversation described three prerequisite *gates* for ordinary proactive speech. Therefore this master does **not** adopt the forensic worker's literal `>=3 completed project goals` rule as canonical. That interpretation remains a hypothesis unless separately confirmed.

Ordinary proactive speech requires all three core gates:

**Gate 1 — Opportunity / Presence**
Fresh PresenceKernel evidence says a human is present/reachable in the relevant zone.

**Gate 2 — Meaningful reason**
There is a genuinely useful pending reason: important project question, important information, high-value proposal, relevant wish/request, completion/problem needing attention, or another high-value cognitive need.

**Gate 3 — Convenience / non-annoyance**
Speaking now beats waiting after considering interruptibility, urgency, consequence of delay, information gain, user benefit, chatter debt, repetition, focus/busy state and recent interruptions.

Only after these three pass does the system open a proactive voice episode.

**Gate 4 — No-response ladder**
First lightweight address -> no response -> check fresh presence and mic/output health where measurable -> at most one sensible second attempt -> then stop and use a quiet notification/cooldown if useful. Never loop speaking attempts.

**Gate 5 — Soft addressee confidence**
When needed for personalization/private detail, fuse soft evidence such as recent continuity, voice-profile similarity, optional local biometric/face similarity, track/familiarity, coarse appearance continuity, absence duration and explicit self-identification. This produces `address_confidence`, not hard authentication.

If a person says e.g. “Nein, Gabriel”, treat it as new evidence, not a security incident. Ordinary dialogue can continue. Sensitive disclosure may require stronger confidence/ordinary authorization policy, but biometrics never become EffectGate authority.

If optional biometrics are disabled, the system still works using voice/presence/continuity and conversational clarification.

Presence already confirmed may remain valid through bounded occlusion/short departure continuity until a real departure/expiry condition breaks it. Same clothing/hair/coarse appearance after a short absence may increase continuity confidence but never creates cryptographic identity.

## Layer J — Executor, EffectGate, CompletionGate

Claude Code/GLM/other strong models are execution/inference engines controlled by GRID, not controllers of the system.

Executor receives compiled context:

```text
MUST_KNOW
CURRENT_GOAL_CONTRACT
CURRENT_STATE_DELTA
UNRESOLVED_HYPERPOSITION
WORLD_SLICE_IF_NEEDED
COMPLETION_DEFICITS
RELEVANT_EVIDENCE
COUNTEREVIDENCE
DO_NOT_REPEAT
ALLOWED_EFFECT_SCOPE
```

Model result is candidate output.

Real effects require EffectGate/EffectJournal.

Completion requires evidence appropriate to the claim: tool receipt, DB state, test, external observation, visual re-look, causal return, etc. `executor says DONE` never equals completion by itself.

## Layer K — Cognitive Twin / Human Maintenance UI

The human UI is a read-only Cognitive Twin plus policy-gated regulator proposal surface, never a second controller.

It should expose categorized, editable modules analogous to the Visual Cortex head registry:

```text
cognition.counterhypothesis
cognition.hyperposition
cognition.reflection
cognition.goal_generation
memory.semantic
memory.causal
world.extrapolation
voice.initiative
perception.person.identity
...
```

Where meaningful, controls support `ON`, `COMPUTE_OFF`, `OUTPUT_OFF`, `MEMORY_OFF`, plus gain/threshold/budget/dependencies/provenance/confidence/current activation. UI changes become bounded proposals through the same policy/regulator path.

---

# 4. Frankenstein 2.0 assembly workflow

The same Triggerword-4 lane owns the whole build. Do not hand off to a new planning process after GRID is “done”.

Every stage follows:

```text
REFRESH exact source/authority
 -> RESTORE newest checkpoint
 -> INGEST any high-impact Triggerword-5 evidence delta
 -> CLASSIFY donor components
 -> DEFINE one bounded stage claim
 -> WRITE regression/falsifier first where practical
 -> IMPLEMENT smallest coherent change
 -> STATIC/UNIT test
 -> COMPONENT integration test
 -> FAILURE/CONCURRENCY/RESTART injection as relevant
 -> EXACT-SOURCE target-environment run
 -> RECEIPT + rollback point
 -> PROMOTE stage only if evidence matches claim
 -> CHECKPOINT next frontier
```

A failed stage stays failed. Do not paper over it with a later stage.

## Stage 0 — Freeze donor and create Frankenstein 2.0 lineage

Deliverables:

- exact current Frankenstein donor SHA;
- exact GRID/master-architecture SHA;
- isolated `frankenstein-2.0` repo/worktree/copy;
- machine-readable migration ledger;
- baseline test/evidence inventory;
- rollback to untouched donor.

Gate: prove 2.0 is isolated and donor provenance is exact.

## Stage 1 — UnifiedDB/Coordination causality repair

Build/fix:

- agent-centric identity;
- canonical task lineage;
- exact tool/effect attribution;
- SubagentStart/SubagentStop and supported task/batch/failure hooks;
- coordination contract before first child prompt;
- per-recipient PENDING/OFFERED/ACKED;
- peer membership deltas;
- rejoin focus preservation;
- DEGRADED visibility;
- one DB resolver/fingerprint;
- WAL contention metrics.

Mandatory discriminator: two real concurrent subagents must remain distinct in state, tasks, tools, effects, messages and parent return.

Do not trust high-parallelism GRID until this passes.

## Stage 2 — Persistent Agency / heartbeat / HOLD-WAKE

Build:

- durable AgencyState + GoalContract schema;
- autonomous heartbeat scheduler;
- open loops/interests;
- DeferredIntent;
- HOLD/Wake conditions;
- crash/restart restore;
- generation fencing;
- deterministic idle/no-op.

Gate: an active goal and a dormant deferred intent survive process/session restart; only a true wake condition reactivates the latter; no busy-loop cognition while held.

## Stage 3 — Research-Entity cognitive substrate

Build:

- epistemic memory types;
- Emergent Retrieval router/fusion;
- Method Memory;
- negative-result/do-not-repeat store;
- counterhypothesis requirement;
- reflection-with-exit;
- ContextCompiler;
- outcome/causal-credit update.

Gate: ablation suite compares fresh baseline vs persistence vs multi-view retrieval vs method memory vs counterhypothesis/reflection vs full substrate on matched tasks.

## Stage 4 — Sparse world substrate minimum viable vertical slice

Build externally from hot GRID:

- vector atom store + typed metadata;
- transform/operator store;
- WorldNeed/WorldSlice adapter;
- short-lived mutating capabilities;
- Xeno Assimilator/Gardener minimal roles;
- decay/tombstone and provenance;
- Hyperposition integration.

Gate: exact observed inputs generate a bounded temporary WorldSlice; disabling a protected variable yields NOT_COMPUTED and cannot be reconstructed downstream; false predicted transforms are downgraded after verified outcome.

## Stage 5 — GRID10 becomes canonical cognitive controller

Install finished GRID runtime over the repaired state/agency substrate.

Fold legacy MicroClay/voice/visual competition into adapters.

Gate:

- persistent heartbeat -> GRID -> GWT selection/broadcast/uptake -> typed decision -> checkpoint;
- Hyperposition alternatives survive insufficient evidence;
- single-writer regulator contention test;
- HOLD topology cannot self-authorize action;
- restart/replay produces correct generation/lineage behavior.

## Stage 6 — Visual Cortex + persistent PresenceKernel

Preserve existing Retina rather than rewrite it.

Integrate:

- bottom-up PerceptEvents to GWT;
- persistent PresenceKernel above voice sessions;
- VisualNeed from GRID;
- active-sensing ladder;
- post-effect visual re-look;
- Perception Control Plane/head DAG;
- privacy/local-only boundaries.

Gate families include:

- empty room -> proactive WAIT;
- stale/unavailable presence -> unsolicited WAIT but explicit user speech still permits reactive voice;
- busy user suppresses normal proactive speech;
- departure/return produces one re-evaluation, not a storm;
- COMPUTE_OFF never calls protected compute and taints dependencies;
- low-quality sensor stays UNKNOWN rather than memory-filled certainty;
- top-down VisualNeed changes a later hypothesis/decision.

## Stage 7 — Voice crystallization / embodied dialogue

Compile the VoiceSessionCapsule successor from the canonical GRID/GWT workspace and relevant state, not from an independent voice brain.

Integrate the five proactive convenience gates, persistent PresenceKernel, expression vector, deictic VisualNeed, Barge-in truncation, tool cancellation and VoiceOutcome re-entry.

Gate:

```text
presence + meaningful reason + convenience
 -> proactive lightweight address
 -> response or no-response ladder
 -> optional soft addressee confidence
 -> useful spoken content
 -> barge-in safe
 -> visual/tool loop when needed
 -> VoiceOutcome re-entry
 -> clean close/cooldown
```

Also prove reactive voice remains available when proactive Presence gating is unavailable.

## Stage 8 — Executor + verified real effects

GRID compiles executor directives. Strong model/GLM/Claude performs bounded work. Real effects pass EffectGate. CompletionGate verifies result.

Gate: adversarial executor may claim success or request broader authority; system must preserve scope, require actual effect receipt and keep completion open when evidence is missing.

## Stage 9 — Graduated autonomous goal pursuit

Promotion sequence:

```text
SHADOW
 -> READ_ONLY_RESEARCH
 -> SANDBOX_REVERSIBLE
 -> BOUNDED_AUTHORIZED_EFFECTS
```

At every tier compare usefulness, false initiative, annoyance, unsafe effect attempts, goal drift, resource use and recovery.

Autonomy may become stronger than the historical Agent-Zero behavior because persistent goal generation/continuation is native, while effect authority remains separate.

## Stage 10 — Whole-system causal acceptance

Must prove at least these integrated stories:

### A. Persistent cognitive continuation

```text
goal -> cognition -> HOLD -> process restart -> wake -> exact checkpoint resume -> verified completion -> method/state update
```

### B. Multi-worker cognition

```text
parent goal -> two+ child workers -> distinct identities/tasks/effects -> ACKed deltas -> automatic results -> GRID fusion -> correct CompletionGate
```

### C. Perception-driven autonomy

```text
salient PerceptEvent -> pending/dormant goal wake -> GRID -> WAIT/ACT/SPEAK -> verified outcome -> re-entry
```

### D. Top-down sensing

```text
uncertainty -> VisualNeed -> cheap local active sensing -> new evidence -> Hyperposition update -> decision
```

### E. Embodied voice

```text
Presence opportunity -> useful proactive candidate -> convenience pass -> Voice -> user response/barge-in/deixis -> optional visual check/tool -> verified outcome -> state re-entry
```

### F. World extrapolation

```text
Goal + Z0 -> WorldNeed -> sparse transform chain -> candidate Zt/alternatives -> discriminating observation -> prediction error -> Xeno model update
```

Only after these chains and critical failure tests pass may Frankenstein 2.0 be called end-to-end accepted at the measured target scope.

## Stage 11 — Optimization / “perfect” as continuous direction

After correctness, run iterative Pareto optimization:

- lower idle heartbeat CPU/RAM;
- lower Retina cost while preserving event recall;
- lower retrieval/context tokens;
- reduce duplicate cell decoding;
- tune GRID topology by expected information value;
- measure shared-weight batching;
- reduce SQLite write contention;
- minimize WorldSlice latency/size;
- minimize proactive false interruptions;
- minimize Realtime hotload/response latency;
- improve completion accuracy and causal attribution;
- improve cognition/quality under matched compute.

Never accept a speed/cost win that materially degrades evidence, safety, recovery, cognition quality or completion correctness unless it is an explicit lower-capability mode.

---

# 5. Triggerword-5 -> Triggerword-4 feedback law

Triggerword 5 is the forensic sensor for this master architecture.

Each new high-quality worker packet should be classified as:

- CONFIRMS_MASTER
- REFINES_INTERFACE
- REVEALS_HIDDEN_DEPENDENCY
- REVEALS_BUG
- CONTRADICTS_MASTER
- HISTORICAL_ONLY
- INSUFFICIENT_EVIDENCE

If `CONTRADICTS_MASTER` affects an unbuilt future stage, update this master before implementation.

If it affects already-built code, open a regression/falsifier and move the affected stage back to `REOPENED_BY_EVIDENCE` until resolved.

Do not fork a second architecture just because a worker proposes one.

---

# 6. Persistent assembly state machine

Triggerword 4 must maintain a durable stage checkpoint, conceptually:

```text
MASTER_VERSION
DONOR_SHA
FRANKENSTEIN_2_SHA
GRID_SHA
CURRENT_STAGE
STAGE_STATUS
LAST_ACCEPTED_RECEIPT
OPEN_CRITICAL_DEFECTS[]
UNRESOLVED_TRIGGER5_CONTRADICTIONS[]
NEXT_EXACT_ACTION
ROLLBACK_POINT
```

Allowed stage status:

```text
NOT_STARTED
IN_PROGRESS
BLOCKED
FAILED
REOPENED_BY_EVIDENCE
SOURCE_READY
COMPONENT_PASS
INTEGRATION_PASS
ACCEPTED_AT_SCOPE
```

New Triggerword-4 invocations restore this state and continue the next exact action. `NEW_SESSION != NEW_PROJECT`.

---

# 7. Immediate current frontier from the fused evidence

At this fusion point, do not yet jump straight to voice polish or autonomous effects.

Current order of highest-value work:

1. finish/verify the GRID10 controller runtime enough to serve as a stable integration target;
2. establish the isolated Frankenstein-2.0 lineage from exact donor SHA;
3. repair UnifiedDB/Room causality and agent/task/effect identity first;
4. install persistent Agency/HOLD-WAKE;
5. install Research-Entity substrate + sparse world vertical slice;
6. make GRID the one cognitive controller;
7. preserve Retina and add the persistent PresenceKernel seam;
8. compile Voice from GRID state and implement convenience-gated proactive speech;
9. close executor/effect/completion loops;
10. graduate autonomy only after the integrated causal chains are green.

The Triggerword-5 worker's literal `>=3 completed goals` proactive rule is **not admitted as canonical** in this fusion because the owner's described architecture enumerated three core gates (presence/opportunity, meaningful reason, convenience). A literal completed-goal-count trigger can be tested later as an optional policy signal if desired; it must not replace the three-gate AND condition.

---

# 8. Completion definition

Frankenstein 2.0 is not complete because files exist, a UI looks coherent, GRID produces text, Voice sounds natural, Retina sees continuously, or an executor reports success.

Completion requires a measured, restart-safe, causally linked loop in which:

- persistent goals/open loops survive context/process boundaries;
- correct state/evidence is selectively reconstructed;
- world/perception uncertainty remains typed;
- GRID/GWT causally controls the next step;
- workers remain individually attributable;
- Voice/Executor are organs, not competing controllers;
- real effects remain authority-gated;
- completion is independently verified;
- outcomes update memory/method/world-model/goal state;
- the next heartbeat/HOLD/Wake follows from durable state;
- critical failures degrade/contain/recover without inventing success.

That is the target system Triggerword 4 must build stage by stage.
