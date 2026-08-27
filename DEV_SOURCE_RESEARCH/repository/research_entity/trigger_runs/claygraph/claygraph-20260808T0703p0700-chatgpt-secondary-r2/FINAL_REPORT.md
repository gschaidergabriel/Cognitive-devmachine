# CLAYGRAPH RESEARCH RUN — Cycle 2 · G1b Query-Planned Evidence-Bounded Activation

**run_id:** `claygraph-20260808T0703p0700-chatgpt-secondary-r2`  
**trigger:** `claygraph`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**accepted ClayGraph:** generation 0 `claygraph-v0-seed`  
**prior held candidate:** G1 `claygraph-g1-temporal-qualified-activation`  
**cycle-2 candidate:** generation 1 variant `claygraph-g1b-query-planned-evidence-bounded-activation`  
**decision:** **HOLD** — accepted graph remains generation 0.

## Executive synthesis

The previous ClayGraph run established the strongest architecture boundary so far: exact/event state remains authoritative; ClayGraph is a derived temporal/provenance-aware semantic relation space; activation is transient and non-authoritative. The important new fact since that run is operational rather than scientific: RAE now has a **runtime-verified seven-branch rich active-knowledge contract** with deterministic Topic/Micro-Packet envelope selection and raw expansion on demand.

That creates a stronger question than G1 asked:

> Can ClayGraph become a better **active-knowledge selector** than the deterministic packet envelope while preserving negative results, provenance, evidence-family independence, exact-state authority and bounded context?

Cycle 2 answers: **promising, but not yet.**

A source-grounded designed proxy found that the revised G1b planner improved overall recall (`0.6250` vs G1 `0.5917`), independent evidence-family recall (`0.7083` vs `0.6792`) and stale suppression (`0.0767` vs `0.1650`) at similar context budget. But on a held-out half of the queries, recall merely tied (`0.5250`) and precision was slightly worse (`0.3050` vs `0.3133`). This blocks promotion.

A second adversarial experiment injected erroneous *qualified* graph edges. Across 200 runs, G1b retained higher mean recall/precision, much lower stale leakage and better lower-tail recall than G1. This supports the **relevance gate** and query-adaptive routing direction, but remains a constructed proxy.

The architecture therefore advances without promotion: G1b introduces an explicit **AssemblyPlanner** before activation.

`query -> classify exact/history/semantic/multihop/audit -> select seed routes -> bounded qualified traversal -> preserve conflicts/evidence ancestry -> exact-anchor validation where required -> active assembly + plan/certificate -> FRANK memory candidate`

## 1. Mesh and accepted-parent discipline

All seven registered scientific branches were covered before Fusion 1. No newer scientific branch run superseded the sources used in the previous ClayGraph run. The material new since G1 is the runtime-verified active-domain knowledge policy and seven-branch contract.

The accepted graph is still generation 0. Since G1 was HOLD, Cycle 2 does **not** create generation 2. The new candidate is another generation-1 child of accepted generation 0, labelled **G1b**. This preserves lineage rather than promoting a held candidate by chronology.

The earlier governance drift where the interconnect protocol still listed six branches is resolved: the current protocol, registry and runtime contract all use seven scientific branches.

## 2. New runtime target: active knowledge envelopes

`DOMAIN_ACTIVE_KNOWLEDGE_POLICY.md` establishes two knowledge levels:

1. complete indexed/reachable research;
2. bounded active Topic/Micro-Packet envelopes.

The deterministic selector prioritizes status plus category, reserves diversity across negative/contradiction/experiment/architecture/hypothesis/feedback/general material, and then fills the remaining budget by priority. This is intentionally not a query-specific retriever: it is a robust cross-domain grounding layer.

The policy explicitly states that ClayGraph may eventually become the better active-envelope selector, but deterministic ranking remains baseline until this is empirically demonstrated.

Cycle 2 therefore treats deterministic envelopes as a **safety/fallback baseline**, not a strawman to delete.

## 3. External research synthesis

### Adaptive graph traversal

**PolyG** argues that different question types require different graph traversal strategies and reports gains from classifying questions and selecting traversal adaptively. Transfer to ClayGraph: one fixed hop strategy is unlikely to be optimal across exact current-state, semantic association, contradiction audit and true multihop tasks.

### Plan-guided hybrid retrieval

**GRASP (2026)** combines plan-based graph retrieval, plan-conditioned fusion with dense retrieval and reranking, reporting large improvements across STaRK benchmarks. Transfer: graph traversal should be one planned retrieval branch, not the only retrieval surface.

### Projection-aware graph grounding

