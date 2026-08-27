# UnifiedDB Research Run U2 — Causal Polyglot Placement Fabric

**run_id:** `unifieddb-20260808T2212p0700-chatgpt-secondary-r3`  
**trigger:** `unifieddb`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent UnifiedDB:** U1 / `UD-RC1 Clay Unified Semantic Persistence Fabric`  
**fresh Clay:** CACC-G12  
**fresh GWT:** R5 Nested Workspace Bridge  
**fresh meta-screen:** Hypofusion H1  
**late workers ingested:** FRANK C8 SCRF + Hyperposition H5 HYP-RC5  
**candidate:** **UD-RC2 — Causal Polyglot Placement Fabric (CPPF)**  
**decision:** **OPEN / HOLD — no canonical or physical-database promotion**

## 1. Executive result

U1 established the correct broad direction: one logically unified Clay semantic/query/causal fabric over an authoritative event-state spine plus specialized replayable derived views.

U2 finds that U1's physical classification was still too coarse.

The question is not simply:

`one database vs many databases`.

The useful physical decision is a vector:

`transaction domain × data placement × index placement × compute placement × process domain × fault domain × rebuild policy`.

Therefore U2 proposes **CPPF**:

> **Unify semantic identity, typed query contracts and causal receipts; choose transaction, data, index, compute, process and fault placement independently under hard correctness/replay constraints.**

This resolves an apparent external contradiction. 2026 integrated systems show that graph/vector/relational query execution can profitably share one DBMS/query plan, while PostgreSQL-V and DecoupleVS show that vector indexes or vector payload/index storage can benefit from physical decoupling. Those are not contradictory once query-compute placement is separated from data/index placement.

A second U2 addition is **result admissibility**. A single unified query language must not flatten:

- authoritative exact facts;
- exact deterministic derived values;
- approximate retrieval candidates;
- salience/activation priors;
- model-internal state;
- external evidence;
- protected external resource references.

The compact U2 law is:

> **unified access != interchangeable epistemic role.**

## 2. Whole-mesh integration

### Clay / CACC-G12

Retained:

`integrity != cognitive utility != authority`.

U2 gives this a persistence/query implementation: utility receipts can inform salience/routing state, while canonical fact state remains in the authoritative spine. `UNKNOWN` dependency closure remains a planner state that broadens, instruments, recomputes or defers consequential operations.

### FRANK C8 / SCRF — late arrival

FRANK C8 completed while U2 was running and directly ingested U2's live E2B results. C8 independently at the architecture-view level reaches:

`rich persistent state != active cognitive slice`

and preserves per-path evidence-dependent physical placement. This is convergence within shared RAE ancestry, not independent replication.

CPPF supplies C8 with a `PlacementVector` and result-admissibility layer for its Memory Lifecycle / Cognitive Resource Governor paths.

### ClayCode CC12 / TCQS

TCQS collection semantics survive and become mandatory input to UnifiedQueryIR. `SET`, `ORDERED`, `MULTISET` and `WEIGHTED` are not backend defaults.

U2 additionally separates:

`typed semantic identity != exact emitted representation identity`.

A service/IPC adapter can preserve declared semantics while changing concrete bytes/host containers; both identities can matter for different questions.

### ClayGraph G1d

ClayGraph remains a specialist derived associative substrate, not the database authority. U2 adds explicit selection/search-space integrity and independently variable graph data/index/compute placement.

### Hyperposition H5 — late arrival

HYP-RC5 independently separates semantic relation topology, active propagation, dependency invalidation, selection/workspace, physical topology and authority path. This strongly matches CPPF's multi-axis placement/causal split, but shares project ancestry and therefore does not count as replication.

### GWT R5

Nested Workspace Bridge requires candidate formation to be receipted before system-workspace or model-internal-workspace effects can be attributed. U2 supplies query/collection/search-space/source-epoch/physical-plan identity upstream.

### Emergenz E-CERT2

No database or persistence result is emergence evidence. U2 improves intervention/replay identity only.

## 3. External evidence fusion

External evidence supports both integration and decoupling.

### Selection Integrity

Fei et al. 2026 show that authentic records can still be misselected when mutable graph structure controls information flow. Their AuthSelect architecture recomputes exposed selection over authenticated structure. U2 treats selection provenance as independent from record provenance and replay integrity.

### PostgreSQL-V

CIDR 2026 PostgreSQL-V keeps an integrated PostgreSQL query environment while decoupling vector indexing from PostgreSQL's core page-oriented index machinery. This is direct evidence that logical/query integration does not require index-storage colocation.

### DecoupleVS

2026 DecoupleVS argues that vector payloads and auxiliary index metadata have different storage/update characteristics and reports substantial storage reduction in its experiments when they are decoupled.

### AkasicDB

SIGMOD 2026 AkasicDB supplies the counterpressure: relational, graph and vector execution can be fused in one DBMS/query plan. CPPF therefore does not adopt decoupling as doctrine either.

