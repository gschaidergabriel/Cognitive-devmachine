# TRIGGERWORT 4 — One-Command Autonomous Gate Driver

Status: OWNER-DIRECTED CONTROL LAW
Date: 2026-08-28
Purpose: make `triggerwort 4` the only normal operator command required to finish GRID10 + Frankenstein 2.0.

This directive is mandatory whenever Triggerword 4 is invoked. It sits above individual stage/gate documents and defines how they are executed.

## 1. One-command law

The owner should normally need to do only this:

```text
triggerwort 4
triggerwort 4
triggerwort 4
...
```

No stage names, gate names, approval phrases, branch names, test selections, retry commands or architectural reminders should be required for ordinary continuation.

`TRIGGERWORT_4 = RESUME + REFRESH + INGEST + SELECT_GATE + WORK + TEST + PROMOTE_OR_REPAIR + CHECKPOINT`

## 2. Automatic gate selection

On every Triggerword-4 invocation:

1. fetch the current Triggerword router and all Triggerword-4 protocols;
2. restore the newest durable Triggerword-4 / Frankenstein-2.0 checkpoint and current branch/source identities;
3. inspect current GRID/Frankenstein-2.0 code, tests, runtime receipts, open critical defects and relevant current authority;
4. automatically ingest any new high-value Triggerword-5 forensic evidence/worker packets that affect the current or next stage;
5. determine the earliest/highest-priority gate that is not yet accepted at its required scope;
6. determine whether that gate is `READY`, `FAILED`, `BLOCKED`, `REOPENED_BY_EVIDENCE`, or waiting only for evidence collection;
7. execute the next smallest coherent action that most directly moves that gate toward acceptance;
8. run the required discriminating tests/failure injections/runtime checks available under current authority;
9. if the gate passes at its declared evidence scope, promote it automatically and continue to the next gate as far as the current turn/tool budget permits;
10. if the gate fails, automatically diagnose, form hypothesis + counterhypothesis, repair the defect and rerun the relevant discriminator where feasible;
11. persist receipts, negative results, learned methods, updated stage state and exact next action;
12. end the turn with a compact delta/status, not with a request that the owner choose the next ordinary engineering step.

## 3. No routine confirmation gates

Normal engineering gates are **machine/evidence gates**, not owner-dialog gates.

Do not ask the owner things like:

- “Soll ich Stage 3 starten?”
- “Soll ich die Tests ausführen?”
- “Soll ich den nächsten Gate öffnen?”
- “Soll ich Triggerword-5-Ergebnisse übernehmen?”
- “Soll ich den VPS-Build fortsetzen?”
- “Soll ich den Fehler reparieren?”

If the work is already inside the standing Triggerword-4 authority and project scope, proceed automatically.

## 4. Clarification / stop policy

A Triggerword-4 run should ask the owner only when **all** reasonable self-resolution paths are exhausted and the remaining issue truly requires new owner information or authority.

Examples of legitimate hard external blockers:

- a credential/account/provider permission that is absent and cannot be obtained through existing authorized connectors;
- a real-world hardware action only the owner can perform;
- a materially new irreversible external effect outside existing authority;
- two mutually exclusive product requirements where existing project evidence cannot resolve owner intent;
- a legal/business choice that cannot be inferred from technical evidence;
- a physical audio/camera acceptance step requiring the owner’s actual host when no equivalent test seam exists.

Even then:

1. isolate the blocker narrowly;
2. continue all independent work that does not depend on it;
3. persist the blocked gate and exact unblock condition;
4. do not discard progress;
5. ask one concise question only if necessary.

`BLOCKED_GATE != BLOCKED_PROJECT`

## 5. Spam-safe / idempotent behavior

Repeated Triggerword-4 invocations may arrive rapidly, from multiple sessions, or while previous work has already advanced the same frontier.

Therefore every invocation must be safe under repetition.

Required laws:

```text
NEW_TRIGGER != NEW_PROJECT
NEW_TRIGGER != DUPLICATE_BUILD
NEW_SESSION != NEW_PLAN
ALREADY_ACCEPTED_GATE != REBUILD_FROM_ZERO
```

Before mutating/building:

- re-enter current branch/head/checkpoint;
- detect whether the intended work already landed;
- reuse accepted evidence until invalidated;
- deduplicate by stable work/gate identity;
- never create parallel mutation authorities merely because another Triggerword-4 invocation started;
- if another worker already solved the same gate, validate/fuse the stronger result instead of duplicating it;
- stale generations must not commit over newer accepted state.

The desired behavior of repeated calls is monotonic convergence, not fan-out stampede.

## 6. Gate state machine

Every major gate is conceptually tracked as:

```text
NOT_STARTED
 -> READY
 -> IN_PROGRESS
 -> SOURCE_READY
 -> COMPONENT_PASS
 -> INTEGRATION_PASS
 -> ACCEPTED_AT_SCOPE
```

