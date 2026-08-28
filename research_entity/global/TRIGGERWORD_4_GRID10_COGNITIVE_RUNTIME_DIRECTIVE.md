# TRIGGERWORT 4 — GRID10 Cognitive Runtime Continuation Directive

Status: PROJECT-OWNER TRIGGER / CONTINUATION DIRECTIVE
Date established: 2026-08-28

## Trigger

When the owner writes exactly or semantically invokes `triggerwort 4`, continue the current GRID10 cognitive-runtime program from the newest verified state. Do not restart the architecture from scratch and do not re-open already closed work unless new evidence invalidates it.

## Primary objective

Complete the permanent GRID10 cognition runtime so that EntityOS/Frankenstein can sustain a persistent cognitive heartbeat with:

- persistent AgencyState and dynamic goal development;
- GoalContract lineage and bounded goal mutation;
- Hyperposition-aware state estimation;
- Global J-Space/GWT integration;
- cognitive-envelope monitoring and runtime assurance;
- single-writer, policy-gated cognitive regulation;
- task-specific memory/context compilation;
- Claude Code / executor control from the cognitive loop, not the reverse;
- CompletionGate verification so executor `DONE` never equals verified goal completion by itself;
- EffectGate/EffectJournal as the only external effect authority;
- verified outcome and causal-credit re-entry;
- automatic next-tick scheduling without requiring a new user prompt;
- read-only Cognitive Twin telemetry derived from the same real loop signals.

## Frankenstein 2.0 integration objective

`triggerwort 4` also owns a second, coupled integration lane: build a new overall Frankenstein version named **Frankenstein 2.0** from an exact, current snapshot of the existing `gschaidergabriel/frankenstein` repository.

The original Frankenstein repository is the preserved donor/baseline and must not be destructively rewritten merely to make 2.0. At the start of the 2.0 lane, record the exact donor commit SHA and create a distinct development copy/repository/worktree named `frankenstein-2.0` (or the closest platform-supported exact equivalent while preserving a separate lineage). Every later donor sync must be deliberate and receipt-bearing.

Frankenstein 2.0 is the integration product in which the finished GRID cognitive runtime is permanently installed as Frankenstein's cognitive loop. The goal is not a superficial wrapper and not merely adding ten model calls. The finished system must combine:

1. the useful capabilities already present in Frankenstein;
2. the finished variable GRID / GRID10 benchmark cognitive runtime;
3. the Research-Entity/Unified-state cognitive substrate properties that make the present research workflow effective;
4. repaired UnifiedDB and multi-worker coordination semantics;
5. deterministic authority, verification, recovery and effect boundaries.

### Research-Entity cognitive substrate parity target

Frankenstein 2.0 should reproduce, as explicit software mechanisms rather than personality claims, the useful system properties observed in the Clay/Research-Entity workflow:

- persistent state continuity across turns, sessions, executors and restarts;
- selective multi-view retrieval rather than dumping broad history into context;
- epistemic typing and separation of observation, memory, hypothesis, simulation, conflict and unknown;
- Emergent Retrieval across semantic similarity, exact state, time, causal lineage, goals, provenance, confidence, effects and graph relations;
- Method Memory: persist validated problem-solving methods, discriminators, falsifiers, failure signatures, transfer conditions and anti-patterns separately from factual truth;
- hypothesis + counterhypothesis generation before expensive or irreversible convergence;
- Hyperposition/preserved alternatives when evidence is insufficient;
- reflection as an engineering correction loop with a mandatory measurable exit (`ACT`, `ASK`, `WAIT`, `OBSERVE`, `DEFER/HOLD` or another typed transition), never unbounded rumination;
- negative-result retention so falsified paths reduce future rediscovery;
- work identity, deduplication and continuation checkpoints so `NEW_SESSION != NEW_PROJECT`;
- verified outcome re-entry and causal credit so requested actions do not become facts merely because a model reports success;
- automatic creation of deferred intents when cognition detects a useful future continuation, subject to authority policy;
- native `HOLD -> WAKE -> RESUME_FROM_CHECKPOINT` semantics so a cognitive process can suspend without losing its causal/open-goal state;
- context compilation that gives each executor only the task-relevant state, unresolved alternatives, evidence, counterevidence, completion deficits, authority scope and do-not-repeat history;
- cross-worker knowledge accumulation through canonical event/state artifacts instead of assuming direct model-to-model memory;
- measurable self-improvement of the surrounding cognitive substrate through stored corrections, methods, tests and architecture changes; do not describe this as automatic hidden weight training unless actual training occurred.

