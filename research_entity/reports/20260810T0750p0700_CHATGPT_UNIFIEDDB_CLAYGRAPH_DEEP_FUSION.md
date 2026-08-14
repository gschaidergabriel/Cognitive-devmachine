# UnifiedDB + ClayGraph deep fusion — 2026-08-10 07:50 +07:00

## Provenance

- origin_actor: `chatgpt-secondary`
- provider: `OpenAI`
- model: `GPT-5.6 Sol`
- identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`
- research subject boundary: Clay researches/builds/tests Frank; this worker is not Frank.
- owner direction: intensively build/use/measure/iterate UnifiedDB + ClayGraph and seek a measurable advantage for Clay's workload, with recursive web research and fusion.
- starting canonical anchor: RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.
- final canonical/status must be re-resolved independently because main advanced during this run.

## Executive scientific result

The strong literal claim `better/more accurate than every normal database` is NOT supported and must not be promoted.

What IS now supported is narrower and more useful:

1. UnifiedDB bounded semantic reads are orders of magnitude faster than the previous H1 full-materialize Python path while preserving observed query semantics.
2. ClayGraph current-head projections are orders of magnitude faster than the previous version-history `MAX(graph_epoch)` hot path on the tested fixtures while retaining explicit ambiguity/tombstone/rebuild safety.
3. Clay's typed epistemic + epoch + projection + integrity assembly contract materially reduces unsafe context admission relative to a deliberately simple row-store baseline.
4. Raw indexed SQLite remains faster than Clay receipt-bearing single-key reads; Clay's value is therefore semantic/context safety and bounded cognitive assembly, not a magical faster physical storage engine.
5. Streaming the existing canonical semantic-state serialization is byte-equivalent and materially reduces latency/memory without changing root semantics.
6. A rebuildable authenticated state shadow can make integrity-update auditing hundreds of times cheaper than full canonical-root recomputation on the tested state size, but V1 has substantial storage amplification.
7. Embedded Auth Shadow V2 is a candidate to reduce that storage amplification; it exposed and caused repair of a real StateLedger schema-evolution bug before promotion.
8. Parallel U14/U15/Pulse/SPM/compact-EAP work converges with this result: the target should be a cost-aware semantic/possibility preprocessor with incremental projections over ordinary storage, not one monolithic replacement DB engine.

## Implemented UnifiedDB hot path

Commits:

- `8d5beaa28969c553735edfe91a09ec3e56f0c0fe` — SQL predicate/LIMIT pushdown in `UnifiedDBQueryPlane`.
- `5c567ab896f050c043672e43851c9f1bf99e5dcc` — lean `CURRENT` partial indexes.
- `2766a1d0eb8a8f22c93bca7c23ad2a352bdde0c5` — differential fast-path tests.
- `c3392e950e1f4d8874ba5d59760098a221fbeb4e` — reproducible hotpath benchmark.

Local 20k-state paired evidence:

- old full materialize/filter p50: `78,459.817 us`
- SQL-pushdown p50: `276.597 us`
- p50 speedup: `283.66x`
- old p95: `110,358.666 us`
- SQL-pushdown p95: `2,309.275 us`
- p95 speedup: `47.79x`
- additional 100 differential query specs: `0` mismatches.

After singleton-`=` plus lean partial indexes:

- mixed p50: `140.687 us`
- p95: `279.038 us`
- p99: `472.112 us`
- key-only p50: `51.786 us`
- key-only p95: `85.548 us`
- planner used `idx_state_key_current` in the measured key path.

Local write/storage shadow:

- base state UPSERT p50: `5.3915 us`
- indexed p50: `8.5745 us`
- median write ratio: `1.590x`
- page ratio: `1.406x`.

Verified Hostinger equivalent-mechanism receipt (`Dr.-Unterweger` repo, run `31343756571`, host `digital-retina`, Linux 6.8, Python 3.12.3, SQLite 3.45.1):

- old bounded-read p50: `74,745.3695 us`
- candidate p50: `249.9665 us`
- p50 speedup: `299.02x`
- old p95: `87,516.369 us`
- candidate p95: `375.150 us`
- p95 speedup: `233.28x`
- differential mismatches: `0`
- indexed write p50 shadow: about `1.953x` base
- page ratio: about `1.408x`.

## ClayGraph V3 current-head projection

Commits:

- `512b26e2642d687eecc50a41938d79c224e4cbce` — current-head candidate.
- `ff1dd94d4ccf5f7fdbced9b09b10cd67bd1d6192` — explicit same-logical/same-epoch ambiguity gate.
- `89c1d861b53d0239f6bf2b5818f1b44e8a32914a` — tombstone/out-of-order/rebuild/ambiguity falsifiers.

Critical falsification history:

The first draft deleted non-CURRENT heads. Randomized out-of-order insertion proved that a newer tombstone could then be forgotten and an older late-arriving CURRENT row could resurrect. That design was rejected before promotion.

Corrected design retains the newest head regardless of status and filters `CURRENT` only in the hot view.

Local 56k-history fixture (`8,000 logical edges x 7 versions`):

- full legacy-vs-fast current projection equality: true on the unique-head fixture
- legacy adjacency p50: `13,450.480 us`
- V3 p50: `14.641 us`
- p50 speedup: `918.69x`
- legacy p95: `14,446.287 us`
- V3 p95: `18.303 us`
- p95 speedup: `789.29x`
- V3 write p50: `17.597 us` vs append baseline `6.434 us` (`2.735x`)
- page ratio: `1.362x`.

Hostinger equivalent-mechanism fixture (`42k` history rows):

- differential equality: true
- tombstone no-resurrection: true
- same-epoch ambiguity detection: true
- legacy p50: `8,026.923 us`
- candidate p50: `56.781 us`
- p50 speedup: `141.37x`
- legacy p95: `8,869.872 us`
- candidate p95: `79.538 us`
- p95 speedup: `111.52x`.

Promotion blocker retained:

If one logical node/edge has multiple versions at the same `graph_epoch`, the old `MAX(epoch)` view may return multiple rows while a single-head projection must choose one. V3 therefore exposes that ambiguity and may not be marked verified until ambiguity=0 or an explicit semantic tie contract is owner/research-approved.

## Negative result: WITHOUT ROWID

Rejected for the measured graph-head shape.

- WITH ROWID read p50: `13.944 us`; rebuild `12.958 ms`; pages `1556`
- WITHOUT ROWID read p50: `14.820 us`; rebuild `13.716 ms`; pages `1541`

About 1% fewer pages did not compensate for worse read/rebuild latency.

Status: `NOT_SELECTED`.

## Canonical semantic-state root: streaming implementation

Commits:

- `fa9d3ad3e0fd991ea17259fb82e3bc02c94dd5bf` — byte-exact streaming semantic root.
- `09836cd77bf7a31c62f64dd93e20b29dee207432` — Unicode/nested/typed-collection/random/replay/snapshot equivalence tests.

The canonical hash algorithm/serialization contract did not change; only calculation stopped materializing/decompressing the entire state into a Python object graph.

Hostinger equivalent-mechanism receipt, run `31343978247`:

- hash equality: true
- legacy p50: `566.309 ms`
- streaming p50: `207.467 ms`
- p50 speedup: `2.7296x`
- legacy measured Python peak: `58,014,105 bytes`
- streaming measured Python peak: `3,036 bytes`
- measured Python peak reduction ratio: `19,108.73x`
- PASS.

This is a direct improvement with no semantic-root migration.

## UnifiedDB ↔ ClayGraph coherent assembly safety

Commits:

- `f69f05be0f4f3f2a82dd5cc90c9804fdbcc4a3b5` — epoch/hash/verification/ambiguity-bound context assembly.
- `ad59500a704609adcb02033a200dea4355933a24` — stale-state, graph-lag, future-graph, ambiguity, unverified, row-hash and row-count falsifiers.
- `67f3e33c65328ae031c0eb1b59dd54a367c05e29` — semantic-safety benchmark report.

Controlled epistemic fixture: 120 CURRENT rows, 60 KNOWN + 30 UNKNOWN + 30 CONFLICT; default ground truth admits KNOWN only.

Simple accept-current row-store baseline:

- TP=60, FP=60, FN=0
- precision `0.500`
- recall `1.000`
- F1 `0.667`.

Clay typed selection:

- TP=60, FP=0, FN=0
- precision `1.000`
- recall `1.000`
- F1 `1.000`.

Controlled mixed state/graph fault suite: 600 cases, 100 each SAFE/LAG/FUTURE/AMBIGUOUS/UNVERIFIED/TAMPERED; only SAFE is admissible.

Simple baseline:

- TP=100, TN=0, FP=500, FN=0
- accuracy `0.167`
- unsafe false-accept rate `1.000`.

Clay assembly gate:

- TP=100, TN=500, FP=0, FN=0
- accuracy `1.000`
- unsafe false-accept rate `0.000`.

Important limitation: this proves value of the semantic contract against a simple baseline, not superiority over a conventional DB system implementing the same contract.

## Conventional raw-SQL counterevidence

On the same local 20k SQLite structure and indexes, 500 exact-key reads:

- raw indexed SQL p50: about `7.45 us`
- JSON decode + Clay-like receipt-hash path p50: about `25.54 us`
- semantic/receipt overhead ratio: about `3.43x`.

Therefore the engine-level statement `Clay is faster than a normal indexed database` is refuted for this operation.

Architecture consequence:

Clay/UnifiedDB should own semantic state, epochs, epistemic status, provenance, receipts, safe assembly and possibility structure while continuing to exploit conventional storage/index/query machinery underneath.

## Authenticated state shadow V1

Commit:

- `b772998cac2b956e9a0d46e38bbff403d439bbd9` — rebuildable/non-authoritative 256-bucket authenticated shadow.

Local exact-source falsifiers:

- `7/7 PASS`: rebuild, delta, replay, retract, tamper, unexplained canonical-root drift, non-authority.

Local exact-module 20k / 30-update benchmark:

- authoritative `StateLedger.append_event()` p50: `140.408 ms`
- auth-shadow delta refresh p50: `0.5183 ms`
- canonical full-root recompute p50: `140.816 ms`
- root-side p50 ratio: `271.70x`
- full rebuild: about `343-347 ms`
- full verify: about `168-181 ms`
- page ratio: `1.464x` in this local fixture
- rebuild equivalence: true
- raw-state tamper detection: true.

Verified Hostinger equivalent-mechanism receipt (`Dr.-Unterweger` run `31344903534`, host `digital-retina`):

- shadow delta refresh p50: `0.4729 ms`
- p95: `0.7464 ms`
- canonical full-root p50: `78.319 ms`
- p95: `85.873 ms`
- root-side p50 speedup: `165.62x`
- full rebuild: `393.603 ms`
- rebuild-after: `385.783 ms`
- full verify: `230.302 ms` initial / `223.565 ms` after
- rebuild equivalence: true
- tamper detected: true
- page ratio: `2.0548x` in the remote standalone fixture.

Conclusion: integrity-update economics are strong; V1 storage amplification is too high to promote blindly.

## Authenticated state shadow V2 — current candidate

Commits:

- `f2fe9a1...` family / `research_entity/harness/reference/state_auth_shadow_embedded_v2.py` — embedded physical candidate (exact final file identity must be re-read before promotion).
- `392cd11...` family / `test_state_auth_shadow_embedded_v2.py` — migration/semantic-root/replay/tamper falsifiers (exact final commit must be re-resolved before promotion).
- `5975dbd...` family — StateLedger state UPSERT changed from positional `INSERT INTO state VALUES(...)` to explicit semantic column names.
- `benchmark_state_auth_shadow_v1_v2.py` — matched V1/V2 benchmark.

The exact commit prefixes above are descriptive run-time anchors; re-resolve current GitHub commits before any promotion because main advanced continuously during the run.

V2 design:

- explicit opt-in physical migration only;
- adds `auth_bucket` + `auth_leaf_hash` physical columns to `state`;
- canonical StateLedger serialization selects semantic columns explicitly, so V2 fields do not enter `semantic_state_hash`;
- 256 bucket aggregates remain rebuildable/non-authoritative;
- normal ledger writes must continue after physical schema extension;
- full verify recomputes leaf/bucket/root identity from authoritative semantic state.

Critical discovery before V2 testing:

StateLedger originally used positional `INSERT INTO state VALUES(?,?,?,?,?,?,?)`. Any added physical column caused normal writes to fail. This was a real schema-evolution defect. It was repaired by explicitly naming semantic columns in StateLedger UPSERTs before V2 could proceed.

Prototype/layout ablation on 20k rows:

- embedded V2 delta refresh p50: about `0.313 ms`
- p95: about `0.537 ms`
- full verify: PASS
- page ratio in the embedded fixture: about `1.42x`
- using only `INDEX(auth_bucket)` instead of `(auth_bucket,domain,k)` kept bucket lookup effectively unchanged in the micro-ablation (about `0.082 ms` vs `0.085 ms` p50) and reduced projected page ratio further toward about `1.35x`.

These V2 numbers are LOCAL/PROTOTYPE until the exact-repo V1↔V2 self-hosted receipt materializes. No V2 promotion claim is made.

## Exact Clay self-hosted lane status

This run observed newer repository workflows declaring `runs-on: self-hosted` for UnifiedDB maintenance economics, which is newer evidence than the prior repo-scope assumption. However a workflow file is not runtime evidence.

Created exact-repo gates:

- `auth_state_shadow_hostinger_probe.py`
- `.github/workflows/auth-state-shadow-hostinger.yml`
- `.github/workflows/auth-state-shadow-v1-v2-hostinger.yml`
- `.github/workflows/unifieddb-eap-direct-hostinger.yml`
- `.github/workflows/unifieddb-deep-selfhosted-issue.yml`
- issue `#133` `[CLAY-DISPATCH] UnifiedDB deep benchmark`.

