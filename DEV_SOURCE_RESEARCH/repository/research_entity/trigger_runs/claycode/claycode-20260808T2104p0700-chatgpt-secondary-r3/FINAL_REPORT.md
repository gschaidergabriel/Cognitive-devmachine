# CLAYCODE RESEARCH RUN — CC12 · Typed Collection & Query Semantics

**run_id:** `claycode-20260808T2104p0700-chatgpt-secondary-r3`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent ClayCode:** CC11 / `CC-RC1.6 Certified Multi-Rail Semantic Compiler`  
**fresh FRANK:** C7 / `Clay Organ Runtime Fabric`  
**fresh Clay:** G11 / `MOSAIC`  
**fresh persistence:** UnifiedDB U1 / `UD-RC1 Clay Unified Semantic Persistence Fabric`  
**candidate:** **CC-RC1.7 — Typed Collection & Query Semantics (TCQS)**  
**decision:** **OPEN / HOLD — no canonical scientific promotion**

---

## 1. Executive result

CC11 and the first E2B compiler loop split three identities that were previously easy to conflate:

`semantic meaning != committed provenance instance != emitted reader view`.

Clay G11/MOSAIC then generalized this into five operation identities by adding causal basis and query/selection-plan identity. UnifiedDB U1 and FRANK C7 now make the next missing language primitive visible:

> **ClayCode has to say what kind of collection a value is.**

A list of elements is not semantically enough. The same physical values can mean:

- a **SET** — order irrelevant, duplicates idempotent;
- an **ORDERED** sequence — position and duplicates matter;
- a **MULTISET** — order irrelevant, multiplicity matters;
- a **WEIGHTED** mapping — key and weight matter, with an explicit duplicate/aggregation policy.

CC12 therefore proposes:

# CC-RC1.7 — Typed Collection & Query Semantics (TCQS)

Core invariant:

> **collection kind is semantic, not container metadata.**

This type must survive canonical identity, query planning, backend lowering, reader projection, replay and effect-relevant revalidation. A SQLite row set, graph adjacency list, vector ranking or model candidate list does not get to redefine Clay semantics merely because its physical API has a default duplicate/order behavior.

Three new E2B experiments strongly discriminate this mechanism in constructed workloads:

1. 100,000 collection/property cases: **0 failures** under explicit SET/ORDERED/MULTISET/WEIGHTED rules;
2. 30,000 SQLite query lowerings: typed lowering **0 mismatches**, while universal DISTINCT produced **16,947** mismatches and universal raw bag/order behavior **16,609**;
3. omitting collection kind from semantic identity produced **27,155/100,000** SET-vs-ORDERED aliases; typed hashes produced **0** in the corpus.

These are executable mechanism results, not production FRANK or target-Qwen evidence.

---

## 2. Eight-branch grounding

The authoritative mesh now has eight scientific branches. CC12 materialized an eight-branch preflight in `INTERCONNECT_MANIFEST.json` with priority:

`FRANK -> Clay -> ClayGraph -> UnifiedDB -> GWT -> Hyperposition -> Emergenz -> ClayCode history`.

A governance defect was found during boot: `CLAYCODE_RESEARCH_PROTOCOL.md` still contained seven-branch wording after UnifiedDB was registered. CC12 followed the authoritative trigger/interconnect registries and added `CLAYCODE_EIGHT_BRANCH_UNIFIEDDB_ADDENDUM.md`. The Goodman validator was also made registry-dynamic and UnifiedDB-aware so future branch additions do not silently repeat this failure.

### FRANK C7

C7 already says runtime organ, process, store and authority boundaries are different dimensions. It also carries typed SET/ORDERED/MULTISET/weighted candidates in the architecture direction and asks ClayCode to provide a packed, semantically exact ABI.

CC12 supports the **semantic typing** part. It does not yet validate the proposed packed Rust/C/Android ABI performance.

### Clay G11 / MOSAIC

MOSAIC distinguishes:

1. semantic identity;
2. contract/provenance identity;
3. basis/epoch identity;
4. query/selection-plan identity;
5. projected reader-view identity.

CC12 refines axis 1: `semantic_hash` must include collection kind and collection-specific canonicalization rules. It also refines axis 4: a rewrite that changes duplicate/order/weight behavior changes `selection_plan_hash` even if record bytes remain identical.

### ClayGraph

ClayGraph's structures cannot all be treated as sets. Examples:

- role-bound n-ary relations can be ordered or role-keyed;
- graph neighborhoods may be SET-like;
- repeated observations can require MULTISET semantics;
- activation/ranking candidates can be WEIGHTED or ordered;
- Assembly membership and Assembly ranking are separate structures.

Universal set normalization would erase real semantics.

### UnifiedDB U1

U1's strongest persistence result is logical semantic/query unification over specialized physical engines, not one forced database monolith.

CC12 makes that more concrete: a **Unified ClayCode Query IR must carry result cardinality/order/multiplicity/weight semantics into every physical lowerer**. Logical unification without this type information is unsafe because SQL, graph, vector and FTS engines expose different default collection behavior.

### GWT

A workspace candidate membership set and a ranked/weighted competition structure are not the same state. GWT interventions must pin which structure is being held constant. Reordering an ORDERED candidate stream or changing multiplicity/weights can be a causal intervention even if the underlying unique member set is unchanged.

### Hyperposition

Semantic firebreak equality must include collection type. `SET[a,b]` and `ORDERED[a,b]` can carry different meaning despite equal element bytes. Cross-kind casts therefore need explicit policy/loss receipts.

### Emergenz

Recurrence and macrostate matching must preregister equivalence rules. Permutation may be inert for SET but not ORDERED; duplicate changes may be inert for SET but causal for MULTISET. CC12 does not make any consciousness claim.

### ClayCode history

CC-RC1.5 ICSL remains upstream for intent adequacy. CC-RC1.6 MRSC remains the reader-rail compiler. CC12 inserts a typed semantic algebra used by canonicalization, query lowering and view receipts; it does not replace those layers.

---

## 3. External evidence and anti-echo

FRANK, Clay, UnifiedDB and ClayCode share RAE ancestry, so their agreement is not counted as independent evidence.

Independent compiler/database-language evidence supports the mechanism class:

- Set/bag research explicitly separates Set and Multiset semantics and their rewrites rather than treating them as one interchangeable container.
- Compiler equivalence/translation-validation research shows that apparently valid transformations need independent semantic checking; compiler trust alone does not make every lowering correct.
- OR-Set/CRDT designs independently illustrate a useful identity split: the externally visible set value can be identical while internal causal add-tags/history remain distinct.
- Typed multi-level IR/compiler systems show that higher-level semantic types can survive lowering into different physical representations.

The full Goodman review yields:

- `SUPPORTED`: typed collection semantics in the C7 ABI;
- `SUPPORTED`: semantic vs provenance-instance identity separation;
- `SUPPORTED`: exact emitted-view binding;
- `REFINED`: UnifiedDB logical unification — supported only with explicit result collection semantics;
- `UNRESOLVED`: packed hot-path ABI performance on the target runtime.

No multi-branch echo is treated as replication.

---

## 4. Experiment 1 — typed collection identity

Artifact: `tools/claycode_collection_semantics_lab.py`  
Remote runtime: E2B isolated Linux/Python  
Experiment: `EXP-CC12-TYPED-COLLECTION-IDENTITY-001`

### Tested semantics

`SET<T>`
- permutation invariant;
- duplicate idempotent.

`ORDERED<T>`
- sequence order semantic;
- duplicate occurrences semantic.

`MULTISET<T>`
- permutation invariant;
- multiplicity semantic.

`WEIGHTED<T,W>`
- key and normalized weight semantic;
- input order irrelevant;
- duplicate key rejected unless a future explicit aggregation policy exists.

### Result

