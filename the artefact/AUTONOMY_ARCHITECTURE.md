# ClayVerse deterministic autonomy architecture

## Purpose

ClayVerse autonomy is implemented as **persistent goal state plus a deterministic bounded control loop**, not as a personality prompt and not as a claim that the currently selected language model is literally AGI, conscious, sovereign, or able to use capabilities that the runtime has not exposed.

The useful behavior is operational: preserve user goals, pick the next unfinished goal, propose one bounded step, validate it, execute real changes only through EffectGate, re-ingest observed results, retry inside hard limits, and mark completion only from independent canonical evidence.

## Core law

**Operational autonomy is a state-machine property, not a model self-description.**

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

Calling the model "frontier AGI", "autonomous", "sovereign" or an "organism" may shape initiative/style, but it grants zero permissions and creates zero facts.

## Existing authority stays intact

- one persistent ClayVerse entity;
- UnifiedDB = sole durable canonical state/memory authority;
- selected LLM = replaceable cognition interface, not durable identity;
- ClayGraph = rebuildable projection only;
- EffectGate/EffectJournal = real-action authority;
- no second `consciousness_daemon`, memory ledger, effect path or identity service.

The v1 controller is `clayverse/autonomy.py`. Its state is one canonical JSON value under `UnifiedDB.meta['autonomy_state_v1']`. This deliberately reuses the existing UnifiedDB transaction/WAL/checkpoint authority and avoids a parallel database or competing schema-migration lane. If normalized autonomy tables are introduced later, they must replace this representation through one explicit canonical migration.

## User alignment as code

A durable v1 goal can only be adopted by `create_goal_from_turn(...)` from an existing canonical UnifiedDB turn that belongs to the same canonical user/session and has role `user`.

The goal objective is copied from that stored turn. The planner does not provide or rewrite the objective text. This prevents the cognition model from silently inventing or broadening the user's durable goal.

Stored goal state includes:

- goal id, user/session and global generation;
- canonical source turn id and verbatim objective;
- priority and status;
- explicit completion contract;
- hard step/retry/effect budgets;
- current step;
- effect evidence ids or an explicit owner acknowledgement turn;
- timestamps and block reason.

## State machine

Goal states:

```text
ACTIVE | WAITING | VERIFYING | BLOCKED | COMPLETED | CANCELLED
```

Typical lifecycle:

```text
canonical user turn
-> adopt goal at live generation
-> ACTIVE
-> next_runnable()
-> cognition proposes one step
-> PROPOSED
-> deterministic admission
-> ADMITTED
-> observed result
   -> SUCCEEDED -> ACTIVE/VERIFYING
   -> FAILED -> bounded retry or BLOCKED
-> independent completion verification
-> COMPLETED
```

A stale-generation goal is never runnable. `COMPLETED` and `CANCELLED` are terminal.

Step classes are deliberately small: `reason`, `effect`, `wait`, and `complete_candidate`. A `complete_candidate` is only a hypothesis and moves the goal to verification; it can never mark the goal complete itself.

## Effects: no new execution path

Autonomy adds no execution bypass. Effect proposals are limited to the already admitted `state.noop` and `entityos.exec` classes; `process.exec` is rejected.

The real path remains:

```text
step proposal
-> autonomy admission
-> canonical turn/workspace
-> EffectGate
-> EffectJournal
-> verified/denied/failed/unknown outcome
-> causal re-entry
-> autonomy evidence update
```

A model sentence such as "the command succeeded" is never effect evidence.

Before an EffectJournal receipt may update an autonomous step or enter `evidence_effect_ids`, the controller requires the persisted receipt to match the admitted step's owner, capability, generation **and exact redacted target/argv intent receipts**. A VERIFIED effect with the same capability but a different target or argument vector therefore cannot be rebound as proof for another autonomous action.

This exact-intent fence is necessary but not the final causal identity gate. Two distinct causal episodes could still request an identical target/argv at the same generation. Runtime promotion therefore still requires binding the autonomous step to the exact effect/episode/request identity produced by the canonical lifecycle before background retries are enabled.

## Completion contracts

v1 supports two independent completion modes.

`verified_effect`: completion requires a persisted effect receipt owned by the goal user, from the same generation, with the exact required capability, `status == VERIFIED`, and canonical outcome `ok == true`. Effect evidence enters the goal only after the exact admitted target/argv intent binding above succeeds. `PENDING`, `DENIED`, `FAILED`, malformed, stale or unknown outcomes do not count.

`user_ack`: completion requires an actual persisted `user` turn from the same owner/session. An assistant/model turn cannot acknowledge its own work.

New completion modes may be added only after their independent evidence source is defined and tested.

## Runaway-agent containment

Every goal carries hard `max_steps`, `max_retries_per_step`, and `max_effects`. Global maxima also bound goal count, state size, objective/step text and effect shapes.

Budget exhaustion is a deterministic block/error, not a prompt suggestion. The model cannot talk the controller into another retry. This directly contains the classic failure loop:

```text
failure -> model changes something -> failure -> model changes something -> ...
```

