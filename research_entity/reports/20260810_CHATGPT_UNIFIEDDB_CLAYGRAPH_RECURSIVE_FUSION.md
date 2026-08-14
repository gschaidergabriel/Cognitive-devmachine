# UnifiedDB + ClayGraph recursive fusion — 2026-08-10

Status: RESEARCH DELTA / CANDIDATE ARCHITECTURE CONSEQUENCE  
Actor provenance: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Persistent entity: Clay Research Entity; actor is a temporary worker, not Frank.  
Authority: research/build/test only; Frank self-Harness authority remains proposal-only.  
Primary mission: Frank v0.1 fully operational on Andreas' Ubuntu developer system.

## 1. Question

Can UnifiedDB + ClayGraph become measurably better *for Clay/Frank retrieval workloads* than a conventional flat database path, while preserving or improving correctness, provenance, replay and recovery?

The phrase “better than every normal database” is treated as a falsifiable workload-specific target, **not** as a universal engine-superiority claim. A conventional DB can implement arbitrarily sophisticated application semantics; therefore the relevant comparison is the end-to-end Clay/Frank read workload under matched correctness and resource constraints.

## 2. Fresh local execution — semantic history + versioned ClayGraph

Fresh local run on Linux / Python 3.13.5 / SQLite 3.46.1:

- workload: 120,000 logical edges × 3 versions = 360,000 `graph_edges` rows;
- 100 source-neighborhood queries;
- 15 repeated global latest-view measurements;
- 10,000 adversarial logical-edge histories;
- 100 semantic-history update cycles.

### Legacy latest-edge baseline

- source-neighborhood p50: `138.3209435 ms`;
- source-neighborhood p95: `145.9231840 ms`;
- global latest p50: `209.7355720 ms`;
- query plan includes full `graph_edges` scan + temporary B-tree for GROUP BY.

### Indexed anti-probe candidate

- source-neighborhood p50: `0.0807200 ms`;
- source-neighborhood p95: `0.1041750 ms`;
- source-neighborhood p50 speedup: `1713.5895x`;
- global latest p50: `123.5837270 ms`;
- global p50 speedup: `1.6971x`;
- adversarial exact result equivalence: `0 / 10,000` symmetric differences;
- latest-row count equal: `true`.

### Semantic history correctness

Legacy `semantic_records UNIQUE(record_kind,record_key,scope,status)` fails reproducibly at history cycle 3 with `UNIQUE constraint failed` once a second `SUPERSEDED` row is required.

Partial-current-head candidate:

- history cycles retained: `100 / 100`;
- exact epoch sequence retained: `true`;
- current heads: `1`;
- result: PASS for this falsifier.

### Selection consequence

The anti-probe candidate is **NOT_SELECTED as the final ClayGraph read projection**, because concurrent Research Entity work produced a materialized graph-head projection that dominates it on the primary read path while preserving version/tombstone/ambiguity tests. Preserve the anti-probe result as a simple correctness/performance baseline and fallback design.

## 3. Concurrent materialized-head evidence

Current shared-repo evidence already measured the materialized ClayGraph head against historical GROUP-BY retrieval:

- adjacency p50: about `13,450.480 us -> 14.641 us` = about `918.69x` faster;
- p95: about `14,446.287 us -> 18.303 us` = about `789.29x` faster;
- equality with the version-log truth passed in the reported workload;
- write cost increased about `2.735x`;
- storage pages increased about `36.2%`;
- tombstone, out-of-order, rebuild and same-epoch ambiguity falsifiers exist.

Architecture interpretation: ClayGraph is derived/rebuildable and read-heavy, so paying more on projection maintenance can be rational when the exact read-equivalence/recovery contract passes. This is not a reason to move canonical truth into ClayGraph.

## 4. Fresh hybrid retrieval mechanism run

Fresh local run on Linux / SQLite FTS5:

- semantic rows: `11,200`;
- noise rows: `10,000`;
- query cases: `200`;
- flat FTS `recall@3`: `0.3333333`;
- hybrid lexical-seed + explicit semantic binding + bounded graph expansion `recall@3`: `1.0000000`;
- exact-seed retention: `1.0000000`;
- stale-binding leaks: `0`;
- flat FTS p50: `0.020851 ms`;
- hybrid p50: `0.034651 ms`;
- hybrid p95: `0.058006 ms`.

