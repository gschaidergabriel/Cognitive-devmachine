# UnifiedDB + ClayGraph V16 accuracy fusion — Hostinger verified

## Provenance

- origin_actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- worker identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- subject: Clay UnifiedDB + ClayGraph retrieval/assembly quality for Frank research/harness work
- feature branch: `chatgpt/udb-claygraph-v16-accuracy-fusion-20260810`
- Clay PR: #108
- exact remote execution receipt: `research_entity/receipts/20260810T0739p0700_UNIFIEDDB_CLAYGRAPH_RANKER_HOSTINGER.json`

## Result in one sentence

On an exact-source Hostinger Ubuntu execution of the frozen 12-case relation-target engineering benchmark, the verified query-aware ClayGraph ranker achieved 12/12 Hit@1 versus 3/12 for SQLite FTS5/BM25 and 4/12 for plain graph-weight ordering; its p50 was 64.22 us versus 104.69 us for FTS5 and 5.13 us for plain graph weight, so the correct architecture is adaptive: use the semantic ranker only when relational insufficiency/ambiguity justifies its cost.

## Why this is not a universal database-superiority claim

The owner target was interpreted as a falsifiable engineering goal, not a marketing claim. Conventional databases can implement full-text search, graph traversal, materialized projections and the same typed ranking formula. Therefore the measured advantage belongs to Clay's semantic query composition — resolved entity + verified topology + query evidence + epoch/provenance/admissibility gates — rather than to a magical physical storage engine.

No claim is made that UnifiedDB/ClayGraph is faster or more accurate than every database, dataset, graph engine or workload. PostgreSQL/pg_trgm and a graph-engine baseline remain required cross-engine falsifiers. Real UnifiedDB/ClayGraph held-out records and automatic entity resolution remain required before an end-to-end Frank retrieval claim.

## Iteration history preserved

### V4 — negative result

A synonym-heavy hybrid looked strong on development data but lost on the first fresh paraphrase/OOD set:

- SQLite FTS5/BM25 Hit@1: 71.43%
- V4 Hit@1: 67.86%
- V4 Recall@3: 92.86%

V4 was rejected rather than promoted.

### V5 — small gain

On a second fresh 36-query holdout:

- stronger FTS5 + semantic baseline Hit@1: 86.11%, MRR 92.59%
- V5 Hit@1: 88.89%, MRR 93.98%

Positive but too small to justify a new retrieval architecture.

### V7 — graph causal contribution

On a frozen 40-query/41-record/26-edge holdout created after the V7 rule was frozen, graph-off Hit@1 was 80.0% and graph-on Hit@1 was 97.5%. This established that typed graph context can add useful information, but a standalone V7 retrieval plane was later superseded by the concurrent U14/U15 architecture.

## Swarm fusion with current UnifiedDB / ClayGraph

Concurrent mainline work changed the best architecture during this run:

- UnifiedDB SQL pushdown and lean indexes already established large hot-read speedups with differential equivalence, while ClayGraph V3 established rebuildable current-head projections, tombstone safety and explicit same-epoch ambiguity blockers.
- U14 Adaptive Semantic Read Plane established cheapest-valid-route semantics: exact/indexed read, compiled semantic field, compositional frontier, resolved-entity graph path, or conventional fallback.
- U15 Sufficiency-Gap Deepening established that graph work should happen only for explicit unresolved evidence gaps and stop when no novel evidence is produced.
- U16 and subsequent maintenance-economics work made rebuild/maintenance cost a first-class decision rather than assuming every prepared structure should always stay hot.

Consequence: the earlier standalone `cognitive_retrieval.py` prototype was deleted from the feature branch. The promoted candidate surface is only a small verified graph callback compatible with U14/U15/U16.

## Candidate implementation

`research_entity/runtime/verified_claygraph_ranker.py`

The ranker is one-hop only and has no truth/effect authority. It requires:

1. requested graph epoch equals latest CURRENT graph epoch;
2. zero rows in the V3 same-epoch ambiguity view;
3. a matching `verified_equal=1` graph projection receipt binding graph epoch to UnifiedDB source epoch;
4. no graph head newer than that verified receipt;
5. an injected UnifiedDB-owned `admissible_ref` check for anchor and targets;
6. explicit path receipt containing anchor, relation, direction, edge identity, source epoch and graph epoch.

Scoring combines graph edge weight/confidence with residual query evidence in the target and relation. Reverse traversal is permitted but discounted. Output authority is `ASSEMBLY_CONTEXT_ONLY`.

## Exact-source remote execution

A direct Clay self-hosted workflow could not obtain the repository-scoped runner, so the exact candidate blobs were copied to a temporary, unmerged Dr.-Unterweger execution bridge and hash-verified before execution. This was an executor transport only; it did not install or mutate Frank runtime/harness.

Remote run:

- GitHub Actions run: 31344999729
- job: 93325176306 `exact-source-vps`
- runner name: `clay`
- machine: `digital-retina`
- Ubuntu/Linux kernel: 6.8.0-117-generic
- architecture: x86_64
- virtualization: KVM full
- CPU: AMD EPYC 9354P, 4 allocated CPUs
- memory: about 15 GiB, no swap
- Python: 3.12.3
- SQLite: 3.45.1

Exact Clay Git blob identities verified before execution:

- ranker: `83a470d3b7449b9e2d140c6a170342d9053b8cee`
- tests: `2858e0d14a1d2027a1ec1cf1058ca6d3a0ff6d80`
- benchmark: `e069d138a179f3a8b4ae2dd4d5304c39666a6966`

All 8 ranker falsifiers passed remotely in the workflow. They cover correct neighbor ranking, path receipt, UnifiedDB admissibility/conflict blocking, same-epoch ambiguity fail-closed, missing receipt fail-closed, stale graph epoch fail-closed, future-head fail-closed, and reverse-edge discount.

## Hostinger benchmark

Benchmark: `U16_VERIFIED_CLAYGRAPH_RELATION_TARGET_V1`

Frozen scope: 12 Clay-shaped one-hop relation-target cases, 9 lexical-decoy cases, 8 cases where plain edge weight favors the wrong neighbor. Resolved anchors are supplied; automatic entity resolution is not credited. Each strategy was timed for 6,000 queries.

| strategy | Hit@1 | MRR | Recall@3 | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|
| SQLite FTS5/BM25 | 25.00% | 62.50% | 100% | 104.6905 us | 145.9330 us | 171.0631 us |
| plain SQL graph weight | 33.33% | 66.67% | 100% | 5.13 us | 9.5205 us | 17.6515 us |
| verified query-aware ClayGraph | 100.00% | 100.00% | 100% | 64.22 us | 96.8206 us | 115.8718 us |

Measured deltas:

- +75.0 percentage points Hit@1 versus FTS5/BM25;
- +66.67 percentage points Hit@1 versus plain graph weight;
- about 1.63x faster p50 than FTS5 on this benchmark;
- about 12.52x slower p50 than plain graph weight.

The candidate therefore dominates the measured FTS baseline in both top-1 quality and p50 latency on this workload. It does not dominate plain graph traversal on latency, so always invoking it would be a regression in the easy-path case.

Artifact evidence:

- artifact id: 9047031479
- artifact name: `clay-udb-graph-ranker-31344999729`
- zip SHA-256: `df388a42ed04bf6dfea5639474e14446547f5384c18d23f4333a68a6ca5d377c`
- artifact size: 6,831 bytes

## Post-measurement web fusion

Fresh primary-source research remains consistent with the architecture rather than suggesting a new storage engine:

- SQLite FTS5 remains a valid conventional full-text/BM25 candidate baseline.
- SQLite recursive CTEs demonstrate that ordinary relational engines can themselves walk graphs.
- Microsoft GraphRAG Local Search uses query-related entities as graph access points, gathers connected entities/relationships/text units and prioritizes/filter context before generation. This independently supports the entity -> graph-context pattern.
- PostgreSQL `pg_trgm` provides trigram similarity with GiST/GIN indexing and is selected as the next stronger conventional text/similarity falsifier.

## Architecture decision after fusion

Status: `SUPPORTED_FEATURE_BRANCH_CANDIDATE`, not universal promotion.

Use the verified query-aware ranker only when all of the following are true:

- U14/U15 has a provenance-bound resolved entity;
- direct/compiled/plain graph evidence is insufficient or ambiguous for the target relation;
- the V3 graph projection is verified for the same source epoch;
- UnifiedDB admissibility accepts the neighbor;
- expected information gain justifies the extra ~59 us p50 versus the measured plain-graph baseline.

Otherwise retain the cheapest sufficient route: exact/indexed read, compiled field, or plain graph/current-head lookup. This places the remote result directly into the existing adaptive read/maintenance-economics architecture instead of creating another subsystem.

## Remaining falsifiers

1. automatic entity/anchor resolution measured independently, including missing/wrong/multiple/adversarial anchors;
2. real UnifiedDB/ClayGraph held-out records instead of synthetic engineering cases;
3. PostgreSQL full-text/`pg_trgm` matched baseline and one suitable graph-engine baseline;
4. scale/churn/rebuild tests at realistic state sizes with CPU/RAM/storage/write amplification;
5. end-to-end U14 -> U15 gap decision -> verified ranker -> provenance-bound assembly differential;
6. current-main integration/identity-guard clean run before main promotion;
7. final Andreas Ubuntu target evidence remains separate and later.

## Conclusion

The run produced a measurable, remotely reproduced improvement for Clay's relation-target retrieval problem: 100% Hit@1 versus 25% FTS5 and 33.3% plain graph-weight on the declared frozen workload, while also beating FTS5 latency. The strongest counterevidence is retained: plain graph traversal is about 12.5x faster, so query-aware semantic ranking must remain selective. The correct fused architecture is therefore not "replace the database" but "UnifiedDB truth + cheap prepared paths + verified ClayGraph semantic deepening only when the evidence gap requires it."
