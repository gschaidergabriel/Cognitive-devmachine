# TRIGGERWORT 4 — Native Subagent Delegation + Workpackage Execution Law

Status: MANDATORY FRANKENSTEIN-2.0 EXECUTION ARCHITECTURE
Date: 2026-08-28

## 1. Owner-original correction: efficiency-calibrated, not absolute

The owner supplied the original `CLAUDE.md` delegation contract. It explicitly corrects the simplistic historical slogan `nie selbst bauen` into:

```text
nicht "nie", sondern "klug"
```

The actual rule is efficiency-calibrated:

```text
SMALL + CLEAR + ALREADY-KNOWN CHANGE
    -> coordinator may do it directly

REAL BUILDING
(new feature / multi-step change / implementation detail / iteration / debugging)
    -> spawned build agent / child harness
```

The goal is maximum efficiency and minimum forgotten work, **not delegation for its own sake**.

This supersedes any Triggerword-4 wording that implied Frankenstein/GRID may never directly perform even trivial deterministic edits.

The original also states the structural PHASE-5 trace:

```text
handoff -> entityos_arbeitspaket + deterministic UnifiedDB capsule
child build agent executes
reconcile -> mechanically checked evidence
invalid/missing evidence -> failed / unbelegte_behauptung, never success
```

Current donor source independently confirms the same `handoff()` / `reconcile()` / `lastschutz` architecture.

## 2. Why delegation exists: preserve the coordinator's cognitive bandwidth

The original contract gives the key systems reason, not just a cost reason:

- implementation details, diffs, failed attempts and debug output stay inside the child context;
- the coordinator's own context stays compact enough to remember multiple outstanding user goals;
- Caveman-compressed coordinator↔worker communication reduces narrative overhead;
- verification is separated from generation/execution;
- the worker can iterate locally without forcing every micro-step through the central cognition loop.

Frankenstein 2.0 should preserve and generalize that property.

Conceptually:

```text
CENTRAL COGNITIVE CONTEXT = goals + state + decisions + evidence + dependencies + unresolved work
CHILD EXECUTION CONTEXT   = local implementation detail + tool output + failed attempts + debug/test iteration
```

This separation is one of the strongest reasons GRID10 should sit **above** native child execution rather than becoming the child itself.

## 3. Efficiency-calibrated execution classifier

Before spawning a model-driven child, classify the work.

### DIRECT_SMALL

Eligible for direct coordinator/controller execution when all are true:

- tiny and bounded;
- obvious implementation;
- no meaningful exploration or debugging expected;
- no large tool-output/context pollution;
- cheaper than spawn/handoff/reconcile overhead;
- still subject to normal authority/effect/completion verification.

Examples: typo, one-line obvious correction, tiny deterministic metadata update, mechanical routing edit already fully specified.

### DELEGATE_BUILD

Use a spawned native build agent/harness when any are true:

- new feature;
- multi-file or multi-step change;
- implementation design is not already closed;
- iterative tool use is needed;
- debugging/testing/revision is expected;
- repository/source discovery is needed;
- substantial output would pollute coordinator context;
- task can run independently while GRID retains other goals.

### GENERATION_ONLY

Pure text/code generation without repository/tool access may use the cheapest currently **authorized/admitted** generation route and then be reviewed/applied by a tool-capable worker/coordinator.

The owner-original historically named a free external pool for this purpose. That is architectural provenance, **not standing provider authority**. Triggerword 4 must obey the current provider/spend admission surface; a historically named provider route must never be silently re-enabled when current authority says it is not admitted.

### DETERMINISTIC

Use deterministic code/SQL/transforms instead of any agent when semantics do not require a model.

## 4. Hard architecture law

