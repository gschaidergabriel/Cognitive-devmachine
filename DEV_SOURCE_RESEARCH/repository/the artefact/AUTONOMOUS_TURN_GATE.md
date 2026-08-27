# Autonomous Turn Gate

## Purpose

Autonomous goal pursuit must enter the same ClayVerse causal runtime as interactive work without becoming a second turn authority and without displacing a human turn.

The gate therefore changes **admission mode**, not the lifecycle/effect architecture.

```text
human prompt
  -> existing preempting sequential admission

autonomous goal step
  -> non-preempting admission
  -> same active_turns / workspace / causal episode
  -> same EffectGate / EffectJournal
  -> same UnifiedDB
```

## Human-priority law

If an `active_turns` row already exists for the canonical session, autonomous admission fails closed with no mutation to that active turn.

A later human prompt is allowed to retire an autonomous predecessor. Human interaction therefore has priority without introducing a parallel queue or second executor.

This asymmetry is deliberate:

```text
AUTONOMY MAY NOT PREEMPT HUMAN
HUMAN MAY PREEMPT AUTONOMY
```

## Identity and anti-hallucination law

An autonomous internal observation is stored as role `system`, never role `user`.

Its provenance binds:

- source = `clayverse-autonomy:goal-step`;
- canonical user/session already owning the TurnLifecycle;
- entity/session generation;
- turn id;
- workspace episode id;
- causal id;
- `goal_id`;
- `autonomy_step_id`.

This prevents planner/internal prose from becoming a new owner-authored goal source merely because it entered the canonical context.

Autonomous admission also skips the immediate explicit-user-memory extraction path. Model/planner prose therefore does not receive user-memory authority at admission.

## Effect law

The gate adds no execution primitive.

An autonomous step requesting a real/state-changing action must still use:

```text
TurnLifecycle.request_effect
-> EffectGate
-> EffectJournal
-> verified/denied/failed outcome
-> causal re-entry
```

No scheduler or model may call EntityOS or a host process directly.

The already-landed AutonomyController target/argv receipt fence prevents a different effect intent from being rebound as the step's evidence. The next consumer-side promotion gate is stronger: `AutonomyController.record_effect_result` must also require the exact autonomous goal-step causal episode/request/effect identity emitted by this gate, so even two identical intents from distinct episodes cannot be confused.

## Completion and failure law

Interactive completion cannot close an active autonomous turn.

Autonomous completion/abort must provide the same `goal_id` + `autonomy_step_id` carried by the active observation provenance. A mismatch fails closed before terminalization.

Autonomous terminal turns use autonomy-specific provenance rather than pretending they came from Claude `UserPromptSubmit`/`Stop` hooks.

## Promotion boundary

This source candidate intentionally does **not** start a periodic background supervisor.

Default-on autonomous scheduling remains blocked until exact authorized isolated execution verifies at least:

1. active human turn cannot be preempted by autonomous admission;
2. human prompt can safely retire autonomous work;
3. autonomous system observation cannot mint a user goal;
4. autonomous effects use the same workspace/effect/causal path;
5. completion and abort require exact goal-step provenance;
6. AutonomyController consumes only the exact matching autonomous causal receipt;
7. restart/UNKNOWN effect recovery never blindly replays an effect;
8. dual-user concurrency does not fork global entity state;
9. step/retry/effect/time/cost ceilings stop runaway loops;
10. exact OCI restart preserves goal state and uncertainty.

Until those gates pass, the architecture has a deterministic autonomy state/control spine and a source-candidate human-priority turn gate, but not an accepted always-on background agent.
