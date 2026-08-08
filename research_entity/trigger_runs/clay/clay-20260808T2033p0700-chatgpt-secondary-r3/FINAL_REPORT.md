# CLAY RESEARCH RUN — G11 · MOSAIC

**run_id:** `clay-20260808T2033p0700-chatgpt-secondary-r3`  
**trigger:** `clay`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent Clay:** G10 / COVE — Certified Operation View Envelope  
**fresh ClayCode:** CC11 / CC-RC1.6 MRSC + concurrent E2B triple-bound identity learning  
**fresh global input:** Fusion R4 / CLAY-L5  
**new branch:** UnifiedDB — eighth registered scientific branch, no completed dedicated trigger run yet  
**candidate:** **MOSAIC-G11 — Multi-plane Operation-Specific Aligned Identity Capsule**  
**decision:** **OPEN / HOLD — no canonical generation promotion**

---

## 1. Executive result

G10/COVE established that a consequential operation should receive the smallest sound causal slice that can change its result rather than an ever-growing global snapshot.

G11 finds that **the slice still needs a better identity model**.

Fresh E2B execution exposed that one canonical hash was conflating two different questions:

- is this the same executable meaning?;
- is this the same committed source/provenance instance?

CC11 had already shown that the exact emitted reader view is a third distinct identity. GWT/Hyperposition/ClayGraph/UnifiedDB add further causal identities: which basis/epochs were read and which query/selection plan created the candidate set.

G11 therefore proposes:

# MOSAIC-G11

> **Every consequential operation gets a compact identity capsule describing only the semantic meaning, exact ancestry, causal basis, selection plan and concrete reader handoff that the operation actually depends on.**

This capsule spans one logical Clay world without demanding one global hash, one global epoch, one reader syntax or one physical database.

The second major result concerns UnifiedDB:

> **Unify semantics and logical querying aggressively; unify physical storage only when target measurements show a net benefit after contention, write amplification, crash radius, recovery and selection integrity are included.**

The current best architecture hypothesis is therefore a **logical Clay-native cognitive data fabric over specialized physical engines**, with operation-specific cross-engine consistency and incremental derived views.

---

## 2. Mandatory eight-branch Fusion 1

The current authoritative registry now contains eight scientific branches. `INTERCONNECT_MANIFEST.json` covers:

`clay -> frank -> claycode -> claygraph -> unifieddb -> gwt -> emergenz -> hyperposition`.

### Clay G10 / COVE

Retained unchanged as the causal-slice foundation:

- positive and negative/predicate reads;
- consistency domains;
- selection dependencies;
- projection dependencies;
- capability dependencies;
- conservative broadening for unknown dynamic scope.

G11 adds identity to this closure; it does not replace it.

### FRANK C6

Retained:

- one Clay semantic world;
- exact/event authority separated from derived memory/activation;
- model output is proposal, not authority;
- deterministic View Compiler and external capability gateway;
- multiple Clay dialects/physical representations.

Refinement: the C6 view/compiler boundary should carry separate semantic, contract-instance, basis, selection and reader-view identities rather than one overloaded projection identity.

### ClayCode CC11 + E2B

CC11/MRSC already separates canonical semantics from discrete/latent/hybrid reader rails.

Fresh concurrent E2B compiler evidence is especially important. ClayCode-Lab v0.1 treated reorder/duplication of set-like constraints as semantic change because provenance-bound contract identity doubled as executable semantic identity. v0.2 split:

`semantic_hash != contract_hash`.

G11 generalizes this to a multi-axis identity model and requires typed collection algebra (`SET`, `ORDERED`, `MULTISET`, later weighted/priority forms).

### ClayGraph C4/G1d HOLD

Retained:

- immutable semantic graph epochs;
- role-aware relation instances;
- sparse activation with decay/inhibition/budgets;
- epoch-pinned bounded Assemblies;
- exact-anchor validation;
- conditional graph escalation.