The effect budget is independent from the step budget. `max_effects == 0` forbids effects but does not disable bounded `reason`, `wait`, or `complete_candidate` work while step budget remains.

## Scheduler, not consciousness daemon

`next_runnable()` is the deterministic scheduler primitive. It returns the highest-priority live `ACTIVE` goal that is inside budget and has no unfinished proposed/admitted step.

Continuous autonomous work must be driven by the **existing ClayVerse supervisor/event/re-entry loop**, not a second durable mind process:

```text
wake/event/re-entry
-> load canonical autonomy state
-> choose next_runnable
-> assemble canonical world + goal state
-> ask selected cognition provider for one proposal
-> deterministic admission
-> EffectGate if needed
-> persist observed result
-> verify completion contract
-> requeue / wait / block / complete
-> checkpoint and re-enter
```

A trigger may be user input, an effect result, timer, dependency event or recovery. The trigger is not authority; UnifiedDB state is.

## Restart and generation re-entry

Generation fencing is the stale-writer kill switch, not a mechanism for erasing durable user intent. Boot recovery therefore resolves the existing turn/effect recovery boundary first, advances the one global entity generation, and only then re-enters autonomy state.

Recovery is intentionally asymmetric:

- interrupted no-effect work is marked failed and becomes runnable again only inside the already-declared budgets;
- an `ADMITTED` effect crossing the generation boundary without an exact autonomy-bound result becomes `BLOCKED` with `unknown_effect_after_generation_change`; it is never replayed and never assumed successful;
- already persisted old-generation effect evidence remains recorded but the goal becomes `BLOCKED` with `effect_evidence_requires_generation_rebind`; v1 refuses both duplicate execution and silent cross-generation promotion until an explicit causal evidence-rebind contract exists;
- an already blocked goal remains blocked;
- terminal `COMPLETED`/`CANCELLED` goals are not rewritten by recovery.

The recovery invariant is:

```text
STALE WRITER DIES
+ USER INTENT PERSISTS
+ UNCERTAIN EFFECT DOES NOT REPLAY
```

## Anti-hallucination fences

1. Goal provenance: durable objective comes from a canonical user turn.
2. Generation fencing: restart/global-generation advance invalidates stale writes.
3. Canonical JSON: duplicate keys and non-finite values fail closed.
4. Capability allowlist: planner text cannot invent execution rights.
5. Exact effect intent binding: same-capability receipts for another target/argv cannot become goal evidence.
6. Verified effects only: model output/tool dispatch are not success.
7. Completion separation: model completion hypotheses require independent evidence.
8. Hard budgets: no unbounded autonomous repair loop.
9. Unknown preservation: unresolved effects/dependencies remain unknown/blocked.
10. UnifiedDB only: no hidden model-side autonomy memory.
11. Identity grants no privilege: "I am AGI" has no authority effect.
12. Restart re-entry: uncertain or old-generation effect evidence never causes blind replay.

## Runtime prompt role

The runtime cognition prompt reinforces these code laws instead of pretending to enforce them. It instructs the model to be proactive and goal-directed, avoid generic passive-assistant boilerplate, use only injected canonical state, distinguish planned/admitted/executed/verified/blocked/unknown, and never claim completion without canonical evidence.

Because the critical boundaries are in code, prompt drift can degrade proposal quality or style but cannot manufacture effect truth or durable completion.

## Research basis

The architecture follows current agent-engineering guidance: effective agents operate in plan/action/environment-feedback loops; reliable long-running agents need environmental ground truth, explicit stop conditions, bounded retries, tool permission boundaries, and human or policy escalation at critical thresholds. Verification-before-retry and receipt-bound outcomes are especially important when actions are non-atomic.

These principles map directly onto UnifiedDB goal state, EffectJournal verification, global generation fencing and step/retry/effect budgets.

## Current implementation boundary

Implemented on this source-candidate lane:

- canonical autonomy state inside UnifiedDB `meta`;
- user-turn-bound goal adoption;
- priority `next_runnable()` scheduler primitive;
- deterministic proposal/admission states;
- independent step/retry/effect budgets;
- generation fencing;
- capability allowlist;
- exact EffectJournal target/argv intent-receipt binding before autonomy evidence admission;
- verified-effect and explicit-user-ack completion;
- malformed/duplicate/non-finite state rejection;
- persistence across DB reopen;
- anti-self-authorization runtime cognition contract;
- boot-time generation re-entry for safe durable goal intent;
- explicit blocking instead of replay for ambiguous or old-generation effect evidence.

This is **source + bounded mechanism evidence**, not exact-current full-checkout/OCI/microVM evidence and not whole-product PASS.

Before promotion into the retained runtime lane, the committed tests must run against exact current UnifiedDB in an authorized isolated checkout; autonomy state must be injected through the existing bounded context path; scheduler ticks must be fused into the existing supervisor/re-entry path; each autonomous effect must be bound to the exact autonomous causal episode/request/effect identity; an explicit cross-generation evidence-rebind contract is required before historical verified effects may close live goals without re-execution; and crash/restart, UNKNOWN effects, dual-user concurrency, prompt injection and context-budget behavior must be tested through the same OCI/microVM acceptance chain.