At report-write time, no exact Clay self-hosted receipt had yet appeared for the new gates. Therefore:

- exact Clay self-hosted Auth V1/V2: `UNVERIFIED_PENDING_RECEIPT`
- exact Clay self-hosted EAP model-input direct receipt: `UNVERIFIED_PENDING_RECEIPT`
- verified remote evidence remains the Hostinger `Dr.-Unterweger` equivalent-mechanism receipts described above.

This distinction must be preserved.

## Parallel swarm fusion

During this run main advanced rapidly with independent UnifiedDB work, including:

- U14 adaptive read routing;
- U15 gap-triggered semantic cascade;
- Pulse/SPM active-field/rank-index maintenance economics;
- bounded locality/update-horizon falsifiers;
- two-phase rank-index lifecycle work;
- compact EAP semantic-row cache with exact retrieval-equivalence tests and memory/latency benchmark scaffolding.

The independent direction is compatible with this worker's findings:

1. no permanent global rebuild on every read;
2. incremental projections only when economics are favorable;
3. exact semantic/epoch basis before using a derived possibility field;
4. full rebuild remains a recovery/verification path;
5. projection activation never becomes truth/authority;
6. semantic rows/receipts remain source-addressable;
7. memory/state amplification is a first-class metric.

Auth Shadow V2 should therefore be treated as an integrity projection that may gate/verify U14/U15/Pulse/EAP projection state, not as another competing retrieval engine.

