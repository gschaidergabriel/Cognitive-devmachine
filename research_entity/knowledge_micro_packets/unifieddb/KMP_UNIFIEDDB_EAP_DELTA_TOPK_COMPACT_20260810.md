<!-- RAE_META
{
  "packet_id": "KMP-UNIFIEDDB-EAP-DELTA-TOPK-COMPACT-20260810",
  "title": "EAP evolves from database-style querying toward an incremental bounded possibility preprocessor",
  "domains": ["unifieddb", "claygraph", "retrieval", "performance", "memory", "gwt"],
  "topics": ["incremental_topology", "exact_topk", "active_assembly", "compact_cache", "possibility_preprocessor", "negative_space"],
  "epistemic_class": "MEASURED_CANDIDATE",
  "status_hint": "TESTING",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-10T00:50:00Z",
  "source_refs": [
    "research_entity/harness/reference/unifieddb_emergent_incremental.py",
    "research_entity/harness/reference/benchmark_unifieddb_incremental_updates.py",
    "research_entity/harness/reference/benchmark_unifieddb_incremental_end_to_end.py",
    "research_entity/harness/reference/unifieddb_emergent_exact_topk.py",
    "research_entity/harness/reference/benchmark_unifieddb_exact_topk.py",
    "research_entity/harness/reference/unifieddb_emergent_compact.py",
    "research_entity/harness/reference/benchmark_unifieddb_compact_cache.py",
    "research_entity/knowledge_micro_packets/unifieddb/KMP_UNIFIEDDB_EAP_PREPROCESSOR_20260810.md",
    "https://arxiv.org/abs/2405.14831",
    "https://arxiv.org/abs/2410.05779",
    "https://arxiv.org/abs/2605.13938",
    "https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/"
  ],
  "confidence": 0.80,
  "verification_required": "Reference-harness and self-hosted Ubuntu execution receipts for current exact repository code; repo-native held-out Frank retrieval and process-RSS measurements before architecture promotion.",
  "falsifier_or_next_test": "Reject or revise any candidate if exact selected-Assembly equivalence fails, end-to-end ledger+retrieval latency does not improve, compact cache increases hot latency beyond accepted resource tradeoff, or repo-native held-out tasks show no downstream benefit."
}
RAE_META -->

## Current architecture interpretation

The strongest current interpretation is **not** “replace SQLite/UnifiedDB with a graph database.”

The architecture is converging toward:

`canonical UnifiedDB/StateLedger persistence -> evidence-bound seed resolution -> incrementally maintained derived ClayGraph topology -> bounded possibility compilation -> ActiveAssembly -> GWT/model`

The database remains canonical truth, transaction, replay and provenance. The model-facing retrieval organ is a **preprocessor/compiler of possibilities**. ClayGraph is a derived sparse topology used to compile context, not a second persistent truth store.

## EAP-1.4: transaction-coupled dependency deltas

Problem found in EAP-1.3:

- dependency mutation invalidated the transient topology;
- local synthetic EAP-1.3 cold rebuild plus first query was about 17.38 ms on the 12k-node/11.76k-edge mechanism workload;
- with about 11.62 us hot-read advantage over the matched staged SQL model-input path, that rebuild cost required roughly 1496 reads to amortize.

Candidate EAP-1.4 therefore patches dependency edges only when all of these hold:

- caller owns the just-committed transaction path;
- cached preprocessor epoch exactly equals the pre-commit epoch;
- cached semantic-state hash exactly equals the pre-commit hash;
- the changed dependency row can be reread from canonical StateLedger after commit.

Otherwise it fails back to the normal full rebuild. External/stale writes never claim incremental coherence.

Local algorithm reconstruction on 6000 semantic nodes / 5880 dependency edges / 120 dependency mutations:

- EAP-1.3 full-rebuild update + next query p50: ~8661 us;
- EAP-1.4 incremental patch + next query p50: ~29.6 us after the lazy reverse-map change;
- p50 mechanism speedup: ~292x;
- exact selected-reference equivalence: true for all 120 mutations;
- first dependency write may pay the lazy reverse-map construction cost;
- robust local cold medians were approximately equal (~6.62 vs ~6.69 ms), indicating the reverse map should remain lazy rather than paid on read boot.

Boundary: these are local algorithm-reconstruction measurements, not current-repository self-hosted Ubuntu receipts.

The current repository also contains `benchmark_unifieddb_incremental_end_to_end.py`, which measures real reference `StateLedger` commit + preprocessor maintenance + next Assembly and checks final semantic-state/trace-root equality. It is committed but lacks an executed runner receipt in the present tool lane.

## EAP-1.5: exact Top-K score-bound early stop

EAP activation is monotone under the current constraints:

- edge weight in [0,1];
- hop decay in (0,1];
- therefore a descendant cannot have higher activation score than its frontier ancestor.

This yields a safe exact stopping rule:

If at least K admissible candidates have been visited and the current Kth selected score is **strictly greater** than the best remaining frontier score, no unseen descendant can enter the final Top-K. Equal-score frontier items are not pruned, preserving depth/ref tie ordering.

Local mechanism check across 1800 hot traversals:

- selected Top-12 equality vs full EAP expansion: 100%;
- median frontier expansions: 40 -> 13 (-67.5%);
- median pure traversal time: ~20.28 us -> ~11.86 us;
- speedup: ~1.71x.

This optimization changes how much of the unused/suppressed frontier is enumerated. It is therefore appropriate for model-input Top-K compilation, not for a request that explicitly requires complete negative-space enumeration.

The exact repository implementation and `benchmark_unifieddb_exact_topk.py` are committed and self-hosted gates exist, but no current remote receipt has been materialized in this connector-triggered run.

## EAP-1.6: compact semantic row cache

The EAP transient cache originally retained both:

1. all semantic/materializable state rows; and
2. all raw dependency rows after those dependency rows had already been compiled into adjacency tuples.

The raw dependency-row bodies are redundant for hot retrieval. Each edge already retains:

- target;
- effective weight;
- relation type;
- exact `dependency_ref` provenance.

The canonical StateLedger still retains the complete dependency object.

EAP-1.6 therefore keeps only model-materializable non-dependency rows in `_rows_by_ref` after compilation and discards raw dependency row bodies from the transient Python cache.

Local object-graph reconstruction on 12,000 semantic nodes + 11,760 dependency edges:

- approximate base EAP cache structures: 14.98 MiB;
- compact semantic cache: 8.78 MiB;
- saved: ~6.20 MiB;
- fraction saved: ~41.4%.

This is Python-object-graph memory, not process RSS. The repository benchmark `benchmark_unifieddb_compact_cache.py` measures reachable cache bytes plus cold/hot latency using the actual reference classes when executed.

## Accuracy / epistemic safety remains prior to speed

The earlier `EXP-GO-EAP-NEGATIVE-SPACE-001` remains the exactly-one unusual experiment for this `go` cycle:

- hiding a CONFLICT node only at final output allowed it to relay activation to a decoy and produced precision@2 0.5 in the toy graph;
- blocking propagation through inadmissible CONFLICT evidence produced precision@2 1.0;
- explicit policy admission can re-enable propagation.

U12 -> EAP also independently checks resolution class, confidence, candidate consistency, epoch and current logical-id binding before graph ignition.

## External research fusion

External primary/official work supports the direction, not Clay-specific superiority:

- HippoRAG: graph/PPR-based long-term memory retrieval for multi-hop association;
- LightRAG: graph + vector retrieval with incremental update emphasis;
- LazyGraphRAG: best-first/breadth-first iterative deepening under a relevance budget instead of mandatory expensive full preprocessing;
- 2026 query-aware spreading-activation work: query-conditioned activation gates can improve graph-retrieval quality and latency relative to query-blind spreading activation.

Next Clay candidate after the exact speed/resource gates: typed calibrated query-affinity evidence may modulate propagation, but it must remain a separate falsifiable layer because mixing it directly into EAP would conflate ranking-accuracy changes with pure execution optimizations.

## Runner/trigger negative result

Multiple push/issue-dispatch attempts and a same-repository PR probe were created. In the current GitHub connector lane:

- no workflow-run object was produced for connector-generated PR `opened` or `synchronize` events;
- no persisted dispatch, EAP, incremental or exact-TopK runner receipt appeared;
- therefore runner execution is **UNKNOWN/BLOCKED_TRIGGER_LANE**, not PASS or FAIL.

A persistent read-only `.github/workflows/unifieddb-eap-pr-probe.yml` now exists on `main`. A future human/external PR touching the guarded paths can produce directly inspectable self-hosted job/log/artifact evidence.

## Promotion gate

Do not promote EAP-1.4/1.5/1.6 to canonical runtime solely from these local measurements.

Promotion requires at minimum:

1. current repository regression pass;
2. self-hosted Ubuntu evidence tied to exact SHA;
3. end-to-end StateLedger commit + next-Assembly improvement or justified Pareto tradeoff;
4. exact selection/state/trace equivalence where the candidate claims semantics-preserving optimization;
5. held-out natural-language seed accuracy and abstention safety;
6. repo-native Frank retrieval episodes;
7. cache/process-RSS and rebuild/recovery measurements;
8. no regression of provenance, epoch safety, negative-space gating or effect-authority boundaries.