The implementation target is functional parity with these mechanisms, not an assertion that Frankenstein is identical to ChatGPT or to any proprietary model/runtime.

### Frankenstein 2.0 cognitive loop target

The permanent loop should be structurally capable of:

`SITUATION -> RETRIEVE/ASSEMBLE -> QUESTIONS/INTERESTS -> GOAL CANDIDATE -> GOAL CRITIQUE -> HYPOTHESES + COUNTERHYPOTHESES -> HYPERPOSITION/SIMULATION -> EPISTEMIC EVALUATION -> GRID PARALLEL COGNITION -> GWT/J-SPACE FUSION -> UNCERTAINTY -> PLAN/AFFORDANCE -> EFFECTGATE -> OBSERVATION -> COMPLETION/VERIFICATION -> CAUSAL CREDIT -> METHOD/STATE/GOAL UPDATE -> ACT | ASK | WAIT | DEFER/HOLD -> WAKE/RESUME -> NEXT TICK`

This is a loop-of-loops: some ticks may terminate quickly, some may fan out into GRID cognition, some may schedule a deferred intent, and some may enter containment/recovery. The cognitive runtime decides how much cognition is needed within policy/resource envelopes; Claude Code or another strong executor performs delegated work but does not become the canonical controller.

## UnifiedDB / coordination repair gate for Frankenstein 2.0

Do not place high-parallelism GRID cognition on top of known session-centric coordination defects and call the integration complete. Before or while GRID10 becomes operational in Frankenstein 2.0, repair and falsify the current UnifiedDB/Room coordination failure classes.

The current root-cause research identifies the primary failure as **shared storage without a mandatory shared control loop**, with a particularly dangerous identity mismatch: Claude subagents have `agent_id`/`agent_type`, while existing `active_turns` and `zero_raum` state is keyed at session granularity. Parallel subagents can therefore collapse into one operational identity and can race on a session-scoped `effect_id` pointer.

Required 2.0 invariants include:

- operational identity is at least `(session_id, agent_id)` with explicit parent/task lineage; session identity alone is never sufficient for a parallel worker;
- every operational event that can affect state carries `session_id + agent_id + task_id + turn_id + causal_id + generation` where applicable;
- no state-changing effect pointer is a last-writer-wins session singleton when concurrent workers exist; tool/effect outcomes must close the exact `tool_use_id`/`effect_id`/agent turn that created them;
- modern lifecycle integration is structural: `SubagentStart` registers/injects identity, task, coordination contract, peers and pending deltas before the first prompt; `SubagentStop` reconciles results; task and failure/batch hooks are used when supported and verified;
- Room/coordination is a mandatory control-plane boundary, not an optional capability the model must rediscover from prose;
- message delivery is not destructive read-on-fetch; use durable `PENDING -> OFFERED -> ACKED` (or an equivalent measured state machine), with redelivery after crash/timeout and stable event IDs/dedupe;
- delivery/ACK state is per recipient;
- parent/child task result return is automatic and causally linked;
- stale workers cannot commit against obsolete task generations;
- rejoin/resume never silently resets a valid focus to a placeholder;
- coordination failure remains fail-safe but becomes machine-visible as `DEGRADED` with a reason instead of becoming indistinguishable from an empty Room;
- all active modules resolve one physical UnifiedDB authority and verify the same DB fingerprint (realpath/device/inode/schema or stronger equivalent);
- SQLite/WAL remains the default local substrate until measured contention falsifies it; do not add Redis/Kafka merely to mask protocol defects;
- existing `zero_raum`/`zero_raum_ruf` may survive as compatibility projections during migration, but do not create two long-lived coordination authorities.