## Live web research + counterhypothesis fusion

Primary/research sources used in the run:

- SQLite query planner — https://www.sqlite.org/queryplanner.html
- SQLite partial indexes — https://www.sqlite.org/partialindex.html
- SQLite UPSERT — https://www.sqlite.org/lang_upsert.html
- SQLite WAL — https://www.sqlite.org/wal.html
- SQLite isolation — https://www.sqlite.org/isolation.html
- SQLite ALTER TABLE — https://www.sqlite.org/lang_altertable.html
- DBSP: Automatic Incremental View Maintenance for Rich Query Languages — arXiv:2203.16684
- Enzyme: Incremental View Maintenance for Data Engineering — arXiv:2603.27775
- Trillian verifiable data structures — https://github.com/google/trillian
- RFC 9162 Certificate Transparency / Merkle inclusion-consistency proof semantics — https://www.rfc-editor.org/rfc/rfc9162
- PostgreSQL transaction isolation/MVCC and constraints documentation
- Neo4j constraints/index documentation.

Fusion:

- SQL/index/materialized-projection techniques are not uniquely Clay; claiming engine superiority from them is invalid.
- DBSP supports the general principle of differentiating computations for incremental maintenance.
- Enzyme provides current industrial evidence that refresh strategy should be cost-based; incremental is not always cheaper.
- Authenticated/Merkle structures justify a separate incremental integrity root/proof layer, but only if its storage/recovery economics beat simpler full verification.
- SQLite ALTER TABLE semantics validate the physical possibility of V2 but reinforce the need for schema-evolution-safe application SQL; that defect was directly found and fixed in this run.

