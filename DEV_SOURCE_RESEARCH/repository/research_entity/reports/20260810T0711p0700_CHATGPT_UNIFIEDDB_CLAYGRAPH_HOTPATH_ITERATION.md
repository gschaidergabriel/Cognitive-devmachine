# UnifiedDB + ClayGraph hotpath iteration — 2026-08-10 07:11 +07:00

## Provenance

- origin_actor: `chatgpt-secondary`
- provider: `OpenAI`
- model: `GPT-5.6 Sol`
- worker_identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- subject: Clay UnifiedDB / ClayGraph architecture used by Frank research/harness work
- canonical boot: RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- current program stage observed: `BASE_CLAYCODE_RELEASE`
- evidence classes in this report: `VERIFIED_REPO_STATE`, `LOCAL_EXECUTION_RECEIPT`, `PRIMARY_WEB_RESEARCH`, `CANDIDATE_ARCHITECTURE_DELTA`
- target Ubuntu/Hostinger evidence: separate bounded runner probe dispatched from `gschaidergabriel/Dr.-Unterweger`; no remote-success claim is made here until a host receipt exists.

## Question / falsifiable target

Owner direction: make UnifiedDB + ClayGraph measurably better and more accurate for Clay than a normal database workflow, then iterate with live web research and fusion.

Scientific interpretation used here:

`BETTER_FOR_CLAY` is not a universal claim that one storage engine beats every DBMS. It means Pareto improvement on Clay's declared workload while preserving semantic correctness:

1. exact current-H1 query result/truncation semantics;
2. stale-epoch rejection and semantic-state receipt binding unchanged;
3. no UNKNOWN/CONFLICT authority widening;
4. ClayGraph remains derived/rebuildable and non-authoritative;
5. out-of-order history cannot resurrect a newer tombstone;
6. bounded cognitive reads materially faster;
7. write/storage overhead explicitly measured;
8. rebuild/differential verification available;
9. ambiguity is surfaced rather than silently collapsed.

Counterhypothesis: the apparent win is only a synthetic microbenchmark; SQL pushdown/indexes/current-head projections either change semantics, fail on history disorder/tombstones, or cost too much on writes/storage to be useful.

## Current baseline defect localized

Current H1 `UnifiedDBQueryPlane.query()` materialized the entire StateLedger state, decoded every JSON value in Python, filtered/sorted, then applied LIMIT. That makes ordinary bounded cognitive reads O(N) in total state size.

Current ClayGraph `v_latest_graph_nodes` / `v_latest_graph_edges` derive each latest version with GROUP BY + MAX(graph_epoch) over version history on each read. This is correct for the ordinary unique-head case but makes repeated hot adjacency reads history-dependent in cost.

## Build delta A — UnifiedDB bounded SQL pushdown

Committed:

- `8d5beaa28969c553735edfe91a09ec3e56f0c0fe` — bounded query pushdown into SQLite; LIMIT+1 preserves truncation; singleton predicates use `=`; conservative legacy fallback remains for unusually large filter sets/alternate ledgers.
- `5c567ab896f050c043672e43851c9f1bf99e5dcc` — lean partial CURRENT-state index family:
  - `(domain,k,epistemic) WHERE status='CURRENT'`
  - `(k,domain,epistemic) WHERE status='CURRENT'`
- `2766a1d0eb8a8f22c93bca7c23ad2a352bdde0c5` — differential regression tests for filter, Unicode ordering, truncation, empty epistemic/status sets and large-filter fallback.
- `c3392e950e1f4d8874ba5d59760098a221fbeb4e` — reproducible benchmark contract.

No query receipt, stale-epoch or assembly-authority semantics were relaxed.

## UnifiedDB local measurements

Local runtime metadata:

- Python 3.13.5
- SQLite 3.46.1
- Linux 6.18.35 x86_64
- glibc 2.41
- synthetic state: 20,000 rows, fixed seeds, in-memory SQLite
- failures/timeouts are retained as data: initial oversized repeated full-scan benchmark exceeded the 45 s local execution budget and was reduced without changing query semantics.

Paired baseline vs SQL-pushdown run, 60 bounded mixed queries:

| metric | old full materialize/filter | candidate SQL pushdown | ratio |
|---|---:|---:|---:|
| p50 | 78,459.817 us | 276.597 us | 283.66x faster |
| p95 | 110,358.666 us | 2,309.275 us | 47.79x faster |

