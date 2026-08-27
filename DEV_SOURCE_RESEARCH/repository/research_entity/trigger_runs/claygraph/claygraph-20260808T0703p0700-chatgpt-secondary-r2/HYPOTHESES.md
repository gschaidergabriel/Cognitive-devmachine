# ClayGraph Cycle 2 — G1b Hypotheses

All hypotheses are OPEN unless stated otherwise. Proxy results remain synthetic/designed evidence.

| ID | Hypothesis | Counterhypothesis | Highest-information falsifier/test |
|---|---|---|---|
| H-CG2-01 | Query-class routing (exact / semantic / multihop / audit) can outperform one fixed traversal policy at matched context budget. | A strong single hybrid retriever is simpler and equally good. | Replay >=50 independently grounded current-RAE queries; compare per-class quality/cost. |
| H-CG2-02 | Exact/current questions should default to zero graph hops and authoritative anchors. | Graph routing adds useful context without accuracy loss. | Inject stale but semantically close graph facts against current exact truth. |
| H-CG2-03 | One hop should remain the default associative expansion; two+ hops should require explicit multihop evidence need. | Fixed 2-hop is more complete without unacceptable noise. | Sweep hop policy on actual corpus with recall/precision/false-association curves. |
| H-CG2-04 | Independent lexical/semantic support for an expanded target reduces damage from erroneous graph edges. | The relevance gate suppresses bridge nodes needed for genuine multihop recovery. | Edge-corruption stress plus bridge-node gold cases. |
| H-CG2-05 | Evidence-family-aware reranking improves independent-evidence coverage. | Family controls mostly reduce useful complementary descendants. | Compare soft penalty vs hard cap vs none; measure unique-family recall and answer quality. |
| H-CG2-06 | Hard one-per-family deletion is too aggressive for RAE because one evidence family can contain distinct claim/negative/experiment roles. | Strict dedup is sufficient. | Re-run packet queries with role-aware family compression. |
| H-CG2-07 | The deterministic active packet envelope is best retained as a safety/fallback layer until ClayGraph wins on actual-corpus retrieval. | Graph selection is already good enough to replace deterministic ranking. | Execute repository preflight and graph selector over same packet candidate pool. |
| H-CG2-08 | A query plan/certificate improves replayability and debugging of active assemblies. | The extra metadata costs more context/latency than it saves. | Log plan/stop/paths and test root-cause time + token overhead. |
| H-CG2-09 | Projection-aware retrieval (graph navigates, exact/raw source grounds) reduces unsupported graph-induced answers. | Exact fallback rarely changes answers and only adds latency. | Graph-only vs graph+anchor factorial on stale/conflict queries. |
| H-CG2-10 | Temporal/status filtering should be query-intent dependent: current queries suppress stale/refuted; audit/history queries actively retrieve them. | One uniform status prior is sufficient. | Mixed current/history/contradiction benchmark. |
| H-CG2-11 | Salience/retention policy must be separate from truth status; low-salience facts can remain true and auditable. | Salience can safely drive deletion. | Long-horizon recall/forgetting test with rare-but-critical facts. |
| H-CG2-12 | Adaptive expansion budget should stop on marginal evidence gain rather than fixed K/hops. | Fixed tuned K is adequate. | Plot quality/cost across K/hops and marginal-gain stopping. |
| H-CG2-13 | FRANK `M.MEMORY_FABRIC` can consume ClayGraph assemblies without altering `S.COGNITIVE_FRAME` or capability authority. | Integration creates hidden causal or freshness coupling. | Stale-assembly/frame lesion plus effect-gateway trace. |
| H-CG2-14 | Physical database migration dispositions remain independent of retrieval improvements. | Better graph retrieval justifies physical consolidation. | Store-by-store parity/replay/p99/crash tests; no retrieval metric alone permits MERGE. |
| H-CG2-15 | Query-planned ClayGraph can eventually reduce the active packet envelope size without losing negative/contradiction coverage. | Larger deterministic envelopes remain more robust. | Matched-answer-quality curve versus active token budget. |
| H-CG2-16 | Graph extraction/ontology errors should be treated as first-class uncertainty, not silently trusted edges. | Extracted typed edges are reliable enough to treat uniformly. | Inject/measure real extraction disagreement and calibrated edge confidence. |