```text
FRANKENSTEIN / GRID10 =
    PERCEIVE
  + REMEMBER
  + FORM / CRITIQUE GOALS
  + CLASSIFY WORK
  + DIRECTLY CLOSE TRIVIAL WORK WHEN CHEAPER
  + DECOMPOSE REAL BUILD WORK
  + CREATE DURABLE WORKPACKAGES
  + SELECT EXECUTION/HARNESS UNIT
  + SPAWN / SUPERVISE / ADAPT CHILD WORK
  + FUSE RESULTS
  + VERIFY / REJECT / RETRY
  + LEARN FROM OUTCOMES

NATIVE CHILD AGENT / CHILD HARNESS =
    SUBSTANTIVE RESEARCH / CODING / EDIT / DEBUG / TEST-DRIVEN EXECUTION
```

Thus:

```text
FRANKENSTEIN != NEVER-WRITES-ANYTHING
FRANKENSTEIN != MONOLITHIC-BUILD-WORKER
```

The correct target is an **efficiency-calibrated cognitive orchestrator**.

## 5. Canonical work lifecycle for delegated building

```text
GRID goal / uncertainty / completion deficit
        -> classify: DIRECT_SMALL | DETERMINISTIC | GENERATION_ONLY | DELEGATE_BUILD
        -> if DELEGATE_BUILD:
             WorkContract / entityos_arbeitspaket successor
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

## 6. Native spawn first; bespoke agent runtime only when justified

Where the installed Claude Code runtime exposes native subagent/task facilities that satisfy the required contract, prefer them as the R2 execution substrate.

Do not prematurely build a parallel home-grown agent shell merely because RAH literature uses a generic child-harness abstraction.

Fallbacks such as bounded headless child sessions are legitimate only when a required capability cannot be provided by the installed native mechanism and the difference is measured/documented.

Triggerword 5 must pin the exact installed/current spawn semantics before Frankenstein 2.0 freezes this interface. Tool names and behavior must not be guessed from memory.

## 7. What GRID10 adds above the native subagent loop

GRID should operate one level above the child agent's ordinary local reasoning loop.

GRID controls:

- why a workpackage exists;
- whether work should be direct, deterministic, delegated, recursive or held;
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

## 8. Workpackages become durable cognitive/execution objects

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

## 9. Self-monitoring/adaptation: preserve the emergence, externalize the evidence

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

## 10. Coordination repair is a prerequisite for safe native parallelism

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

## 11. RAH reinterpretation for Frankenstein

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
EFFICIENCY-CLASSIFIED WORK
+ NATIVE SPAWN FOR REAL BUILDING
+ DURABLE WORKPACKAGE
+ EXACT ACTOR/TASK/EFFECT LINEAGE
+ GRID GOAL/RESOURCE/UNCERTAINTY CONTROL
+ GWT/HYPERPOSITION RESULT FUSION
+ COMPLETION VERIFICATION
+ HOLD/WAKE/REENTRY
```

## 12. Required acceptance tests

### NS-00 Efficiency routing
A trivial known one-line task closes directly without child-spawn overhead; a matched substantive multi-step task is delegated. Measure correctness, coordinator-context growth, token/tool cost and completion latency.

### NS-01 Native child execution
A substantive bounded coding/research package is created, a real native child is spawned, and the result returns with exact package/actor lineage.

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

### NS-08 Context-pollution ablation
Run the same multi-step implementation once centrally and once delegated. Compare central-context growth, forgotten/outstanding-goal accuracy, redundant rediscovery and verification quality. This tests the original CLAUDE.md claim that delegation improves coordinator continuity by keeping implementation noise local.

## 13. Triggerword-4 consequence

Every Triggerword-4 run must interpret Frankenstein 2.0 as a **persistent, efficiency-calibrated cognitive orchestrator of native work agents**.

For every new unit of work, the question is:

> Is this cheapest and safest to close directly, deterministically, through a generation-only route, or as a durable native child workpackage — and what evidence closes it?

For real building, the default remains delegation. For trivial, already-understood changes, avoid agent overhead.

This preserves the original design instead of mythologizing it into an absolute rule.
