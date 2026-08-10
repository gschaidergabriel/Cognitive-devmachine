# UnifiedDB + ClayGraph cognitive retrieval V7 — 2026-08-10 07:20 +07:00

## Provenance

- origin_actor: `chatgpt-secondary`
- provider: OpenAI
- model: GPT-5.6 Sol
- worker_identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- subject: Clay UnifiedDB + derived ClayGraph cognitive retrieval for Frank research/harness work
- canonical boot observed at run start: RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- current program stage observed at run start: `BASE_CLAYCODE_RELEASE`
- branch: `chatgpt/udb-claygraph-cognitive-retrieval-v7-20260810`
- evidence classes: VERIFIED_REPO_STATE, LOCAL_EXECUTION_RECEIPT_SYNTHETIC_HELDOUT, PRIMARY_WEB_RESEARCH, CANDIDATE_ARCHITECTURE_DELTA
- exact current-repository checkout / Hostinger Ubuntu receipt for this V7 branch: OUTSTANDING at report write time

## Owner target and scientific translation

Owner target: intensively improve UnifiedDB and ClayGraph until they are measurably better and more accurate for Clay than a normal database workflow, use the result, measure it, iterate, then perform fresh web research, fuse the evidence and continue building.

The phrase "better than every normal database" is not treated as already proven. A normal SQLite/PostgreSQL/graph system can implement full-text indexes, graph traversals and materialized projections. The falsifiable target used here is narrower and useful:

`BETTER_FOR_CLAY_COGNITIVE_RETRIEVAL` means a matched workload win in retrieval quality while preserving the semantic invariants normal text search does not itself provide: epoch/state-hash binding, epistemic/status gates, provenance, non-authoritative graph semantics, rebuildability, explicit conflicts, and fail-closed projection verification.

Universal or cross-engine superiority remains UNSUPPORTED until matched PostgreSQL/pg_trgm, graph-engine and other relevant baselines are run with equivalent semantics.

## Shared-state coordination

A parallel Clay worker materially improved the hot read substrate before this accuracy branch completed:

- `abe54f134f26dd8b0204a289b6d73328176ae961` records UnifiedDB SQL pushdown + lean indexes and ClayGraph V3 current-head projection work.
- UnifiedDB bounded reads preserved differential semantics in that lane and improved synthetic hot-read latency by orders of magnitude while explicitly measuring write/storage cost.
- ClayGraph V3 retained authoritative version history, derived rebuildable current heads, falsified tombstone resurrection, and surfaced same-logical/same-epoch ambiguity as a promotion blocker.
- That report explicitly left target-shaped context-assembly accuracy against simpler SQL-only and graph-only baselines as an open frontier. V7 closes that specific measurement gap instead of duplicating the hotpath work.

Relevant V3 safety artifacts already on main before this branch:

- `research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_PROJECTIONS.sql`
- `research_entity/harness/reference/test_claygraph_v3_current_projections.py`

## Hypothesis and strongest counterhypothesis

H1: for relation-target cognitive queries, a typed two-stage retrieval path — conventional FTS candidate generation followed by a verified ClayGraph path rerank — materially improves top-result accuracy over the identical lexical/semantic candidate path without graph context.

H0/counterhypothesis: any apparent graph win is caused by hand-written synonym tuning or leaked ground truth; explicit anchors/hints perform all useful work, and the graph adds no robust signal. A second counterhypothesis is that graph acceleration creates semantic danger by admitting stale/conflicting/tombstoned relations.

Cheapest discriminating experiment: freeze a fresh holdout after the V7 scoring rule is frozen, run the exact same records/query text/semantic hints/candidate generator with graph disabled versus enabled, and preserve failures.

## Iteration history and negative result

### V4 — rejected overfit

A synonym-heavy hybrid looked perfect on its development set, then regressed on the first new paraphrase/OOD set:

- SQLite FTS5/BM25 Hit@1: 71.43%
- V4 Hit@1: 67.86%
- V4 Recall@3: 92.86%

Interpretation: extra hand-crafted semantic reranking improved recall but damaged first-result precision. V4 was rejected; no promotion claim was made.

### V5 — small OOD gain, insufficient alone

On a second fresh 36-query holdout:

- stronger FTS5 + semantic baseline Hit@1: 86.11%, MRR 92.59%
- V5 Hit@1: 88.89%, MRR 93.98%

This was directionally positive but too small to justify a strong graph-accuracy claim.

### V7 — typed anchor -> relation -> target ablation

