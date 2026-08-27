# Strongest Counterhypothesis — LSCW-001

## Counterclaim

A new lifecycle witness primitive is unnecessary for Frank v0.1.

The simpler architecture is:

1. keep stage-specific semantic validators where semantics are actually understood;
2. keep the fresh conjunctive ProductStart gate;
3. carry one ordinary typed `CurrentExecutionContext` with current identity/state/effect/reward/runtime fields;
4. verify exact consumed artifact/dependency/state objects at their consume boundaries;
5. retain current execution-generation/idempotency/reconciliation and recovery mechanisms;
6. add explicit cross-stage mutation tests for stale/sibling/replay/chimera substitutions;
7. do **not** persist or consume/reissue a second general witness lineage unless those tests expose a gap.

## Why this is strong

The current system is rapidly acquiring exactly the missing local guards:

- ProductStart evidence is conjunctive rather than substitutable;
- build provenance is being decomposed into trusted policy, cryptographic verification, subject digest and installed-byte equality;
- the storage path now has an exact private SQLite 3.53.4 V4 candidate;
- unique selected-state lineage and execution-generation fences exist as separate mechanisms;
- ClayCode now has target-validated package/module binding plus semantic differential gates;
- the fresh unary-negation bug was repaired by a small semantic-survival regression and a 200576-case differential rather than by a universal provenance object.

That evidence predicts a general LSCW object may become a second semantic architecture or receipt amplification layer, violating the Clay principle of keeping semantic authority singular and bounded.

## Hard kill test

Build a shadow-only matched target test. For every frozen real transition episode, evaluate:

- `BASE_CURRENT`: current actual guards only;
- `BASE_CONTEXT`: current guards + one conventional immutable CurrentExecutionContext tuple;
- `LSCW_SHADOW`: same inputs plus LSCW residual/linear-lineage validator, with no new effect authority.

Inject at minimum:

- stale state epoch;
- sibling selected-state root at same epoch;
- same source but different admitted artifact;
- correct artifact but wrong runtime dependency object;
- stale execution generation;
- duplicate/replayed parent transition;
- wrong effect-policy epoch;
- reward dimension present without utility authority;
- ProductStart missing exactly one conjunctive axis at a time;
- installed restart into sibling state;
- compiler semantic mutation where lifecycle hard fields remain equal;
- benign semantic-preserving rebuild/normalization;
- benign translator/observability-only change.

## Decision rule

Kill LSCW as a runtime architecture if `BASE_CONTEXT` matches every LSCW safety rejection and valid acceptance on real target episodes while using lower code/latency/RAM/persisted-state and a smaller trusted computing base.

Retain LSCW only as a research/test notation if its residual formalism improves mutation coverage or diagnosis but does not justify production state.

Promote only if LSCW uniquely rejects a real, material cross-stage substitution/replay/chimera that the strongest simple baseline misses, while still accepting valid transformations and staying within resource/recovery budgets.

## Current verdict

**UNRESOLVED / COUNTERHYPOTHESIS NOT DEFEATED.**

The synthetic reference corpus favors LSCW by construction on cross-stage lineage cases, but fresh real evidence also shows stage-specific semantic differential tests are effective and that broad semantic preservation cannot be inferred from a hard-field witness. No target-live LSCW promotion is justified.