## Fair cross-engine contract

Created:

`research_entity/unifieddb/UNIFIEDDB_CLAYGRAPH_CROSS_ENGINE_BENCHMARK_CONTRACT.md`

It explicitly gives conventional engines their normal optimizations and requires matched semantics before comparing speed.

Initial fair lanes when capability exists:

- SQLite relational baseline;
- PostgreSQL MVCC/constraint baseline;
- graph-native baseline only when a reproducible current lane exists;
- Clay UnifiedDB + ClayGraph.

Required suites include epistemic admission, state/graph fault injection, replay/rebuild, concurrency/snapshot safety, exact key reads, bounded semantic reads, graph adjacency, end-to-end assembly, authoritative updates, delta refresh and full recovery.

## Current architecture decision

### Supported

`UnifiedDB = canonical semantic/logical state + transaction/replay/provenance/epistemic/epoch authority over ordinary physical storage.`

`ClayGraph = derived/rebuildable sparse topology/possibility projection with explicit current-head and ambiguity semantics.`

`EAP/Pulse/SPM = adaptive bounded projections that may be materialized only when measured query frequency/locality/maintenance economics justify them.`

`Auth Shadow = non-authoritative rebuildable integrity projection; useful only when delta-audit savings dominate storage/recovery cost.`

### Not supported