V7 removes graph use from generic direct lookups. The caller/model may supply semantic hints and explicit anchor refs. Graph influence is admitted only for `CONNECTED_TARGET` intent and produces a path receipt. The matched baseline receives the same query text and semantic hints but disables the graph and anchor transition.

Frozen holdout fixture:

- benchmark id: `UDB_CLAYGRAPH_COGNITIVE_RETRIEVAL_V7_HOLDOUT3`
- records: 41
- graph edges: 26
- queries: 40
- evidence class: `LOCAL_SYNTHETIC_HELDOUT_FIXTURE`
- raw fixture SHA-256 before gzip/base64: `7ee842fc68ea35c6649bbb55593dfde0eaa5937023be4c5485d60f08a3be9f1c`
- fixture was created after the V7 rule was frozen and was not used to tune V7 afterward.

Exact final-module local result on that frozen fixture:

| metric | direct same candidate path, no graph | V7 typed graph path | delta |
|---|---:|---:|---:|
| Hit@1 | 80.00% | 97.50% | +17.50 pp |
| MRR | 87.2917% | 98.7500% | +11.4583 pp |
| Recall@3 | 95.00% | 100.00% | +5.00 pp |
| nDCG@5 | 89.8860% | 99.0773% | +9.1913 pp |

Graph-off had 8 first-rank failures. V7 graph-on had 1 first-rank failure (`z33`, relevant answer at rank 2). The surviving error is retained as evidence rather than hidden.

This supports a causal contribution from the typed graph rerank on the frozen synthetic Clay workload because the lexical candidate path and semantic hints are held constant while graph use is ablated. It does NOT prove that arbitrary graph construction or automatic anchor generation will generalize.

## Local latency measurement

Final-module local runtime metadata:

- Linux 6.18.35 x86_64, glibc 2.41
- CPU: AMD EPYC 9V74 80-Core Processor
- MemTotal: 6,219,544 kB
- Python 3.13.5
- SQLite 3.46.1
- corpus: 41 records / 26 edges / 40 queries
- 2,000 timed queries per variant after first index build

Latest run `chatgpt-udb-claygraph-v7-local-20260810T0720p0700`:

| latency | direct no graph | V7 graph |
|---|---:|---:|
| p50 | 0.232109 ms | 0.232144 ms |
| p95 | 0.390055 ms | 0.371465 ms |
| p99 | 0.479750 ms | 0.415795 ms |
| mean | 0.250100 ms | 0.248477 ms |

First query including projection + in-memory FTS construction: 2.048889 ms.

Interpretation: at this tiny fixture size the graph rerank adds no material median-latency penalty; scheduler/cache noise is larger than the measured median difference. This is not a target-machine or large-scale latency claim.

An earlier 10,041-record synthetic-noise stress run kept median query latency near 0.41 ms but had ~11.7 ms p95 due to larger FTS candidate work. That stress result is exploratory and not the primary accuracy receipt.

## V7 architecture delta

New candidate file:

`research_entity/harness/reference/cognitive_retrieval.py`

Semantics:

1. Derived in-memory FTS5 projection is rebuilt when UnifiedDB epoch or semantic-state hash changes.
2. SQLite FTS5 remains the conventional candidate generator; token-overlap is only a fallback where FTS5 is unavailable.
3. `CognitiveQueryIntent` binds query id, text, semantic hints, anchor refs, target mode, status/epistemic allowance, limit and basis epoch.
4. Generic `DIRECT` retrieval gets no graph boost.
5. `CONNECTED_TARGET` traverses only supplied anchors and emits an explicit `(anchor, relation, target, direction)` graph-path receipt.
6. Graph candidates must still pass UnifiedDB status and epistemic gates; ClayGraph cannot widen authority.
7. Result receipts retain the source semantic hash plus last-touch provenance reconstructed from the UnifiedDB event log.
8. The ledger epoch and semantic-state hash are checked again before returning; concurrent semantic change raises stale-state failure rather than returning an unbound mixture.
9. `load_verified_claygraph_edges()` fails closed unless the current ClayGraph V3 projection has zero same-epoch ambiguity and a matching `verified_equal=1` projection receipt for the requested UnifiedDB source epoch.
10. ClayGraph remains a rebuildable context/ranking projection. Graph activation is never truth or effect authority.

Candidate safety tests added:

- direct retrieval
- connected target yields path + provenance
- graph cannot admit CONFLICT by default
- stale basis rejection
- retrieval projection rebuild after ledger write
- verified V3 graph loader
- fail-closed on V3 ambiguity
- fail-closed without matching verified V3 receipt

