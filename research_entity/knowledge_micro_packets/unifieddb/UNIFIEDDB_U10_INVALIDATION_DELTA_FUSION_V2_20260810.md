<!-- RAE_META
{"packet_id":"UNIFIEDDB_U10_INVALIDATION_DELTA_FUSION_V2_20260810","title":"Possibility preprocessor targeted invalidation V2","domains":["unifieddb","claygraph","hyperposition","harness"],"topics":["possibility preprocessor","targeted invalidation","dynamic reachability","incremental view maintenance","anchor mask","weighted field repair","memory shadow"],"epistemic_class":"LOCAL_EXECUTION_PLUS_PRIMARY_RESEARCH_FUSION","claim_status_hint":"SUPPORTED_RESEARCH_CANDIDATE_NOT_PROMOTED","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T07:30:00+07:00","verification_required":true,"falsifier_or_next_test":"Wrap actual persistent U10/EAP compiler with V2 shadow invalidation, replay exact U10 mutations, require field/witness/hash equality versus full rebuild, then run Hostinger Ubuntu."}
RAE_META -->

# UnifiedDB / ClayGraph possibility-preprocessor invalidation V2

## Architecture statement

The intended cognitive surface is not a generic database query API. Conventional storage remains a persistence/transaction substrate. Model-facing access is a continuously maintained, epoch-bound possibility/context preprocessor whose hot reads consume already prepared semantic fields/frontiers. ClayGraph remains derived/rebuildable; Hyperposition alternatives remain preserved; activation/rank never becomes truth or effect authority.

Current-main fusion already contains this direction in the Possibility Field Compiler and the emergent assembly preprocessor. This V2 packet targets one remaining measured cost: dependency/graph mutations that can cause broad invalidation/recompilation.

## V1 falsified and retained as negative result

V1 materialized every <=2-hop prepared ref and only then intersected with active U10 anchors. On a 6,000-node / 41,963-edge / 120-anchor random topology:

- on-demand reverse BFS<=2 p50: 0.004607 ms;
- V1 materialize-all-refs then intersect p50: 0.032689 ms;
- V2 direct prepared-anchor bitmask intersection p50: 0.000681 ms.

V1 materialization is therefore `NOT_SELECTED` for this hot path. The negative result is preserved rather than hidden.

## V2 memory shadow

The speed gain is not free. On the same cardinality fixture the Python support-count prototype contained 333,846 support pairs. Approximate recursive `sys.getsizeof` shadows were:

- support dictionaries: 31,620,904 bytes;
- reachability masks: 4,856,552 bytes;
- reverse adjacency: 5,477,604 bytes.

These are Python-object estimates, not allocator/RSS or production-layout measurements. They establish only that prepared dynamic reachability can materially amplify memory. Therefore on-demand BFS is retained as a low-memory fallback and the final mode must be selected from measured read/update/memory/recompile break-even, not ideology.

## Exact U10 topology reproduction

The current U10 benchmark generator is deterministic: seed 73419, 6,000 nodes, candidate metadata RNG, 7 outgoing-edge attempts per node, then 120 sampled anchors. Reproducing that exact sequence produced 41,963 edges and 120 anchors, matching the repository benchmark exactly.

For every existing edge, the depth-3 structural invalidation law predicts affected anchors as:

`active_anchors INTERSECT reverse_reachability_le2(edge.source)`

On the exact U10 topology:

- mean structurally affected anchors: 1.1335 / 120;
- median: 1;
- p95: 3;
- maximum: 7;
- zero affected: 35.324%.

A separate 1,000-mutation add/remove run on the same exact topology remained similar (mean 1.125, p95 3, max 7, zero 35.3%). Anchor-mask lookup p50 was 0.0008565 ms; exact support-count mutation p50 was 0.016504 ms. Sampled reverse-reachability checks remained exact.

## Weighted-field differential falsifier

An equivalent in-memory implementation of the U10 depth-3 weighted semantics was first checked against the original recursive SQLite oracle on all 120 initial anchors. Top-20 equality was 120/120.