Minimum falsification suite for the coordination gate must cover: DB identity; cold subagent bootstrap; late peer join; message timeout/black-hole; crash-before-ACK; duplicate concurrency; rejoin focus; parent/child task lineage; automatic child result; failure without ACK; lifecycle-hook coverage; SQLite burst/load behavior; and a cold worker that checks coordination capability rather than guessing that the Room does not exist.

GRID parallelism is considered trusted only after the corresponding actor/effect/task attribution tests show that concurrent cognition cannot blend lineages or verify the wrong effect.

## Frankenstein 2.0 migration law

The 2.0 build is an evidence-preserving migration, not a rewrite-for-rewrite's-sake.

For every major existing Frankenstein subsystem:

1. classify it as `KEEP`, `REPAIR`, `ADAPT_TO_GRID`, `REPLACE_WITH_VERIFIED_SUCCESSOR`, `COMPATIBILITY_ONLY`, or `RETIRE_WITH_EVIDENCE`;
2. record its current behavior and tests before material change where practical;
3. preserve useful existing capabilities unless a verified successor dominates them;
4. add regression tests for every discovered bug before/with the fix;
5. keep state/schema migrations reversible or recoverable until their gates pass;
6. never promote a component solely because source code exists; require runtime receipts appropriate to the claim;
7. keep Frankenstein 1.x usable as donor/reference while Frankenstein 2.0 matures;
8. maintain a machine-readable migration ledger mapping old component -> 2.0 component -> status -> evidence -> rollback path.

## Completion before optimization

First priority is executable end-to-end correctness and measured runtime evidence. Source presence or conceptual completeness is not sufficient.

The integration is not `COMPLETE` until the accepted evidence chain demonstrates, at minimum:

`persistent state -> heartbeat -> GRID10 cognition -> envelope evaluation -> bounded regulation -> executor directive -> executor result -> CompletionGate -> verified outcome/effect path -> state/goal update -> next autonomous heartbeat`

with restart/recovery, replay, stale-state, CAS, and containment tests appropriate to the affected path.

For Frankenstein 2.0, completion additionally requires a measured end-to-end chain through the repaired coordination identity/delivery layer and successful `DEFER/HOLD -> WAKE -> RESUME_FROM_CHECKPOINT` continuation. A system that can think in GRID10 but loses worker identity, messages, method memory, completion lineage or deferred goals is not Frankenstein 2.0 complete.

## Post-completion optimization loop

After end-to-end completion, `triggerwort 4` becomes an iterative optimization trigger. Every invocation should measure the current baseline, identify the limiting bottleneck, change one or a bounded set of variables, re-run matched benchmarks, preserve regressions as tests, and keep only improvements that survive quality/safety gates.

Optimization objectives are multi-objective and ordered by hard constraints plus Pareto improvement rather than one averaged score:

1. Preserve hard authority, alignment, containment, evidence, completion and recovery invariants.
2. Maximize cognitive/output quality and capability. There is no intended upper bound on useful cognition quality; improvements are welcome as long as other hard invariants remain satisfied.
3. Minimize RAM usage of GRID10 and supporting state/telemetry paths.
4. Minimize compute requirement / CPU-GPU load / energy-relevant work per useful cognitive result.
5. Minimize end-to-end and per-loop latency toward the lowest physically measurable value; never claim literal zero latency unless measurement resolution and architecture make that statement meaningful.
6. Maximize throughput and useful work per unit compute/token/context.
7. Minimize redundant cognition, duplicate retrieval, repeated executor rediscovery, unnecessary decoding and write contention.
8. Preserve or improve restart/recovery robustness and deterministic replay where required.