### Cephalopod / graph-relational work

Cephalopod's partial query translation and graph-relational typed-model research support a planner that can keep one higher-level semantic contract while choosing virtual translation or physical transformation/lowering per subplan.

### Replay/versioning/incremental views

FoundationDB supports the usefulness of a clear transaction/commit domain. SQLite documents limitations of crash atomicity across attached databases in some configurations. DBSP/Feldera supplies mature precedent for maintaining views incrementally from deltas. Living Databases strengthens the need to bind transformation/version identity into derived-view replay.

### Arrow boundary correction

Apache Arrow's C Data Interface supports zero-copy exchange in the same process; cross-process sharing/persistence are separate concerns. U2 therefore treats compute/process/data placement as distinct dimensions.

## 4. Empirical work

All new numbers are E2B mechanism tests or explicit synthetic calibrations, not FRANK production estimates.

### EXP-U2-PLACEMENT-001 — mixed read path

Dataset:
- 5,000 entities;
- 18,000 graph edges;
- SQLite FTS5;
- 24-dimensional in-memory vectors;
- 700 mixed exact + graph + FTS + vector operations.

Results:

- logical separate stores, same process: p50 **99.514 µs**, p95 **143.808**, p99 **204.813**;
- physical SQLite monolith: p50 **101.687 µs**, p95 **145.929**, p99 **202.541**;
- service-like JSON boundaries: p50 **120.382 µs**, p95 **164.018**, p99 **229.071**.

The result does not establish a winner. It shows that in this cache-hot mechanism test, same-process logical composition retained specialization without paying the explicit service serialization cost.

### EXP-U2-RECOVERY-002

Across 1,200 constructed fault trials:

- unsynchronized two-store commits tore in **533** cases;
- canonical+outbox had **554** intentionally pending derived updates before replay and **0** mismatches after replay;
- one-engine transactional monolith had **0** atomicity mismatches.

Therefore both physical atomicity and explicit replay can provide correctness, but with different lag/performance/fault-domain properties.

### EXP-U2-SELECTION-INTEGRITY-003

700 PPR-like constructed selection cases retained authentic record data while allowing untrusted structure to influence selection.

- naive selected result changed in **516 / 700** cases;
- attacker target became selected in **498**;
- trusted-structure reselection recovered the constructed baseline in **700 / 700**.

This reproduces the mechanism class behind selection-integrity research, not the external paper's production system/result.

### EXP-U2-BOUNDARY-TYPE-005

10,000 JSON roundtrips:

- exact Python host representation equality: **0 / 10,000**;
- explicit typed `ORDERED` semantic equality: **10,000 / 10,000**.

The initial U2 comparator had flagged tuple→list as a query mismatch. That was a test bug and is preserved as a negative result. It demonstrates why semantic and concrete representation identities must be separate.

### EXP-U2-WRITE-006

In-memory SQLite write p50:

- monolith atomic transaction: **6.866 µs**;
- two unsynchronized commits: **8.797 µs**;
- canonical+outbox+derived update: **18.199 µs**.

The recovery-safe hybrid is not free. U2 therefore rejects the assumption that replayable sidecars dominate a monolith on every write-critical path.

### EXP-U2-EPOCH-ADMISSION-007

Constructed 200,000-case lag-policy calibration:

- naive critical stale accepts: **30.6645%**;
- universal exact barrier block rate: **87.578%**;
- operation-adaptive block rate: **63.2585%**.

These rates are distribution-specific. The transferable result is that exactness requirements can legitimately differ by operation class, but only when dependency closure is known; G12's `UNKNOWN` fallback remains mandatory.

## 5. CPPF architecture

```text
AUTHORITATIVE EVENT / STATE / EFFECT / OUTCOME SPINE
                         ↓
Clay semantic identity + time + provenance
                         ↓
Typed UnifiedQueryIR
  TCQS collection semantics
  result admissibility
  required epochs / closure state
  authorized search space
                         ↓
semantic plan enumeration
                         ↓
hard correctness/recovery constraints
                         ↓
CPPF PlacementVector optimization
  transaction domain
  data placement
  index placement
  compute placement
  process domain
  fault domain
                         ↓
polyglot physical subplans
 exact | relational | graph | vector | FTS | activation
                         ↓
selection + physical-plan + source-epoch receipt
                         ↓
exact validation where operation requires
                         ↓
Assembly / system workspace / reader / internal uptake
                         ↓
consequential release-time revalidation
                         ↓
outcome + canonical re-entry append
                         ↓
incremental derived updates
```

## 6. Result admissibility

U2 introduces an OPEN type discipline:

- `AUTHORITATIVE_EXACT` — exact canonical state/effect record;
- `EXACT_DERIVED` — deterministic, source/version-bound derived result;
- `APPROXIMATE_CANDIDATE` — ANN/search/ranking candidate, not fact truth;
- `SALIENCE_ONLY` — accessibility/prior only;
- `MODEL_INTERNAL_ONLY` — reader-runtime state;
- `EXTERNAL_EVIDENCE` — preserved external source/provenance;
- `PROTECTED_EXTERNAL_RESOURCE` — opaque reference whose use is governed outside cognitive storage.

