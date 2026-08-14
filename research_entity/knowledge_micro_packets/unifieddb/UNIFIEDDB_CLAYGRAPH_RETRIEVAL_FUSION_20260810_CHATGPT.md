<!-- RAE_META
{"packet_id":"UNIFIEDDB_CLAYGRAPH_RETRIEVAL_FUSION_20260810_CHATGPT","title":"UnifiedDB + ClayGraph measured retrieval fusion","domains":["unifieddb","claygraph","frank","retrieval","recovery"],"topics":["authoritative state","derived projections","SQL pushdown","latest heads","semantic sufficiency","typed gap deepening","Unicode normalization","Database Pulse"],"epistemic_class":"MULTI_SOURCE_MEASURED_FUSION","claim_status_hint":"CANDIDATE","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T07:33:00+07:00","confidence":"HIGH_FOR_COMPONENT_RESULTS_MEDIUM_LOW_FOR_GENERALIZATION","verification_required":true}
RAE_META -->

## Decision

The best current direction is **not** to replace a conventional storage engine with a monolithic bespoke database. Keep UnifiedDB as the canonical semantic/logical authority over conventional transactional storage, and win the Frank workload by compiling its repeated semantic access patterns into bounded, epoch-bound, rebuildable projections and typed retrieval plans.

Target hot path:

`UnifiedDB authoritative state -> coherent generation/cycle pin -> exact/compiled semantic access -> sufficiency check -> typed evidence-gap signature -> only-if-needed ClayGraph deepening -> provenance/proof gate -> bounded context`

ClayGraph/Active Field remains derived acceleration and topology. Activation/accessibility is never proof, truth, causal credit or external effect authority.

## Measured support

### Storage plane

Independent synthetic replication on 100k StateLedger-compatible rows preserved exact compared outputs while SQL predicate pushdown removed the legacy full materialize+JSON-decode scan. Depending on query class, p50 moved from about 480-649 ms to about 0.31-0.34 ms; point lookup moved from about 502 ms to 0.0185 ms. This supports bounded pushdown, not universal database superiority.

ClayGraph V3 latest-head projection independently reproduced the legacy latest-version set over 80k logical edges / 240k physical versions, preserved a retraction against a deliberately late older insert, and reduced three tested hot reads from ~69-99 ms p50 to ~0.119-0.123 ms (~576x-836x).

A heavy broad covering State index was rejected: only ~1.56x large-read gain in the tested 300k fixture while increasing logical storage ~1.58x and the measured append batch ~3.19x. Two lean partial CURRENT indexes are complementary and should remain separately lesionable/workload-conditioned.

### Semantic retrieval / accuracy

The strongest current real-snapshot comparison is the committed Clay semantic retrieval benchmark using current claims plus real bootstrap distractor chunks. Against the stronger SQLite FTS5 claim-only baseline, the compiled semantic sufficiency-stop arm held recall 1.0 while improving precision ~0.498 -> 1.0, MRR ~0.848 -> 1.0, nDCG ~0.887 -> 1.0 and median latency ~0.0721 -> ~0.0109 ms (~6.63x) on its 11 query families. This is a real Clay-workload Pareto win, but it is still a small curated task family and is not a universal database claim.

V15.1 adds a useful invariance mechanism after upstream semantic resolution: 15,000 synthetic paraphrase queries produced 0 raw-surface plan-cache hit rate versus 0.95 for an epoch-bound typed gap signature, with 1.0 family invariance. This is plan reuse/mechanism evidence; upstream entity/intent/evidence-requirement resolution remains the harder OOD accuracy problem.

### Accuracy defects found during this cycle

V13's ASCII-only normalized-key path could collapse distinct non-ASCII inputs and erase non-Latin keys. A separate candidate branch replaces it with explicit versioned NFKC + casefold Unicode tokenization, rejects unbounded SQLite `LIMIT` values outside 1..4096, and abstains on empty/punctuation-only normalized queries. Promotion remains pending CI/Ubuntu and real German/Frank corpus evaluation.

Database Pulse v0's current last-known-good recovery path has a separate unresolved source-audit blocker: it selects only the newest checkpoint rather than scanning backward for the newest valid checkpoint, and an older rollback does not yet prove atomic rewind/replay of post-checkpoint acknowledgements/receipts/checkpoints/invalidation bookkeeping. Carry this falsifier into whichever Pulse generation becomes release-relevant.

## Web/research fusion

Current SQLite guidance supports measured persistent indexes, planner statistics/`PRAGMA optimize`, and bounded query planning rather than indiscriminate index proliferation. Current graph-retrieval research supports adaptive/iterative traversal only when evidence gaps justify expansion; naive expansion can add noise, so Clay's sufficiency gate and activation-vs-proof separation are architecture requirements, not optional decoration.

## Promotion rule: "better for Frank", not "better at everything"

A UnifiedDB/ClayGraph candidate may be called better for Frank only on a declared workload vector when it simultaneously meets:

1. higher or non-inferior held-out task/retrieval correctness (Recall@k, precision, MRR/nDCG, counterevidence recall, calibration/abstention, downstream task outcome);
2. lower or Pareto-competitive p50/p95/p99 latency at matched context/result budgets;
3. bounded CPU/RSS/storage/WAL/write amplification;
4. epoch/provenance correctness and stale-fastpath fail-closed behavior;
5. deterministic replay plus crash/rebuild/last-known-good recovery;
6. no graph-derived proof/authority escalation;
7. real German/multilingual Frank data and OOD paraphrase/entity-resolution coverage;
8. Ubuntu/Hostinger replication followed by Andreas target-host acceptance.

Comparison set should include at least plain indexed SQLite, SQLite FTS5, the current legacy UnifiedDB path, and task-appropriate conventional vector/graph retrieval baselines where they are actually relevant. A single scalar "database accuracy" is invalid.

## Next discriminating experiments

- Run the V13 Unicode branch over a real Frank/Clay German query corpus with relevance labels and an explicit old-normalizer ablation.
- Measure V14/V15 end-to-end entity resolution -> typed gap -> graph deepening on held-out natural-language paraphrases, including null queries and counterevidence-seeking queries.
- Persist the Pulse v2 matched benchmark result and include pre-ranking truncation accuracy, cold/warm latency, replay roots and resource shadows.
- Execute ClayGraph head rebuild after crash/restart and compare full set/hash to the canonical legacy latest-version derivation.
- Replay the LKG recovery falsifier against the release-relevant Database Pulse generation.
- Collect real query-frequency telemetry before deciding whether both lean CURRENT indexes should ship by default.

## Falsification boundary

If a conventional baseline matches the same semantic/provenance guarantees at lower total cost, keep the conventional mechanism. `KEEP_ISOLATED`, `NO BENEFIT`, and `NOT_SELECTED` remain valid. Clay wins by workload-specific semantic compilation and measured closed-loop usefulness, not by renaming conventional indexing as intelligence.
