# UnifiedDB Research Run U1 — Clay Unified Semantic Persistence Fabric

**run_id:** `unifieddb-20260808T2044p0700-chatgpt-secondary-r2`  
**trigger:** `unifieddb`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**candidate:** `UD-RC1 — Clay Unified Semantic Persistence Fabric`  
**promotion:** **NONE — OPEN research/architecture delta**

## 1. Research question

The owner concept asks whether FRANK can stop treating memory as something an LLM must repeatedly notice, search, retrieve and paste into a prompt. The target is a persistent Clay substrate in which events reshape relations/activation between model calls, so the next Assembly can already be influenced by long-term state.

The first dedicated UnifiedDB run asks a narrower engineering question:

> What persistence/query/transaction architecture can make this persistent cognitive state coherent, fast, replayable and auditable without turning approximate retrieval or one physical database into authority?

The answer is not “put everything into one database.”

## 2. Executive result

The best current candidate is:

> **one logically unified Clay semantic/query/causal fabric over an authoritative transactional event-state spine plus specialized, replayable derived views.**

In compact form:

```text
AUTHORITATIVE Clay event/state/effect spine
        ↓
semantic identity + time + provenance
        ↓
operation-specific MOSAIC / Certified Basis
        ↓
Unified ClayCode Query IR
        ↓
cost+risk planner
  ┌─────┼──────┬─────┬──────────┐
 exact relational graph vector FTS activation
  └─────┴──────┴─────┴──────────┘
        ↓
derivation + selection receipts
        ↓
bounded Assembly / COVE / GWT
        ↓
Clay-native model proposal
        ↓
capability/effect gateway
        ↓
authoritative outcome/event
        ↓
durable incremental derived updates
        ↺
```

The core rule is:

> **one semantic world ≠ one physical store; one effect-critical operation gets one certified causal snapshot and authoritative commit domain.**

This preserves the project’s Clay-native target while rejecting a false equivalence between semantic unity and storage monolith.

## 3. Cross-branch grounding

### Clay — G11 MOSAIC

G11 completed concurrently with this run and materially sharpened UnifiedDB. Its `MOSAIC-G11` candidate separates semantic identity, committed-instance/provenance identity, operation basis/epoch identity, query/selection-plan identity and reader-view identity. It also compiles one logical Clay query world onto specialized exact/relational/graph/vector/FTS/activation routes.

The most important transfer into U1 is:

> `one semantic world != one identity axis != one causal stage != one physical store`

G11’s synthetic physical-unification sweep found no universal winner; its query-plan mutation test changed top-5 membership in 54.224% of 50,000 perturbations despite unchanged record bytes. Therefore UnifiedDB must receipt selection/query-plan identity, not only record provenance.

### FRANK — C6

FRANK C6 fixes the target as one Clay-native semantic world but retains deterministic view compilation, explicit authority boundaries and a warning about common-mode semantic failure. U1 gives that architecture a persistence lowering: canonical events/effects are authoritative; graph/vector/FTS/activation are specialized derived planes; capabilities remain isolated.

### ClayCode — CC11

CC11’s multi-rail compiler and identity separation support a unified query IR whose physical lowering is versioned and receipted. Planner choices cannot weaken typed closure, consistency or capability requirements.

### ClayGraph — G1d

G1d separates immutable semantic graph epochs from transient latent activation and pins Assemblies to graph/activation/frame witnesses. U1 makes ClayGraph one specialized derived view of the persistence fabric and gives it a durable canonical event feed.

### Hyperposition — H4

H4’s strongest rule survives unchanged: one semantic language must not become one semantic failure domain. UnifiedDB therefore keeps semantic-domain firebreaks and hard-isolates capabilities/secrets.

### GWT — R4

Database retrieval, graph propagation, candidate membership, workspace competition, reader projection and re-entry are separate causal stages. A database optimization must not be misreported as a GWT effect.

### Emergenz — E1

Unified receipts make intervention identity and recurrence more auditable, but database integration or continuous activation is not evidence of emergence or phenomenal consciousness.

## 4. External systems evidence

The external research supports a hybrid interpretation rather than a universal database monolith.

