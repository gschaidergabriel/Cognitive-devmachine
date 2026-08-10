<!-- RAE_META
{"packet_id":"UNIFIEDDB_U10_INVALIDATION_DELTA_FUSION_V1_20260810","title":"U10 possibility compiler exact structural invalidation delta","domains":["unifieddb","claygraph","hyperposition","harness"],"topics":["possibility compiler","incremental invalidation","support counts","prepared reachability","anchor reuse","depth-3 potential fields"],"epistemic_class":"LOCAL_MECHANISM_BENCHMARK_PLUS_CURRENT_MAIN_FUSION","claim_status_hint":"TESTING_CANDIDATE","origin_class":"CHATGPT_LOCAL_EXECUTION_AND_REPO_FUSION","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T07:00:00+07:00","verification_required":true,"falsifier_or_next_test":"Run the delta invalidation index against the exact U10 synthetic topology and then real UnifiedDB/ClayGraph replay mutations; recompile only predicted anchors and verify all weighted top-k/witness outputs against full U10 rebuild after every mutation."}
RAE_META -->

# U10 exact structural invalidation delta — fusion candidate

## Why this delta exists

Current `main` already contains the stronger U10 Potential-Field possibility compiler. It is the semantic owner of weighted path witnesses, bounded alternative derivations, dynamic bitset facets, exact-fallback on truncation, epoch checks and last-known-good publication. This packet does **not** introduce another database, another truth plane or a competing possibility compiler.

The remaining measured bottleneck in U10 is compilation/invalidation: the current synthetic receipt reports 6,000 candidates, 41,963 edges, 120 anchors, depth 3, median compile 54.6797 ms/anchor and 6,926.546 ms total compile, while hot reads are already 7.63x p50 / 7.80x p95 faster than the matched recursive SQLite baseline with exact top-20 on that fixture.

This candidate targets only the structural invalidation frontier so unchanged anchor fields can be reused.

## Exact depth-3 invalidation law

For U10 `max_depth=3`, mutation of forward edge `u -> v` can change a compiled anchor field only if that anchor reaches `u` within at most two edges **before the mutation**.

Therefore:

`affected_anchors(edge u->v) = active_anchors INTERSECT reverse_reachability_le2(u)`

A prepared <=2-hop reachability index over the reversed ClayGraph is sufficient to produce a no-false-negative structural invalidation frontier. It does not decide whether the weighted top-k actually changes; it only decides which fields may need U10 recompile. U10 remains responsible for weighted path scoring, witness preservation, truncation and semantic verification.

## Exact add/remove delta mechanism

The reverse reachability index stores sparse support counts for every direct and two-edge path. For an edge update `u -> v` in the indexed graph, only these path supports can change:

- direct `u -> v`;
- `u -> v -> w` for current successors `w` of `v`;
- `p -> u -> v` for current predecessors `p` of `u`.

A relation remains prepared while at least one support path remains. This fixes the weakness of OR-only bitmap deltas: removal/revocation cannot erase a relation that is still supported by another valid path.

## Local exactness evidence

Mechanism stress tests executed in the ChatGPT local Linux container, Python 3.13.5 / GCC 14.2.0:

### Mixed reachability mutations

Random graph, 500 semantic refs / 2,000 initial edges, then 5,000 mixed add/remove mutations:

- exact brute-force <=2-hop equality at all periodic verification points: PASS;
- final bad source count: 0.

Matched 1,400-ref / 5,600-edge / 2,000-mutation comparison against exact targeted local recompute:

- targeted recompute ADD p50 0.015543 ms; support-delta ADD p50 0.004802 ms -> 3.24x;
- targeted recompute ADD p95 0.030105 ms; support-delta ADD p95 0.007802 ms -> 3.86x;
- targeted recompute REMOVE p50 0.0136655 ms; support-delta REMOVE p50 0.005218 ms -> 2.62x;
- targeted recompute REMOVE p95 0.026629 ms; support-delta REMOVE p95 0.007831 ms -> 3.40x;
- exact final reachability: PASS.

### U10 depth-3 invalidation falsifier

Separate random fixture with 220 nodes / 1,100 edges / 24 active anchors and 1,000 mixed mutations. For every mutation, brute-force <=3-hop reachable sets were captured for every anchor before and after the mutation. The predicted reverse-<=2 invalidation set was checked against the anchors whose reachable set actually changed.

