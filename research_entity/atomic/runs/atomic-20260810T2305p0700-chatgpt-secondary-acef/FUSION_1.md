# FUSION 1 — current Frank v0.1 problem surface

Status: research synthesis; not architecture promotion.

## Existing strengths that must not be duplicated

The current repo already contains semantic_transactions/state_epochs in UnifiedDB, graph epochs/deltas and invalidation machinery in ClayGraph, Hyperposition-capable hyperrelations, GWT receiver/use/outcome/re-entry receipts, one global execution lease with epoch fencing, and an effect lifecycle that distinguishes authorization, reservation, execution, unknown outcome, verification, re-entry and DONE.

Therefore a valid ATOMIC candidate cannot merely add transactions, event sourcing, idempotency, a graph, a lease, or a belief store.

## Cross-boundary weakness selected for research

The remaining architectural risk is cross-surface semantic partiality: cognition, memory, goals, GWT episode state, Hyperposition alternatives, effect lifecycle, causal credit and re-entry are specified with strong local invariants but do not yet share one explicit atomic visibility/causal-commit geometry in the current executable Frank v0.1 workspace.

This creates a research question rather than a proven bug: can one substrate make a crash/restart/retraction leave fewer semantically half-admitted states while preserving low-latency access to safe monotone observations?

## Selected problem

Create one ClayCode-native commit fabric that distinguishes:

- raw monotone evidence that can be admitted without global coordination;
- non-monotone beliefs/goals/reward/personality updates that remain branch-local until validated;
- external effect intents whose outcome can become UNKNOWN and must be reconciled;
- GWT/Hyperposition activity that is causally observable but never truth/authority;
- re-entry that is valid only when provenance, outcome and commit lineage close.

## Strongest counterhypothesis

A unified causal fabric may be architectural overreach. Current separate mechanisms plus narrower component-level transactions may be simpler, faster, easier to compile and easier to recover. Cordon-like task transactions or MemTX-like belief commits may capture most safety value without imposing a universal semantic delta layer.

## Minimum discriminating question

Under matched episode/fault traces, does a unified fabric reduce cross-surface invariant violations and recovery ambiguity versus loose surfaces while matching the safety of a full task transaction with fewer synchronous commit barriers and better retention of harmless raw evidence?