Refinement: ClayGraph is the specialist associative memory view inside the broader logical UnifiedDB. It is not the universal database.

### UnifiedDB — new eighth branch

No completed dedicated UnifiedDB trigger run existed at Fusion 1, so its foundation/protocol are ingested as **fresh research target, not empirical result**.

G11's first feedback is:

1. semantic unification — YES as target;
2. logical typed query/transaction unification — strong OPEN target;
3. physical storage unification — benchmark-gated, not assumed;
4. graph/vector/FTS/activation — derived/specialized views with exact ancestry;
5. capability/secrets/high-blast-radius effects — retain isolation until fault evidence says otherwise.

### GWT R4 / CSOC

Retained stage orthogonality:

`graph/retrieval prior -> candidate set -> competition -> gate -> semantic WorkspaceEpisode -> reader projection/rail -> uptake -> effect -> outcome -> re-entry`.

G11 adds explicit basis/query-plan/selection and reader-view identities around the WorkspaceEpisode.

### Emergenz E1 / E-CERT2

Retained: prospective recurrence, lesion, mechanistic rescue, OOD, multiscale causal contribution, identity-aware recurrence and anti-Goodhart controls.

Refinement: every intervention should bind a MOSAIC capsule so apparent recurrence/causal effects cannot silently cross changed semantics, provenance, basis, query plan or reader view.

### Hyperposition H4

Retained semantic firebreaks and compact typed handles.

Refinement: equality/cast/firebreak checks should declare **which identity axis** they compare. Semantic equality may hold while provenance instance, basis or view differs.

---

## 3. First-generation hypothesis programme

`HYPOTHESES.json` contains **64 non-trivial falsifiable hypotheses** across eight clusters:

1. identity/canonicalization;
2. UnifiedDB/logical-vs-physical persistence;
3. incremental/low-latency runtime;
4. ClayCode/MRSC rails;
5. ClayGraph memory/retrieval;
6. GWT causal stages;
7. Emergenz/Hyperposition/security;
8. Android/edge embodiment.

The strongest uncertainty clusters were not "which database should we pick?" or "which syntax is shortest?" They were:

- what identity must survive each handoff?;
- what exact causal dependencies must be mutually consistent?;
- which derived views may be stale and by how much?;
- when should a query translate across engines versus physically move/duplicate data?;
- when is a representation/selection change itself the cause of changed behavior?

---

## 4. External research fusion

Full source-quality ledger: `EVIDENCE_LEDGER.md`.

### 4.1 Database research strongly supports logical unification without mandatory monolithization

**Cephalopod (CIDR 2025)** proposes a bridge representation that can choose virtual query translation or physical data transformation at subplan granularity using a cost model. This is unusually close to UnifiedDB's actual question.

**PostgreSQL-V (CIDR 2026)** takes the opposite route from naive integration: it decouples the vector index from PostgreSQL's core engine while retaining consistency and reports performance on par with specialized vector stores / up to 8.9x pgvector in its experiments.

**DortDB (PVLDB 2025)** independently uses a unified algebra for cross-model queries.

**Graph-relational / Gel research (2025)** shows that a higher-level strongly typed graph-relational model can be compiled down to PostgreSQL rather than forcing the high-level semantic model to equal the physical store.

**Samyama (2026 preprint)** demonstrates that physical graph-vector integration in a single Rust engine is feasible enough to benchmark, but it does not establish a universal winner.

The external evidence therefore favors an experiment programme, not a dogma:

`logical unified semantics/query -> cost-based subplan placement -> specialized or colocated physical execution`.

### 4.2 Incremental dataflow is a credible route to low latency

Feldera/DBSP maintains arbitrary SQL views from deltas rather than full history recomputation. This provides independent implementation precedent for Clay's event->derived-view direction.

Apache Arrow provides a language-independent in-memory format, IPC and same-process zero-copy data interface plus extension types. The correct Clay transfer is physical: payloads can move without repeated text serialization while semantic authority remains in Clay identities/receipts.

