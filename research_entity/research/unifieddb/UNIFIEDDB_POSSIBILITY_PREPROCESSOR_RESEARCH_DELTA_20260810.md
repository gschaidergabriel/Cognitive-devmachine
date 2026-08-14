# UnifiedDB / ClayGraph Possibility Preprocessor — Research Delta

**Experiment:** `EXP-UDB-POSSIBILITY-PREPROCESSOR-20260810-A`  
**Status:** `SUPPORTED_LOCAL_SYNTHETIC_NOT_PROMOTED`  
**Branch:** `chatgpt/unifieddb-possibility-preprocessor-20260810`  
**Canonical parent:** RAE-8.8 revision 2 / `04234ef...9346`

## 1. What changed

This iteration treats UnifiedDB less like a database that cognition searches and more like a **semantic possibility preprocessor**. ClayCode/UnifiedDB/ClayGraph/Hyperposition evidence can produce versioned `possibility_candidates`; the preprocessor compiles those into bounded, provenance-bound `possibility_packets` before the hot cognitive read.

Hot path target:

`input -> canonical cue refs -> context signature -> CURRENT PossibilityPacket -> GWT/residual cognition`

Cold/unknown path remains allowed:

`missing packet -> LAZY/HYBRID retrieval/derivation -> optional materialization if measured benefit justifies it`

The packet is a derived model-facing product. It does not become truth or execution authority. ClayGraph activation can change accessibility/ranking only. Hyperposition alternatives/conflicts are retained as refs rather than destructively collapsed.

## 2. Why this is not merely another database index

The important object is not a stored document. The preprocessor can materialize a concrete possibility only after combining current semantic state, capability/resource bindings, typed rules, graph topology, evidence, authority and uncertainty. In the benchmark, 771 concrete possibilities were derived from 2,500 resources, 10,000 capabilities and 420 rules; the possibilities were not pre-existing text documents.

The database is therefore physical backing for an incremental semantic compiler. The model-facing unit is a prepared **possibility packet**, not a row search result.

## 3. Hypothesis and counterhypothesis

**H1:** standing possibility packets can preserve exact structured selection while moving expensive composition off the prompt path.

**H0 / strongest counterhypothesis:** aggressive precomputation can be worse for cold or rapidly changing contexts because indexing/materialization/storage costs dominate. Recent LazyGraphRAG work makes this cost objection concrete, and current IVM theory shows that constant update complexity is query-shape dependent rather than universal.

Resulting design: materialization is adaptive:

- `STANDING` — repeated reads and cheap targeted maintenance;
- `LAZY` — cold/high-update/high-maintenance spaces;
- `HYBRID` — uncertain/borderline cases or partial prepared topology.

The mode is selected by measured `read_rate * (lazy_query_ms - packet_query_ms) - update_rate * maintenance_ms - storage_penalty`, not by architectural preference.

## 4. External fusion

The design takes four useful external mechanisms but does not copy their architecture:

1. **DBSP / incremental view maintenance** — recompute deltas rather than full results. Primary: https://arxiv.org/abs/2203.16684
2. **Differential Dataflow arrangements** — build/share indexed dynamic state once and reuse it across later queries. Primary: https://timelydataflow.github.io/differential-dataflow/chapter_5/chapter_5.html
3. **GraphRAG / HippoRAG 2** — graph structure can recover global/associative relations missed by plain text/vector retrieval. Primaries: https://arxiv.org/abs/2404.16130 and https://arxiv.org/abs/2502.14802
4. **LazyGraphRAG + 2026 IVM complexity work** — full upfront materialization is not always cost-optimal; use lazy/hybrid mode for cold or expensive query families. Primaries: https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ and https://arxiv.org/abs/2606.07795

## 5. Production-candidate benchmark

Five deterministic seeds were run against the actual candidate runtime/migration, not only the first standalone prototype. Each main run used 2,500 resources, 10,000 capabilities and 420 rules; 102-115 valid context signatures were evaluated depending on seed.

### Accuracy@1

- PossibilityPacket: **100.0%**
- exact relational query-time derivation: **100.0%**
- FTS5 text/document baseline: **27.3%**