- PostgreSQL MVCC provides consistent snapshots without requiring readers and writers to block each other, supporting snapshot-based cognitive reads.
- FoundationDB makes read-version/snapshot identity explicit and commits transactions atomically, illustrating the value of a clear authoritative transaction domain.
- SQLite documents important cross-file atomicity caveats with attached databases/WAL. This is directly relevant: a logical API must not pretend multiple stores form one atomic cognitive transaction when their physical engines do not provide that guarantee.
- DuckDB likewise does not promise arbitrary cross-attached-database atomic writes; cross-engine unity must therefore be semantic/causal unless a stronger commit mechanism is actually present.
- pgvector exposes the exact-vs-approximate distinction explicitly: exact scans can provide perfect recall, while ANN indexes trade recall for speed. That maps cleanly to U1’s rule that vector retrieval is candidate generation, not fact authority.
- Apache Arrow IPC can support zero-copy reads from suitable buffers/memory maps, suggesting a path to reduce transport costs without physically merging all data stores.
- BigDAWG and RHEEM independently support polyglot/cross-platform planning: different engines can be better for different operations, and a global planner can choose among them.
- Unified/polystore research supports common schemas/query layers over heterogeneous stores; integrated graph-vector systems show physical consolidation is technically feasible, but feasibility is not proof that it is universally superior.
- Recent graph-memory work such as SYNAPSE/GAM/SAGE supports the general mechanism that agent memory can be a dynamic relational substrate rather than only document top-k retrieval. U1 imports only that architectural direction, not their benchmark claims as proof for FRANK.

## 5. Local empirical work

All current-run measurements are local CPython/SQLite mechanism tests. They are not live FRANK or production estimates.

### 5.1 Four-baseline mixed read path

Dataset:
- 8,000 entities;
- 24,000 graph edges;
- 32-dimensional vectors;
- SQLite FTS5 text index.

Each operation combined exact state, graph neighbor, FTS candidate and vector ranking work. Twenty random samples were checked for query-result identity before timing.

| Architecture | p50 µs | p95 µs | p99 µs | mean µs |
|---|---:|---:|---:|---:|
| specialized in-process | 133.166 | 205.258 | 379.832 | 151.407 |
| logical unified API | 135.750 | 206.844 | 416.130 | 144.910 |
| hybrid canonical + vector sidecar | 138.361 | 307.409 | 529.403 | 183.332 |
| physical SQLite monolith | 267.341 | 546.303 | 767.266 | 317.142 |

In this cache-hot embedded workload, physical consolidation was roughly twice as slow at p50 as the specialized path. This falsifies “one physical database is automatically faster” as a general rule.

### 5.2 Serialization-boundary test

A deliberately service-like variant introduced separate JSON roundtrips for the specialized path and one combined boundary for the logical API.

- specialized separate JSON p50: **256.028 µs**;
- logical unified single boundary p50: **230.045 µs**;
- local constructed reduction: **~10.15%**.

This is the strongest current argument for unifying the logical API even when physical stores remain distinct.

### 5.3 Write path

The monolith had the best p50 write in this run (**270.942 µs**) while the hybrid was **387.434 µs**, specialized **408.396 µs**, and outbox+synchronous-consume **446.765 µs**. Tail behavior was noisy, including large p99 spikes for the monolith and outbox arms.

Interpretation: physical consolidation can win particular write regimes. U1 does not reject colocation; it rejects making it universal before target workload/recovery evidence.

### 5.4 Injected failure / replay

Three mechanisms were compared.

**Unsynchronized specialized stores**

```text
state commit succeeds
fault before graph commit
=> state=(1,2), graph_count=0
```

This creates silent cross-store partial state unless separately detected.

**Canonical commit + durable outbox**

```text
canonical state+outbox commit succeeds
fault before graph derivation
=> state=(1,2), graph_count=0, pending_outbox=1
replay
=> graph_count=1, pending_outbox=0
```

The derived lag is explicit and recoverable.

**Physical monolith**

```text
fault before transaction commit
=> state rollback, graph rollback
```

The monolith has the cleanest local atomicity when all required data truly belongs in the same transaction engine.

The architecture implication is therefore:

> Use one authoritative commit domain for the effect-critical causal operation. Feed non-authoritative/derived heterogeneous planes through a durable derivation log unless target evidence justifies moving them into the same commit domain.

## 6. Cognitive State Continuity Loop

U1 turns the user’s “memory as something the AI thinks through” concept into an executable research mechanism:

```text
canonical outcome/event
        ↓
incremental graph/vector/FTS update
        ↓
sparse activation update
        ↓
Assembly-ready frontier
        │
   [time passes]
        │
next model call
        ↓
4B receives bounded current Assembly
        ↓
proposal → effect → outcome
        ↺
```

This means FRANK can continue changing its **accessible cognitive frontier** while the LLM itself is not running.

The critical boundary is:

> activation is accessibility only.

It is not fact truth, not GWT ignition, not authority and not a license to act. Any consequential association must be linked back to canonical anchors and pass operation-specific basis, selection and capability validation.