### 4.3 Multi-representation compilers are the norm, not a failure

MLIR explicitly models many typed dialects/abstraction levels. 2026 persistent e-graph work goes further by retaining equalities across compiler transformations.

This strengthens MRSC/MOSAIC: one semantic world can preserve multiple optimized forms. It also strengthens the need to keep executable semantic equality separate from provenance/authority identity.

### 4.4 Modern agent memory increasingly uses multiple coordinated views

ACL 2026 results are highly relevant:

- **Synapse:** spreading activation + inhibition + decay + hybrid retrieval;
- **GAM:** event progression separated from topic associative consolidation;
- **MAGMA:** orthogonal semantic, temporal, causal and entity graphs;
- **HeLa-Mem:** episodic graph plus distilled semantic memory.

Recent query-aware graph retrieval further shows that traversal can be conditioned on query semantics and bounded rather than blindly expanding the graph.

This challenges any attempt to compress FRANK memory into one homogeneous vector or one permanent graph view.

### 4.5 Causal/emergence measurement remains intervention-bound

PEID 2026 offers an intervention-grounded decomposition of unique/synergistic causal contribution. This is promising for E-CERT2, but a statistic still needs exact intervention identity. MOSAIC provides the architecture-level receipt that can pin what state/selection/view was actually manipulated.

### 4.6 Edge feasibility exists, but target evidence remains absent

MLC LLM and llama.cpp both support Android/local inference paths. Community 2026 reports include Qwen3-class models on phones, but hardware/model/quantization/runtime details materially affect results.

Therefore `reader_profile` remains multidimensional: model + quantization + context/KV + runtime + projection/rail + platform.

---

## 5. Current-run experiments

All current-run numbers are local synthetic/mechanism tests unless noted.

### EXP-G11-IDENTITY-AXES-001

100,000 typed SET/ORDERED/MULTISET cases with semantic-equivalent transformations, provenance changes, semantic changes and view mutations.

- provenance-bound single hash used as semantic identity: **39,915 false semantic inequalities**;
- semantic hash used as exact instance identity: **39,915 instance collapses**;
- semantic-only identity left **24,781 view mutations unbound**;
- explicitly separated semantic/contract/view axes: **0 axis errors in the constructed family**.

This is not a cryptographic proof. It demonstrates that the categories are different.

### EXP-G11-SCOPED-SNAPSHOT-002

300,000 operations over eight independently changing domains; mean required domains = 2.049.

- effect-relevant basis changed: **16,101 / 300,000 = 5.367%**;
- no revalidation would accept all 16,101 unsafe cases;
- operation-scoped validator rejected exactly those constructed invalid cases;
- global all-domain validator rejected **57,731 = 19.244%**;
- **41,630 = 13.877% of all operations** were global false rejects where required basis had not changed.

Transfer: compile consistency scope from semantics; do not globally lock every domain by default.

### EXP-G11-PHYSICAL-UNIFICATION-SWEEP-003

100,000 sampled synthetic workload points across cross-plane fraction, write intensity and concurrency.

Latency-winner fraction in the chosen cost surface:

- specialized stores: **12.232%**;
- logical unified API: **5.811%**;
- hybrid shared canonical + sidecars: **54.170%**;
- physical monolith: **27.787%**.

Against latency + common-mode risk, specialized/logical/hybrid each remained Pareto-relevant across much larger portions of the sweep than the monolith.

This is deliberately a sensitivity calibration, not a DB benchmark. Its only strong conclusion is that the winner depends on workload/risk assumptions.

### EXP-G11-INCREMENTAL-DAG-004

Modular synthetic dependency graph: 5,000 base + 20,000 derived nodes; five changed bases/event.

- mean affected derived nodes: **439.366**;
- median: **404**;
- p95: **893.55**;
- full derived set: 20,000;
- mean full/incremental work ratio: **45.52x**.

