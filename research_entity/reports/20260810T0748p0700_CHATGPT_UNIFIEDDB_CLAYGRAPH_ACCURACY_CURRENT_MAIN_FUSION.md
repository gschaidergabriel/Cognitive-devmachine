# UnifiedDB + ClayGraph accuracy — current-main fusion after Hostinger verification

## Provenance

- origin_actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- worker identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- clean branch parent: main `48aa2dfe32771048f53d030049cf151a3a99457d`
- remote receipt: `research_entity/receipts/20260810T0739p0700_UNIFIEDDB_CLAYGRAPH_RANKER_HOSTINGER.json`
- target: improve Clay UnifiedDB + derived ClayGraph cognitive context selection by measurement, falsification and current-main fusion without creating a second semantic database architecture.

## Research result

The run did not validate a universal claim that Clay is better than every database. It did validate a narrower and useful claim on an exact-source Ubuntu execution: for the frozen Clay-shaped one-hop relation-target workload, a verified query-aware ClayGraph ranker is materially more accurate than conventional FTS5/BM25 and than query-blind graph-weight ordering, while also beating FTS5 p50 latency.

Exact Hostinger result, 12 frozen cases and 6,000 timed queries per strategy:

| strategy | Hit@1 | MRR | Recall@3 | p50 | p95 |
|---|---:|---:|---:|---:|---:|
| SQLite FTS5/BM25 | 25.00% | 62.50% | 100% | 104.6905 us | 145.9330 us |
| plain SQL graph weight | 33.33% | 66.67% | 100% | 5.13 us | 9.5205 us |
| verified query-aware ClayGraph | 100.00% | 100.00% | 100% | 64.22 us | 96.8206 us |

Deltas:

- +75.0 percentage points Hit@1 versus FTS5/BM25;
- +66.67 percentage points Hit@1 versus plain graph weight;
- about 1.63x faster p50 than FTS5;
- about 12.52x slower p50 than query-blind plain graph weight.

All eight fail-closed/ranking tests passed on the Hostinger self-hosted Ubuntu runner. The tested production, test and benchmark Git blobs were verified byte-identical before execution.

## Negative results and iterations retained

V4 synonym-heavy reranking overfit: on the first fresh paraphrase/OOD set, FTS5/BM25 Hit@1 was 71.43% while V4 fell to 67.86%. V4 was rejected.

V5 on a second fresh 36-query holdout gave only a small gain: stronger FTS5+semantic baseline 86.11% Hit@1 / 92.59% MRR versus V5 88.89% / 93.98%. This was insufficient for architecture promotion.

V7 then used a frozen 40-query graph ablation and raised Hit@1 from 80.0% without graph to 97.5% with typed graph context, establishing a graph contribution. During the run, concurrent U14/U15/U16 work made the standalone V7 retrieval plane architecturally obsolete, so that prototype was deleted rather than creating a competing retrieval architecture.

## Current-main fusion

The clean branch is rebased by construction from main `48aa2dfe...`, after the Database Pulse V1-V5 line landed. This matters because the mainline now explicitly optimizes prepared read/rank lifecycle economics and uses hosted falsifiers. The new graph ranker is therefore not a replacement for Pulse or the adaptive semantic read plane.

Final composition:

1. UnifiedDB remains canonical semantic/logical truth, provenance, transaction, epoch and replay authority.
2. Prepared exact/index/compiled/Pulse paths remain the cheapest default when sufficient.
3. ClayGraph remains derived/rebuildable and never becomes truth/effect authority.
4. U14/U15 resolves an entity and exposes a relational evidence gap/ambiguity before expensive graph semantic ranking is justified.
5. `VerifiedClayGraphRanker` performs one-hop query-aware ranking only then.
6. The ranker requires a V3 verified projection receipt for the exact UnifiedDB source epoch, zero same-epoch ambiguity, no future head beyond the receipt and an external UnifiedDB-owned admissibility callback.
7. Every selected graph result carries an explicit path/edge receipt and `ASSEMBLY_CONTEXT_ONLY` authority.

This is a Pareto composition rather than one universally dominant primitive: plain graph weight is much faster; the query-aware ranker is much more accurate on ambiguous relation-target cases; FTS5 is both slower and less accurate on this declared workload. The adaptive controller should choose the cheapest path that already meets the evidence need.

## Web fusion

Fresh primary-source research supports this composition rather than a custom physical store:

- SQLite FTS5 is an appropriate conventional full-text/BM25 baseline.
- SQLite recursive CTEs show that ordinary relational databases can themselves traverse graphs, so graph traversal alone is not a Clay-specific advantage.
- Microsoft GraphRAG Local Search uses query-related entities as graph access points, then collects/prioritizes connected relationships and text context, independently supporting the entity -> graph-context pattern.
- PostgreSQL `pg_trgm` provides trigram similarity with GiST/GIN indexing and is selected as the next stronger conventional text/similarity baseline.

## Current status and next falsifiers

Status of this delta: `SUPPORTED_FEATURE_BRANCH_CANDIDATE`.

The clean current-main branch contains only five scientific artifacts: production ranker, eight-test falsifier suite, frozen benchmark, exact Hostinger receipt and this report. No obsolete direct-runner workflow is carried forward.

Before main promotion the next checks are:

- inspect clean-branch PR merge/check state against moving main;
- automatic entity/anchor resolution, including wrong/missing/multiple/adversarial anchors;
- real held-out UnifiedDB/ClayGraph data instead of synthetic cases;
- PostgreSQL full-text/`pg_trgm` and a suitable graph-engine matched baseline;
- end-to-end U14/U15/Pulse -> gap decision -> verified graph ranker -> provenance-bound assembly differential;
- realistic scale/churn/rebuild CPU/RAM/storage/write-amplification measurements;
- final Andreas Ubuntu target acceptance remains separate and later.

## Conclusion

A measurable improvement has been built, falsified, iterated, web-checked, fused with concurrent UnifiedDB/Pulse work and reproduced on Hostinger. Within the declared relation-target benchmark, the clean candidate reaches 100% Hit@1 and beats SQLite FTS5 in both Hit@1 and p50 latency. It does not beat plain graph traversal in latency, so the correct architecture is selective semantic graph deepening rather than replacing ordinary database primitives.
