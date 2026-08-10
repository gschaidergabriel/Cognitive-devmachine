# Hostinger exact-branch + cross-engine fusion — UnifiedDB / ClayGraph — 2026-08-10

Status: SUPPORTED CANDIDATE / NOT UNIVERSAL DATABASE CLAIM
Origin: chatgpt-secondary / OpenAI / GPT-5.6 Sol

## Evidence upgrade

The previous Hostinger co-location result was an equivalent-mechanism probe executed from the runner-bound `gschaidergabriel/Dr.-Unterweger` repository. A new read-only bridge now clones `gschaidergabriel/clay-global-research-entity` on the same Hostinger runner, fetches the exact research branches, records each exact SHA, and executes them without merging to Clay `main`.

Persistent bridge receipt:

`gschaidergabriel/Dr.-Unterweger/runtime/vps_unifieddb/exact_clay_branch_bridge_v2/LATEST.json`

Observed bridge state for this cycle:

- clone return code = 0;
- overall PASS = true;
- exact SHA provenance = true;
- `chatgpt/udb-claygraph-colocation-20260810` return code = 0;
- `chatgpt/udb-repo-native-retrieval-20260810` return code = 0;
- `chatgpt/udb-sparse-merkle-shadow-20260810` return code = 0.

This removes the earlier `exact_clay_repository_sha=false` limitation for these three branch tests. It does not turn branch evidence into canonical `main` promotion automatically.

## Exact Clay co-location branch

The exact Hostinger branch run executes:

- V1 and V2 co-location migration tests;
- same-snapshot assembly adapter tests;
- local schema collision / ambiguity / rollback guards;
- source-snapshot race guards in V2;
- 1,000 matched coupled commits;
- 100 cross-file snapshot-coherence trials;
- 100 guarded two-store adversarial trials plus steady reads.

All branch tests/benchmarks returned zero.

Independent equivalent-mechanism Hostinger receipt on the same machine previously measured:

- one-file coupled commit p50 = 865.883 us;
- two-file ATTACH p50 = 1587.744 us;
- two/single p50 ratio = 1.8336715x;
- one-file mixed snapshots = 0/100;
- two-file ATTACH mixed snapshots = 100/100 under deliberately adversarial first-touch ordering;
- explicit two-store source-epoch guard accepted 0 unsafe mixed reads and recovered 100/100 on fresh retry;
- guarded two-file steady p50 = 9.433 us vs same-field one-file p50 = 7.933 us, ratio = 1.1890836x.

Interpretation:

For the tested SQLite deployment model, one physical commit/snapshot domain is supported as both a performance and coherence simplification. The strong separate-store counterbaseline remains valid because epoch pinning can fail-closed; therefore the architectural advantage is reduced physical skew/retry/guard complexity plus measured latency, not a claim that every multi-store architecture is invalid.

## Exact repository-native retrieval branch

The exact Hostinger branch indexes the real checked-out Clay repository and compares:

- SQLite FTS5/BM25;
- UnifiedDB + bounded explicit repository-reference graph activation;
- missing-graph control;
- shuffled-graph control.

The exact run passes the benchmark and supports all of the following conservative statements:

- truthful repository-reference graph retrieval is not worse than FTS5/BM25 on Hit@1, Recall@5 and MRR in this frozen suite;
- it is strictly better on at least one of those quality metrics;
- shuffled graph control reduces at least one of those quality metrics relative to truthful graph use.

This is materially stronger than the earlier purely synthetic semantic-seed benchmark because corpus text and graph edges come from the real repository. It is still a bounded hand-authored query suite, not universal retrieval evidence.

## Exact authenticated-root branch

The exact Hostinger branch executes both the rejected 256-level sparse-Merkle control and the compressed deterministic Merkle-treap shadow.

At the largest exact benchmark tier:

- state rows = 50,000;
- Merkle-treap stored nodes = 50,000;
- inclusion proof verifies;
- incremental-vs-full-rebuild differential checks pass;
- p50 canonical flat-root / incremental treap-update ratio is greater than 100x.

The earlier naive sparse tree remains rejected because of approximately O(256*N) node amplification. The compressed treap remains SHADOW ONLY until durable persistence, crash recovery, migration/versioning and target-runtime tests are complete.

## Strong relational/vector counterbaseline

A read-only Hostinger capability probe found:

- native PostgreSQL absent;
- native pgvector absent;
- Docker 29.5.1 available.

A temporary resource-bounded Docker benchmark therefore uses PostgreSQL 16 + pgvector 0.8.5 and freezes five strong conventional lanes:

- PG full-text search with GIN + `ts_rank_cd`;
- exact pgvector nearest-neighbor recall oracle;
- exact-vector + FTS reciprocal-rank fusion;
- HNSW vector search with Recall@5 checked against exact;
- HNSW + FTS reciprocal-rank fusion.