**PAGE-RAG (2026)** explicitly treats the graph as a semantic skeleton/projection rather than an independent replacement for source knowledge, adds adaptive routing and knowledge-boundary controls. This converges strongly with ClayGraph's exact-anchor boundary: graph navigation may select evidence, but exact/raw sources remain available for grounding.

### Bounded retrieval

**G-Retriever** reports a non-monotonic retrieval-size effect: performance rises with K and then falls at larger K in one benchmark. Transfer: more graph context is not monotonically better; adaptive stopping should be a first-class hypothesis.

### Current implementation/practitioner evidence

Current Graphiti issues reinforce open engineering risks rather than supplying ClayGraph proof:

- issue #1515 requests standardized temporal retrieval benchmarks and explicitly calls out supersession and graph-vs-vector evaluation;
- issue #1166 reports destructive updating of node attributes without historical temporal versioning in that implementation;
- issue #1602 describes production-style graph growth with low-signal facts increasing retrieval noise/storage/query cost and proposes salience/multi-tier memory;
- a practitioner Reddit report describes correct user data existing in Graphiti while an irrelevant relation is returned for a simple query.

These are heterogeneous evidence classes, but they converge on one methodological point: **correct graph storage is not sufficient evidence of correct retrieval, and retrieval policy must be benchmarked independently.**

## 4. G1b semantic architecture

G1b retains G1's three semantic commitments and adds a planner layer.

### 4.1 Exact anchor index

References current/history truth in authoritative stores. Exact/current claims, migration parity, CognitiveFrame validity and authority-sensitive decisions can be revalidated here.

### 4.2 Temporal/provenance semantic graph

Assertions remain versioned, source-attributed and conflict-preserving. `CURRENT`, `OPEN`, `SUPERSEDED`, `REFUTED`, `NEGATIVE_RESULT`, `STALE`, `REVOKED` and related states remain explicit.

### 4.3 AssemblyPlanner

New query classes:

- `CURRENT_EXACT`
- `HISTORICAL_EXACT`
- `SEMANTIC_ASSOCIATIVE`
- `RELATIONAL_MULTIHOP`
- `AUDIT_CONTRADICTION`
- `MIXED`

Default routing:

- current exact: **0 graph hops**, exact anchor required;
- semantic associative: **1 hop**;
- relational multihop: adaptive up to **2 hops**;
- audit/contradiction: actively include negative/refuted/superseded/stale material;
- mixed: split exact subclaims from associative context.

### 4.4 Relevance-gated expansion

A typed/qualified edge is no longer enough to justify activation by itself. Its target must also have independent query relevance, except when an explicitly requested multihop plan needs a bridge node. This is the main robustness delta from G1.

### 4.5 Evidence-family anti-echo

Cycle 2 falsified the simplest hard family cap. One evidence family may contain different useful roles: a claim, a negative result, an experiment and an architecture consequence. Shared ancestry should reduce **independent evidence weight** and duplicate context, but not blindly delete all but one descendant.

Preferred research candidate: soft family penalty + role diversity.

### 4.6 Assembly certificate

Every active assembly should be replayable/explainable through:

`plan_id, query_class, graph_revision, selected refs, exact anchors, paths, epistemic states, evidence families, conflicts, omitted duplicates, stop reason, token cost`.

This metadata has no execution authority.

## 5. Self-use proxy

`EXP-CG2-ACTIVE-ENVELOPE-ROUTER-001` used 53 source-grounded packet-like items, seven branches, 20 research questions and stale/refuted adversarial lexical decoys under a 620-token proxy budget.

| arm | recall | precision | evidence-family recall | stale rate | median token proxy |
|---|---:|---:|---:|---:|---:|
| deterministic packet envelope | 0.1000 | 0.0700 | 0.1292 | 0.0000 | 535.0 |
| lexical/direct staged proxy | 0.5875 | 0.3183 | 0.6417 | 0.2050 | 602.5 |
| G1 fixed qualified graph | 0.5917 | 0.3675 | 0.6792 | 0.1650 | 570.0 |
| G1b query-planned hybrid | **0.6250** | 0.3633 | **0.7083** | **0.0767** | 600.0 |

The deterministic envelope result must be interpreted carefully: it is query-independent by design and therefore not expected to maximize task-specific recall. Its value is safety/diversity grounding.

### Held-out split

Only a minimum relevance threshold was selected on ten development queries; ten alternating queries were held out.

- G1 holdout recall `0.5250`; precision `0.3133`; family recall `0.5750`; stale `0.1933`.
- G1b holdout recall `0.5250`; precision `0.3050`; family recall `0.6417`; stale `0.0833`.

This is the decisive promotion blocker: G1b has a better epistemic hygiene profile, but has not yet shown a held-out task-recall/precision win.

## 6. Erroneous-edge stress

