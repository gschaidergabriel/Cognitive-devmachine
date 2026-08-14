# Clay U10 — Incremental Possibility Compiler / Preprocessor

Status: `TESTING_CANDIDATE`  
Branch domains: `unifieddb + claygraph + hyperposition + emergenz`  
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`  
Date: `2026-08-10`  
Mission: `Frank v0.1 voll lauffähig auf Andreas Ubuntu developer system`

## Research question

Can the current UnifiedDB + ClayGraph read architecture be changed from query-time database search into an incrementally compiled **possibility preprocessor**, while preserving exact provenance/epoch semantics and matching an authoritative recursive graph evaluation on a bounded retrieval workload?

This candidate does **not** claim to be universally better than relational, vector, graph, document, or analytical databases. The claim under test is narrower: for Frank/Clay's repeated context-local possibility retrieval, compile structural reachability and alternative derivations outside the hot path, then apply rapidly-changing admissibility constraints as cheap facets at read time.

## Internal research lineage

The candidate is a continuation of two earlier project findings:

1. SyntheticEquilibrium 4.0: pay complexity while building/indexing/experimenting; normal runtime consumes deltas and prepared slices. Graph/search indexes are rebuildable derivatives, not truth.
2. GRF implementation bridge: historical Frank implemented `M`, the structured possibility space, as 5+ separate constraint systems. Their lack of unification was explicitly identified as a formal architecture gap.

Current U7/U9/ClayGraph already encode the precursor laws:

- prompt read path must not execute eager global combinatorial closure;
- semantic dependencies and invalidations are canonical in UnifiedDB;
- ClayGraph is a derived topology / accessibility surface, not truth authority;
- Hyperposition preserves unresolved alternatives;
- possibility / affordance does not grant effect authority.

## Hypothesis

`H-U10-001`:

> A two-stage possibility compiler can reduce hot retrieval latency while preserving the exact top-k result of the matched recursive graph baseline:
>
> 1. compile a graph-epoch-specific **Potential Field** per active anchor while retaining multiple admissible derivation witnesses;
> 2. project rapidly changing constraints (availability, authority, modality, freshness, privacy, cost class, etc.) as bitmap facets after structural compilation.

Expected consequence: hot-path cost scales primarily with the prepared local field and requested facets rather than total memory / global graph closure.

## Strongest counterhypothesis

`CH-U10-001`:

> Precomputation merely moves query cost into invalidation/build cost; frequent topology changes, high-cardinality contexts, or path-state explosion erase the latency advantage or introduce stale / truncated results. A well-indexed query engine may be simpler and equally accurate.

The candidate therefore has hard fallbacks and no promotion from synthetic results alone.

## Architecture

### Truth plane

UnifiedDB remains semantic/provenance authority. Source and graph epochs must be explicit. Compiled fields are disposable and rebuildable.

### Structural compile plane

For each active anchor:

- bounded simple-path expansion over current ClayGraph;
- multiplicative path score in the current reference implementation;
- all explored alternative path states survive until candidate projection;
- candidates retain best-path score plus derivation count;
- up to `max_witnesses_per_candidate` concrete path witnesses persist;
- `max_path_states` is a hard safety bound;
- hitting that bound marks the anchor field `truncated`.

A truncated field cannot satisfy an exact caller; it must fall back to authoritative recursive evaluation / recompile.

### Dynamic facet plane

Candidate ordinals are stable. Dynamic exact-match constraint memberships are encoded as typed bitsets. V10 reference runtime implements `DENSE_BITSET_LE`; schema also reserves measured alternatives such as `ROARING32` or sorted integer sets.

Hot query:

`anchor field -> intersect requested facet bitsets -> scan pre-ranked candidates -> top-k`

This avoids structural graph recursion for every request while still allowing high-frequency capability / availability / authority changes to update as facet deltas.

### Recovery / continuity

A new field epoch is built in `BUILDING` shadow state. The last-known-good `CURRENT` epoch remains readable. Promotion occurs atomically only after the new epoch is complete. Expected source/graph epochs can be enforced on read; mismatch is a hard fallback condition.

## Exactly one out-of-the-box `go` experiment

Experiment `EXP-U10-POTENTIAL-WAVEFRONT-001`:

Treat the prepared possibility neighborhood as a **Potential Field** rather than a cached query result. Preserve alternate derivation wavefronts (Hyperposition-style unresolved paths) until projection, while keeping dynamic admissibility outside the structural compile as bitset facets.

Why unusual: ordinary materialized query results tend to collapse derivations into rows/results. This candidate intentionally keeps a bounded witness set and a conservative truncation signal so a temporarily non-winning path can remain available to explain or rescue a later candidate.

Result: `SUPPORTED_IN_SYNTHETIC_LOCAL_SCOPE`; not promoted.

## Differential benchmark — actual V10 runtime

Benchmark: `U10-POSSIBILITY-PREPROCESSOR-SYNTH-001`  
Fixture: 6,000 candidates; 41,963 directed weighted edges; 120 anchors; depth 3; top-k 20; fixed seed 73419.  
Dynamic filters: availability + authority + modality.  
Ground truth for fixture: matched recursive SQLite CTE computing best reachable path score then identical filters/ranking.  
Environment: Python 3.13.5; SQLite 3.46.1; Linux 6.18.35 x86_64 glibc 2.41.

Latest reproducible local run:

- recursive SQL p50: `0.8353 ms`
- recursive SQL p95: `1.2274 ms`
- V10 p50: `0.1095 ms`
- V10 p95: `0.1575 ms`
- p50 speedup: `7.63x`
- p95 speedup: `7.80x`
- exact top-20 fraction: `1.0000`
- mean recall@20: `1.0000`
- compiler median per anchor: `54.6797 ms`
- compiler total for 120 anchors: `6926.546 ms`
- LKG shadow-build check: PASS
- source-epoch mismatch guard: PASS

Interpretation: the actual V10 materialized runtime preserves the reference result on this fixture and materially accelerates the hot read. Build cost remains substantial and is the next optimization/invalidator tradeoff to measure.

Earlier exploratory in-memory Potential Field + bitmap test reached ~28.9x p50 / ~23.5x p95 with exact top-20, but that number is **not** the implementation claim because it excluded persisted V10 materialization overhead. The durable claim uses the actual-runtime numbers above.

## Differential semantic tests

Reference unit suite currently covers:

1. two alternative derivation paths to the same candidate survive and retain their scores;
2. dynamic facet projection selects the correct ranked subset;
3. incomplete shadow build does not evict last-known-good epoch and epoch mismatch fails closed;
4. path-state truncation forces exact fallback.

Current local result: `4/4 PASS`.

## External research fusion (primary / official sources)

The architecture is consistent with established/current database techniques but combines them for the Clay possibility workload:

- SQLite recursive common table expressions: authoritative query-time graph traversal baseline.
- Gupta & Mumick et al., incremental/materialized view maintenance: maintain deltas to derived views rather than recomputing every query.
- DBToaster: higher-order delta processing for repeated incremental queries.
- F-IVM: factorized incremental view maintenance; useful counterpoint that representation/factorization matters as much as materialization.
- Enzyme (2026): current production-scale incremental view maintenance evidence; reinforces selective incrementalization rather than blanket recomputation.
- Roaring bitmap project: compressed set representation optimized for set intersection/union and indexed filtering.
- DuckDB official Parquet/index documentation: pushdown, zonemaps, and ART indexes demonstrate both read acceleration and the update/memory costs of extra index structures.

Fusion conclusion: **do not materialize all context combinations.** Compile relatively stable graph potential once per relevant anchor/graph epoch; keep volatile constraints as independent facet sets. This is the architectural delta from U7/U9 rather than simply adding another cache.

## What is measured vs. not measured

Measured:

- exactness against one matched recursive SQL reference fixture;
- latency distribution for 120 synthetic queries;
- compiler cost per anchor;
- epoch mismatch guard;
- LKG shadow-build continuity;
- bounded witness behavior.

Not yet measured:

- real Frank replay corpus;
- target Hostinger self-hosted runner / Andreas PC behavior for V10;
- write amplification and invalidation under realistic mutation rates;
- memory/RSS and persisted bytes per million candidates/edges;
- facet update latency under high churn;
- OOD graph degree / deep-path explosion;
- comparison with specialized graph engines / vector search / production materialized-view systems under their native workloads;
- crash injection during atomic promotion;
- long-run rebuild/recovery and corruption tests.

Therefore `better than every normal database` is **not an admitted claim**. Current evidence supports only: `specialized possibility hot-read is materially faster than matched recursive SQLite on the synthetic fixture with no observed top-20 accuracy loss`.

## Promotion gate

U10 remains `TESTING_CANDIDATE` until at minimum:

1. real Frank/Clay replay corpus with frozen expected possibility sets;
2. Ubuntu Hostinger runner benchmark with raw rows + CPU/RAM/I/O/storage metadata;
3. mutation/invalidation workload and break-even curve (read frequency vs. update frequency);
4. crash/restart/LKG/atomic-promotion fault injection;
5. high-degree and path-explosion adversarial cases;
6. comparison against at least recursive SQL + FTS/vector/graph baseline where semantically applicable;
7. no mixed-epoch or authority leakage;
8. measured benefit survives after all provenance/witness/receipt costs.

## Architecture delta

Candidate disposition: `CLAY_REDESIGN_CANDIDATE` for the UnifiedDB/ClayGraph **read product**, not replacement of canonical persistence.

New conceptual boundary:

`UnifiedDB truth + ClayGraph topology + Hyperposition alternatives -> Possibility Compiler -> Potential Fields + Facets -> context capsule/GWT/Needle candidates`

The name "UnifiedDB" can remain as persistence compatibility, but the cognitive read surface should be treated as a **compiler/preprocessor** if the promotion gate continues to pass.

Rollback: delete/disable V10 migration/runtime; V7/V9 + ClayGraph recursive/materialized read paths remain authoritative fallbacks. No canonical stack pointer is changed by this candidate write.
