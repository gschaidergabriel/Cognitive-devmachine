# ClayVerse bounded autonomy supervisor

## Status

**SOURCE INTEGRATION CANDIDATE — LIVE PULSE ACTIVATION STILL FAIL-CLOSED.**

This layer turns durable UnifiedDB goals into bounded autonomous work without creating a second agent, state authority, inference engine, effect path or daemon.

## One canonical loop

```text
canonical /goal user turn
-> UnifiedDB goal
-> AutonomyPlanner.prepare_next
-> admitted reason/effect step
-> one-shot autonomy-dispatch lease in existing UnifiedDB.leases
-> detached/idle managed Claude terminal attestation
-> terminal receives only opaque dispatch nonce
-> UserPromptSubmit hook atomically consumes lease
-> system-role autonomous TurnLifecycle with exact goal/step/causal identity
-> Claude reason JSON OR exact request_autonomy_effect(goal_id, step_id)
-> Stop / EffectJournal causal re-entry
-> typed next step / retry / block / completion verification
-> repeat
```

## What the model may and may not do

The model may propose a bounded next step. It does not own:

- durable objective text;
- goal status;
- step admission;
- capability admission;
- target/argv mutation after admission;
- effect success;
- completion truth;
- retry budgets;
- scheduler authority.

`ClayVerseAutonomyDecision/v1` accepts only `reason`, `effect`, or `complete_candidate`. `wait` is deliberately not admitted yet because a typed wake-condition contract has not been implemented.

## Dispatch authority

The terminal prompt is not an instruction authority. It is only:

```text
__CLAY_AUTONOMY_DISPATCH__:<random 128-bit nonce>
```

The real goal id, step id, generation and autonomous instruction remain inside a one-shot generation-fenced UnifiedDB lease. The hook consumes the exact nonce once and then admits a `system` autonomous turn. A user typing a similar string without the live matching lease produces ordinary user input, not autonomous authority.

## Terminal safety

Synthetic input is admitted only after all of these source-level checks:

1. canonical user;
2. process-local Autonomy reservation;
3. no canonical active turn;
4. current managed tmux session exists and passes policy attestation;
5. no tmux clients attached;
6. exactly one pane;
7. pane is alive and not in tmux mode;
8. `pane_current_command == claude`;
9. current Claude pane process started before at least one successful canonical human UserPromptSubmit roundtrip;
10. one live admitted reason/effect step;
11. one exact one-shot dispatch lease.

The process-start check prevents historical successful turns from making a newly started login/consent surface look ready.

If terminal dispatch fails, the exact dispatch lease is deleted and the admitted controller step remains unfinished. No effect is executed and no completion credit is minted.

## Human priority

Human work outranks autonomous work.

- Autonomy may not preempt an active human canonical turn.
- A human prompt may preempt an autonomous turn.
- no-effect preemption re-enters the existing retry budget;
- final-effect preemption re-enters the exact receipt, never replay;
- pending effect blocks until reconciled;
- exhausted retry budget becomes explicit `BLOCKED`.

`terminal_activity.py` is intentionally non-durable process-local arbitration. It owns no state truth. The web terminal and pulse must share the same arbitration instance before live pulse activation is allowed.

## Goal completion

Explicit natural-language goals use `user_ack` unless a stronger typed completion contract exists.

Owner commands:

```text
/goal <objective>
/goal-ack <canonical-goal-uuid>
/goal-cancel <canonical-goal-uuid>
```

Ack/cancel are accepted only from the exact live canonical owner UserPromptSubmit turn and only for goals visible in that owner's user-scoped snapshot. Ordinary prose cannot mutate goal status.

Verified-effect completion requires the exact capability **and exact completion target** plus exact causal goal-step evidence. A generic successful intermediate effect is not goal completion.

## Same-process pulse

`AutonomyPulse` is a normal asyncio task in the existing application process. It opens short-lived connections to the same UnifiedDB, uses the same controller/planner/effect contracts and emits no separate durable queue.

`AutonomyPulseLifecycle` provides FastAPI startup/shutdown callbacks. It does not create another server or process.

## Activation gate still open

The pulse must **not** be installed into the live service until the browser/PTTY path and pulse path demonstrably share one process-local terminal activity arbiter, or an equivalently strong atomic tmux-side arbitration is proven.

Reason: separate `TerminalSessionManager` objects currently create separate registry objects. tmux detached-client attestation is strong but leaves a narrow check-to-send attach race if the browser manager does not participate in the same transient reservation.

The correct repair is small and architectural:

```text
ONE service-process TerminalActivityRegistry
-> ONE shared TerminalSessionManager or shared registry
-> browser attach uses begin_human/end_human
-> pulse uses try_reserve_autonomy/release_autonomy
-> tmux detached/idle attestation remains defense-in-depth
```

Do not activate the timer by accepting that race.

## Evidence boundary

The source modules and focused regressions are not exact-current runtime evidence until an authorized isolated exact-checkout executor actually starts and runs them. GitHub Actions jobs that fail before runner assignment/steps remain zero test credit.

Whole-product acceptance still additionally requires exact OCI build/digest/start/readiness, Clerk/browser/PTTY, real managed Claude runtime behavior, effect/recovery fault tests, dual-user concurrency and the same accepted OCI digest behind the required VM/microVM guest-kernel boundary.