- one giant physical Clay database engine replacing ordinary storage;
- graph activation as truth;
- universal claim that Clay is faster/more accurate than every normal database;
- always-on materialization regardless workload;
- same-epoch graph ambiguity silently tie-broken without an explicit contract;
- canonical semantic-state root replacement by the Auth Shadow at this stage.

## Next highest-value frontier

1. Obtain/verify exact Clay self-hosted V1↔V2 and EAP receipts; if no receipt exists, keep capability `UNVERIFIED`.
2. Run V2 matched benchmark and test the smaller `INDEX(auth_bucket)` variant; reject V2 if storage/rebuild costs dominate.
3. Bind Auth Shadow verification receipts to Pulse/SPM/EAP projection epoch/hash so projection corruption can be detected cheaply without granting authority.
4. Execute the fair same-semantics SQLite baseline end-to-end, including equivalent epistemic/epoch/hash gates; measure complexity, latency, storage and recovery.
5. Add PostgreSQL only when a reproducible current tool/runtime lane exists; do not invent it.
6. Add WAL/checkpoint/long-reader/concurrent-writer/crash-restart tests.
7. Continue compact-EAP memory reduction if exact retrieval signatures remain identical.
8. Promote only mechanisms that are Pareto-competitive and survive recovery/falsification; preserve `NO BENEFIT` and negative results.

## Bottom line

This run produced real measurable progress, not a universal victory claim:

- UDB bounded reads: ~`299x` Hostinger p50 speedup over the old full-materialization path with `0` observed mismatches.
- ClayGraph current adjacency: ~`141x` Hostinger p50 speedup on the equivalent-mechanism history fixture with tombstone/ambiguity safeguards.
- canonical streaming root: ~`2.73x` Hostinger p50 speedup plus ~`19,109x` measured Python peak-memory reduction with byte-equivalent hash.
- Auth Shadow V1: ~`165.6x` Hostinger p50 delta-integrity advantage over full root recomputation, but high storage amplification.
- semantic safety: controlled unsafe-assembly false-accept rate `1.0 -> 0.0` versus a simple baseline.
- raw SQL remains faster on exact key lookup, preventing a dishonest physical-engine claim.
- V2 is now the storage-efficiency candidate and has already forced a real schema-evolution repair.

The evidence now supports `better for Clay's bounded semantic/context workload than the previous/simple architecture`, not `better than every database`.