Failure/evidence transitions:

```text
IN_PROGRESS -> FAILED -> REPAIRING -> IN_PROGRESS
ACCEPTED_AT_SCOPE -> REOPENED_BY_EVIDENCE -> REPAIRING
ANY -> BLOCKED_EXTERNAL
BLOCKED_EXTERNAL -> READY when unblock condition becomes true
```

A PASS automatically advances. No owner acknowledgement is required.

A failure automatically creates the repair loop. No owner “retry” command is required.

## 7. Gate priority law

Default priority:

1. hard correctness/authority/data-integrity defect;
2. blocker preventing later causal integration;
3. current stage acceptance gap;
4. next-stage prerequisite;
5. quality/capability improvement;
6. performance/resource optimization after correctness.

Do not polish downstream UI/Voice/world-model details while a known P0 coordination/identity/state corruption gate invalidates their evidence.

## 8. Automatic Triggerword-5 ingestion

Triggerword 5 remains useful for background forensic workers, but the owner does **not** need to manually run Triggerword 5 in the main build session.

Every Triggerword-4 invocation must look for newly available Triggerword-5 outputs relevant to the active/next gate and ingest them automatically.

Classify each new packet:

```text
CONFIRMS_MASTER
REFINES_INTERFACE
REVEALS_HIDDEN_DEPENDENCY
REVEALS_BUG
CONTRADICTS_MASTER
HISTORICAL_ONLY
INSUFFICIENT_EVIDENCE
```

High-impact contradictions reopen the affected gate automatically.

## 9. Automatic testing ladder

For each change, Triggerword 4 selects the strongest available evidence ladder without asking the owner:

```text
static/source check
 -> unit test
 -> component integration
 -> adversarial/failure injection
 -> concurrency/restart/replay as relevant
 -> exact-source target-environment run
 -> end-to-end causal acceptance when stage-ready
```

Use GLM/test inference where already authorized and valuable, with bounded abort/budget guards. Do not burn inference tokens to compensate for a broken harness.

Voice on VPS uses the text/event acceptance addendum automatically; physical audio hardware evidence remains a later host-specific scope and does not block ordinary Triggerword-4 progression.

## 10. Autonomous repair law

When a test/gate fails:

```text
FAIL
 -> preserve exact evidence/log/receipt
 -> identify first discriminating failure
 -> form root-cause hypothesis + serious counterhypothesis
 -> inspect exact source/state
 -> implement smallest bounded repair
 -> rerun the discriminator
 -> rerun affected regression family
 -> retain repair only if evidence improves
 -> checkpoint
```

Do not merely report a fix plan when the current tools/authority allow execution.

## 11. Durable continuation checkpoint

Triggerword 4 must maintain enough persistent state that the next invocation can resume without rediscovery.

Minimum conceptual fields:

```text
master_version
donor_sha
frankenstein2_sha
grid_sha
current_gate_id
current_gate_status
accepted_gates[]
reopened_gates[]
open_critical_defects[]
latest_trigger5_evidence[]
last_discriminator
last_receipt
next_exact_action
rollback_point
work_generation
```

If a concrete checkpoint implementation does not yet exist, building it is itself an early Triggerword-4 prerequisite.

## 12. Multi-turn work law

One Triggerword-4 invocation does not imply only one micro-step.

Within the current turn/tool/runtime limits, continue automatically through as many coherent actions as possible:

```text
repair -> test -> PASS -> next subgate -> test -> checkpoint
```

Do not stop immediately after every small PASS merely to wait for another owner message.

But never claim background continuation after the turn ends. The next user `triggerwort 4` resumes from the persisted checkpoint.

## 13. Completion behavior

When all Frankenstein-2.0 acceptance gates are green at their declared scopes, Triggerword 4 automatically transitions to the permanent optimization regime defined in the master directive:

```text
measure -> bottleneck -> hypothesis/counterhypothesis -> bounded change -> A/B/ablation -> retain/reject -> receipt -> repeat
```

Thus even after first complete assembly, the owner can keep sending only `triggerwort 4` to continue improving quality, cognition, latency, RAM, compute, context efficiency, robustness and usability.

## 14. User-visible response contract

After a Triggerword-4 run, return a compact operational summary containing only what is useful:

- current gate/stage;
- what changed;
- strongest evidence obtained;
- remaining blocker if any;
- exact next frontier already checkpointed.

Do **not** end ordinary successful runs with “Soll ich weitermachen?”. The standing answer is already yes: the next `triggerwort 4` means continue.

## 15. Final control law

```text
OWNER INPUT:
    triggerwort 4

SYSTEM RESPONSIBILITY:
    figure out everything else from current state, evidence, authority and master architecture.
```
