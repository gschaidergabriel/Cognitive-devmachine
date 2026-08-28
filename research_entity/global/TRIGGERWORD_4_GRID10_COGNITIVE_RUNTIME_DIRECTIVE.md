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

## Completion before optimization

First priority is executable end-to-end correctness and measured runtime evidence. Source presence or conceptual completeness is not sufficient.

The integration is not `COMPLETE` until the accepted evidence chain demonstrates, at minimum:

`persistent state -> heartbeat -> GRID10 cognition -> envelope evaluation -> bounded regulation -> executor directive -> executor result -> CompletionGate -> verified outcome/effect path -> state/goal update -> next autonomous heartbeat`

with restart/recovery, replay, stale-state, CAS, and containment tests appropriate to the affected path.

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
- ablation results for each major cognitive module/regulator.

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

The trigger must follow newer verified implementations when they supersede these anchors.
