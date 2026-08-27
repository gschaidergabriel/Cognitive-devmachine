<!-- RAE_META
{"packet_id":"UNIFIEDDB_CLAYGRAPH_COHERENT_ACCESS_V11_20260810","title":"UnifiedDB U11 + ClayGraph V4 coherent verified semantic access","domains":["unifieddb","claygraph","harness"],"topics":["semantic access generations","materialized graph paths","single-query fastpath","counterevidence","atomic publication","FTS5 baseline","graph planning verification execution"],"epistemic_class":"LOCAL_COMPONENT_BENCHMARK_PLUS_EXTERNAL_PRIMARY_RESEARCH_SYNTHESIS","claim_status_hint":"CANDIDATE","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T07:30:00+07:00","source_refs":["research_entity/runtime/RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql","research_entity/runtime/RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql","research_entity/runtime/RAE_CLAYGRAPH_V3_SEMANTIC_ACCESS_PATHS.sql","research_entity/runtime/RAE_CLAYGRAPH_V4_VERIFIED_ACCESS_PLANS.sql","research_entity/runtime/semantic_retrieval_runtime_v11.py","research_entity/runtime/semantic_access_generation_builder_v11.py","arXiv:2507.08945","arXiv:2412.18431","arXiv:2405.14831","arXiv:2401.18059","https://sqlite.org/fts5.html"],"evidence_refs":["git:c4ead2e741641fc7593ced77f186187efb58e86a","git:404be9428668debacb93c14e8710a5fd985fbf66","git:69febf0808aec8197e69edc49ae2b01c32f49682","git:faee6afae2a08b2077e6da1ad46dbac36eb222ae","git:da521fd2a42e74c03e89d181909ac3f152abe004","git:7c9f2b45dbd1f4cd33b69427740b3e7e0892b9b4","local:semantic_access_v11_tests_5_of_5_pass","local:semantic_retrieval_v11_112_queries_11200_ops"],"confidence":"HIGH_FOR_SYNTHETIC_TYPED_SEMANTIC_ACCESS_ONLY","verification_required":true,"falsifier_or_next_test":"Run repository-native 12-case natural-language/counterevidence suite and U11 differential benchmark on the self-hosted Ubuntu runner; then run on real UnifiedDB/ClayGraph snapshots with dense/hybrid baseline, paraphrases, null queries, stale/corrupt graph variants, counterevidence recall and downstream task outcomes."}
RAE_META -->

### Problem found during iteration
U10 made each seed rebuild transactional, but rebuilding many seeds under one unchanged semantic/graph epoch could still expose a mixed derivation generation to concurrent readers. This is a correctness/replay risk even when every individual seed row is valid.

### Architecture delta
U11 adds coherent semantic-access generations. A complete generation is built under `STAGING`, verified, then published by one transaction that supersedes the previous CURRENT generation and swaps a single `semantic_access_head`. Empty, stale or unverified generations cannot replace last-known-good. The U11 reader resolves current head + generation + semantic seed + access projection in one indexed SQL statement. ClayGraph V4 adds explicit access-plan staging and verification receipts so plan generation, topology verification and publication remain distinct phases; counterevidence path coverage is measured explicitly.

### Local measured result
Deterministic synthetic Clay semantic-access workload: 4,320 records, 4,000 distractors, 16 project-relevant semantic topics, 112 queries. Strong conventional baseline is SQLite FTS5/BM25 candidate generation plus CURRENT filtering and authority metadata ordering. Final coherent U11 was measured over 11,200 timed operations after warm-up.

- SQLite FTS5 + CURRENT + authority: Hit@1 0.892857, Recall@5 0.9375, MRR 0.911458; p50 ~89.98 us, p95 ~6.95 ms in the rerun.
- U10 materialized semantic access: Hit@1/Recall@5/MRR 1.0/1.0/1.0; p50 ~13.09 us in a 11,200-op differential run.
- A naked one-statement materialized JOIN reached p50 ~5.27 us / p95 ~6.00 us, proving the multi-roundtrip overhead was avoidable, but lacked generation-level coherence.
- U11 coherent generation + one-statement read preserved 1.0/1.0/1.0 and measured p50 ~8.17 us, p95 ~9.07 us, p99 ~11.27 us over 11,200 operations.
- Five explicit U11 recovery/coherence tests passed locally: exact coherent fastpath, stale epoch fail-closed, empty rebuild preserves last-known-good, unverified generation cannot publish, atomic generation swap.

Storage/build shadow from U10 materialization on the same fixture: +77,824 bytes over a 2,568,192-byte baseline (~3.0%); projection build about 1.7-2.0 ms across observed reruns. These values are environment-specific.

### Interpretation boundary
This is measurable dominance on the tested Clay semantic-access workload, not evidence that UnifiedDB is universally better than every conventional database. The workload benefits from project-native typed/normalized semantic seeds, so the 100% result cannot be generalized to unseen natural-language queries. The repository-native 12-case natural-language/counterevidence benchmark remains the next stronger test. VPS/Hostinger execution is instrumented by `.github/workflows/semantic-access-hostinger-benchmark.yml`, but no remote execution receipt was observable through the current connector at packet creation time.

### External research fusion
SQLite FTS5 remains the correct strong lexical substrate: it supplies BM25, prefix indexes and configurable tokenization/index tradeoffs. The Clay delta therefore does not replace SQLite; it compiles stable semantic/graph knowledge into small verified access structures above SQLite. GraphRunner supports separating graph traversal planning, verification and execution rather than interleaving unconstrained reasoning with each hop. GeAR supports graph expansion on top of base retrievers for multi-hop retrieval. HippoRAG and RAPTOR independently support precompiled graph/hierarchical retrieval structures for associative or multi-step retrieval. These papers support the direction but do not validate Clay implementation claims.

### Strongest counterhypotheses
1. U11 wins because the fixture aliases are too aligned with semantic seeds; gains may collapse on paraphrases and unseen intents.
2. A dense or late-interaction retriever may match target retrieval quality without seed maintenance or graph projection complexity.
3. Materialized access can omit rare decisive counterevidence even when common paths are perfect; counterevidence recall must be a first-class metric.
4. Rebuild/storage/write amplification may dominate read savings at high update rates.
5. The self-hosted Ubuntu runner may show different cache, filesystem and SQLite behavior than the local environment.

### Promotion decision
CANDIDATE, not CURRENT. Do not change `RAE_LATEST_COGNITIVE_STACK.clay` yet. Promotion requires repository-native natural-language/counterevidence differential evidence, coherent-generation recovery evidence, and an Ubuntu execution receipt. If those pass, prefer the fused path: SQLite authoritative physical substrate + UnifiedDB semantic authority + bounded possibility preprocessing + ClayGraph verified access plans + U11 coherent materialized hot path + lexical/graph RRF fallback.