`EXP-CG2-ERRONEOUS-QUALIFIED-EDGE-002` injected twelve random erroneous `DEPENDS_ON/SUPPORTS/CONSTRAINS/IMPLEMENTS` edges per run for 200 runs.

| metric | G1 | G1b |
|---|---:|---:|
| mean recall | 0.58965 | **0.62333** |
| mean precision | 0.35377 | **0.36220** |
| stale rate | 0.17202 | **0.07831** |
| evidence-family recall | 0.67500 | **0.70525** |
| recall p05 | 0.5750 | **0.6125** |
| precision p05 | 0.33667 | **0.35333** |

This supports requiring query relevance in addition to edge type. It does not establish real extraction-error distributions.

## 7. Negative ablation: anti-echo overreach

An earlier G1b variant enforced an aggressive one-per-evidence-family cap. Mean recall fell to `0.5375`.

This is a useful architecture correction:

> **Evidence ancestry and retrieval diversity are not the same problem.**

The system must avoid double-counting descendants as independent support while still allowing multiple descendants when they provide distinct functional information.

## 8. FRANK architecture feedback

Primary integration remains `M.MEMORY_FABRIC`.

New candidate components:

- `OP.MEMORY_PLAN` — classify retrieval need/budget;
- `OP.MEMORY_ASSEMBLE` — hybrid seeds + bounded qualified traversal;
- `OP.MEMORY_EXACT_VALIDATE` — validate exact/current claims against authoritative anchors.

`S.ACTIVE_ASSEMBLY` gains query-plan, evidence-family, conflict, exact-anchor and stop-reason fields.

Explicit non-changes:

- `M.DURABLE_EVENT_STATE` remains exact authority;
- `S.COGNITIVE_FRAME` remains causal snapshot/consistency contract;
- `M.WORKSPACE_ARBITER` owns GWT selection; graph activation is not ignition;
- `M.CAPABILITY_GATEWAY/K0` remain effect authority.

## 9. Database migration

No new live store evidence exists, so Cycle 2 does not advance physical migration.

Current provisional dispositions remain:

- `consciousness.db` → `PROJECT`;
- `world_experience.db` → `PROJECT`;
- Thalamus current store → `DEFER`;
- Titan/Ego current store → `DEFER`;
- invariant/safety authority if current → prefer `KEEP_ISOLATED`;
- unresolved current stores → `DEFER/UNKNOWN`;
- **MERGE → none**.

Retrieval quality and physical persistence topology are explicitly separate decisions.

## 10. Cross-branch deltas

- **Clay:** extend adaptive semantic resolution to retrieval-planning resolution; hard family cap is a new negative result.
- **FRANK:** test AssemblyPlanner inside memory fabric, not authority fabric.
- **ClayCode:** represent plans/certificates/evidence-family lineage and exact-anchor obligations.
- **Hyperposition:** distinguish query-conditioned active traversal topology from semantic dependency and physical topology.
- **GWT:** factorially separate graph assembly from workspace competition/selection.
- **Emergence:** `NO_CHANGE`; memory/retrieval improvements remain functional and do not satisfy emergence/consciousness criteria.
- **ClayGraph:** G1b becomes preferred HOLD candidate; accepted generation remains 0.

## 11. Highest-information next gates

1. Run current repository candidate pool through deterministic envelope vs BM25/FTS vs G0 vs G1 vs G1b.
2. Create an independently grounded >=50-query gold set spanning exact, historical, stale/conflict, contradiction and true multihop queries.
3. Measure actual ClayGraph extraction errors/edge confidence and replay the relevance-gate stress test.
4. Run Qwen3-4B matched-context downstream answer-quality factorial when target inference is available.
5. Inject stale graph assemblies against fresh FRANK CognitiveFrames; exact-anchor validation must reject/refresh them.
6. Run graph-relation-shuffled and temporal-shuffled memory lesions before GWT arbitration.
7. Complete read-only 71-store inventory and shadow parity/replay/p99/crash/privacy gates.
8. Measure AssemblyPlan/Certificate overhead and whether it reduces debugging/recovery cost.

## 12. Evolution decision

**HOLD.**

Cycle 2 materially improves the candidate's architecture and adversarial robustness, but the evolutionary gate is not satisfied. `research_entity/claygraph/CLAYGRAPH_LATEST.claycode.json` remains generation 0.

The most important new conclusion is not that ClayGraph should spread farther. It is the opposite:

> **ClayGraph should learn when not to traverse.**

Exact questions should route to exact truth. Ordinary association should remain local. Multi-hop should be earned by the query. Negative/stale material should surface when the task asks for audit or contradiction. Shared ancestry should lower evidential independence without erasing useful descendants. And the runtime deterministic packet envelope should remain available until ClayGraph beats it on the real corpus rather than a designed proxy.