This is **synthetic mechanism evidence only**. It demonstrates that relational expansion can recover required multi-hop evidence at very small absolute local latency in the fixture. It does not establish live-project accuracy.

## 5. Existing U14/U15 shared evidence fused in

Existing current Research Entity measurements show:

- compiled intent/entity semantic fields retained top-1 accuracy `1.0` against matched online SQL in the synthetic U14 workload;
- U14 compiled hot-read mean latency was about `12.64x–14.15x` faster than its matched online-SQL comparator;
- exact B-tree reads can still be faster than compilation and remain a valid ordinary-DB route;
- build cost was material (roughly 62–72 ms in the recorded field-generation benchmark), so high-churn semantic families may rationally stay online;
- U15 therefore deepens only on an explicit sufficiency gap rather than graph-expanding every read.

This evidence supports an adaptive planner, not a universal compiled/read-cache mandate.

## 6. Retrieval hardening defects found by adversarial review

The disposable UnifiedDB+ClayGraph retrieval candidate had three reproducible defects:

1. ASCII-only query regex split German/Unicode terms (`ä/ö/ü/ß`) even though FTS5 uses `unicode61`;
2. verified file-backed projection basis was not restored after process restart;
3. final SQL `LIMIT` bounded output count but did not bound recursive graph work; fanout stress rose from about 1.8 ms at branching 25 to about 318 ms at branching 400.

A fourth planner defect appeared after adding a fanout cap: SQLite could still reorder the document join into a full document-table scan.

Draft hardening candidate therefore adds:

- Unicode-aware tokenization + German intent terms;
- fail-closed persisted basis restoration;
- deterministic per-source graph rank;
- reserved admission positions for explicit counter/refuting relations;
- live fanout cap of 32;
- bounded graph work followed by forced indexed document probes;
- stale/unverified/restart/fanout/counterevidence falsifiers.

SQLite primary documentation supports `CROSS JOIN` as a deliberate join-order control and a recursive-CTE `LIMIT` as an additional hard recursion safety bound. A global geometric walk cap should therefore accompany the per-node cap in the next revision.

## 7. Strong conventional-database adversary

A new matched PostgreSQL 18.4 benchmark candidate is in Draft PR #115.

Workload design:

- 3 deterministic seeds;
- 600 component -> service -> resource families;
- 4,000 distractor records;
- 5 repeats per family;
- exact-key, 1-hop, 2-hop and lexical read classes;
- PostgreSQL receives B-tree and GIN indexes;
- PostgreSQL receives parameterized/prepared online SQL;
- matched deterministic entity/intent extraction is measured;
- a separate fully-online alias-resolution path is measured;
- embedded SQLite B-tree remains the simpler exact-key baseline;
- Clay uses repository `AdaptiveSemanticReadPlaneV14` with verified basis receipts.

The first GitHub-hosted run failed before workflow steps/logs, so it is classified as an infrastructure/service-container failure, **not** as PostgreSQL query evidence. The workflow was changed to start PostgreSQL explicitly inside a normal step and capture `pg_isready` plus container logs. GitHub-hosted and Hostinger self-hosted runs are currently pending/queued at this report revision.

PostgreSQL primary documentation confirms that the baseline can legitimately use `tsvector`/`tsquery`, GIN and `ts_rank`/`ts_rank_cd`, including application-specific ranking factors. The baseline must therefore remain strong rather than deliberately crippled.

## 8. New shared exact Top-K frontier work

Current main has added an exact best-first Top-K EAP stop. Its key proof obligation is monotone activation: edge weights and hop decay are bounded to `(0,1]`, so descendants cannot exceed the frontier ancestor score. Early stop is permitted only when the Kth admissible visited score is **strictly above** the best remaining frontier upper bound; equal-score frontiers continue so tie ordering is not silently changed.

A benchmark and self-hosted Ubuntu gate have been added in the shared repo. Treat it as CANDIDATE until the executed receipt confirms exact selected-signature equivalence and the measured expansion/latency improvement.

## 9. Fused adaptive UnifiedDB read architecture

Current best architecture hypothesis is a **Pareto-routed semantic read plane**, not a one-mechanism database replacement:

### A — `EXACT_INDEX`
Use the cheapest exact current-key/index lookup when the query is structurally exact. Ordinary B-tree/index implementations are allowed to win.

