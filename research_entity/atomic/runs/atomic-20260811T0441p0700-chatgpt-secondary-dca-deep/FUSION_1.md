# FUSION 1 — bounded active assembly problem surface

## Current gap

Frank v0.1 explicitly requires authoritative UnifiedDB state and model-visible bounded assemblies. The global operating source forbids whole-repository context dumps when a bounded assembly suffices. G9 already exposes `materialize(Query) -> CognitiveView`, `ViewDelta` with `dependency_hash` and `selector_hash`, and `current_answer_context = AnswerCapsule + relevant(ViewDelta)`.

The missing semantic distinction is not ordinary retrieval quality. A bounded context can omit current facts for budget reasons. A model that sees only the payload cannot tell the difference between:

1. no such fact exists in the current query scope;
2. such a fact exists but the selector omitted it;
3. the underlying source is incomplete for that query scope;
4. the fact existed in the certified scope but a relevant state delta made the certificate stale.

This is dangerous for negative claims, unresolved alternatives, Needle abstention, goal/blocker checks and any reasoning where absence itself changes the action.

## Selected problem

Construct the smallest model-visible assembly that preserves all material decision/hypothesis distinctions under a token budget **without converting omission into absence**.

## Strong baselines

- full current CognitiveView;
- relevance top-k with mandatory identity/intent witnesses;
- decision-focused greedy weighted test/set cover;
- ordinary query-aware retrieval plus global completeness flag;
- ordinary query-relative completeness metadata plus state/selector dependency checks.

## Core falsifier

If ordinary query views + query-relative completeness metadata + selector/dependency hashes match DCA correctness, staleness handling and resource cost, DCA is not a distinct runtime architecture. Retain at most a semantic interface contract.

## Non-goals

DCA does not mint truth, SELF, user intent or effect authority. It does not replace UnifiedDB, ClayGraph, Hyperposition, GWT or Needle. It does not claim that missing context is evidence of absence.