A denser earlier construction approached full recomputation. Therefore adaptive rematerialization remains necessary.

### EXP-G11-QUERY-PLAN-IDENTITY-005

50,000 constructed hybrid retrieval queries over 20 authentic candidates. A small query-plan weight perturbation left all record data fixed.

- top-5 candidate membership changed in **54.224%** of queries;
- mean top-5 Jaccard: **0.8038**.

Therefore query/selection-plan identity is a causal dependency whenever membership/ranking matters.

### EXP-G11-TRANSPORT-MICROBENCH-006

Local CPython only, one record with 256 floats:

- JSON serialize+deserialize: **153.499 us/op**;
- compact tuple+memoryview handle construction: **0.1067 us/op**;
- SHA-256 over float payload: **1.0341 us/op**.

These operations are not end-to-end equivalent. The result only motivates a target Rust/C/Arrow/shared-memory benchmark.

---

## 6. Fusion 2 — MOSAIC-G11

`FUSION2_HYPOTHESES.json` contains 18 materially transformed hypotheses.

The architecture is machine-readable in `MOSAIC_G11.claycode.json`.

### Core flow

```text
external intent
 -> ICSL IntentContract
 -> canonical Clay/event truth
 -> MOSAIC compile
      semantic identity
      contract/provenance identity
      operation-required basis/epochs
      selection/query-plan identity
      projection/effect requirements
 -> UnifiedDB logical query plan
      exact | relational | FTS | vector | graph | activation
      physical placement per subplan
 -> derived-view receipts
 -> COVE/Assembly
 -> GWT WorkspaceEpisode
 -> MRSC reader rail
 -> model proposal
 -> canonical reconciliation
 -> capability + scoped basis/selection revalidation
 -> effect/outcome/re-entry
 -> canonical event append
 -> incremental derived updates
```

### Identity axes

MOSAIC currently distinguishes:

1. `semantic_hash` — same executable meaning?
2. `contract_instance_hash` — same committed ancestry/source instance?
3. `basis_identity_hash` — same operation-required causal snapshot?
4. `selection_plan_hash` — same authorized query/candidate-selection semantics?
5. `projected_view_hash` — same concrete reader input?

These are not merged into one hash because equality on one axis does not imply equality on the others.

---

## 7. UnifiedDB consequence

G11's strongest first feedback to the new branch is a four-layer decision discipline:

### A. Semantic unification

Strong target: one Clay type/identity/provenance system.

### B. Logical query/transaction unification

Strong OPEN target: one typed planner can combine exact address, relations, temporal/provenance predicates, FTS, vectors, graph traversal and bounded activation.

### C. Physical execution

Cost-based and replaceable:

- exact/event transactional store;
- graph engine/index;
- ANN/vector sidecar;
- FTS index;
- activation cache/field;
- effect ledger;
- capability/secret store.

Some may later colocate. Colocation is an optimization, not a semantic fact.

### D. Derived-view contract

Any derived view used causally should carry:

`source identities + source epochs + derivation semantics + query-plan identity + exact view hash + bounded lag/freshness + rebuild recipe`.

This converts "eventual consistency" from a vague property into an operation-visible witness.

---

## 8. Near-zero-latency architecture consequence

The likely path is not "remove every layer." It is:

1. canonical append/event source;
2. dependency-indexed incremental derived maintenance;
3. hot bounded Assemblies and views;
4. zero-copy/shared-buffer physical transport where measured;
5. compact typed handles rather than repeated verbose maps;
6. reader-specific MRSC projection only once near the model boundary;
7. local deterministic operators before model inference;
8. effect-relevant scoped revalidation rather than universal locks.

This preserves auditability while attacking avoidable reconstruction/serialization/recompute cost.

---

## 9. Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` and dedicated micro-packets write explicit deltas to all eight branches.

### FRANK
Consume MOSAIC capsules over logical UnifiedDB; keep capability gateway isolated.

