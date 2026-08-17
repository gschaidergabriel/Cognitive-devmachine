# ClayVerse autonomy architecture

ClayVerse autonomy is **runtime architecture, not an AGI role-play prompt**. The useful properties of a strong agent identity—continuity, initiative, goal focus and causal persistence—are encoded as canonical state, deterministic transitions and bounded execution gates. Claims such as “sovereign AGI”, consciousness or unrestricted capability have no authority.

## One canonical durable authority

`UnifiedDB` remains the sole durable state authority. `AutonomyController` owns `autonomy_state_v1`: user-owned goals, canonical objective source turn, generation, scheduling status, completion contract, budgets, counters, current step and evidence references. There is no second goal database and no hidden scheduler memory.

The durable goal objective is copied from the canonical owner **user turn**. Cognition may reason about that objective but cannot silently rewrite or broaden it.

`AgencyView` adds a frozen server-side operating profile over that state:

- identity mode: `PERSISTENT_GOAL_AGENT`
- substrate anchor: `SERVER_UNIFIEDDB`
- behavior mode: `PROACTIVE_GROUNDED`

This profile describes how the runtime operates. It is not a claim of biological life, consciousness or unrestricted AGI capability.

## Explicit goal admission

Interesting conversation is not automatically converted into a durable goal. Goal/control mutations use dedicated owner-scoped AgencyGate tools during an active canonical user turn.

A goal mutation must carry an exact `authorization_quote` from that current prompt. ClayVerse verifies the quote against the active user turn and journals a control receipt containing the source turn id and a digest of the quote. The model therefore cannot create, pause, resume, cancel or acknowledge a durable goal from its own text alone.

Goal creation calls `AutonomyController.create_goal_from_turn`, so the actual durable objective is the already-recorded human turn rather than a model-written paraphrase.

## Autonomous machine loop

The process-local `AutonomyScheduler` is a timer/driver, **not a second durable mind**. Each wake opens canonical state again and asks `AutonomyController.next_runnable()` for work. If no runnable goal exists, no model call occurs.

A bounded wake executes the following loop:

1. load the highest-priority runnable canonical goal;
2. persist an autonomous observation;
3. assemble owner-scoped world/agency state and live EffectGate capabilities;
4. ask cognition for exactly one schema-constrained next-step proposal;
5. persist that proposal;
6. ask `AutonomyController` to propose/admit the step under generation and budget fences;
7. route operational effects only through `EffectGate`;
8. persist/re-ingest the observed effect outcome;
9. let `AutonomyController` independently match EffectJournal identity, generation and exact redacted target/argv intent before accepting the receipt;
10. test the independent completion contract; then continue only while a bounded wake still has runnable work.

The scheduler uses explicit step markers (`REASON`, `EFFECT`, `WAIT`, `COMPLETE_CANDIDATE`). A text/effect mismatch fails closed. A `WAIT` yields after one bounded step, and a wake has a hard maximum number of steps.

Background cognition uses the canonical goal owner's persistent terminal `HOME`; it does not attach to tmux, simulate browser input or inherit another user's authentication context.

## Anti-hallucination laws

The architecture enforces these distinctions:

`proposal != admission != execution != verified success != completed goal`

A model sentence is never evidence that an action happened. An operational effect is evidence only after the canonical EffectGate/EffectJournal receipt is verified. `PENDING`, missing, malformed, stale, denied or failed outcomes are not converted into success.

A `COMPLETE_CANDIDATE` is only a hypothesis. Completion becomes authoritative only when the canonical completion contract succeeds:

- `verified_effect`: persisted EffectJournal evidence satisfies the required capability and canonical fences;
- `user_ack`: a fresh canonical owner user turn acknowledges completion.

This prevents fluent self-certification from becoming state truth.

## Bounded autonomy / runaway protection

Canonical goal budgets limit:

- total admitted steps;
- retries per step;
- effectful steps.

The scheduler adds a wake-level step bound and a minimum interval between wakes. Invalid proposals, stale generations, exhausted budgets, runtime failures and unverified completion fail closed instead of entering tight retry loops.

The scheduler carries no durable hidden state across restart. Restart reconstruction comes from `UnifiedDB`, checkpoints and canonical causal/effect state.

## Concept -> Prototype -> Final

`CONCEPT -> PROTOTYPE -> FINAL` is retained as a **deterministic delivery projection** over the one canonical goal/effect state. It is intentionally not a second milestone state machine, because duplicate authorities can drift.

`AgencyView` derives the phase lens from canonical counters, evidence and completion state. The phases are useful for user-facing progress and delivery discipline while `AutonomyController` remains the single source of completion truth.

## ERS

ERS is observational telemetry only. It is derived from observed non-`state.noop` effect outcomes. `state.noop` cannot inflate reputation. ERS cannot grant capabilities, bypass EffectGate, alter a completion contract, create a goal or authorize spending.

## Explicit exclusions

This architecture contains no USB identity anchor, crypto identity key, smart contract, escrow or autonomous financial authority. It also makes no consciousness claim. The persistent anchor is the server-side ClayVerse runtime and its canonical UnifiedDB state.