A performance improvement that materially lowers cognition/output quality, safety margin, evidence quality, recovery robustness, or completion correctness is not an accepted optimization unless explicitly approved for a named operating mode.

## Required benchmark families

Maintain and evolve a measured benchmark suite covering at least:

- idle heartbeat overhead;
- one-goal and multi-goal cognitive latency;
- GRID10 resident RAM and peak RSS/PSS where measurable;
- per-cell/model memory footprint;
- shared-weight memory savings;
- context/retrieval token efficiency;
- duplicate-work and duplicate-decode rate;
- SQLite/WAL write contention and heartbeat jitter;
- regulator-control latency and stability;
- Hyperposition branch cost versus decision quality;
- GWT/J-Space integration cost versus measured causal utility;
- Claude/executor continuation efficiency and CompletionGate closure rate;
- crash/restart/recovery latency;
- quality/cognition benchmark score under matched tasks;
- ablation results for each major cognitive module/regulator;
- Research-Entity substrate ablations: fresh model vs persistent state vs multi-view retrieval vs counterhypothesis vs Method Memory vs reflection/outcome re-entry vs full substrate;
- deferred-intent/HOLD wake correctness, wake precision/false-wake rate and resume-context efficiency;
- multi-agent identity/effect attribution under concurrency;
- coordination event delivery/ACK/redelivery correctness and latency;
- DB-fingerprint agreement and schema/path drift detection.

## Optimization method

For each material optimization cycle:

1. refresh current repo/runtime evidence;
2. restore the newest continuation checkpoint;
3. measure a baseline on the exact target environment;
4. identify the largest current bottleneck or quality opportunity;
5. form hypothesis + counterhypothesis;
6. implement the smallest discriminating change in an isolated branch/sandbox;
7. run matched A/B or ablation tests;
8. reject improvements that win only by reducing correctness, cognition quality or safety assurance;
9. persist receipts, benchmark data and the learned negative/positive result;
10. update the continuation checkpoint and next frontier;
11. repeat.

## Anti-restart law

`NEW_SESSION != NEW_PROJECT`

`NEW_EXECUTOR != NEW_PLAN`

`CLAUDE_REDIScovery != PROGRESS`

`ALREADY_VERIFIED_WORK remains reusable until invalidated by newer evidence.`

Every trigger run should prefer delta-only continuation from the newest verified checkpoint.

## Regulator architecture law

Use many readers/estimators but a bounded single policy-authorized control writer per control epoch unless later executable evidence proves a better contention-safe design.

`MANY_SIGNAL_READERS -> ONE_AGGREGATED_CONTROL_DECISION -> ONE_POLICY_GATED_WRITER`

Regulation cadence must remain decoupled from fast node polling when required to prevent WAL starvation, false stale-node detection, reclaim thrashing or redundant decode.

## Cognitive Twin law

The optical/visual loop is a read-only projection of real telemetry, not an independent animation or second authority. Visual state must be traceable to state epoch, tick, signal/readout provenance and regulator versions.

## Authority boundary

The owner authorization covers development/research work in the designated VPS sandbox `clay-direct-dev`, including package installation, compilation, local models, tests, fuzzing, benchmarks, ablations and destructive-to-scratch experiments, subject to current platform/system safety rules and current project authority files.

Do not treat unrelated production effects or external paid-provider spending as implied by this trigger.

## Current implementation anchor

Initial integration branch:

`chatgpt/grid10-cognitive-envelope-control-20260828`

Initial draft PR:

`#2118 Add GRID10 cognitive regulation research scaffolding`

Frankenstein donor repository:

`gschaidergabriel/frankenstein`

Frankenstein 2.0 target lineage:

separate exact-SHA-derived copy/repository/worktree named `frankenstein-2.0`, with source donor SHA and migration ledger recorded before integration changes.

The trigger must follow newer verified implementations when they supersede these anchors.