Then 500 mixed edge additions/removals were applied. After each mutation:

1. predict structural affected anchors from pre-mutation reverse<=2 reachability;
2. recompile only predicted anchors;
3. independently fully recompile all 120 anchors;
4. compare the entire maintained top-20 state.

Result:

- full-vs-targeted state mismatch steps: 0 / 500;
- predicted affected anchors mean: 1.08, p95 3, max 6;
- actually changed weighted top-20 anchors mean: 0.096;
- 91.6% of mutations changed no weighted top-20 anchor;
- actual changed max: 3.

Equivalent-mechanism latency:

- full 120-anchor recompile p50 27.389176 ms, p95 29.712454 ms;
- targeted-frontier recompile p50 0.2356155 ms, p95 0.77253 ms;
- p50 speedup 116.25x; p95 speedup 38.46x;
- 0 output mismatches.

This is strong mechanism evidence, not yet the persistent SQLite-backed U10 end-to-end result. Persistent witness writes, generation publication, recovery and I/O remain unmeasured for targeted repair.

## External primary-research fusion

Fresh primary research was used to challenge the design:

- DBSP (Budiu et al., arXiv:2203.16684) shows a general route to incremental view maintenance over rich/recursive query languages.
- Differential maintenance of recursive graph queries (arXiv:2203.08832) shows recursive deltas can avoid recomputation but can incur prohibitive memory, motivating dropping/recomputing selected differences.
- Empirical fully dynamic transitive-closure and single-source-reachability work (arXiv:2002.00813; arXiv:1905.02042) shows dynamic reachability performance is workload/topology dependent rather than universally superior.

Fusion consequence: do not generalize the bounded support-count index into eager all-pairs closure. Keep a tiered repair system and measure the operating regime.

## Tiered possibility-preprocessor invalidation

Candidate control law:

`L0 FACET_ONLY`
: update dynamic bitsets/epistemic availability without structural field rebuild.

`L1 STRUCTURAL_DEPTH3_DELTA`
: use exact reverse<=2 anchor-mask frontier for dependency edge add/remove/revocation; maintain support counts only when the measured memory/recompile break-even favors it; otherwise use on-demand BFS.

`L2 WITNESS_DEPENDENCY_REPAIR`
: recompile only structurally affected U10/Pareto fields and verify weighted candidate/witness hashes. Future witness reverse-dependency indexing may shrink this below the conservative structural frontier.

`L3 EXACT_FALLBACK_REBUILD`
: if truncation, hub/path explosion, unsupported relation semantics, invalid epoch, ambiguous heads, corruption or resource tripwire appears, fail closed to exact affected/full rebuild and preserve last-known-good.

This complements current-main U15 gap-controlled deepening: once a verified field is sufficient, no new retrieval is performed; if a genuine gap remains, only explicit gap terms drive bounded deepening.

## Strongest counterhypothesis

Real ClayGraph may have hubbed, typed, rapidly changing dependencies where support-pair memory/cache pressure plus persistent write amplification outweighs saved recompilation. A tuned graph DB, recursive SQL/materialized view, compressed bitmap or on-demand BFS may dominate some regimes. Targeted invalidation is therefore an operating-window candidate, not a universal replacement engine.

## Required next gate

1. Integrate V2 as a shadow invalidation planner around the actual persistent U10/EAP compiler.
2. Replay exact U10 mutations through full vs targeted persistent builds; compare field members, witnesses, dynamic facets, output hashes and LKG generation.
3. Measure write latency, total compile latency, RSS/heap, SQLite pages/I/O, support-pair amplification and recovery.
4. Stress high-degree hubs, path explosion, deletions/revocations, stale epochs and ambiguous graph heads.
5. Replay real Clay/Frank dependency mutation traces.
6. Replicate on Hostinger Ubuntu, then Andreas Ubuntu target.

Promotion remains `NONE` until those gates pass.