Differential correctness: 100 additional query specs, `0` mismatches.

Planner/index iteration with singleton `=` + lean partial index family, 200 specs:

- differential mismatches: `0`
- candidate p50: `140.687 us`
- candidate p95: `279.038 us`
- candidate p99: `472.112 us`
- key-only p50: `51.786 us`
- key-only p95: `85.548 us`
- EXPLAIN QUERY PLAN selected `idx_state_key_current` for the key-specific hot path.

Isolated state UPSERT shadow, 20,000 rows / 2,000 updates:

| metric | base PK only | + lean CURRENT indexes | ratio |
|---|---:|---:|---:|
| write p50 | 5.3915 us | 8.5745 us | 1.590x slower |
| write p95 | 6.6405 us | 10.7526 us | 1.619x slower |
| pages | 683 | 960 | 1.406x |
| bytes @ 4096 B/page | 2,797,568 | 3,932,160 | 1.406x |

Interpretation: this is a strong read-heavy trade for Clay's bounded context assembly, but it is not a universal database claim. The write/storage shadow remains an explicit cost.

## Build delta B — ClayGraph V3 rebuildable latest-head projection

Candidate commits:

- `512b26e2642d687eecc50a41938d79c224e4cbce` initial corrected head-projection candidate.
- `ff1dd94d4ccf5f7fdbced9b09b10cd67bd1d6192` adds explicit same-logical/same-epoch ambiguity views and promotion gate.
- `89c1d861b53d0239f6bf2b5818f1b44e8a32914a` adds tombstone/out-of-order/rebuild/ambiguity falsifier tests.

Design:

- append-only/versioned graph history remains authoritative;
- `graph_head_nodes` / `graph_head_edges` are derived acceleration state only;
- heads retain the newest row regardless of CURRENT vs tombstone status;
- fast CURRENT views filter the retained head status;
- AFTER INSERT UPSERT only advances when incoming graph_epoch is newer (or deterministic same-epoch version-id tie-break);
- same-logical/same-epoch duplicate history is exposed by `v_graph_projection_ambiguous_*_epochs` and prevents verified promotion until resolved/verified;
- projection receipts can only be marked verified after ambiguity=0 and full fast-vs-legacy equality.

## ClayGraph falsification history

The first draft deleted non-CURRENT heads. Randomized out-of-order insertion falsified it: a newer RETRACTED tombstone could disappear and a later-arriving older CURRENT version could resurrect. That design was rejected before promotion.

Corrected design keeps tombstone heads. Randomized differential test after correction:

- current nodes: 276 baseline / 276 candidate, equal
- current edges: 752 baseline / 752 candidate, equal
- rebuild nodes: equal
- rebuild edges: equal
- out-of-order late-old-current after newer tombstone: no resurrection

Additional ambiguity falsifier found later: if one logical relation has >1 versions at the exact same graph_epoch, the legacy MAX(epoch) view may emit multiple rows while a single-head projection chooses one. The candidate now surfaces this case explicitly and the regression suite deliberately proves non-equivalence in that ambiguous condition. This is a promotion blocker, not hidden normalization.

## ClayGraph local performance measurement

Larger corrected V3 run:

- logical edges: 8,000
- versions per logical edge: 7
- history rows: 56,000
- current rows: 7,529
- full baseline-vs-fast projection equality: true

| metric | legacy MAX(epoch) view | V3 current-head view | ratio |
|---|---:|---:|---:|
| adjacency p50 | 13,450.480 us | 14.641 us | 918.69x faster |
| adjacency p95 | 14,446.287 us | 18.303 us | 789.29x faster |
| candidate p99 | — | 27.793 us | — |

Write/storage shadow:

- append-only edge insert p50: `6.434 us`
- trigger-maintained V3 insert p50: `17.597 us`
- median write ratio: `2.735x`
- base pages: `1969`
- V3 pages: `2681`
- synthetic page ratio: `1.362x`

Earlier 30,000-history-row corrected projection rebuild was ~13 ms locally; current promotion still requires target-shaped rebuild/recovery measurement.

## Negative result — WITHOUT ROWID

Rejected. On the measured graph-head schema:

- WITH ROWID read p50: 13.944 us; rebuild 12.958 ms; 1556 pages
- WITHOUT ROWID read p50: 14.820 us; rebuild 13.716 ms; 1541 pages

