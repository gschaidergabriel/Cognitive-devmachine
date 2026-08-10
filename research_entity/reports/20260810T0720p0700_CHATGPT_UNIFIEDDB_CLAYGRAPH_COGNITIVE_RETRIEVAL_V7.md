# UnifiedDB + ClayGraph accuracy iteration: V7 evidence -> V14/V15 fusion

## Provenance

- origin_actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- worker identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- canonical boot observed at run start: RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- program stage observed at run start: `BASE_CLAYCODE_RELEASE`
- branch: `chatgpt/udb-claygraph-cognitive-retrieval-v7-20260810`
- evidence: VERIFIED_REPO_STATE + LOCAL_SYNTHETIC_HELDOUT + PRIMARY_WEB_RESEARCH + CANDIDATE_ARCHITECTURE_DELTA
- exact private-repository CI / Hostinger receipt for this branch: required before main promotion; not yet claimed here

## Owner target / claim boundary

The owner requested intensive UnifiedDB + ClayGraph work until it is measurably better and more accurate for Clay than a normal database workflow, followed by fresh web research, fusion and more building.

A universal claim that Clay is "better than every database" is NOT supported. Conventional databases can implement full-text search, graph traversal, materialized/compiled projections and similarity indexes. The supported target is workload-specific: beat strong conventional retrieval baselines for Clay's semantic/relational context assembly while preserving Clay invariants — epochs, provenance, epistemic/status gates, non-authoritative graph semantics, rebuildability, conflict visibility and fail-closed verification.

## Coordination with concurrent UnifiedDB / ClayGraph work

During this run main advanced materially:

- `abe54f134f26dd8b0204a289b6d73328176ae961`: UnifiedDB SQL pushdown + lean indexes and ClayGraph V3 current-head performance/falsifier work.
- `096003221ab40de179745ca23bb9c4aac4cd9b65`: U14 adaptive semantic read plane. It routes exact keys to normal indexes, sufficient compiled semantic fields to a sufficiency stop, resolved entities to ClayGraph, compositional queries to a frontier, and unresolved misses to conventional fallback.
- `75d1b9c5fa20f8c8e91e922c7bfca22f771830d7`: V14 compiled intent/entity benchmark: 6,000 synthetic queries, Top-1 100% for online SQL and compiled strategies, with roughly 12.6x–14.1x lower mean hot-read latency for compiled fields; compile cost remains explicit.
- `4fd81671412b64e279c446e65167982acd1a73a2`: U15 sufficiency-gap controller. Graph deepening occurs only for explicit unresolved evidence gaps and stops on no novel evidence.

This invalidated the idea of promoting a second standalone cognitive-retrieval architecture. The initial V7 top-level prototype and its test were therefore deleted from the feature branch before PR. The durable contribution is now a small verified ClayGraph ranker that plugs directly into U14 `graph_lookup` and can back U15 deepening.

## Iteration / falsification history

### V4 — negative result, rejected

A synonym-heavy hybrid overfit its development set. On the first fresh paraphrase/OOD set:

- SQLite FTS5/BM25 Hit@1: 71.43%
- V4 Hit@1: 67.86%
- V4 Recall@3: 92.86%

The extra reranking harmed first-result precision. V4 was rejected.

### V5 — small gain, insufficient

On a second fresh 36-query holdout:

- FTS5 + semantic baseline Hit@1: 86.11%, MRR 92.59%
- V5 Hit@1: 88.89%, MRR 93.98%

Positive but too small for a strong architecture claim.

### V7 frozen holdout — graph contribution established

A third fixture was created only after the graph rule was frozen:

- benchmark: `UDB_CLAYGRAPH_COGNITIVE_RETRIEVAL_V7_HOLDOUT3`
- 41 records, 26 graph edges, 40 queries
- 12 queries explicitly require `CONNECTED_TARGET`; 28 are direct semantic retrieval
- raw fixture SHA-256 before gzip/base64: `7ee842fc68ea35c6649bbb55593dfde0eaa5937023be4c5485d60f08a3be9f1c`
- no holdout item was used to tune the earlier V7 scorer afterward

The original graph-off/graph-on ablation was 80.0% -> 97.5% Hit@1. After reading U14/U15, the graph logic was simplified further into a U14-compatible one-hop callback and rerun on the SAME frozen fixture.

## Final fused candidate: `VerifiedClayGraphRanker`

Path:

`research_entity/runtime/verified_claygraph_ranker.py`

It does only one job: rank direct neighbors of an already-resolved entity for a typed relation-target query. It does not own general text search, persistence, truth or effect authority.

Hard gates:

1. requested `graph_epoch` must equal the latest CURRENT graph epoch;
2. `v_graph_projection_ambiguous_edge_epochs` must be empty;
3. a matching `graph_current_projection_receipts` row must bind exact graph epoch + UnifiedDB source epoch with `verified_equal=1`;
4. no head newer than the verified receipt may exist;
5. an injected `admissible_ref(ref, source_epoch)` callback must accept both anchor and target, keeping status/epistemic authority in UnifiedDB;
6. only one hop is traversed;
7. every result carries anchor, relation, direction, edge receipt, source epoch and graph epoch;
8. graph output authority remains `ASSEMBLY_CONTEXT_ONLY`.

The score uses edge weight/confidence plus residual query evidence in the target and relation. Reverse traversal is allowed with a discount. There is no learned model and no graph activation -> truth promotion.

## Frozen-holdout result after U14/U15 fusion

Matched benchmark behavior:

- baseline: conventional SQLite FTS5/BM25-style direct retrieval with the same query text + semantic hints for all 40 queries;
- candidate: same direct path for the 28 direct queries, but the 12 typed relation-target queries use the verified one-hop callback from their supplied resolved anchor.

Result:

| metric | conventional direct baseline | U14-compatible verified graph callback |
|---|---:|---:|
| Hit@1, all 40 | 80.00% | 100.00% |
| MRR, all 40 | 87.2917% | 100.00% |
| Recall@3, all 40 | 95.00% | 100.00% |
| nDCG@5, all 40 | 89.8860% | 100.00% |
| Hit@1, 12 relation-target queries | 33.33% | 100.00% |
| MRR, 12 relation-target queries | 57.6389% | 100.00% |
| Recall@3, 12 relation-target queries | 83.33% | 100.00% |
| nDCG@5, 12 relation-target queries | 66.2866% | 100.00% |

Causal delta on the relation-target subset: +66.67 percentage points Hit@1. Across all 40 held-out queries: +20.0 pp Hit@1. Candidate first-rank failures on this fixture: 0/40.

This is stronger than the earlier V7 result while using less architecture. It supports the hypothesis that, once U14 has an evidence-bound resolved entity, verified one-hop graph context materially improves relational retrieval on this frozen Clay fixture.

It does NOT yet prove automatic entity/anchor resolution quality, real Frank OOD quality, or cross-engine superiority.

## Local timing after final fusion

Runtime metadata: Linux 6.18.35 x86_64 / glibc 2.41, Python 3.13.5, SQLite 3.46.1. 2,000 timed queries per variant after fixture-engine build.

- fixture FTS + graph projection build: 1.682265 ms
- conventional baseline p50: 0.167824 ms; p95: 0.314812 ms; p99: 0.352555 ms; mean: 0.191059 ms
- fused candidate p50: 0.158891 ms; p95: 0.322565 ms; p99: 0.363752 ms; mean: 0.181958 ms

At this tiny synthetic size the latency distributions overlap; no meaningful speed advantage is claimed from this accuracy benchmark. The important result is the retrieval-quality improvement without a material local latency penalty. Performance at realistic scale is covered separately by the concurrent UDB/V3/V14 performance lanes.

## Tests / falsifiers added

`research_entity/harness/reference/test_verified_claygraph_ranker.py` adds eight deterministic tests:

- residual query terms choose the correct neighbor;
- explicit graph path/edge receipt;
- UnifiedDB admissibility callback blocks a conflict target;
- same-epoch graph ambiguity fails closed;
- missing verified projection receipt fails closed;
- stale graph epoch fails closed;
- future head beyond the verified receipt fails closed;
- reverse edges remain possible but are discounted.

The file is self-contained except for the production ranker import, so exact repository CI can validate it directly. Local reconstructed execution passed the same logic; that does not replace CI evidence.

## Reproducible artifacts

- frozen fixture: `research_entity/benchmarks/udb_claygraph_cognitive_retrieval_v7_fixture.json.gz.b64`
- benchmark: `research_entity/benchmarks/benchmark_udb_claygraph_cognitive_retrieval_v7.py`
- production candidate: `research_entity/runtime/verified_claygraph_ranker.py`
- tests: `research_entity/harness/reference/test_verified_claygraph_ranker.py`

The updated benchmark preserves per-query rows and graph-path receipts in machine-readable output.

## Fresh web research and fusion

Post-measurement primary-source research supports the fused architecture rather than a custom physical DB:

- SQLite FTS5 provides conventional full-text retrieval/relevance ordering: https://www.sqlite.org/fts5.html
- SQLite recursive CTEs can traverse trees/graphs: https://www.sqlite.org/lang_with.html
- Microsoft GraphRAG Local Search maps a query to entities, gathers connected relationships and linked text, then prioritizes context within a bounded window: https://microsoft.github.io/graphrag/query/local_search/
- PostgreSQL `pg_trgm` provides trigram similarity with GiST/GIN index support and is a credible next strong conventional baseline: https://www.postgresql.org/docs/17/pgtrgm.html

Fusion consequence:

- KEEP ordinary DB/index primitives for exact/lexical retrieval;
- KEEP U14's adaptive cheapest-valid-route selection;
- KEEP U15's sufficiency-gap-only deepening;
- USE the verified one-hop ranker only for the resolved-entity ClayGraph callback;
- KEEP V3 graph projection verification as a mandatory gate;
- KEEP graph path receipts but never let graph activation become truth/effect authority;
- DO NOT promote the superseded standalone V7 retrieval engine;
- NEXT compare the full adaptive stack against PostgreSQL/pg_trgm and a graph-engine baseline under matched semantics.

## Current research conclusion

SUPPORTED on frozen synthetic Clay workload:

> Conventional direct text retrieval is insufficient for a class of relation-target questions. Reusing U14's resolved entity and adding a V3-verified, UnifiedDB-admissibility-gated one-hop ClayGraph callback raised relation-target Hit@1 from 33.3% to 100% and whole-fixture Hit@1 from 80% to 100% without a material local latency penalty.

NOT SUPPORTED:

> Clay UnifiedDB/ClayGraph is universally more accurate or faster than every conventional database.

The next falsifier is end-to-end automatic entity resolution + real UnifiedDB/ClayGraph held-out data + exact branch CI/Hostinger execution, followed by matched PostgreSQL/pg_trgm and graph-engine baselines.

No paid-training gate is crossed. No Frank self-harness authority is introduced.