The 100% packet result means selection equivalence to the deterministic structured ground truth in this fixture. It does **not** mean universal semantic accuracy on real Frank tasks.

### Hot latency (median across five run p50s)

- PossibilityPacket: **0.023885 ms**
- exact relational derivation: **4.084586 ms**
- FTS5 text baseline: **0.640499 ms**

Measured p50 speedup vs exact query-time derivation: **171.0x**.

### Incremental mutation

- median targeted refresh: **2.957 ms**
- median full rebuild: **151.595 ms**
- median full/targeted speed ratio: **51.3x**
- median retired candidate fraction: **0.3822%**
- targeted selection equivalent to independent full rebuild: **true across all five seeds**

### Scaling spot-check

| resources | candidates | packet p50 ms | exact relational p50 ms | targeted refresh ms | full rebuild ms | retired fraction |
|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 310 | 0.021983 | 1.572974 | 2.311 | 44.359 | 0.9677% |
| 5000 | 1583 | 0.028478 | 8.203838 | 3.501 | 195.931 | 0.1895% |
| 20000 | 6410 | 0.0419475 | 34.209516 | 10.921 | 860.250 | 0.0624% |

Packet latency stays close to a direct keyed read while query-time relational derivation grows with the source state in this workload. Update work remains dependency-local, but targeted refresh cost does rise with the amount of source work needed to regenerate the affected resource closure.

## 6. Negative result preserved

A second prototype added a separate top-k frontier table and then joined it back to prepared possibilities on the hot path. It preserved correctness but was slower than the simpler prepared lookup. That design is **NOT_SELECTED**. The useful part—bounded top-k model payload—was retained by materializing the full packet directly.

## 7. Architecture delta

New candidate surfaces:

- versioned `possibility_candidates` (`candidate_version_id` + logical `candidate_id`);
- reverse dependency index over semantic/graph/evidence members;
- versioned `possibility_packets`;
- one-current-packet-per-context invariant;
- targeted invalidation queue;
- compile receipts with latency/count/hash;
- adaptive `STANDING/HYBRID/LAZY` materialization policy;
- direct current-packet read view.

This deliberately reuses the existing U7 direction (`semantic_dependencies`, cognitive materializations, `answer_capsules`, affordance materializations, emergent coalitions) rather than building a competing second memory architecture.

## 8. Local verification

Unit tests currently cover:

1. deterministic packet content + direct current read;
2. dependency-targeted packet invalidation;
3. graph activation never manufacturing authority;
4. dependency-targeted candidate retirement with history preserved;
5. adaptive standing/lazy/hybrid policy.

Local result: **PASS 5 tests**.

Environment: Linux/KVM x86_64, 5 logical vCPU, AMD EPYC 9V74, Python 3.13.5, SQLite 3.46.1. This is local execution evidence only.

## 9. What is still unproven

This result does **not** justify “better than every normal database.” It currently supports a narrower, useful claim: for this structured possibility workload, prepared packets match exact relational selection, greatly reduce hot-read latency, and outperform FTS text retrieval on structured selection. A sufficiently specialized relational/materialized-view/dataflow system can implement the same underlying idea.

Still required before promotion:

- self-hosted Hostinger Ubuntu runner parity;
- concurrent reader/writer + epoch publication tests;
- crash/restart/cold rebuild/rollback;
- storage/write-amplification curves under sustained updates;
- real UnifiedDB/ClayGraph snapshots rather than generated fixtures;
- Frank/Harness replay measuring misunderstanding/task success, not merely synthetic selection;
- cold/OOD query fallback and STANDING↔LAZY promotion/demotion;
- false-binding, stale-graph, provenance-broken and Hyperposition conflict controls;
- ClayCode compiler emission of semantic/dependency signatures into this path.

## 10. Current decision

`U10 Possibility Preprocessor = RESEARCH CANDIDATE / SUPPORTED_LOCAL_SYNTHETIC / NOT PROMOTED.`

The strongest next falsifier is a real project-state replay on the Ubuntu self-hosted runner with the same differential test: targeted update must produce the same selected possibilities as a full rebuild while remaining materially cheaper on the declared metric vector.