100,000 random mutation/property iterations:

- failure count: **0**;
- SET reorder invariant: PASS;
- SET duplicate idempotence: PASS;
- ORDERED reorder distinction: PASS;
- MULTISET reorder invariance: PASS;
- MULTISET multiplicity distinction: PASS;
- WEIGHTED normalization/value distinction: PASS;
- duplicate weighted key rejection: PASS;
- cross-kind type distinction: PASS;
- exact reader-view mutation rejection: PASS.

Again: zero means no failure in the generated property family, not a proof of language correctness.

### Identity result

Semantically equivalent reordered/duplicated SET sources can share a `semantic_hash` while retaining different provenance-bound `contract_instance_hash` values.

The projection receipt therefore keeps separate:

`semantic_hash + contract_instance_hash + projected_view_hash`

and MOSAIC additionally retains basis and selection-plan identities.

### Cost proxy

E2B/CPython, 50,000 rounds:

- recompute semantic+contract+view identities: **15.34 us/round**;
- cached semantic/contract IDs + view hash path: **3.37 us/round**;
- simple dual JSON identity object: **163 bytes**;
- current triple receipt JSON object: **332 bytes**;
- delta: **+169 bytes**.

Architecture consequence: compute canonical semantic/contract identity when the contract commits; hot reader paths should normally pass compact IDs/handles and bind the concrete emitted view rather than repeatedly serializing/re-hashing the entire semantic object.

This is not target ABI evidence.

---

## 5. Experiment 2 — UnifiedDB query lowering

Artifact: `tools/claycode_query_semantics_lab.py`  
Remote runtime: E2B / SQLite  
Experiment: `EXP-CC12-UNIFIEDDB-COLLECTION-LOWERING-002`

30,000 generated result workloads were lowered three ways.

### Typed reference lowerer

- SET -> duplicate-eliminating set result;
- ORDERED -> explicit positional order;
- MULTISET -> element plus multiplicity.

Result: **0 / 30,000 mismatches** against the Python semantic reference.

### Bad control A — everything DISTINCT

Mismatches: **16,947 / 30,000**.

Breakdown:
- ORDERED: 7,861 mismatches / 10,174;
- MULTISET: 9,086 / 10,010;
- SET: 0 / 9,816.

### Bad control B — everything raw bag/row order

Mismatches: **16,609 / 30,000**.

Breakdown:
- SET: 7,523 mismatches / 9,816;
- MULTISET: 9,086 / 10,010;
- ORDERED: 0 / 10,174.

This is the strongest CC12 negative result:

> **A type-erased unified query compiler cannot safely assume one backend result algebra.**

The correct physical SQL happened to be simple in this toy backend. The scientific point is not SQL syntax; it is that the physical lowerer needs the declared Clay result semantics.

---

## 6. Experiment 3 — cross-kind identity alias

Artifact: `tools/claycode_cross_kind_alias_lab.py`  
Remote runtime: E2B  
Experiment: `EXP-CC12-CROSS-KIND-ALIAS-003`

Constructed 100,000 SET-vs-ORDERED source cases.

If only canonical items were hashed and the collection kind was omitted:

- false cross-kind aliases: **27,155 / 100,000 = 27.155%**;
- nontrivial multi-element aliases: **5,038**.

When type was included:

- typed cross-kind aliases: **0**.

The numeric alias rate is distribution-specific. The robust conclusion is categorical:

> Same item representation does not imply same semantic collection type.

---

## 7. CC-RC1.7 TCQS contract

Machine artifact: `CC_RC1_7_TCQS.claycode.json`.

### Core types

```text
SET<T>
ORDERED<T>
MULTISET<T>
WEIGHTED<T,W>
```

Future priority/ranking types may split from WEIGHTED if rank/tie semantics require it.

### Explicit cast classes

`SET -> MULTISET`
- lossless embedding with multiplicity 1;
- semantic type still changes.

`MULTISET -> SET`
- lossy explicit `distinct` conversion.

