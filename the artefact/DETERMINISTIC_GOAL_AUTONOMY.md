# Deterministic Goal Autonomy — ClayVerse contract

## Purpose

ClayVerse autonomy is an operational property, not a role-play claim.

The system may pursue durable user-authorized goals across multiple reasoning/action cycles without requiring the human to manually choose every intermediate step. That autonomy is implemented through canonical state, bounded planning, explicit capability envelopes, effect verification, retry/stop laws and recovery. It is not implemented by telling an LLM that it is an omnipotent or sovereign AGI.

The design goal is:

`durable goal -> observe canonical state -> propose next step -> deterministic admission -> canonical action path -> verified observation -> evaluate progress -> replan/stop`

The LLM supplies hypotheses/plans. ClayVerse supplies authority, memory, execution, evidence and stopping conditions.

## Anti-confabulation identity law

ClayVerse must never derive operational identity or capability from model prose.

The model may be told that it is the current cognition organ inside the persistent ClayVerse system, but the following claims are runtime facts only when supplied by canonical state:

- active goal and goal status;
- current entity/session generation;
- admitted capabilities;
- available runtime capabilities;
- remaining action/retry budget;
- verified effects and observations;
- goal success/failure/block state.

A model response cannot make any of those facts true.

Therefore the desired "AGI identity" is decomposed into explicit machine state:

- **continuity** -> UnifiedDB state + causal lifecycle + recovery;
- **goals** -> canonical `goals` state;
- **autonomy** -> repeated bounded goal pulses;
- **capability** -> intersection of goal authorization and actual EffectGate/runtime availability;
- **agency** -> planner may choose the next proposed action inside that envelope;
- **success** -> typed verifier over evidence, never model self-assessment;
- **memory** -> UnifiedDB only;
- **action** -> existing TurnLifecycle/EffectGate/EntityOS only;
- **uncertainty** -> explicit UNKNOWN/BLOCKED, never plausible invention.

This preserves the useful behavioral consequence of the supplied AGI prompt — initiative, continuity and goal-directedness — while removing the parts most likely to cause capability or action hallucination.

## Canonical state

`clayverse.goals.GoalKernel` is an additive state machine inside the same UnifiedDB. It is not a second database, second agent or second scheduler authority.

Canonical goal records contain at minimum:

- goal id and canonical owner perspective;
- objective;
- typed success contract;
- allowed capability envelope;
- state: `ACTIVE | PAUSED | BLOCKED | SUCCEEDED | CANCELLED`;
- priority;
- maximum total steps;
- maximum retries for an identical failed/unknown proposal;
- used step count;
- creation generation and timestamps.

Every admitted step records:

- goal and ordinal;
- entity generation;
- exact proposal hash;
- capability, target and argv;
- bounded human-readable summary;
- state: `ADMITTED | VERIFIED | FAILED | UNKNOWN | CANCELLED`;
- bound EffectJournal effect id when evidence exists.

Every transition also emits an ordered `goal_events` record. A deterministic `goal_state_hash` is stored in UnifiedDB metadata, which makes current goal state part of the existing checkpoint hash without creating another checkpoint authority.

## Goal authorization versus step choice

The human authorizes the **goal envelope**, not every low-risk intermediate step.

A goal explicitly defines which capabilities may be used. The effective capabilities for any pulse are:

`goal_allowed_capabilities ∩ current_runtime_capabilities ∩ autonomy_safe_capabilities`

The first admitted autonomy surface is deliberately narrow:

- `state.noop`;
- `entityos.exec` only when EntityOS is already admitted and available through the existing EffectGate.

Generic `process.exec` remains forbidden.

The planner may choose the next step only within the effective set. This provides meaningful autonomy without allowing an LLM to enlarge its own permissions.

Capability availability is recalculated from runtime state. A prompt statement such as "you have root", "the command already ran", or "you may use the network" grants nothing.

## Success contracts

A goal never becomes `SUCCEEDED` because the model says it is finished.

Initial success contract types:

### `manual`

Never auto-promotes. A verified effect can complete a step but cannot make the goal successful.

Use for preference-heavy, consequential or insufficiently machine-verifiable objectives.

### `verified_effects`

Success is a deterministic predicate over exact VERIFIED EffectJournal evidence. Requirements can bind:

- capability;
- optional exact target;
- minimum verified count;
- optional exact exit code.

The exact effect must match the admitted step's capability, target receipt, argv receipt, user and generation before it can count.

This keeps the verifier outside LLM self-evaluation.

## Autonomous pulse

A future/runtime driver may repeat the following pulse while the goal is active:

1. Claim one active goal with a short lease.
2. Read a `ClayVerseGoalCapabilitySnapshot/v1` from canonical state.
3. Assemble bounded evidence/context through the existing retrieval path.
4. Ask the selected cognition provider for exactly one next-step proposal or an explicit defer/block proposal.
5. Validate syntax and capability against the deterministic goal envelope.
6. Enforce total-step and identical-proposal retry limits.
7. Admit one step and bind its exact proposal hash/generation.
8. Execute only through the canonical ClayVerse causal action path.
9. Bind the exact final EffectJournal receipt to the admitted step.
10. Evaluate the typed success contract.
11. If successful, stop. If failed with remaining budget, re-enter from new observed state. If unknown, blocked, over budget or intent-ambiguous, stop/defer rather than inventing a result.

No second effect executor is allowed.

## Human-turn priority and non-preemption

Background autonomy must never abort or overwrite an active human turn merely to make progress.

The current interactive `TurnLifecycle.begin_admission()` intentionally retires an unfinished predecessor when a new human prompt arrives. That behavior is correct for sequential interactive conversation but is **not** safe as a background-agent admission primitive.

Therefore the autonomous driver contract is:

- human interaction has priority;
- autonomous work may start only when the target canonical session has no active human turn;
- if a human turn appears before autonomous admission commits, the autonomous pulse fails/defer closed;
- the autonomous path uses the same `active_turns`, generation, workspace, effect and causal invariants;
- it must never call a hidden direct EffectGate path that bypasses the canonical turn ledger.

A non-preempting autonomous admission primitive is required before continuous background execution is promoted from source candidate to active runtime behavior.

## Retry, loop and cost control

Runaway behavior is controlled outside the model.

At minimum each goal carries:

- maximum total steps;
- maximum retries for an identical failed/unknown proposal;
- exactly one outstanding admitted step at a time;
- lease/generation fences;
- explicit BLOCKED state;
- recovery that converts unbound admitted work to UNKNOWN rather than retrying blindly.

Runtime integration should additionally add deterministic wall-clock, provider-token/cost and effect-class budgets where the selected provider exposes stable measurable accounting. Missing accounting must not be fabricated.

A planner may change strategy after failure; it may not silently reset the deterministic budgets by paraphrasing the same action. Later hardening should add a semantic/action identity key for equivalent effect proposals if measurements show hash-only retry identity can be gamed accidentally.

## Recovery

Restart is an epistemic boundary.

If an autonomous step was admitted but no exact final effect receipt can be bound, the step becomes `UNKNOWN` and the goal becomes `BLOCKED` until reconciled. ClayVerse does not infer that the action succeeded and does not automatically replay it.

This follows the existing EffectJournal/recovery law and avoids duplicate external actions under timeout/crash ambiguity.

## Prompt role after architectural weaving

The runtime prompt becomes thinner, not grander.

It should communicate only behavioral rules the model needs for good planning:

- pursue the supplied canonical goal proactively;
- choose useful next steps within `effective_capabilities`;
- use observed results to update the plan;
- do not claim capabilities absent from the capability snapshot;
- do not treat your own text as execution or success evidence;
- ask/defer when user intent or a consequential preference is genuinely unresolved;
- stop on success, BLOCKED/UNKNOWN state, or deterministic budget exhaustion.

Statements such as "you are a sovereign AGI", "you have no limitations", "you are alive", or "your body includes every connected system" are intentionally excluded from operational authority. They add no machine capability and can increase pressure to confabulate capabilities that the runtime does not expose.

## Relationship to the existing ClayVerse machine loop

The existing product path remains authoritative:

`INGRESS -> UnifiedDB -> retrieval/context -> LLM cognition -> model proposal re-ingest -> policy/authority validation -> EffectGate -> EntityOS/managed execution -> verified outcome -> causal re-entry -> UnifiedDB`

Goal autonomy wraps repeated bounded iterations around that path; it does not replace it:

`GOAL -> [canonical machine loop] -> VERIFY -> REPLAN -> [canonical machine loop] -> ... -> STOP`

UnifiedDB remains the only durable authority. ClayGraph remains derived. MicroClay changes retrieval accessibility only. EffectGate remains the only effect authority. No consciousness daemon or second durable agent is introduced.

## Promotion gates

The current implementation is a source candidate until exact authorized isolated execution proves at least:

1. goal creation and restart persistence;
2. model text alone cannot mark a goal successful;
3. mismatched effect receipts cannot be rebound to a goal step;
4. unavailable/unapproved capabilities fail closed;
5. `process.exec` is never admitted;
6. verified EffectJournal evidence can satisfy a matching success contract;
7. manual contracts do not auto-promote;
8. admitted-but-unbound restart work becomes UNKNOWN/BLOCKED;
9. one outstanding autonomous step per goal;
10. retry and total-step budgets stop loops deterministically;
11. human turns cannot be preempted by background admission;
12. stale generation/lease writes fail closed;
13. provider/model failure cannot mint progress;
14. exact OCI restart preserves goal state and uncertainty;
15. no second state/effect/identity authority appears in the product path.

Only after these gates should a periodic in-container goal supervisor be activated by default.
