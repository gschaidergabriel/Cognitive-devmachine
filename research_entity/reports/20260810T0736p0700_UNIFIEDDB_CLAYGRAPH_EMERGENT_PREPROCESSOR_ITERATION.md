# UnifiedDB + ClayGraph emergent possibility-preprocessor iteration

Date: 2026-08-10 +07:00  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Status: `RESEARCH_CANDIDATE · NOT_CANONICAL · PR #75 DRAFT`

## Research question

Continue the owner-fixed direction that UnifiedDB/ClayGraph should cease behaving like a generic model-facing database search API and instead become a continuously maintained semantic possibility/context preprocessor: prepare relevant semantic structure before cognition asks for it, preserve uncertainty/Hyperposition, stop retrieval when sufficiency is proven, and repair only what changed.

The target is workload-specific superiority for Clay/Frank cognition, not a scientifically meaningless claim that one implementation dominates every database primitive or DBMS.

## Canonical architecture fusion observed on current main

Concurrent main already advanced substantially during the run:

- U10 Potential-Field compiler: bounded simple-path possibility fields, dynamic facet bitsets, witnesses, exact fallback on truncation.
- Possibility Field Compiler fusion candidate: model-facing access is explicitly a bounded semantic preprocessor/context compiler, not a generic DB query API.
- U12 segmented semantic-access Pulse: immutable per-seed segments, reverse dependency index, coherent generation->segment maps, atomic head swap and last-known-good.
- U15 sufficiency-gap controller: sufficient compiled fields stop retrieval; only explicit unresolved evidence gaps drive bounded deepening.
- U16 compile amortization/horizon gate: choose ONLINE vs COMPILE from measured build/query costs, quality and expected reads before invalidation.
- Strong exact-key SQLite counterbaseline: when the normalized semantic identity is already known, a plain B-tree lookup remains the correct physical primitive.

Therefore this branch does not introduce another truth plane, another semantic compiler, or another permanent routing controller.

## Measured baseline evidence already on main

### Hot semantic field versus matched recursive SQL

Current U10 synthetic receipt (6,000 candidates, 41,963 edges, 120 anchors, depth 3, top-20):

- recursive SQLite p50 ~0.8353 ms, p95 ~1.2274 ms;
- U10 compiled field p50 ~0.1095 ms, p95 ~0.1575 ms;
- ~7.63x p50 and ~7.80x p95 speedup;
- exact top-20 fraction 1.0 / recall@20 1.0;
- compile ~6.93 s total / ~54.68 ms median per anchor.

This made compile/update/invalidation the next bottleneck rather than hot read.

### Compositional possibility frontier

Current-main compositional stress over 600 queries:

- direct SQL feasible-route hit ~0.494;
- direct SQL exact-best-route ~0.279;
- compiled Pareto frontier feasible hit 1.0 / exact best route 1.0;
- compiled read median ~0.0030 ms versus recursive SQL oracle ~26.78 ms;
- but compile median ~3.39 s and ~68.9k retained Pareto routes.

Again, compilation/frontier growth rather than read latency dominates the next iteration.

### Semantic safety accuracy

Current typed Clay assembly rejects injected UNKNOWN/CONFLICT or stale/future/ambiguous/unverified/tampered UDB<->ClayGraph states under its controlled fault model while a deliberately simple row-store admits them. This is evidence for the semantic admission contract, not evidence that storage engines cannot implement equivalent checks.

## Branch iteration 1 — direct prepared possibility mechanism

A local 1,400-token / 5,600-edge / 4,200-rule synthetic benchmark compared:

- direct database lookup: p50 0.0205855 ms but recall@10 0.0282 on latent/compositional targets;
- matched semantic recursive SQLite: p50 0.4434 ms with exact top-10;
- prepared anchored possibility preprocessor: p50 0.079198 ms with exact top-10.

Prepared semantics was ~5.60x faster than matched semantic SQL while preserving the target result. Direct DB remained faster only by solving the wrong (non-compositional) task.

The first write path was too expensive, which triggered delta-maintenance research.

## Web/primary-research fusion

Primary research used to challenge the candidate:

- DBToaster / higher-order delta processing: repeated views can move work from full recomputation to maintained deltas.
- DBSP (arXiv:2203.16684): general incremental maintenance over rich/recursive query languages.
- differential maintenance of recursive graph queries (arXiv:2203.08832): recursive deltas can save recomputation but materialized differences can become memory-heavy.
- fully dynamic transitive closure and single-source reachability empirical work (arXiv:2002.00813; arXiv:1905.02042): dynamic maintenance wins only in matching topology/query/update regimes.
- Roaring bitmap research: compressed bit-parallel set operations are a candidate representation, not an automatic win.
- GraphBLAS: sparse frontier algebra is a candidate backend when Python maps/bitsets cease to scale.
- SQLite FTS5: retain as strong lexical/cold-search fallback baseline.