`ORDERED -> SET`
- loses order and duplicate occurrence information.

`ORDERED -> MULTISET`
- loses order, preserves multiplicity.

`SET/MULTISET -> ORDERED`
- requires explicit order/comparator policy.

`WEIGHTED -> SET`
- loses weights.

`WEIGHTED -> ORDERED`
- requires explicit ranking/tie-break policy.

No effect/query-critical implicit cross-kind cast is accepted merely because the physical container can be converted.

### Query IR additions

A result contract should carry at least:

- `result_collection_type`;
- `element_type`;
- `duplicate_policy`;
- `order_policy`;
- `weight_policy`;
- `basis_requirements`;
- `selection_plan_hash`.

Backend defaults are implementation choices, not Clay semantics.

---

## 8. Key negative results

1. **Universal DISTINCT semantics rejected.**
2. **Universal raw bag/order semantics rejected.**
3. **Collection kind omission from semantic identity rejected.**
4. **One universal canonicalizer rejected.**
5. **Verbose triple receipts have measurable representation cost; compact handle lowering still needs target evidence.**
6. **Packed Rust/C/Arrow/Android ABI performance remains unresolved.**
7. **WEIGHTED duplicate aggregation must not be guessed.**
8. **ClayCode protocol/validator seven-branch drift was a governance bug and has been explicitly repaired/addended.**

---

## 9. Cross-branch architecture consequences

### FRANK
Carry compact collection type IDs in the runtime ABI. Do not infer semantics from wire layout.

### Clay / MOSAIC
Collection kind belongs inside semantic identity. Collection-changing query rewrites belong inside selection-plan identity.

### UnifiedDB
Make collection/result algebra a first-class query-IR type and test cross-engine equivalence.

### ClayGraph
Annotate relation operands, neighborhoods, observation recurrence, Assembly membership and rankings with appropriate collection algebra.

### GWT
Separate candidate membership from ranking/order/weight structure in causal interventions.

### Hyperposition
Cross-kind equality/casts are semantic operations and must pass firebreak/loss policy.

### Emergenz
Macrostate recurrence equivalence must explicitly define order/multiplicity/weight invariance.

### ClayCode
Retain ICSL + MRSC; integrate TCQS as canonical/query semantic typing rather than inventing another execution-authority layer.

---

## 10. Highest-information next experiments

1. **Cross-engine query equivalence:** same TCQS corpus lowered to PostgreSQL, DuckDB and representative graph/vector routes; preserve typed results and selection receipts.
2. **Typed cast fuzz:** SET/ORDERED/MULTISET/WEIGHTED transformations with explicit loss receipts; verify forbidden implicit casts fail closed.
3. **CC11/MOSAIC integration:** integrate TCQS into the MRSC reference compiler and ProjectionReceiptV3 rather than leave it as a separate lab.
4. **Rust/C/Arrow packed ABI:** semantic roundtrip + mutation fuzz + latency/memory on Linux; then Android.
5. **UnifiedDB planner mutation:** hold records fixed while changing collection semantics/query lowering; require selection-plan identity and effect revalidation to detect the change.
6. **ClayGraph field audit:** classify every collection-valued schema field as SET/ORDERED/MULTISET/WEIGHTED/other instead of inferring from JSON arrays.
7. **Target Qwen reader factorial:** only after actual target full-FT Qwen is available; test whether typed compact views improve model behavior, not merely deterministic compiler correctness.

---

## 11. Decision

**CC-RC1.7 TCQS remains OPEN/HOLD. No canonical generation or claim promotion.**

The run does establish a strong executable mechanism delta:

> **ClayCode cannot be a serious canonical/query language while collection cardinality, ordering, multiplicity and weights remain implicit.**

The same type information that makes semantic hashes correct also makes UnifiedDB lowering safer, MOSAIC identity sharper, FRANK ABI less ambiguous and causal experiments better controlled.

The next step is therefore integration and cross-engine falsification, not more notation design.