This layer exists because semantic/logical unification otherwise risks making unlike values look interchangeable.

## 7. Derived-view identity

A causal derived view should bind at least:

`source IDs + source epochs + derivation-program hash + schema/model version + collection semantics + selection/query-plan identity + lag bound + rebuild recipe + admissibility class`.

Event history alone is not enough to identify a derived projection after transformation logic changes.

## 8. Query routing consequence

CPPF planning order is:

1. compile typed semantics;
2. determine dependency closure and admissibility;
3. enumerate semantically legal exact/relational/graph/vector/FTS/activation subplans;
4. prune plans that violate transaction, epoch, type, selection-integrity or recovery constraints;
5. optimize the remaining physical PlacementVectors;
6. execute and receipt the actual plan;
7. validate approximate/derived results according to the operation;
8. only then hand candidates/state to cognition or a consequential effect path.

Cost optimization therefore cannot silently weaken correctness.

## 9. Replay integrity vs selection integrity

U2 establishes an important orthogonality:

- a view can be perfectly replayable but choose the wrong authentic records;
- a selector can be structurally correct while reading stale/unreconstructible derived state.

Both must be measured independently.

For consequential retrieval, receipts should cover:

`source epochs + derivation identity + authorized search space + collection semantics + ranking/truncation/tie policy + candidate set + selector identity`.

## 10. Migration

U2 rejects a big-bang physical database migration.

Recommended sequence:

1. inventory current semantics/lineage;
2. introduce typed logical facade over existing stores;
3. add causal/query/selection receipts in shadow mode;
4. introduce durable derivation/replay for non-authoritative views;
5. add selection-integrity validation where exposed;
6. fuse high-affinity query compute only when measured;
7. independently test graph/vector/FTS data/index placement;
8. colocate only writes proven to require one atomic transaction domain;
9. replay real FRANK traces across placement vectors;
10. lower the same contracts separately for Android/edge.

Each step retains rollback to preserved canonical data/legacy path.

## 11. Negative results / corrections

1. The first U2 service-equivalence check was wrong because it compared host tuple/list representation as though it were semantic identity.
2. Canonical+outbox replay has measurable write cost; it is not automatically faster than one-engine atomic transactions.
3. The constructed Placement-Lattice sensitivity fractions are not target performance evidence and cannot select CPPF placement values.
4. Logical unification did not make the physical monolith universally faster in either U1 or U2 mechanism tests.
5. Physical decoupling is also not a universal answer; integrated systems such as AkasicDB remain credible counterexamples.
6. Record provenance is insufficient for selection integrity.
7. Same-process zero-copy is not automatically cross-process IPC.
8. No result here measures real FRANK, production durability, Android sustained behavior, target-Qwen cognition benefit or phenomenal consciousness.

## 12. Cross-branch writeback

Feedback was written to all eight scientific branches, with dedicated FRANK, ClayCode and ClayGraph micro-packets.

The late FRANK C8 and Hyperposition H5 workers were reread before close. Both converge with U2's axis separation; neither reverses CPPF. Their agreement is retained as shared-ancestry convergence only.

## 13. Highest-information next experiments

1. **Real FRANK trace-driven placement benchmark** — replay the same causal episodes over competing PlacementVectors with correctness fixed before measuring p50/p95/p99, write amplification, memory and failure radius.
2. **Cross-engine typed query equivalence** — PostgreSQL/DuckDB/SQLite plus representative graph/vector routes under TCQS semantics.
3. **Persistent crash/restart/rebuild** — real process termination and durable files, including derivation-program upgrades.
4. **Live ClayGraph selection integrity** — mutate selector-visible graph structure while record bytes remain authentic; compare trusted reselection and overhead.
5. **Same-process packed ABI vs IPC** — distinguish serialization, copying, scheduling and persistence costs.
6. **Migration rollback rehearsal** — current FRANK stores behind logical facade, then selective physical changes with rollback.
7. **Linux/Android sustained lowering** — same semantic/query corpus, different physical engines/placement, including energy/thermal/storage footprint.
8. **Target-Qwen CACC/Nested Workspace integration** — after an exact target route/runtime is available.

## 14. Final decision

**UD-RC2 CPPF remains OPEN/HOLD. No canonical revision, no physical database selection and no irreversible migration is promoted.**

U2 changes the UnifiedDB research question from:

> “Should FRANK use one database?”

into:

> **“Which semantics must be unified, which operations require one transaction domain, which query computation should be colocated, which data/indexes should remain specialized, and which exact receipts prove that the resulting cognitive state is replayable, correctly selected and admissible for its downstream use?”**

That is now the more precise target for the next live implementation cycle.