~1% page saving did not compensate for slower reads/rebuild. `WITHOUT ROWID` remains NOT_SELECTED unless a future target workload reverses the result.

## Live primary-source research and fusion

SQLite primary documentation supports the mechanism but not any universal-superiority claim:

- Query planner: matching multi-column indexes can search and satisfy ordering without a full table scan/sort — https://www.sqlite.org/queryplanner.html
- Partial indexes: smaller subset indexes can reduce database size and improve read/write performance, but their predicate implication rules are syntactically conservative — https://www.sqlite.org/partialindex.html
- UPSERT: `ON CONFLICT ... DO UPDATE ... WHERE` supports conditional replacement, matching the newer-head update pattern — https://www.sqlite.org/lang_upsert.html
- Trigger semantics: AFTER INSERT trigger bodies may execute INSERT/UPSERT-derived maintenance logic — https://sqlite.org/lang_createtrigger.html
- WAL/isolation: WAL permits concurrent readers and writers with snapshot isolation, while checkpoints can be starved by long-lived readers — https://www.sqlite.org/wal.html and https://www.sqlite.org/isolation.html

Fusion consequence:

1. keep singleton equality predicates in generated hot-path SQL;
2. keep lean partial indexes, not broad covering-index inflation by default;
3. retain authoritative version/event history and derive current heads;
4. never delete tombstone heads merely because the hot view filters them;
5. treat same-epoch duplicate heads as an explicit ambiguity/failure state;
6. do not relax FULL durability based on read-speed work; checkpoint/recovery is a separate test lane;
7. do not adopt WITHOUT ROWID without workload evidence.

## Accuracy conclusion

Measured claim now supported:

> For the tested Clay workload, the new UnifiedDB bounded-read path preserves current H1 query semantics with zero observed differential mismatches while reducing bounded-read latency by orders of magnitude. The corrected ClayGraph V3 projection preserves ordinary unique-head latest-view semantics, survives randomized out-of-order/tombstone/rebuild falsifiers, and reduces repeated adjacency lookup latency by roughly three orders of magnitude on the tested history size.

Not supported and therefore NOT claimed:

> “UnifiedDB/ClayGraph is more accurate or faster than every normal database.”

A normal PostgreSQL/SQLite/graph database can implement indexes/materialized projections too. Clay's differentiator is the combined semantic contract (epochs, epistemic state, provenance/receipts, non-authoritative derived graph, rebuild/falsification gates) plus measured workload-specific latency. Cross-engine superiority requires matched PostgreSQL/Neo4j/DuckDB/etc. workloads and is not yet evidence-backed.

## Architecture status

- UnifiedDB SQL-pushdown: `IMPLEMENTED_IN_H1_REFERENCE_PATH`, locally differential-tested; remote exact-repo run outstanding.
- UnifiedDB lean hot indexes: `IMPLEMENTED_IN_H1_REFERENCE_PATH`, local read/write/storage shadow measured.
- ClayGraph V3 latest-head projection: `TESTING_CANDIDATE`, NOT promoted to current stack.
- ClayGraph V3 same-epoch ambiguity: `KNOWN_PROMOTION_BLOCKER_UNTIL_TARGET_DATA_VERIFIED_ZERO_OR_SEMANTICS_DEFINED`.
- Universal DB superiority: `UNSUPPORTED_CLAIM`.
- WITHOUT ROWID: `NOT_SELECTED`.

## Next falsifiers / frontier

1. Read back the repository-scoped Hostinger Ubuntu equivalent-mechanism receipt; do not call it exact Clay checkout evidence.
2. Run exact Clay repo tests once a Clay-scoped runner or authorized ferry exists.
3. Add crash/restart + WAL checkpoint pressure with long reader and write contention.
4. Measure StateLedger `_roots()` full-state rehash cost; it remains O(N) on writes and is the likely next UnifiedDB scaling bottleneck.
5. Shadow an incremental authenticated-state root (Merkle/radix candidate) without changing the current canonical semantic-state hash; promote only if replay/rebuild/proof semantics and resource cost win.
6. Benchmark target-shaped context assembly accuracy/precision and latency against deliberately simpler SQL-only and graph-only baselines.
7. Only then consider cross-engine baselines; never use different semantics to manufacture a win.
