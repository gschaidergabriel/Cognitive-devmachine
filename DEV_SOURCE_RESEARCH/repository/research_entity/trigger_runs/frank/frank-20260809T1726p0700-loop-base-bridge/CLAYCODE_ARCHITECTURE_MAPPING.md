# ClayCode Architecture Mapping — FRANK Loop/Base Bridge

Run: `frank-20260809T1726p0700-loop-base-bridge`

## Decision

Do **not** create a new ClayCode semantic subsystem for recurrence. The current BASE-stage rule is `less change, more compile`: represent loop identity, timescale, residual pressure, recurrence budget, interventions, decisions and rollback using the existing typed state/effect/provenance machinery unless a real executable counterexample proves insufficiency.

## Minimal executable vertical slice

The highest-information FRANK-to-ClayCode bridge is:

`LoopDynamicsReadout -> RecurrenceDecision -> typed effect-free control proposal -> GWT/route update -> optional capability-gated effect -> outcome/re-entry receipt`

It must traverse the real ClayCode path:

`source -> parser -> canonical typed IR -> semantic hash + exact contract hash -> type/effect validation -> reference evaluator -> lowering/runtime -> receipt`

A source spelling is never semantic identity. Current parser work already supports the architecture rule that relation spelling remains below deterministic typed semantic identity and that parse acceptance mints neither truth nor authority.

## Required types

### LoopDynamicsReadout

Minimum fields:
- `loop_id`, `loop_family`, `timescale`;
- `state_epoch`, `state_delta_norm`, `residual_pressure`;
- `input_injection`, `recurrence_count`, `recurrence_budget`;
- optional `coupling_estimate`, `jacobian_proxy`, `oscillation_indicator`;
- `marginal_utility_next`, `stagnation_indicator`, `overthinking_indicator`;
- `intervention_ref`, `rollback_ref`;
- evidence, uncertainty and provenance.

`LoopDynamicsReadout` is observation state only. It cannot authorize effects.

### RecurrenceDecision

Typed variants:
- `CONTINUE`;
- `HALT_CANDIDATE_CONVERGED`;
- `ROUTE`;
- `ESCALATE_STALLED`;
- `ABORT_DIVERGING`;
- `ROLLBACK`.

The critical distinction is executable:

`low_delta && low_residual_pressure -> convergence candidate`

`low_delta && high_residual_pressure -> stalled/escalation candidate`

## ClayGraph mapping

ClayGraph should expose an epoch-bound derived loop topology:
- loop node identity;
- typed coupling relation;
- gain/delay/inhibition/timescale metadata;
- route/attractor alternatives;
- intervention handles;
- state-transition/outcome receipts.

The graph remains derived. Activation or repeated loop use never promotes truth.

## UnifiedDB mapping

UnifiedDB should persist/reconstruct:
- loop-state time series;
- semantic epochs;
- recurrence counts/budgets;
- residual pressure/error;
- intervention/lesion/rescue identities;
- decisions, outcomes and causal-credit receipts;
- checkpoints/rollback identities.

Logical semantic unification does not require physical storage monolith. Exact event/effect authority and secrets/capabilities retain isolation/replay-safe semantics.

## GWT mapping

GWT receives a new **testable role candidate**, not a fixed architectural promotion: ignition/focus may route expensive recurrent compute by admitting, continuing, interrupting or re-entering loops. Selection, recurrence stability, causal emergence and authority remain separate measurements.

## Hyperposition mapping

Preserved alternatives are a candidate anti-stagnation mechanism. A stalled loop may reopen a compatible alternative route, but route reopening must be budgeted and measured for destabilization risk.

## Harness mapping

H1 must be the first live causal test surface:
1. freeze representative FRANK episodes;
2. instrument loop families and typed readouts;
3. classify converging/productive-cycle/stalled/diverging regimes;
4. compare fixed recurrence budget with adaptive outcome-gated stopping;
5. lesion historical controller variables and rescue them mechanistically;
6. compare truthful, shuffled and absent re-entry;
7. record latency, compute, memory, false halt, correction time, outcome quality and recovery.

H2 must reproduce these semantics in ClayCode and differential-test against H1. H3 must preserve the semantic loop/intervention structure after one-module consolidation.

## Release-gate consequence

This FRANK run does not justify reopening ClayCode syntax design. It tightens BASE priorities: `CC-WP-02` must hand into `CC-WP-03/04/05/06/07`, and the first FRANK proof should be this bounded loop-controller slice. If the existing semantics cannot compile it, that executable failure becomes admissible evidence for a language change.
