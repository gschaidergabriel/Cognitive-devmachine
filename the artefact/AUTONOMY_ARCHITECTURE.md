# ClayVerse deterministic autonomy architecture

## Purpose

ClayVerse autonomy is **persistent user-goal state plus a deterministic bounded control loop**. It is not a personality prompt and it is not a claim that the selected language model is literally AGI, conscious, sovereign or able to use capabilities that ClayVerse has not exposed.

The operational target is:

```text
canonical user goal
-> durable UnifiedDB goal state
-> bounded next-step selection
-> cognition proposal
-> deterministic admission
-> exact causal execution when admitted
-> EffectJournal/environment observation
-> causal re-entry
-> bounded retry/wait/block/complete
```

## Core epistemic law

```text
CLAIM != EVIDENCE
PROPOSAL != ADMISSION
ADMISSION != EXECUTION
TOOL_DISPATCH != SUCCESS
MODEL_COMPLETION != GOAL_COMPLETION
UNKNOWN != SUCCESS
UNKNOWN != FAILURE
FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT
```

Calling cognition "frontier AGI", "autonomous", "sovereign" or an "organism" grants zero permissions and creates zero facts.

## Authority model

Autonomy does not create a new authority:

- one persistent central ClayVerse entity;
- UnifiedDB = sole durable canonical state/world/memory/goal authority;
- selected LLM = replaceable cognition interface;
- ClayGraph = rebuildable projection only;
- TurnLifecycle = canonical observation/workspace/causal spine;
- EffectGate + EffectJournal = action/outcome authority;
- no second memory ledger, effect path, identity service, `consciousness_daemon` or `autonomy_daemon`.

The controller is `clayverse/autonomy.py`. Its state is stored under `UnifiedDB.meta['autonomy_state_v1']`, reusing the existing SQLite/WAL transaction and checkpoint authority rather than introducing a parallel database.

## User alignment as code

A durable goal may be created only from an existing canonical owner `user` turn. The objective is copied from that turn; cognition cannot silently replace or broaden the durable objective text.

The normal managed hook path also supports explicit goal adoption from the newly admitted canonical user turn. Goal adoption occurs only after UserPromptSubmit has created the canonical turn identity.

Stored goal state contains owner/session/generation, source turn and objective, priority/status, completion contract, hard budgets, current step, evidence identities, acknowledgement and timestamps/block reason.

## State machine

Goal states:

```text
ACTIVE | WAITING | VERIFYING | BLOCKED | COMPLETED | CANCELLED
```

Step classes:

```text
reason | effect | wait | complete_candidate
```

A `complete_candidate` is a hypothesis only. It never changes durable completion authority.

`next_runnable()` selects the highest-priority live `ACTIVE` goal within hard budget and with no unfinished proposed/admitted step.

## Human priority and autonomous turns

Autonomous work uses the existing TurnLifecycle with explicit provenance:

```text
source = clayverse-autonomy:goal-step
goal_id
step_id
turn_id
episode_id
causal_id
entity/session generation
```

Autonomy may not preempt a live human turn. A new human prompt may preempt autonomous work.

Human preemption is not allowed to leave an invisible `ADMITTED` zombie:

- before human admission, the managed hook captures the exact autonomous predecessor identity;
- TurnLifecycle performs the canonical abort/preemption;
- if no effect was emitted, the admitted step is re-entered as a normal failed/retryable step inside its existing retry budget;
- if a final effect exists, the controller re-enters that exact effect through `record_effect_result` rather than replaying it;
- a `PENDING` effect blocks preemption/reconciliation until recovery or a final receipt resolves its uncertainty;
- zero remaining retry budget becomes explicit `BLOCKED`, never silent deadlock or invented success.

This preserves both laws:

```text
HUMAN MAY PREEMPT AUTONOMY
AUTONOMY MAY NOT PREEMPT HUMAN
```

without creating a second scheduler or effect path.

## Exact effect admission — before dispatch and after outcome

Autonomous effect safety has two independent fences.

### 1. Pre-dispatch intent fence

An autonomous turn cannot use the generic MCP `request_effect` path. It must call:

```text
request_autonomy_effect(goal_id, step_id)
```

The caller does **not** resupply capability/target/argv. The bridge loads the already-admitted current step from UnifiedDB and requires the active turn to carry the exact autonomous goal/step/causal/generation provenance. Only then is the stored intent passed into the existing `TurnLifecycle.request_effect -> EffectGate -> EffectJournal` path.

Therefore a model cannot execute target B and later discover that target A was the admitted goal step. Intent drift is blocked before any EffectJournal action is started.