### B — `COMPILED_SEMANTIC_FIELD`
For stable, repeated intent/entity/semantic families with adequate horizon, use verified precompiled fields bound to `(source_epoch, graph_epoch, basis_id, derivation_hash)`.

### C — `EXACT_TOPK_FRONTIER`
For monotone active-assembly ranking, use a mathematically exact score-bound frontier stop when equivalence is proven. Do not approximate ties or authority/admissibility.

### D — `TYPED_GAP_DEEPENING`
Consume compiled context first. Invoke bounded ClayGraph deepening only for explicit evidence/sufficiency gaps; stop on no novelty and retain provenance/counterevidence.

### E — `HARDENED_LEXICAL_GRAPH_FALLBACK`
For misses/OOD/uncompiled semantics, use FTS/lexical seeds + explicit UnifiedDB<->ClayGraph bindings + doubly bounded graph expansion + indexed reconstruction to canonical UnifiedDB records.

### F — `CONVENTIONAL_ONLINE_SQL`
If write/churn rate makes projection/compile amortization unfavorable, stay with conventional indexed online SQL. This is an intended adaptive outcome, not a failure.

Hard invariant across all modes:

`UnifiedDB canonical semantic/logical truth -> derived/rebuildable ClayGraph/compiled projections -> context-only retrieval receipt`.

Never:

`graph activation/cache hit/model output -> truth or effect authority`.

## 10. Current hypothesis / counterhypothesis

### H-UDB-ADAPTIVE
A basis-bound adaptive planner choosing the cheapest proven-correct mode per query family will outperform a single conventional online path for Clay/Frank hot reads on the joint vector:

`correctness + stale/provenance integrity + p50/p95/p99 latency + context size + recovery + amortized write/build cost`.

### CH-UDB-ADAPTIVE
Once a strong conventional database receives equivalent materialized views, indexes, semantic aliases, graph extensions and application logic, Clay-specific gains collapse to implementation placement/in-process overhead rather than a database-level advantage; maintenance/churn cost may dominate.

Both remain active. CH-UDB-ADAPTIVE is especially important because any semantics implemented in Clay can in principle be reimplemented over a conventional DB. The project should claim only measured end-to-end advantages for the target workload.

## 11. Promotion blockers / next falsifiers

No universal superiority claim is promoted. Required next evidence:

1. executed PostgreSQL 18 matched adversary on a clean Ubuntu runner;
2. Hostinger self-hosted replication with exact machine/runtime metadata;
3. real, manually adjudicated Clay contract/query suite rather than synthetic family-only accuracy;
4. stale/conflict/negative-result/authority controls in the real suite;
5. 10k/100k/1m scale sweep where feasible;
6. concurrency/read-write interference and WAL/locking effects;
7. build/update amortization break-even by semantic-family churn rate;
8. crash/restart/rebuild/rollback equivalence;
9. pgvector and/or strong vector/reranker baseline where semantic similarity is actually required;
10. graph-native competitor only on workloads where graph traversal is material;
11. final Andreas Ubuntu target evidence before release-level claims.

## 12. Negative results preserved

- “ClayGraph anti-probe latest view is final best design” -> NOT_SELECTED; materialized head dominates relevant reads.
- “Always compile every read” -> REFUTED by exact-index floor and churn/build economics.
- “Always graph-expand retrieval” -> REFUTED; graph work is conditional on typed sufficiency gaps.
- “Final LIMIT means graph work is bounded” -> REFUTED by fanout stress.
- “Fanout cap alone guarantees stable query time” -> REFUTED by SQLite planner full-document-scan case.
- “PostgreSQL job setup failure means PostgreSQL loses” -> REFUTED as invalid inference; no query steps executed.
- “Current evidence proves better than every normal database” -> NOT SUPPORTED.

## 13. Architecture delta status

Status: `TESTING`.

Supported now:

- UnifiedDB stays canonical authority;
- materialized/current projections are legitimate when verified/rebuildable;
- ClayGraph is a high-value derived adjacency/topology plane;
- compiled semantic hot fields can materially reduce repeated read cost without quality loss in current synthetic evidence;
- adaptive routing is superior to a doctrinal one-path architecture in current evidence;
- exact and negative-result evidence must remain first-class.

Not yet supported:

- universal database superiority;
- live Frank answer-quality superiority;
- final Postgres/pgvector/graph-DB dominance;
- final target-host release promotion.
