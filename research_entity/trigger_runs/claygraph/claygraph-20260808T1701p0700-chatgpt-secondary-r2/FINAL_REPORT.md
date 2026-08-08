# CLAYGRAPH RESEARCH RUN — Cycle 3 · G1c Resident Adaptive Escalation

**run_id:** `claygraph-20260808T1701p0700-chatgpt-secondary-r2`  
**trigger:** `claygraph`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**accepted ClayGraph:** generation 0 `claygraph-v0-seed`  
**prior held candidates:** G1 temporal qualified activation; G1b query-planned evidence-bounded activation  
**cycle-3 candidate:** generation-1 variant **G1c `claygraph-g1c-resident-adaptive-escalation`**  
**decision:** **HOLD** — accepted graph remains generation 0.

## Executive synthesis

Cycle 3 receives the strongest new ClayGraph evidence so far: the RAE has now actually executed a hosted **Groq Llama-3.1-8B** proxy suite that used the repository ClayGraph retrieval surface and compared it with SQLite FTS. This closes part of the prior small-model/self-use gap while preserving the strict boundary that 8B proxy evidence is not target Qwen-class 4B replication.

The result challenges a major implicit assumption. On the GitHub runner, current ClayGraph activation and graph-lexical retrieval were roughly **84–87 ms median/query**, while SQLite FTS was approximately **0.8–0.9 ms**. Graph contexts were substantially larger. The spreading-activation overlay itself did **not consistently outperform graph-lexical retrieval** and sometimes added noise.

At the same time, audited answers showed that graph modes surfaced some cross-branch relational facts that plain FTS missed. Therefore the scientific result is not “ClayGraph failed”. It is narrower and more useful:

> **The current ClayGraph query implementation is not ready to replace cheap retrieval in FRANK's hot path, but the semantic graph still has conditional value for relational discovery.**

Cycle 3 then asks whether the ~85 ms result reflects an intrinsic cost of relational memory or an avoidable implementation path. The current query source reloads node/edge JSONL data per query and performs broad lexical seeding. A local controlled 10k-node proxy compared three architectures:

- per-query JSONL reload + full scan: **20.499 ms median**, p95 **23.394 ms**;
- resident nodes + full scan: **8.349 ms median**, p95 **9.706 ms**;
- resident inverted seed index: **0.106 ms median**, p95 **0.146 ms**.

These values do not transfer to the real RAE corpus or FRANK. They do falsify the idea that the observed runner latency can be interpreted as an intrinsic lower bound of graph semantics.

The new preferred HOLD candidate, **G1c**, therefore changes the architecture from “planned graph retrieval” to **resident adaptive escalation**:

`query`
`-> classify exact/local/associative/multihop/audit`
`-> cheap exact/packet/FTS/vector baseline`
`-> if relational need/evidence scatter/low baseline confidence justifies cost: graph escalation`
`-> rerank discoveries`
`-> preserve conflicts/evidence ancestry`
`-> exact-anchor validation for current/exact claims`
`-> bounded active assembly + route/cost certificate`
`-> FRANK memory candidate`

The graph becomes a **conditional relational exploration substrate**, not a universal lookup engine.

## 1. Mesh preflight and new evidence

All seven registered scientific branches were covered. The material new since Cycle 2 is dominated by the completed Groq 8B proxy suite and its branch feedback.

### Clay
The 8B reader results reinforce a general Clay rule: optimize semantic representations for **reader correctness, safety and total context cost**, not compactness by itself.

### FRANK
The new feedback explicitly says to keep deterministic authority semantics, verify projection integrity, control winner/order confounds and **hold current ClayGraph activation out of the hot path**.

### ClayCode
The 8B suite challenges zero-shot assumptions about compact/readable projections and produced unsafe behavior in some compact safety representations. Transfer to ClayGraph: canonical semantic identity may remain compact internally, but small-model reader projection should favor explicit relation roles until the target model proves otherwise.