### 2. Post-outcome causal evidence fence

A receipt can update an autonomous step only when the controller can prove the exact causal spine:

- same goal owner/session;
- same live generation;
- exact admitted capability;
- exact redacted target receipt;
- exact redacted argv receipt;
- exact workspace episode;
- exactly one causal re-entry;
- exact observation turn;
- observation provenance `clayverse-autonomy:goal-step`;
- exact `goal_id`, `step_id` and `causal_id`;
- observation/effect timestamps after goal creation.

A successful identical effect from another episode is therefore not reusable as goal evidence.

## Completion contracts

`user_ack` requires a later canonical owner `user` turn. The source goal turn cannot acknowledge itself and an assistant/model turn cannot acknowledge its own work.

Automatic `verified_effect` completion is deliberately narrower than general effect execution. Current automatic completion authority is restricted to independently meaningful admitted capabilities such as `entityos.exec`; `state.noop` may exercise the effect spine but is non-rewarding and cannot automatically prove real-world goal completion.

`PENDING`, `DENIED`, `FAILED`, `STALE_OUTCOME`, `UNKNOWN_AFTER_RESTART`, malformed or causally mismatched receipts never count as successful completion.

## Recovery and uncertainty

Global recovery remains the only recovery authority. On generation change:

- stale goal writers are fenced;
- interrupted no-effect steps may be requeued under bounded retry policy;
- admitted effects without safe current-generation evidence become explicit blocked/unknown state;
- old effect evidence is not silently rebound into the new generation;
- completed/cancelled goals remain terminal;
- no external effect is blindly replayed.

Human preemption is handled separately at the same live generation, as described above, so it does not require an artificial global-generation bump.

## Bounded cognition context

The managed context path injects a compact user-scoped autonomy projection, not raw mutable controller state. The projection is bounded and marks itself as data, not instructions, with no truth/effect/completion authority.

Cross-user goal state is not widened by the autonomy context path. UnifiedDB remains canonical; prompt text does not become a second controller.

## Runaway containment

Each goal has hard limits for:

- steps;
- retries per step;
- effects.

Global limits bound goal count and objective/step/effect shapes. Budget exhaustion is a deterministic state/error. Repeated human preemption may consume retry budget; when exhausted the goal becomes explicit `BLOCKED` rather than looping indefinitely.

## Scheduler, not a consciousness daemon

The deterministic scheduler primitive is `next_runnable()`. Continuous work must reuse the existing ClayVerse event/supervisor/re-entry continuum:

```text
wake/event/user/effect/recovery
-> canonical state/recovery check
-> next_runnable
-> bounded world + goal context
-> selected cognition proposes one step
-> deterministic admission
-> exact autonomous TurnLifecycle
-> request_autonomy_effect when needed
-> EffectGate / EffectJournal
-> causal outcome re-entry
-> retry / wait / block / completion verification
-> checkpoint
```

A timer or wake signal is a trigger, not an authority. A future periodic scheduler must call this same controller/lifecycle path and may not create a second durable mind process.

## Anti-hallucination fences

1. Durable objective originates from canonical owner input.
2. Model self-description grants no authority.
3. Duplicate/non-finite autonomy JSON fails closed.
4. Global generation fences stale writers.
5. Step/retry/effect budgets are code-enforced.
6. Capability allowlist rejects generic host execution.
7. Autonomous intent is exact before dispatch.
8. Exact turn/episode/causal provenance is required after outcome.
9. Identical effects from another episode cannot become evidence.
10. Model completion hypotheses are non-authoritative.
11. User acknowledgement must be a later canonical owner turn.
12. `state.noop` cannot automatically prove real-world completion.
13. Pending/unknown effects are never converted to success or replayed blindly.
14. Human preemption cannot silently strand an admitted step.
15. UnifiedDB remains the sole durable autonomy authority.

## Evidence boundary

Current source has converged substantially beyond the first autonomy draft: explicit goal adoption, bounded goal context, non-preempting autonomous TurnLifecycle, exact causal effect evidence, pre-dispatch stored-intent enforcement, recovery hardening and human-preemption re-entry are now present on `main`.

The exact-head GitHub-hosted autonomy guard was attempted repeatedly, but the observed runs failed before runner assignment/visible steps (`runner_id=0`, `steps=[]`). Those runs provide **zero pytest/runtime credit** and are not ClayVerse semantic test failures.

Promotion still requires an actually-started authorized isolated exact-checkout run of the focused and adjacent regressions, followed by exact OCI build/runtime and the required same-image VM/microVM acceptance path. Source coherence, commits, a workflow definition and pre-step runner failures do not imply whole-product PASS.