- false-negative invalidations: 0;
- reverse reachability final exactness: PASS.

### U10-cardinality-matched proxy

A separate random-topology proxy matched current U10 cardinalities (6,000 nodes, 41,963 edges, 120 active anchors) but **not** its exact graph topology. Across 1,000 mixed mutations:

- reverse support index build: 245.704 ms;
- affected-anchor identification p50: 0.033495 ms;
- affected-anchor identification p95: 0.062012 ms;
- reverse support-delta mutation p50: 0.017876 ms;
- reverse support-delta mutation p95: 0.027911 ms;
- affected anchors mean: 1.082 / 120;
- median: 1;
- max: 7;
- zero-affected fraction: 0.371;
- final exact reverse <=2 reachability: PASS.

The affected-anchor distribution is **not transferable as a claim about the actual U10 fixture** because topology controls invalidation density. It only demonstrates that at matching cardinality sparse targeted invalidation can be extremely selective. The exact U10 topology must be replayed before claiming compile-amplification reduction for U10 itself.

## Earlier hot-read mechanism evidence retained as lineage

Before current-main U10 arrived concurrently, a smaller 1,400-token / 5,600-edge / 4,200-rule synthetic mechanism test compared:

- direct database rule lookup: p50 0.0205855 ms but recall@10 0.0282 on latent/compositional possibility targets;
- matched recursive semantic SQLite: p50 0.4434 ms, exact top-10 1.0;
- prepared anchored possibility preprocessor: p50 0.079198 ms, exact top-10 1.0;
- prepared vs semantic SQL p50 speedup: 5.60x.

That earlier candidate is superseded as the semantic compiler by current-main U10. Its useful surviving result is the incremental reachability/delta mechanism developed after write amplification was observed.

## Current architecture fusion

`UnifiedDB canonical truth/provenance`
`+ ClayGraph current topology / verified access plans`
`+ Hyperposition alternative witnesses`
`-> U10 Potential Field compiler`
`-> prepared weighted anchor fields + dynamic facets`
`-> hot possibility read`

New candidate beneath the U10 compiler:

`graph edge delta`
`-> exact reverse <=2 support-count delta`
`-> exact depth-3 affected-anchor frontier`
`-> recompile/verify affected U10 fields only`
`-> reuse unchanged current fields`
`-> atomic coherent publication`

This is closer to the owner-fixed target: the cognitive read surface is a continuously maintained possibility preprocessor, while conventional storage engines remain physical persistence/transaction substrates rather than the cognition algorithm.

## External research fusion retained

Primary/official external references used in the iteration:

- DBToaster / higher-order delta processing: repeated incremental queries can shift work from full recomputation to maintained deltas;
- Roaring bitmaps: bit-parallel set operations are an appropriate measured candidate for larger prepared membership/facet sets;
- GraphBLAS: sparse frontier algebra is a candidate backend when Python sparse maps cease to scale;
- SQLite FTS5 remains a strong lexical/cold-search fallback baseline rather than an architecture strawman.

No external source validates this Clay implementation; the implementation claim comes only from local executable receipts and must be independently replayed.

## Strongest counterhypothesis

`CH-U10-DELTA-001`: Actual Frank/Clay topology may be highly hubbed or rapidly changing, causing most anchors to enter the invalidation frontier frequently; support-count maintenance may consume more memory/write bandwidth than selective recompile or a tuned graph/database engine, and weighted witness changes may force more recompilation than structural reachability alone predicts.

## Falsifiers / next measurements

1. Reproduce the exact current U10 synthetic topology and mutate it; compare full rebuild vs targeted-recompile outputs after every mutation.
2. Require equality of weighted top-k, witness counts, facet behavior, truncation state and output hashes, not only unweighted reachability.
3. Measure actual compile-time reduction, write amplification, RSS/heap and persisted bytes.
4. Run high-degree/hub/path-explosion adversarial topologies.
5. Run real UnifiedDB/ClayGraph/Frank replay with mutation traces.
6. Run Hostinger Ubuntu and final Andreas Ubuntu target measurements when the execution lane is eligible.
7. Crash during delta/application/field promotion and verify LKG recovery.

## Promotion

`NONE` — research candidate only.

Current evidence supports: exact bounded support-count deltas and a no-false-negative depth-3 structural invalidation frontier on the tested local fixtures. It does **not** yet support “better than every normal database” or default-stack promotion.
