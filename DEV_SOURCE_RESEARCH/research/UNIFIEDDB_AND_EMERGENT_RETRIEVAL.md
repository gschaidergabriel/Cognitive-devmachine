# UnifiedDB + Emergent Retrieval

This note explains two project terms without turning either into magic.

## UnifiedDB in one sentence

**UnifiedDB means one canonical durable authority substrate can hold many typed kinds of state/evidence without creating multiple competing truth stores.**

It does **not** mean one giant table, one process, one writer, one data type, or one file full of undifferentiated facts.

A coherent SQLite substrate can legitimately contain:

- event / observation tables;
- claims and provenance;
- causal identities;
- task / goal state;
- effect requests and effect journals;
- memory records;
- confidence / uncertainty fields;
- embeddings or references to vector material;
- indexes and materialized/read views;
- append-only audit data;
- policy/capability records;
- rebuildable graph/workspace projections.

High-rate transient sensor buffers can still live in RAM. A rebuildable projection can still be a separate data structure. The invariant is about **authority ownership**, not forcing every byte through one Python object.

## Why the project moved this way

The historical archive contains several generations of memory/state databases and services. That is useful evidence: different modules were solving local problems, but distributed durable ownership makes contradiction, recovery, replay, and provenance harder.

The design pressure is therefore:

```mermaid
flowchart LR
    A[Many independent durable stores] --> B[Conflicting ownership]
    B --> C[Reconciliation cost]
    C --> D[One canonical substrate]
    D --> E[Many typed tables / indexes / views]
    E --> F[Rebuildable projections]
```

This is an engineering simplification of authority boundaries, not a claim that all historical state has already been migrated.

## Repository evidence

The accessible source tree contains reference implementations and benchmarks including:

- `research_entity/harness/reference/unifieddb_emergent_compact.py`
- `research_entity/harness/reference/unifieddb_emergent_exact_topk.py`
- `research_entity/harness/reference/unifieddb_emergent_incremental.py`
- `research_entity/harness/reference/unifieddb_emergent_cascade.py`
- `research_entity/harness/reference/unifieddb_claygraph_assembly.py`
- `research_entity/harness/reference/benchmark_unifieddb_exact_topk.py`
- `research_entity/harness/reference/benchmark_unifieddb_compact_cache.py`
- `research_entity/harness/reference/benchmark_unifieddb_claygraph_hotpaths.py`
- historical/runtime documents such as `research_entity/runtime/UNIFIEDDB_V16_SEGMENTED_PULSE_MAINTENANCE.md`.

**Evidence classification:** `CURRENT_SOURCE` / `HISTORICAL_SOURCE`, depending on the artifact.

**Important boundary:** source and benchmark machinery prove that mechanisms exist. They do not automatically prove current Frankenstein integration, current canonical authority, or whole-product runtime acceptance.

## Emergent Retrieval in one sentence

`Emergent Retrieval` is the project term for **relevance that becomes visible when independently stored evidence dimensions overlap at query time**.

Example dimensions:

- semantic similarity;
- time / recency;
- causal lineage;
- current state;
- task / goal relevance;
- perception source;
- effect/result linkage;
- confidence;
- provenance;
- contradiction status;
- generation / version identity.

A candidate can become more relevant because several independent signals agree.

Nothing is created from nothing.

## A simple scoring picture

A generic retrieval candidate `x` can be thought of as receiving bounded evidence terms:

```text
score(x) =
    w_sem * semantic(x)
  + w_time * temporal(x)
  + w_causal * causal_link(x)
  + w_state * state_match(x)
  + w_goal * goal_match(x)
  + w_effect * effect_link(x)
  + w_prov * provenance_quality(x)
  - w_conflict * contradiction_penalty(x)
  - w_stale * stale_generation_penalty(x)
```

That equation is an explanatory schema, not a declaration that every repository implementation uses exactly those terms or weights.

The engineering point is the **intersection of independently recorded evidence**, not a mystical emergence operator.

## Why this matters for Frankenstein

A practical agent has to answer questions such as:

- Which memory is relevant **now**?
- Which prior correction belongs to this causal line rather than a superficially similar one?
- Which goal is active under the current state?
- Did an effect actually happen, or is there only a request/model narration?
- Is a retrieved fact stale relative to a later observation?

A single embedding similarity score is usually insufficient for those distinctions. Multi-dimensional retrieval can use semantics without letting semantics overwrite time, provenance, effects, or authority.

## Emergent Retrieval does not mint facts

The epistemic law is:

```text
FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT
```

Retrieval can rank evidence. It cannot fill an absent observation simply because a similar memory exists.

Likewise:

- a high similarity score != truth;
- several memories agreeing != independent replication unless their provenance is independent;
- a cached result != a current observation;
- a causal-looking graph edge != experimentally established causality;
- a model explanation of why something was retrieved != the retrieval evidence itself.

## UnifiedDB is not EffectGate

Canonical state and effect authority are related but not interchangeable.

A database can store:

- an effect request;
- an admission decision;
- an execution receipt;
- an UNKNOWN outcome;
- a later verification.

But merely writing `success=true` into memory is not the same as proving the world changed.

The project rule remains: requested effect != verified effect. Unknown external outcomes stay UNKNOWN until re-observed.

## NVIDIA Unified Memory analogy — use carefully

The useful systems-design analogy is narrow: reducing ownership/copy boundaries can make compute operate over a more coherent substrate.

Do **not** infer that GPU Unified Memory and UnifiedDB have the same semantics. Hardware address-space coherence is not database truth, provenance, transaction, causal-identity, or effect semantics.

## Open hypothesis: richer overlap improves useful retrieval

**Hypothesis:** retrieval that combines semantic, temporal, causal, state, goal, effect, confidence and provenance dimensions will reduce wrong-context retrieval compared with semantic similarity alone on Frankenstein tasks.

**Engineering confidence:** 0.82.

**Counterhypothesis:** most apparent gains come from extra metadata that leaks task identity; a well-tuned semantic baseline with recency performs equally well.

**Falsifier:** family-separated matched evaluation where semantic-only retrieval equals or beats the multi-dimensional system on downstream task correctness, stale-memory rejection, causal-line disambiguation and contradiction handling after equalizing compute and available information.

## Promotion checklist

Before claiming a current Frankenstein UnifiedDB/Emergent-Retrieval runtime PASS, require at minimum:

1. exact source/artifact identity;
2. exact schema/generation identity;
3. deterministic fixture replay;
4. stale-generation and provenance-negative tests;
5. comparison against semantic-only and recency baselines;
6. contradiction handling;
7. causal-family leakage controls;
8. current runtime receipt bound to the exact code;
9. proof that no competing durable truth store silently overrides it;
10. no expansion from component pass to whole-product pass without an integrated acceptance test.

Until those gates are met at the claimed scope, the correct wording is **mechanism/source evidence exists**, not **the current Frankenstein runtime is proven to use it**.