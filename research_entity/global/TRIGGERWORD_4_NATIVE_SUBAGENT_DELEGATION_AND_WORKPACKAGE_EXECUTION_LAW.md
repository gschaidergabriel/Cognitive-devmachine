# TRIGGERWORT 4 — Native Subagent Delegation + Workpackage Execution Law

Status: MANDATORY FRANKENSTEIN-2.0 EXECUTION ARCHITECTURE
Date: 2026-08-28

## 1. Source-backed correction

Frankenstein is not intended to be a monolithic agent that directly performs substantive build work itself.

Current donor source explicitly preserves the owner's earlier `~/CLAUDE.md` discipline:

> `nie selbst bauen, immer an einen caveman-Subagenten geben`

`stern.py` PHASE 5 states that `handoff()` creates the durable delegation trace/context capsule and `reconcile()` requires mechanical evidence before a delegated result can count as success. `stern.py` itself explicitly does not perform the delegation; the coordinator/main Claude Code instance performs native spawning.

Additional current donor evidence:

- `pay.py` describes Architekt mode as `Persona + Bau-Delegation an gespawnte caveman-Agenten.`
- `architekt_governance.md` requires `stern.py handoff` before spawning, `stern.py reconcile` afterwards, and `stern.py lastschutz` before parallel build-agent spawn.
- `architekt_tiefensitzung.md` gives a spawned architect agent an independent multi-stage research/build program and permits work to span sessions.
- historical commits record real parallel fixer-agent interference, proving this is an actually used execution pattern rather than only aspirational prose.

Therefore Frankenstein 2.0 must preserve and strengthen this native execution architecture rather than replacing it with a custom monolithic executor.

## 2. Hard architecture law

```text
FRANKENSTEIN != SUBSTANTIVE_EXECUTION_WORKER
GRID10 != BUILD_WORKER

FRANKENSTEIN / GRID10 =
    PERCEIVE
  + REMEMBER
  + FORM / CRITIQUE GOALS
  + DECOMPOSE WORK
  + CREATE DURABLE WORKPACKAGES
  + SELECT EXECUTION/HARNESS UNIT
  + SPAWN / SUPERVISE / ADAPT CHILD WORK
  + FUSE RESULTS
  + VERIFY / REJECT / RETRY
  + LEARN FROM OUTCOMES

NATIVE CHILD AGENT / CHILD HARNESS =
    SUBSTANTIVE RESEARCH / CODING / EDIT / DEBUG / TEST-DRIVEN EXECUTION
```

Deterministic controller operations such as routing, policy evaluation, DB bookkeeping, scheduling, receipt verification, context compilation and state-machine transitions remain controller functions. Model-driven substantive implementation/research should normally become a workpackage executed by a child agent/harness.

The point is not bureaucracy. Native Claude Code agents already contain a useful local loop: inspect -> plan -> edit/use tools -> test -> revise -> continue. Frankenstein should exploit that loop rather than reimplementing every worker micro-step in GRID code.

## 3. Canonical work lifecycle

Target path:

```text
GRID goal / uncertainty / completion deficit
        -> WorkContract / entityos_arbeitspaket successor
        -> deterministic handoff/context capsule
        -> recursion/execution router
        -> native child agent spawn
        -> SubagentStart binds actor + parent + package + generation
        -> child iterates autonomously inside bounded contract
        -> progress / tool / test / failure events become durable deltas
        -> GRID monitors package health, not every token
        -> if blocked/stale/wrong:
              revise contract | add discriminator child | replace child | HOLD
        -> child result is CandidateResult
        -> reconcile / evidence validation
        -> CompletionGate
        -> ACCEPT | REWORK | REJECT | HOLD
        -> causal outcome + Method Memory + next goal
```

A child saying `done` is never canonical completion.

## 4. Native spawn first; bespoke agent runtime only when justified

Where the installed Claude Code runtime exposes native subagent/task facilities that satisfy the required contract, prefer them as the R2 execution substrate.

Do not prematurely build a parallel home-grown agent shell merely because RAH literature uses a generic child-harness abstraction.

Fallbacks such as bounded headless `claude -p` child sessions are legitimate only when a required capability cannot be provided by the installed native mechanism and the difference is measured/documented.

Triggerword 5 must pin the exact installed/current spawn semantics before Frankenstein 2.0 freezes this interface. Tool names and behavior must not be guessed from memory.

## 5. What GRID10 adds above the native subagent loop

GRID should operate one level above the child agent's ordinary local reasoning loop.

GRID controls:

- why a workpackage exists;
- package decomposition and dependencies;
- priority and scheduling;
- deterministic vs direct-model vs RLM vs full child-harness routing;
- model/capability choice when alternatives exist;
- fanout and concurrency;
- resource budget / `lastschutz` successor;
- required evidence and completion definition;
- when to ask for a counterhypothesis/discriminator;
- when to replace/restart a stalled child;
- when to merge or preserve conflicting results in Hyperposition;
- when a package becomes HOLD and which wake condition resumes it.

GRID does NOT need to micromanage the child's internal edit-test-revise cycle unless evidence shows that intervention improves outcomes.