The same PostgreSQL engine also executes the Clay candidate lane: a typed two-hop `DEPENDS_ON` / `LEADS_TO` evidence closure after the same lexical seed.

The strict persisted comparison requires the Clay closure to have strictly better Recall@5 and complete-evidence@5 than every PostgreSQL lane and nDCG@5 not worse. The current controlled receipt satisfies this gate.

Important limitation:

The vector representation in this run is a deterministic 64-dimensional token-hash proxy, explicitly NOT a trained production embedding model. Therefore this is valid mechanism/cross-engine evidence, not the final vector-baseline promotion gate.

## Graph-native counterbaseline

A separate temporary Neo4j Community container runs the same multi-hop topology concept on the same Hostinger runner.

Frozen lanes:

- Neo4j full-text only;
- Neo4j native 0..2-hop traversal over `DEPENDS_ON|LEADS_TO` after the same full-text seed.

The persisted strict receipt requires native graph closure to improve Recall@5 and complete-evidence@5 over full-text with nDCG not worse. The current receipt satisfies this same-engine quality gate.

Interpretation:

This is evidence for topology/closure semantics, not evidence that Clay must own a custom graph storage engine. A graph-native backend may be the best physical executor at some scale. ClayGraph should therefore remain a typed semantic/provenance topology layer that can compile to the best measured physical backend.

## Architecture fusion

The research no longer supports the simplistic target:

`invent one custom database engine and make every query use it`

The stronger supported target is:

`UnifiedDB semantic authority + ClayGraph typed topology + adaptive cheapest-safe physical executor`

Candidate route policy:

1. exact keyed / direct state query
   -> indexed relational pushdown / fastest safe local SQL path;

2. lexical evidence query
   -> FTS path;

3. vector semantic query
   -> exact/ANN vector backend only when a validated embedding model and Recall@k gate exist;

4. relational multi-hop / dependency / counterevidence closure
   -> ClayGraph typed closure, compiled to the best measured backend;

5. ambiguous / stale / conflicting / provenance-broken basis
   -> abstain / fail-closed / rebuild / retry, never silently broaden authority.

For the v0.1 single-host Ubuntu SQLite deployment, the supported physical candidate is:

`one SQLite commit/snapshot domain = StateLedger canonical tables + namespaced derived ClayGraph projection tables`

while preserving the logical law:

`StateLedger / UnifiedDB semantic truth > verified projection receipt > ClayGraph derived activation`

No graph activation, FTS rank, vector similarity, backend rank or model score becomes truth/effect authority.

## Why this can be "better for Clay" without a universal DB claim

The measured advantage is a workload-policy combination rather than a universal storage-engine theorem:

- direct reads avoid graph cost;
- relational closure pays graph cost only when it buys evidence completeness;
- physical co-location removes a demonstrated SQLite cross-file snapshot hazard and reduces coupled commit cost;
- receipts retain source channel, epoch, provenance and authority boundaries;
- authenticated-root shadow reduces incremental integrity cost if later crash/persistence gates pass;
- conventional engines remain reusable implementation backends rather than ideological competitors.

This is a stronger architecture than trying to beat PostgreSQL, SQLite or Neo4j at every primitive operation, because it can select them where they dominate while Clay preserves semantics and causal observability.

## Remaining hard gates

No claim of "better than every normal database" is promoted. Remaining falsifiers include:

- production embedding model vs exact/ANN pgvector on real Clay queries;
- larger repository-native natural-language suite with independently authored expected evidence;
- conflict/stale/missing-edge OOD corpus;
- real current production UnifiedDB + all current ClayGraph projection-layer migration;
- writer+checkpoint stress only on SQLite 3.51.3+ or a documented fixed backport;
- crash/power-loss recovery for the combined file and authenticated-root shadow;
- 10k/100k/1M cross-engine scale tiers where resources permit;
- concurrency/resource measurements with the guarded two-store counterbaseline;
- final Andreas Ubuntu target-system acceptance.

## Current decision

- Physical SQLite co-location: SUPPORTED CANDIDATE, not canonical yet.
- Same-snapshot assembly: SUPPORTED CANDIDATE.
- Repository-native graph-assisted retrieval: SUPPORTED for the frozen suite; expand OOD corpus.
- Compressed authenticated Merkle root: SHADOW SUPPORTED; persistence/recovery unresolved.
- PostgreSQL/pgvector: strong reusable counterbackend; proxy-vector test passed controlled Clay closure gate, final embedding gate unresolved.
- Neo4j: evidence that native graph engines may be useful physical executors; do not reinvent graph storage without a measured reason.
- Universal database-superiority claim: REJECTED AS UNTESTABLE/OVERBROAD.
- Frank-specific adaptive semantic data-plane superiority: ACTIVE MEASURABLE TARGET.