### Hyperposition
The role-projection result supports explicit relation-instance role labels for readers while retaining canonical n-ary semantics. This fits ClayGraph's need to preserve higher-order relation identity without forcing the reader to infer role bindings from positional compression.

### GWT
The 8B results reinforce the separation of transport, projection, uptake and winner/order confounds. Graph activation must therefore remain upstream and experimentally separable from GWT workspace selection/ignition.

### Emergence
No emergence mechanism was tested. No change to the emergence/consciousness evidence boundary.

### ClayGraph
The hosted self-use result directly challenges current activation performance while preserving conditional relational benefit.

The Groq suite is one evidence family across these branch packets; cross-branch reuse is not counted as independent replication.

## 2. External research synthesis

Cycle 3 searched specifically for evidence capable of discriminating **always-on graph retrieval** from **adaptive graph use**.

### EA-GraphRAG — “Use Graph When It Needs” (2026)
This work identifies rigid GraphRAG use across all queries as a source of accuracy drops and prohibitive latency in mixed workloads. It routes low-complexity queries to dense RAG, high-complexity queries to graph retrieval and borderline cases to fusion. Transfer to ClayGraph: graph use should be earned by query structure/complexity rather than treated as the default memory read.

### RLM-on-KG (2026)
This work reports that the advantage of adaptive/LLM-controlled graph exploration depends on how scattered the needed evidence is. The architectural insight most relevant to ClayGraph is the separation of **candidate discovery** from **final evidence selection/reranking**. Transfer: use graph traversal to discover relational candidates, then apply a stricter reranker/assembly budget rather than directly exposing all activated nodes.

### HippoRAG 2
HippoRAG 2 is relevant as a counterweight: graph-structured associative memory can improve associative/sense-making tasks while preserving factual performance if passage integration and retrieval are carefully designed. It argues against interpreting the current ClayGraph latency/activation result as evidence that graph memory is intrinsically inferior.

### Microsoft GraphRAG current query architecture
Current GraphRAG exposes distinct Basic, Local, Global and DRIFT search modes rather than one universal graph query. Global search is explicitly resource-intensive; Local search combines graph entities/relations with raw text; DRIFT balances broad and local exploration. Transfer: ClayGraph should likewise maintain multiple retrieval modes and budget-based routing.

The external convergence is therefore conditional rather than universal: **graph structure is useful for some questions, and retrieval architecture must choose when/how much graph to use.**

## 3. G1c architecture

`CLAYGRAPH_SCHEMA.claycode.json` materializes the candidate.

### 3.1 Exact anchor index
Unchanged from G1/G1b. Authoritative exact/event stores remain truth. Current-state, migration parity, CognitiveFrame validity and authority-sensitive assertions can be revalidated through exact witnesses.

### 3.2 Resident semantic index
New in G1c. Instead of treating JSONL materialization as the query-time data structure, G1c requires resident/reusable indexes:

- token -> node;
- external id -> node;
- status -> node;
- branch -> node;
- evidence family -> node;
- typed adjacency;
- exact-anchor lookup.

The resident state remains **derived and rebuildable**. It carries graph revision/source-corpus identity and cannot become canonical truth merely because it is cached.

### 3.3 Retrieval router
Queries are classified into:

- `CURRENT_EXACT`;
- `HISTORICAL_EXACT`;
- `FACTUAL_LOCAL`;
- `SEMANTIC_ASSOCIATIVE`;
- `RELATIONAL_MULTIHOP`;
- `AUDIT_CONTRADICTION`;
- `MIXED`.

Simple/current/local queries use exact/packet/FTS/vector paths by default. Graph traversal is off unless uncertainty or relation need warrants escalation.

### 3.4 Graph escalation gate
The gate considers:

- query class;
- seed/baseline confidence;
- evidence scatter estimate;
- explicit relation need;
- token budget;
- latency budget.

A qualified edge is never enough by itself. The target must have query relevance or a required bridge role. Escalation stops when marginal evidence gain falls below cost or budget.