Fusion law: `do not eagerly materialize all closure merely because hot lookup is fast`.

## Branch iteration 2 — exact bounded support-count deltas

For <=2-hop reverse reachability, maintain a sparse support count for every direct and 2-edge path. Edge add/remove changes only paths containing that edge. Alternative paths keep a relation alive when one edge is revoked.

Evidence:

- 5,000 mixed add/remove stress mutations: exact reachability at all verification points;
- matched 1,400-ref / 5,600-edge / 2,000-mutation test versus exact targeted recompute:
  - add p50 0.015543 -> 0.004802 ms (~3.24x);
  - remove p50 0.0136655 -> 0.005218 ms (~2.62x);
  - final exactness PASS.

This solved the first OR-only deletion weakness.

## Branch iteration 3 — exact U10 depth-3 structural invalidation law

For current U10 `max_depth=3`, mutation of forward edge `u -> v` can affect a compiled anchor field only if the anchor reached `u` within <=2 hops before mutation.

Therefore:

`affected anchors = active anchors INTERSECT reverse_reachability_le2(u)`

A 1,000-mutation brute-force falsifier compared before/after <=3-hop reachable sets of every active anchor and produced zero false-negative invalidations.

## Exact current-U10 topology reproduction

The deterministic current U10 benchmark generator was reproduced exactly:

- seed 73419;
- 6,000 nodes;
- candidate-meta RNG consumed before edges;
- 7 outgoing-edge attempts per node;
- resulting edge count 41,963;
- exactly 120 sampled anchors.

Across every existing edge:

- structurally affected anchors mean 1.1335 / 120;
- median 1;
- p95 3;
- max 7;
- zero affected 35.324%.

A separate 1,000 mixed-mutation run on this exact topology stayed similar: mean 1.125, p95 3, max 7, zero 35.3%.

## Weighted-field differential validation

An equivalent in-memory implementation of U10 depth-3 weighted top-20 semantics was first checked against the original recursive SQLite oracle on all 120 initial anchors: 120/120 exact top-20 equality.

Then 500 mixed edge additions/removals were applied. After every mutation:

1. derive the pre-mutation structural frontier;
2. rebuild only predicted anchor fields;
3. independently rebuild all 120 fields;
4. compare complete maintained top-20 state.

Result:

- 0 mismatch steps / 500;
- predicted affected anchors mean 1.08, p95 3, max 6;
- actual weighted top-20 changed anchors mean 0.096;
- 91.6% of mutations changed no top-20 field;
- full equivalent recompile p50 27.389176 ms vs targeted 0.2356155 ms -> 116.25x;
- p95 29.712454 ms vs 0.77253 ms -> 38.46x.

This validates the mechanism and frontier on the synthetic U10 semantics. It is not yet persistent U10 SQLite/I/O/VPS evidence.

## Branch iteration 4 — V1 hotpath falsified; anchor mask V2

V1 converted the complete prepared <=2-hop neighborhood back into refs before intersecting anchors. This was correct but slow.

On a 6,000-node / 41,963-edge / 120-anchor fixture:

- on-demand reverse BFS<=2 p50 0.004607 ms;
- V1 materialize all prepared refs then intersect p50 0.032689 ms;
- V2 prepared anchor-bitmask intersection p50 0.000681 ms.

V1 materialization is `NOT_SELECTED`.

## Branch iteration 5 — prepared-mask default self-falsified

The prepared support index carried a large memory/update shadow. Rough Python object-size estimate on the matching fixture:

- support pairs ~333.8k;
- support dictionaries ~31.6 MB;
- reachability masks ~4.86 MB;
- reverse adjacency ~5.48 MB.

On the same exact U10 2,000-mutation sequence, comparing complete structural-maintenance cost:

### ON_DEMAND_BFS
- lookup p50 0.007421 ms;
- adjacency update p50 0.000491 ms;
- total p50 0.007892 ms.

### PREPARED_SUPPORT_MASK
- lookup p50 0.000601 ms;
- support update p50 0.012919 ms;
- total p50 0.01355 ms.

Prepared mode was ~1.72x slower overall at one invalidation lookup per mutation, plus higher memory. Therefore current-U10 candidate default for structural invalidation becomes `ON_DEMAND_BFS`. Prepared support masks remain optional only when measured repeated-read reuse and memory budget cross break-even.

This is a critical negative result: a spectacular lookup microbenchmark is not enough to promote a data structure.

## U12 persistent-generation fusion

U10 fields are epoch-bound, so naive targeted rebuild would otherwise require copying or violating generation coherence. Current-main U12 already solves this with immutable content-addressed per-seed segments and a small coherent generation->segment map:

- rebuild only affected seeds;
- reuse unchanged immutable segments;
- verify complete map;
- atomically flip head;
- preserve LKG on failure.