The 8/8 result observed during development was against a reconstructed local harness/test double. The exact private-repository checkout test is a separate required gate and is not claimed as passed in this report.

## Reproducible benchmark artifacts

- candidate implementation commit: `dbc1a88b32aa846108f689ed36d219e70f912f0c`
- test commit: `1247882fd1da1795ff2efb899ee56b0d42a58aab`
- frozen fixture commit: `38d05549b187c08cec27a457f0d7f0d67202a163`
- benchmark runner commit: `cea7f8a3d5cdfd5f1976b9577bad40aa00a8de8f`

Fixture path:

`research_entity/benchmarks/udb_claygraph_cognitive_retrieval_v7_fixture.json.gz.b64`

Runner path:

`research_entity/benchmarks/benchmark_udb_claygraph_cognitive_retrieval_v7.py`

The runner decodes the frozen fixture, executes the graph-off and graph-on ablation and emits machine-readable JSON with accuracy failures and latency quantiles. `--noise-rows` permits bounded synthetic scale pressure without changing the held-out semantic queries.

## Fresh primary-source web research after measurement

The post-measurement research did not justify replacing the physical database substrate. It supports the composition used by V7:

- SQLite FTS5 official documentation: FTS5 is a full-text-search virtual table and supports relevance ordering through its rank/BM25 machinery. https://www.sqlite.org/fts5.html
- SQLite WITH/recursive CTE documentation: recursive CTEs can walk trees or graphs. https://www.sqlite.org/lang_with.html
- Microsoft GraphRAG Local Search documentation: local search maps a query to graph entities, gathers connected entities/relationships and linked text units, then prioritizes/filter context to a bounded window. https://microsoft.github.io/graphrag/query/local_search/
- PostgreSQL pg_trgm official documentation: trigram similarity plus GiST/GIN index support is a credible stronger non-Clay text baseline for the next cross-engine falsifier. https://www.postgresql.org/docs/17/pgtrgm.html

Fusion consequence:

- KEEP conventional FTS/database primitives as candidate generators and storage mechanisms.
- KEEP UnifiedDB as canonical semantic/logical truth plane with epoch/provenance/transaction/replay semantics.
- KEEP ClayGraph derived/rebuildable and non-authoritative.
- ADD graph context only where a typed relation-target intent exists.
- REQUIRE graph-path receipts and V3 projection verification.
- REQUIRE an automatic-anchor/open-set test before claiming end-to-end retrieval superiority, because V7 currently assumes model/caller-supplied anchors and semantic hints.
- ADD PostgreSQL/pg_trgm and at least one graph-engine baseline before any cross-engine claim.

## Architecture status

- UnifiedDB SQL-pushdown / hot indexes from parallel lane: implemented in H1 reference path; local differential/performance evidence exists.
- ClayGraph V3 current-head projection: testing candidate with explicit ambiguity promotion gate.
- V7 cognitive retrieval: `SUPPORTED_AS_FEATURE_BRANCH_CANDIDATE` on synthetic heldout graph-ablation evidence.
- Main/canonical promotion of V7: NOT YET AUTHORIZED BY EVIDENCE; exact repo branch tests/CI and collision check required first.
- Universal "better than every database" claim: UNSUPPORTED.
- Workload-specific claim now supported: on the frozen 40-query Clay semantic fixture, typed verified graph context raised Hit@1 from 80.0% to 97.5% with essentially unchanged local median latency.

## Next falsifiers / next build frontier

1. Run exact branch tests in the real private repository/CI; read the actual workflow receipt before merge.
2. Rebase/merge only after refreshing main and confirming no newer worker owns the same cognitive-retrieval file/contract.
3. Test wrong-anchor, missing-anchor, multiple-anchor and adversarial-anchor cases; add calibrated abstention/open-set behavior.
4. Measure automatic anchor extraction separately from graph reranking so model hint quality is not silently credited to ClayGraph.
5. Run target-shaped corpus assembled from real UnifiedDB/ClayGraph records with held-out labels and provenance.
6. Run PostgreSQL FTS/pg_trgm and a suitable graph-engine baseline with matched semantics where feasible.
7. Measure FTS projection rebuild churn, memory, concurrent writes, crash/restart and stale-reader behavior at 100k+ state rows.
8. Add multi-hop graph retrieval only behind a stricter path-budget/loop/ambiguity gate; one-hop remains the simpler baseline.
9. Preserve `z33` as an active failure and construct a discriminating query to determine whether relation semantics or candidate-text evidence should win.

No paid training gate is crossed by this work. No Frank self-harness authority is introduced.