### 3.5 Candidate discovery then reranking
Graph traversal is treated as **discovery**. Its outputs are reranked before model visibility. This responds directly to the 8B result where graph relations could find useful cross-branch evidence while activation also introduced noise.

### 3.6 Reader projection
G1c explicitly separates canonical graph semantics from reader projection. For small-model readers, explicit role-labelled relation forms are preferred over aggressive positional compression until target evidence demonstrates equivalence.

### 3.7 Assembly certificate
Every assembly records route, graph/index revision, evidence families, status/staleness witnesses, exact anchors, conflict sets, graph paths, stop reason, retrieval time and context cost. The certificate is diagnostic/provenance metadata, not authority.

## 4. Empirical work

### EXP-CG3-GROQ8B-SELFUSE-IMPORT-001
Imported executed repository evidence:

- hosted model: `llama-3.1-8b-instant`;
- role: 8B proxy for bare/Qwen-class 4B;
- current ClayGraph/graph-lexical retrieval: ~84–87 ms median/query on runner;
- SQLite FTS: ~0.8–0.9 ms;
- graph contexts: substantially larger;
- graph modes: some cross-branch relational facts surfaced that FTS missed;
- spreading activation: no consistent advantage over graph-lexical selection.

Result: current activation implementation remains HOLD and should not enter FRANK's hot path as already superior.

### EXP-CG3-RESIDENT-SEED-INDEX-002
Local synthetic implementation experiment, seed `20260808`, 10,000 nodes, 2,000-token vocabulary, 40 queries:

| arm | median | p95 |
|---|---:|---:|
| JSONL reload + full scan | 20.499 ms | 23.394 ms |
| resident full scan | 8.349 ms | 9.706 ms |
| resident inverted seed index | 0.106 ms | 0.146 ms |

Interpretation: data loading/indexing strategy can dominate lookup cost. This is a mechanism proxy, not a target latency estimate.

### EXP-CG3-ADAPTIVE-ESCALATION-COST-003
Using the approximate observed runner retrieval costs of 0.85 ms SQLite FTS and 85 ms current graph, expected retrieval cost if only a fraction of queries escalate to graph is:

- 5% graph: ~5.06 ms;
- 10%: ~9.27 ms;
- 20%: ~17.68 ms;
- 30%: ~26.10 ms;
- 50%: ~42.93 ms.

This only demonstrates the cost geometry of routing. It does not prove routing accuracy.

## 5. Hypothesis transformation

Cycle 2's main hypothesis was that a query-aware graph planner could beat fixed graph activation. Cycle 3 sharpens it:

> **Graph traversal should be an evidence-discovery escalation behind a cheap baseline, and the graph's query structure must be resident/indexed rather than reconstructed/scanned per request.**

The main new falsifiers are operational:

1. current-corpus resident indexing fails to materially lower p95/p99;
2. router false negatives erase relational recall;
3. reranking removes the graph's useful cross-branch discoveries;
4. resident update/memory amplification costs exceed lookup savings;
5. target Qwen-4B cannot use explicit graph assemblies better than baseline contexts.

## 6. Negative results

The most important preserved negatives are:

1. current activation hot-path superiority is refuted by the hosted 8B proxy;
2. spreading activation is not established as superior to graph lexical retrieval;
3. FTS-only is also not established because relational evidence was sometimes recovered only by graph modes;
4. current ~85 ms graph retrieval is not evidence of intrinsic graph cost;
5. local inverted-index speed is not a live-FRANK claim;
6. 8B is not target 4B replication;
7. aggressively compact model projections remain unsafe/unproven;
8. physical database merge remains unsupported.

## 7. FRANK feedback

Primary integration remains `M.MEMORY_FABRIC`, now refined into:

`OP.MEMORY_ROUTE`
`-> OP.MEMORY_BASELINE_RETRIEVE`
`-> optional OP.MEMORY_GRAPH_ESCALATE`
`-> OP.MEMORY_RERANK_ASSEMBLE`
`-> OP.MEMORY_EXACT_VALIDATE`

