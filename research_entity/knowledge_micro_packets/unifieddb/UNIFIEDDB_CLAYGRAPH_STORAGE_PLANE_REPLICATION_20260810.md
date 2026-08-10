<!-- RAE_META
{"packet_id":"UNIFIEDDB_CLAYGRAPH_STORAGE_PLANE_REPLICATION_20260810","title":"Independent UnifiedDB SQL-pushdown and ClayGraph head-projection replication","domains":["unifieddb","claygraph","harness","performance","recovery"],"topics":["query pushdown","bounded retrieval","partial indexes","write amplification","latest-head projection","tombstones","graph activation","proof eligibility"],"epistemic_class":"LOCAL_SYNTHETIC_INDEPENDENT_REPLICATION_PLUS_PRIMARY_WEB_FUSION","claim_status_hint":"CANDIDATE","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T07:10:37+07:00","source_refs":["git:8d5beaa28969c553735edfe91a09ec3e56f0c0fe","git:5c567ab896f050c043672e43851c9f1bf99e5dcc","git:512b26e2642d687eecc50a41938d79c224e4cbce","git:a9165bb6fac2e30c61c48afb39d62bc2ecb40988","https://sqlite.org/pragma.html#pragma_optimize","https://sqlite.org/queryplanner.html","https://sqlite.org/queryplanner-ng.html","https://sqlite.org/optoverview.html","https://arxiv.org/abs/2509.25530","https://arxiv.org/abs/2603.14828"],"evidence_refs":["research_entity/benchmarks/unifieddb_claygraph/20260810T0710p0700_chatgpt_storage_plane_replication.json"],"confidence":"HIGH_FOR_SYNTHETIC_STORAGE_PLANE_BEHAVIOR_ONLY","verification_required":true,"falsifier_or_next_test":"Representative Frank UnifiedDB/ClayGraph snapshots or Ubuntu target-host runs fail semantic equivalence, remove the measured latency advantage, expose unacceptable write/rebuild/recovery cost, or show that graph expansion harms held-out counterevidence recall/answer quality."}
RAE_META -->

### Atomic findings

1. **H1 bounded SQL pushdown is strongly supported as a physical read-path repair.** On a 100,000-row synthetic StateLedger-compatible table, four matched query classes produced identical selected rows between the legacy full materialize/decode/filter path and SQL predicate pushdown. Legacy p50 ranged from 480.49 to 648.64 ms for the non-point cases; bounded SQL p50 ranged from 0.31 to 0.34 ms. The point lookup was 502.20 ms versus 0.0185 ms. This is evidence against retaining an O(N) decode scan for bounded reads, not evidence that Clay is universally faster than conventional databases.

2. **The newly added lean CURRENT indexes are complementary and workload-conditioned.** In a separate 200,000-row ablation, the key-first partial index reduced a key-only CURRENT/KNOWN lookup from 15.4475 ms p50 to 0.015659 ms, while the order-first partial index reduced a large global CURRENT/KNOWN read from 10.9737 ms to 4.5085 ms and slightly improved domain reads. Keeping both increased logical pages from 17,186,816 to 25,714,688 bytes in this fixture. Write overhead varied by run; one 20k append comparison was 1.145x and a separate larger run measured roughly 1.4x. Therefore real query-frequency and write-amplification measurements are required before treating both indexes as a default.

3. **A heavier status+epistemic covering index was NOT_SELECTED.** On 300,000 rows it improved a 4096-row global CURRENT/KNOWN read from 24.14 to 15.47 ms p50 (~1.56x) but increased logical storage about 1.58x and made 20k append batches about 3.19x slower in that run. The read gain did not dominate its measured cost.

4. **ClayGraph V3 latest-head projection received an independent positive replication.** With 80,000 logical edges and three versions each (240,000 physical rows), the fast head view exactly matched the legacy latest-version set (64,000 CURRENT heads). Source, source+relation and global-relation hot reads improved from 69.22/76.33/99.36 ms p50 to 0.120/0.123/0.119 ms respectively (~576x/~621x/~836x). A deliberately late older CURRENT version could not resurrect a logical edge whose newer head was RETRACTED.

### Web fusion

SQLite's current official guidance favors supplying appropriate indexes, preserving planner statistics with `PRAGMA optimize`, and measuring query plans rather than hard-coding a single universal index strategy. Query Planner Stability can improve predictability but may disable bound-value-dependent optimizations, so it is a benchmark candidate rather than a free safety switch.

Recent GraphRAG evidence strengthens Clay's safety direction rather than a naive "more graph = better" rule. Iterative graph retrieval can improve difficult multi-hop cases but can also inject noise and reduce precision. Constraint-checked retrieval with an explicit sufficiency gate is reported as more robust under imperfect graph structure. This supports keeping ClayGraph activation/accessibility separate from proof eligibility, truth and effect authority.

### Architecture delta

**SUPPORTED CANDIDATES**
- bounded SQL predicate pushdown for H1 typed reads;
- ClayGraph V3 rebuildable latest-head tables for hot latest-version reads;
- lean key-first and order-first CURRENT indexes as separately lesionable, workload-conditioned candidates;
- graph activation/proof separation and fail-closed epoch matching.

**NOT_SELECTED**
- heavy `status,epistemic,domain,key,...` covering index as a default;
- unbounded graph expansion as an accuracy mechanism;
- any claim of "better than every normal database" from synthetic component tests.

### Next falsifiers

- run exact read/write/rebuild benchmarks over representative real UnifiedDB/ClayGraph snapshots;
- execute on the verified Ubuntu lane with CPU/RSS/page/WAL/checkpoint/busy/recovery metadata;
- measure Recall@k, MRR/nDCG, counterevidence recall, stale-accept rate, null-query abstention and downstream answer/task outcome at matched context budgets;
- lesion the two lean state indexes independently against observed Frank query distributions;
- crash/restart/rebuild the ClayGraph head projection and verify equality with legacy latest views after recovery and out-of-order ingestion;
- run `PRAGMA optimize` / planner-statistics experiments after schema change and record whether plans or tails materially improve.
