# PostgreSQL + pgvector matched baseline profile

Status: CANDIDATE / REQUIRED COUNTERBASELINE
Date: 2026-08-10
Origin: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Parent contract: `UNIFIEDDB_CLAYGRAPH_CROSS_ENGINE_BENCHMARK_CONTRACT.md`

## Purpose

Prevent UnifiedDB + ClayGraph from claiming a database advantage merely because SQLite FTS5 or a naive row store is an easier opponent.

The PostgreSQL lane is allowed to use normal production mechanisms needed to implement equivalent Clay semantics:

- MVCC transactions and constraints;
- generated/materialized text-search state;
- GIN indexes for `tsvector`;
- `ts_rank` / `ts_rank_cd` ranking;
- normal relational indexes and partial indexes;
- application-side receipt/provenance verification when equivalent semantics require it;
- pgvector exact nearest-neighbor search as the vector recall oracle;
- pgvector HNSW and IVFFlat as approximate performance candidates;
- full-text + vector hybrid ranking via a frozen Reciprocal Rank Fusion policy.

## Primary-source basis

PostgreSQL current documentation defines `to_tsvector`, `tsquery`, `ts_rank`, and `ts_rank_cd`, with cover-density ranking accounting for proximity.

pgvector documents:

- exact nearest-neighbor search as the default and recall reference;
- HNSW and IVFFlat as approximate indexes trading recall/resource/build properties for speed;
- explicit recall monitoring by comparing approximate results to exact search;
- hybrid search together with PostgreSQL full-text search, with RRF or a cross-encoder as fusion options.

Sources:

- https://www.postgresql.org/docs/current/textsearch.html
- https://www.postgresql.org/docs/current/textsearch-controls.html
- https://github.com/pgvector/pgvector

## Frozen PostgreSQL competitor modes

### PG-FTS

Text-only conventional baseline.

Required:

- one canonical `tsvector` derived from the same textual fields exposed to Clay retrieval;
- GIN index;
- `websearch_to_tsquery` or frozen equivalent query parser;
- `ts_rank_cd` as default rank, with normalization frozen in metadata;
- identical status/epistemic/epoch filters before admission;
- deterministic tie-break by record identity.

### PG-VECTOR-EXACT

Vector recall oracle.

Required:

- identical frozen embedding model/revision for documents and queries;
- exact nearest-neighbor scan with ANN disabled;
- distance metric frozen and recorded;
- no query-specific tuning hidden from other lanes.

This mode is not expected to be the fastest. It is the reference for ANN recall.

### PG-VECTOR-HNSW

Approximate vector performance baseline.

Required:

- record HNSW `m`, `ef_construction`, query `ef_search`, index bytes and build time;
- measure Recall@k against PG-VECTOR-EXACT on every benchmark corpus;
- report filtering/selectivity effects and iterative-scan settings where used.

### PG-VECTOR-IVFFLAT

Alternative approximate vector baseline.

Required:

- record list count, probes, max probes, index bytes and build/training time;
- measure Recall@k against PG-VECTOR-EXACT;
- do not compare a deliberately low-probe configuration to Clay and call the loss architectural.

### PG-HYBRID-RRF

Strong conventional hybrid baseline.

Required:

1. PG-FTS produces lexical ranking.
2. PG-VECTOR-EXACT or the best validated ANN configuration produces semantic ranking.
3. Frozen RRF combines them with the same result budget used by the Clay lane.
4. Equivalent provenance/epoch/status safety gates remain mandatory.
5. Report lexical-only, vector-only and hybrid ablations.

## Embedding fairness

Vector baselines introduce an additional model that Clay may not require for some typed-semantic queries. Therefore report both:

- retrieval latency excluding embedding generation when precomputed query vectors are part of the workload; and
- end-to-end latency including query embedding generation when the real Frank path would need to generate it.

The embedding model must be identical for every engine lane that consumes vectors. Preserve model revision/hash, tokenizer/preprocessor, dimensions, dtype/quantization and normalization.

## Required datasets

At minimum run the parent contract suites plus:

1. synthetic held-out multi-hop fixtures already used by U11/U14/U15;
2. repository-native Clay natural-language/counterevidence queries;
3. stale/missing/conflicting graph-edge cases;
4. alias/paraphrase/OOD queries;
5. scale tiers 10k / 100k / 1M records when resource availability permits.

## Required metrics

Retrieval quality:

- Hit@1;
- Recall@5 / Recall@k;
- MRR;
- nDCG@k;
- counterevidence Recall@k;
- false-admission rate for UNKNOWN / CONFLICT / REVOKED / non-CURRENT;
- abstention and stale-basis rejection.

Vector ANN quality:

- Recall@k versus PG-VECTOR-EXACT;
- distance/rank drift;
- filtered-query result shortfall.

Performance/resources:

- p50/p90/p95/p99/min/max;
- CPU and RSS where available;
- DB/index bytes;
- WAL bytes;
- rows visited/returned and `EXPLAIN (ANALYZE, BUFFERS)`;
- build/rebuild time;
- write/update amplification;
- concurrency and recovery behavior.

## Claim gate

Until this PostgreSQL lane is actually executable on a reproducible Ubuntu environment, the correct status is:

`POSTGRES_PGVECTOR_BASELINE = BLOCKED_NOT_EXECUTED`

A Clay result may still support a workload-specific advantage over the engines actually tested. It may not support “better than every normal database.”

When PostgreSQL becomes available, the first fair comparison is PG-FTS + PG-VECTOR-EXACT + PG-HYBRID-RRF. ANN indexes are then added as speed/recall candidates, never as intentionally degraded strawmen.