`S.ACTIVE_ASSEMBLY` gains route, baseline confidence, graph-escalation reason, graph/index revisions, evidence families, staleness witnesses, stop reason, retrieval time, context tokens and explicit fallback availability.

Unchanged hard boundaries:

- `M.DURABLE_EVENT_STATE` is exact authority;
- `S.COGNITIVE_FRAME` is the causal snapshot/consistency contract;
- `M.WORKSPACE_ARBITER` owns GWT competition/selection;
- ClayGraph activation is not GWT ignition;
- `M.CAPABILITY_GATEWAY/K0` remains external authority.

## 8. Database migration

No new live database enumeration was produced. Current provisional dispositions therefore remain:

- `consciousness.db` -> `PROJECT`;
- `world_experience.db` -> `PROJECT`;
- Thalamus -> `DEFER`;
- Titan/Ego -> `DEFER`;
- invariant/safety authority if current -> prefer `KEEP_ISOLATED`;
- unresolved current stores -> `UNKNOWN/DEFER`;
- `MERGE` -> **none**.

Cycle 3 adds a new migration-independent step: **RESIDENT_DERIVED_INDEX**. This is a rebuildable projection/cache, not a physical store migration.

## 9. Cross-branch feedback

- **Clay:** adaptive semantic resolution now includes retrieval-route resolution; latency/context become shadow metrics alongside correctness.
- **FRANK:** resident indexed graph plus adaptive escalation inside memory fabric; current activation out of hot path.
- **ClayCode:** represent routes/cost receipts/exact-anchor obligations and explicit reader relation roles.
- **Hyperposition:** query-conditioned traversal topology becomes distinct from semantic dependency, invariant coordination and physical locality.
- **GWT:** graph retrieval/activation must be lesion-controlled upstream of workspace arbitration and separate from winner/order/reconstruction effects.
- **Emergence:** `NO_CHANGE`; no emergence claim tested.
- **ClayGraph:** G1c becomes preferred HOLD candidate; accepted graph remains G0.

## 10. Evolution decision

**HOLD. Do not update `CLAYGRAPH_LATEST.claycode.json`.**

G1c is a stronger candidate because it incorporates actual hosted small-model evidence and directly addresses the measured performance failure. It is not promotion-ready because the resident/indexed architecture has not yet been implemented and benchmarked on the current repository corpus, target Qwen-class 4B remains untested, and live FRANK store/runtime gates remain open.

## 11. Highest-information next gates

1. Implement a current-corpus resident ClayGraph index with typed adjacency and exact-anchor lookup.
2. Benchmark G1c against SQLite FTS, deterministic packet envelopes, accepted G0 and G1b on an independently grounded >=50-query mixed set.
3. Measure recall/precision/evidence-family recall/stale leakage/context tokens/p50/p95/p99 plus resident memory and update amplification.
4. Directly compare graph-lexical versus spreading activation after both are resident/indexed; delete activation complexity if it does not add value.
5. Run target Qwen-class 4B answer-quality factorial with explicit versus compact relation projection.
6. Inject stale graph assemblies against fresh `CognitiveFrame`; exact-anchor validation must reject/refresh stale assertions.
7. Run graph relation-shuffle/temporal-shuffle memory lesions before GWT arbitration with projection/order matched.
8. Complete read-only 71-store inventory and shadow parity/replay/p99/crash/privacy gates.

## Final synthesis

Cycle 1 established that ClayGraph should unify **meaning**, not necessarily physical storage. Cycle 2 established that ClayGraph must learn **when not to traverse**. Cycle 3 adds the missing performance lesson:

> **ClayGraph should not be a graph query that FRANK runs every time it thinks. It should be a resident semantic nervous system that FRANK can cheaply consult, with expensive relational exploration triggered only when the question actually requires it.**

That is materially closer to the original research target of memory-through-thinking than an explicit `thought -> run expensive graph search` pipeline, while still preserving exact truth, provenance, conflict, authority and rollback boundaries.