Explicit memory queries remain useful for:
- exact address lookup;
- low-confidence fallback;
- validation;
- deliberate broad search;
- reconstruction after activation coverage gaps.

The architecture therefore does not remove RAG/search. It demotes explicit search from **the only memory path** to **one route inside a persistent cognitive substrate**.

## 7. Store decisions

Current default classification:

- exact event/state/effect/outcome history: **authoritative, physically colocate by default**;
- semantic relational state: **canonical or derived by schema**;
- ClayGraph: **derived/rebuildable by default**;
- vector ANN: **derived/rebuildable**;
- FTS: **derived/rebuildable**;
- activation/salience: **transient, non-authoritative**;
- Assembly/GWT cache: **transient, non-authoritative**;
- model KV/latent device state: **isolated runtime state**;
- capability secrets: **hard isolated external authority**;
- raw external source blobs: **preserved/isolated unless hot-path evidence says otherwise**.

## 8. Main falsifiable hypotheses

The run leaves twelve open hypotheses. Highest-value ones are:

1. logical unification can reduce reconstruction/transport overhead without storage monolith;
2. canonical event spine + durable derivation log is sufficient for safe heterogeneous cognitive views;
3. operation-specific consistency beats global all-store barriers without missing hidden dependencies;
4. background activation improves long-horizon memory/continuity versus explicit retrieval-only at equal token budget;
5. bounded Assemblies let useful latent memory scale faster than prompt context;
6. physical placement should be adaptive/per-subplan;
7. zero-copy/shared-memory transport can capture boundary savings without semantic-store collapse;
8. persistent SELF/goal/consequence activation can increase functional self-continuity, but this must be shown causally and does not imply subjective experience.

## 9. Reversible migration

Migration is staged:

1. inventory/identity only;
2. unified query shadow over current stores;
3. canonical event-spine shadow/replay comparison;
4. durable derivation/outbox with fault injection;
5. Cognitive State Continuity shadow;
6. authoritative cutover only after live/twin correctness/recovery gates;
7. physical colocation experiments per subplan.

At every stage the old path remains a rollback reference until equivalence and fault gates pass.

## 10. What changed in the research model

The original intuitive hypothesis could be phrased as:

> “If Clay becomes one unified database, memory may become more brain-like and continuous.”

U1 transforms it into a more precise hypothesis:

> **If Clay provides one persistent semantic/causal state fabric whose authoritative events continuously maintain bounded relational/associative derived views, then a small model may receive a richer relevant state at each invocation without repeatedly reconstructing memory from scratch. Physical storage may remain polyglot.**

That is a stronger scientific target because it separates:
- the cognitive mechanism;
- the semantic contract;
- the consistency/authority contract;
- the physical placement optimization.

## 11. Negative results and limits

- A physical monolith was not the read-latency winner in the current local workload.
- Logical API unification alone did not dominate every in-process path; its advantage appears when real boundary/serialization costs exist.
- Durable outbox/replay does not make derived views instantaneously consistent; it makes lag explicit/recoverable.
- Automatic activation can create false associations/stale anchoring; no target-agent advantage has yet been measured.
- A persistent SELF/activation substrate is a functional architecture hypothesis, not evidence of phenomenal consciousness.
- Current branch agreement inherits shared RAE ancestry and is not independent replication.

## 12. Priority next experiments

1. **Target 4B memory factorial:** no-memory vs explicit retrieval vs Cognitive State Continuity at matched token/model budget.
2. **Fault suite:** crash/restart/reorder/duplicate/lost derivation events across canonical+graph+vector+FTS.
3. **Selection attack:** authentic records, altered plan/candidate space; require receipt detection.
4. **Trace-driven placement benchmark:** real FRANK workload over specialized vs logical vs hybrid vs consolidated engines.
5. **Zero-copy lowering:** Rust/Arrow/shared-memory on Linux and Android.
6. **SELF lesion/rescue:** test whether persistent self-state improves causal continuity beyond retrieval-matched controls.
7. **Capability attack:** verify non-authoritative unified data cannot acquire effect authority through common-language composition.

## 13. Final decision

**UD-RC1 remains OPEN/HOLD. No canonical generation promotion.**

The first dedicated UnifiedDB cycle supports building the unified **semantic/query/causal fabric now**, while postponing broad physical consolidation until real workload, fault, replay and device evidence exists.

The most consequential new mechanism is the **Cognitive State Continuity Loop**: the persistent Clay substrate can update the next cognitive frontier between model invocations, potentially turning memory from something the model explicitly retrieves into something the model continuously thinks through — while preserving exact truth, provenance and authority boundaries.