## 6. Workpackages become durable cognitive/execution objects

The existing `entityos_arbeitspaket` idea is preserved but strengthened.

Minimum successor identity:

```text
workpackage_id
goal_id
session_id
agent_id
parent_agent_id
parent_workpackage_id?
task_id
recursive_call_id?
causal_id
generation
state
contract_version
created_at
updated_at
checkpoint_ref
expected_evidence
completion_deficit
```

Operational child events additionally bind `turn_id` and exact `tool_use_id` / invocation identity where applicable.

Workpackage states should support at least:

```text
CANDIDATE
READY
SPAWNING
RUNNING
WAITING_INPUT
BLOCKED
HOLD
RETRYING
RESULT_CANDIDATE
VERIFYING
COMPLETED
FAILED
RETIRED
```

State changes are canonical control events, not inferred later from prose/timestamps.

## 7. Self-monitoring/adaptation: preserve the emergence, externalize the evidence

A native child harness can already create the useful emergent behavior the owner describes: a sufficiently rich task becomes an internally iterating work loop that observes failures/tests and adapts its next action without a bespoke FSM for every task.

Frankenstein 2.0 should preserve this.

But:

```text
CHILD_INTERNAL_ITERATION != DURABLE_CONTROL_STATE
```

The only record of progress must not live inside one hidden context window.

Hooks/events should expose enough structure for the parent system to know:

- child exists / stopped;
- package/task identity;
- latest meaningful progress/checkpoint;
- tool/effect lineage;
- tests/evidence produced;
- blocker/wait state;
- result candidate;
- restart/replacement relationship.

That lets the native child remain autonomous while GRID can recover, replace or resume it after context/process failure.

## 8. Coordination repair is a prerequisite for safe native parallelism

Historical evidence already contains a concrete parallel fixer race: one worker accidentally staged a line from another worker's in-progress fix, temporarily producing an inconsistent source state.

Therefore the native multi-agent design strengthens, rather than weakens, the Stage-1 coordination requirement.

Before whole-system credit, prove:

- immutable child identity;
- explicit parent/package/task lineage;
- exact invocation/effect identity;
- path/worktree/edit ownership or collision detection where needed;
- per-child delivery/ACK;
- stale-generation rejection;
- child replacement lineage;
- result reconciliation without timestamp guessing;
- concurrent children cannot transplant each other's tool/effect/test receipts.

Do not solve this by disabling parallelism globally. Solve attribution and ownership.

## 9. RAH reinterpretation for Frankenstein

The Triggerword-4 RAH taxonomy remains useful, but R2 must be read through Frankenstein's existing execution pattern:

```text
R0 = deterministic computation
R1 = bounded recursive model call
R2 = native spawned child agent/harness workpackage
R3 = GRID chooses/decomposes/supervises R0/R1/R2 and fuses results
```

The important novelty is not `spawn agents` by itself; Frankenstein already did that.

The upgrade is:

```text
NATIVE SPAWN
+ DURABLE WORKPACKAGE
+ EXACT ACTOR/TASK/EFFECT LINEAGE
+ GRID GOAL/RESOURCE/UNCERTAINTY CONTROL
+ GWT/HYPERPOSITION RESULT FUSION
+ COMPLETION VERIFICATION
+ HOLD/WAKE/REENTRY
```

## 10. Required acceptance tests

At minimum:

### NS-01 Native child execution
A substantive bounded coding/research package is created, a real native child is spawned, the parent/controller does not perform the implementation itself, and the result returns with exact package/actor lineage.

### NS-02 Child autonomous revision
The child encounters a deliberately failing first attempt/test, adapts and reaches a corrected candidate result without the parent scripting each intermediate action.

### NS-03 Evidence before completion
A child claims success without valid evidence -> package remains unaccepted/rework. Valid bound evidence -> CompletionGate may close it.

### NS-04 Parallel isolation
Two children edit/test separate packages concurrently; actor/task/tool/effect/result lineage cannot cross-transplant. Include an adversarial collision variant inspired by the historical parallel-fixer race.

### NS-05 Replacement
Kill/stall one child -> controller detects package liveness deficit -> replacement child receives a rebuilt handoff/checkpoint -> stale child generation cannot later commit.

### NS-06 Parent restart
Parent/GRID process/session restart -> active child/package state is reconstructed from durable coordination state rather than hidden chat history.

### NS-07 Adaptive decomposition
A complex goal is decomposed into multiple workpackages only when useful; a simple task does not spawn unnecessary children.

## 11. Triggerword-4 consequence

Every Triggerword-4 run must interpret Frankenstein 2.0 as a **persistent cognitive orchestrator of native work agents**.

When a substantive implementation task is selected, the default question is not:

> What code should Frankenstein itself write?

It is:

> What bounded workpackage should GRID create, which native execution unit should own it, what evidence closes it, and how will the result re-enter cognition?

This rule is compatible with the one-command UX: the owner still only needs `triggerwort 4`; spawning, supervision, repair, evidence and promotion are internal operations of the Triggerword-4 system.