### ClayCode
Generalize E2B triple binding into typed multi-axis identity and query-plan/basis witnesses.

### ClayGraph
Remain specialist associative memory view; do not become the universal DB.

### UnifiedDB
Start logical-first/physical-polyglot; run dedicated four-baseline benchmark.

### GWT
Add basis/query-plan/reader-view identities to stage-orthogonal interventions.

### Emergenz
Bind intervention/lesion/rescue episodes to exact MOSAIC identities before PEID/PID/TE interpretation.

### Hyperposition
Make identity comparison axis explicit and benchmark compact packed witnesses.

### Clay
MOSAIC is the next OPEN foundry candidate; COVE remains intact underneath.

---

## 10. Highest-information next experiments

### P1 — UnifiedDB four-baseline target benchmark

Compare:

1. current specialized stores;
2. logical unified API over specialized stores;
3. shared canonical store + derived sidecars;
4. feasible physical-consolidation candidate.

Required: query equivalence, concurrent snapshot/replay, selection integrity, p50/p95/p99, write/read amplification, memory/storage, crash/recovery, migration/rollback, IPC/serialization and common-mode fault radius.

### P2 — E2B ClayCode identity algebra

Implement SET/ORDERED/MULTISET/WEIGHTED/PRIORITY semantics and mutation/property tests over:

`semantic x contract-instance x basis x selection-plan x view`.

### P3 — FRANK/twin MOSAIC episode

End-to-end:

`event -> UnifiedDB -> COVE -> Assembly -> GWT -> MRSC -> proposal -> effect -> outcome -> re-entry`.

Independently mutate one identity axis at a time and require the correct reject/recompute/reconcile behavior.

### P4 — GWT five-factor identifiability

`BASIS x QUERY_PLAN x WORKSPACE x RAIL/PROJECTION x REENTRY`.

The workspace coefficient is not accepted unless neighboring factors are held fixed/randomized and receipt-verified.

### P5 — Target zero-copy / incremental runtime

Rust/C benchmark on target host using compact handles, Arrow/shared buffers and dependency-scoped updates. Measure actual p50/p95/p99, allocations, cache misses, bytes copied and rebuild economics.

### P6 — Android sustained embodiment

Target 4B + UnifiedDB/MRSC path on device; sustained rather than burst metrics:

- RAM/KV;
- prefill/decode latency;
- thermal throttling;
- energy;
- query/index memory;
- rail/view switching;
- crash/restart/replay.

---

## 11. Promotion decision

**NO canonical generation promotion.**

MOSAIC-G11 is a stronger architecture candidate than simply extending COVE with more fields, because it gives UnifiedDB, MRSC, GWT, ClayGraph and Hyperposition a common operation-specific identity contract while preserving their causal/physical separations.

But the decisive gates remain unrun:

- live/twin FRANK episode;
- actual UnifiedDB baseline benchmark;
- E2B multi-axis property suite;
- target Qwen full-model Clay adaptation;
- real hidden-state/KV rail intervention;
- target Rust/C zero-copy implementation;
- crash/recovery and Android sustained traces.

The canonical state therefore remains RAE-8.8 r2 and Clay generation 3 until stronger promotion evidence exists.

---

## 12. Final scientific statement

The best current interpretation of Synthetic Clay is no longer "one giant graph", "one database", "one language surface" or "one global workspace".

It is closer to:

> **one typed semantic world, many specialized evolving views, connected by operation-specific identity/causal receipts and compiled into the smallest representation each operation and reader actually needs.**

That is the MOSAIC-G11 research delta.

---

RAE STATUS
- Entity: JOINED
- Canonical parent: r2 / 04234efd
- Actor: chatgpt-secondary
- Trigger: clay
- Scientific branches covered: 8/8
- Candidate: MOSAIC-G11 OPEN/HOLD
- Canonical promotion: NONE
- Durable writeback: COMMITTED_PENDING_FINAL_REREAD