This is the repository-native persistence strategy for the structural frontier.

A proof-gated adapter candidate was added:

- `REMOVE`: native U12 `EDGE_REMOVE`;
- bounded depth-3 `ADD`: compute hash-bound pre-mutation impact proof first, then allow U12 `LOCAL_REWRITE` only under that explicit proof;
- generic edge additions remain unsafe/full-fallback;
- proof binds source/graph basis and result epochs, operation, endpoints, max depth and affected seeds;
- tampered proof must fail before U12 head effect.

Differential U12 tests are authored on the branch but are not claimed executed because the available PR Actions lane currently fails before job steps.

## U16 fusion — no duplicate controller

A local V3 break-even selector was built to prevent lookup-only promotion. During the run, main independently landed the more general U16 compile-amortization/horizon gate.

Therefore V3 is marked `NOT_SELECTED_AS_ARCHITECTURE_OWNER` and retained only as a lesionable control. New invalidation/targeted-build costs should feed U16 rather than creating a second runtime policy controller.

Final control stack direction:

`exact-key known -> normal B-tree/physical index`

`semantic cue / latent possibility -> compiled possibility field`

`field sufficient -> stop retrieval`

`explicit semantic gap -> bounded gap-directed deepening`

`facet/value delta -> cheap field/facet delta`

`dependency edge mutation -> exact bounded impact frontier`

`U12 segmented pulse -> rebuild only affected segments + reuse others`

`U16 economics -> decide whether/when compilation is worth materializing`

`uncertain/hubbed/truncated/stale/ambiguous/corrupt -> exact fallback / full rebuild / LKG`

This is an adaptive semantic preprocessor, not a new monolithic database.

## Conventional-database comparison — admitted claim boundary

Supported now:

- On defined Clay semantic/compositional workloads, compiled possibility structures materially outperform matched recursive SQLite evaluation while preserving exact target results.
- On controlled semantic-safety fault models, Clay's typed contracts reject invalid contexts that a deliberately simple row-store accepts.
- On compositional routing, direct SQL lookup misses possibilities that the compiled frontier recovers exactly.
- On exact-key identity lookup, a plain B-tree remains the correct comparator and may be superior.

Not supported:

- `Clay is faster/more accurate than every normal database in every operation.`

That universal claim is neither necessary nor scientifically defensible. The meaningful target is: for Frank's cognitive model-input workload, the end-to-end preprocessor should dominate a strong portfolio of conventional retrieval/database implementations on a declared vector of task quality, calibration, latency, update cost, memory, recovery and provenance.

## Current branch materialization

Draft PR #75 contains the additive research candidate and receipts. An earlier redundant second-preprocessor PR #65 was closed unmerged after concurrent main landed a stronger U10 semantic compiler.

Current PR #75 additionally contains:

- exact bounded reachability delta V1;
- U10 structural invalidation V1/V2;
- BFS/prepared break-even measurements;
- exact-U10 weighted differential receipts;
- U12 bounded-edge proof adapter + differential tests;
- negative result marking V3 policy as non-owner;
- fusion packets and benchmark receipts.

No canonical promotion has occurred.

## VPS state

A bounded issue-dispatch event was emitted for the existing main-only UnifiedDB EAP self-hosted Ubuntu workflow. The bridge is hard-wired to `main`, not PR #75. No persisted VPS receipt became observable through the available connector during this invocation, so no Hostinger result is claimed for either main or the branch here.

## Strongest counterhypothesis

Real Frank/ClayGraph distributions may be more hubbed, typed, contradictory and high-churn than the U10 synthetic graph. Persistent witness/segment writes, CPU cache behavior, branch publication, garbage collection and proof state may erase much of the equivalent-mechanism speedup. A tuned conventional graph/database/materialized-view implementation may dominate some operating regimes.

## Next hard gates

1. Execute the branch U12 bounded-edge adapter tests on an eligible runner.
2. Add an actual persistent U10/U12 shadow benchmark: full rebuild vs proof-targeted segmented pulse, compare segment/path/witness/output hashes.
3. Measure total build/update p50/p95/p99, SQLite writes/pages, RSS/heap, CPU, support/proof bytes, crash/restart/LKG.
4. Feed measured targeted-build economics into current U16 horizon gate and re-run regret scenarios.
5. Run high-degree/hub/path-explosion, stale epoch, ambiguous-head, truncation and revocation adversaries.
6. Replay real UnifiedDB/ClayGraph/Frank dependency mutation traces.
7. Compare against strong conventional portfolio: exact B-tree where key known, FTS5, matched recursive/materialized SQL, and graph/dense/late-interaction systems only where semantically appropriate and available.
8. Replicate on Hostinger Ubuntu, then final Andreas Ubuntu target.

Promotion: `NONE` until these gates pass.
