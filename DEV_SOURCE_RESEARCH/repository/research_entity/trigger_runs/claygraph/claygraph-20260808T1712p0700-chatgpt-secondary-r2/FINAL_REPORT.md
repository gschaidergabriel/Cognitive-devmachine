# CLAYGRAPH RESEARCH RUN — Cycle 4 · G1d Epochal Latent Field

**run_id:** `claygraph-20260808T1712p0700-chatgpt-secondary-r2`  
**trigger:** `claygraph`  
**actor:** `chatgpt-secondary`  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**accepted ClayGraph:** generation 0 `claygraph-v0-seed`  
**research predecessor:** G1c resident adaptive escalation  
**cycle-4 candidate:** G1d `claygraph-g1d-epochal-latent-field`  
**decision:** **HOLD** — accepted graph remains G0.

## Executive synthesis

Cycle 4 began only minutes after Cycle 3 and found no newer repository research commits at trigger start. It therefore does not manufacture novelty by rereading the same mesh. Instead it uses the project owner's supplied older research as a historical recovery source and attacks the next untested G1c mechanism: update consistency and between-LLM memory dynamics.

The historical material contains an important architecture thread that survived later evidence: Synthetic Clay was not originally intended to be merely a faster graph retriever. The stronger proposal was that memory can remain latently active and influence what becomes thinkable next before the model explicitly chooses a memory-search action. The older XENO/ClayCode migration material already separated persistent truth, ephemeral activation, temporary Assembly membership and real effects; it proposed incremental relation/materialized views before an activation field with budget/inhibition and an Assembly compiler.

Cycle 3 solved a different problem: current ClayGraph graph retrieval was too slow/noisy for the default hot path, so G1c introduced resident indexes and adaptive escalation. Cycle 4 combines both lines rather than choosing one:

`authoritative exact/event state`
`-> validated immutable semantic graph epoch`
`-> small delta overlays / adaptive compaction`
`-> sparse event-driven latent activation field`
`-> epoch-pinned bounded Assembly`
`-> optional relational graph escalation/rerank`
`-> exact-anchor validation`
`-> FRANK memory/workspace candidate`

The graph is therefore both **resident relation space** and **latent associative substrate**, while expensive traversal remains conditional.

## 1. Historical recovery

Three older project sources were reopened.

### Memory-transcendence concept
The older memory design distinguishes a small active Assembly from a much larger latent relational network and proposes cue-triggered coactivation. The important surviving idea is that the agent should not always need to know that it ought to search memory; the persistent state may already bias which memory becomes available next.

### XENO -> ClayCode migration
The migration document explicitly required canonical Store/Ledger truth, bitemporal history, physically plural storage behind one logical world, incremental relation/materialized views, activation field + budget/inhibition and then Assembly compilation. It also required shadow/dual-observe/dual-write migration and replayable rollback.

### ClayCode RC1.1
The manual separates four lifecycles: persistent world/history, ephemeral activation, temporary Assembly membership and authorized real effects. `ACTIVATE/INHIBIT` alter salience only. Decay, saturation, budget and coarse-to-fine expansion are runtime candidates; fast processes may update activation continuously while slow model transforms are selected.

These documents are one inherited evidence family. Their recurrence does not count as independent replication. Retired XENO compression/motif claims remain retired.

## 2. Why G1c needed another delta

G1c correctly concluded that current graph activation should not be the universal query hot path. But a pure query-router interpretation risks regressing the original Clay goal back toward conventional retrieval:

`query -> decide whether to search graph -> retrieve -> prompt`.

G1d adds an orthogonal fast state:

`event/state change -> cheap local latent activation update -> no LLM -> later Assembly formation`.

The model-visible Assembly remains bounded and can still choose not to traverse the graph. Thus continuous memory influence and conditional expensive retrieval are compatible.

## 3. Semantic epochs

A resident graph introduces a new consistency problem: while the projector updates relations, readers must not observe a half-old/half-new semantic world.

G1d therefore makes the resident semantic index epochal:

- immutable base epoch;
- immutable addition/removal/status delta overlay;
- provenance/integrity validation before publish;
- atomic current-epoch publish;
- pinned readers/Assemblies remain on one graph epoch;
- old epochs remain replayable until no reader requires them;
- failed/unknown delta validation leaves the previous epoch current;
- direct authoritative-store fallback remains available.

The exact implementation may use RCU/MVCC/copy-on-write or another mechanism. Those are implementation choices; the semantic invariant is single-epoch visibility.

## 4. Delta overlay vs rebuild experiment

A local synthetic proxy used 30,000 nodes, a 6,000-token vocabulary and 8 tokens/node. Changed-node batches ranged from 0.01% to 20%. An immutable base + add/remove overlay was compared with rebuilding the inverted index.

Selected results:

| Changed nodes | Delta publish | Full rebuild | Delta query median | Rebuilt query median |
|---:|---:|---:|---:|---:|
| 0.1% / 30 | 0.119 ms | 26.512 ms | 5.938 us | 3.228 us |
| 1% / 300 | 1.469 ms | 24.722 ms | 8.708 us | 3.467 us |
| 5% / 1,500 | 8.971 ms | 27.644 ms | 13.037 us | 3.870 us |
| 10% / 3,000 | 15.459 ms | 25.674 ms | 14.635 us | 4.150 us |
| 20% / 6,000 | 32.971 ms | 26.875 ms | 16.178 us | 4.479 us |

Across 300 random queries per condition, the overlay and rebuilt index had zero result mismatches.

The result rejects **always incremental** as a universal rule. Small deltas are dramatically cheaper to publish, but overlay query tax and memory grow. In this proxy a 10% update's publication saving was amortized away after roughly 974 later queries; at 20% the rebuild was already cheaper at update time. Therefore compaction must use measured workload: changed fraction, overlay size, read count before next update, query tax, rebuild cost, memory and integrity risk.

These are Python-structure timings, not FRANK estimates.

## 5. Epoch snapshot proxy

A 3% update batch was represented as a new immutable overlay epoch. 1,000 random queries were executed against both a pinned old epoch and the new epoch. The old epoch remained equal to the old base and the new epoch remained equal to a fully rebuilt reference: zero mismatches in both comparisons.

This demonstrates the semantic shape of the solution, not real concurrent-process/crash safety. Actual publication/reclamation must still be stress-tested.

## 6. Latent activation experiment

To test whether the older idea of a continuously changing associative field necessarily creates a heavy loop, a 30,000-node synthetic graph with degree 10 received 500 events, three seeds per event, one-hop neighbor gain 0.35 and decay 0.94.

Two implementations were compared:

- **eager dense decay:** touch all 30k salience values each event — median **1.098 ms**, p95 **7.500 ms**;
- **lazy touched-node decay:** timestamp decay only seeds/neighborhood plus bounded cleanup — median **0.0280 ms**, p95 **0.286 ms**.

The final lazy active set contained 1,562 nodes, about 5.2% of the graph.

This is the strongest Cycle-4 mechanism result: continuous associative state does not logically require global continuous graph traversal. A sparse field can update locally between LLM calls. But the experiment does **not** show that the field improves cognition; it only supports implementation feasibility.

## 7. External research synthesis

Current research independently supports the individual design pressures:

- SYNAPSE (2026) combines graph memory with spreading activation, lateral inhibition and temporal decay and reports gains on complex temporal/multi-hop memory tasks.
- The 2026 graph-agent-memory survey treats extraction, storage, retrieval and memory evolution as separate lifecycle problems rather than collapsing memory to retrieval.
- DeltaMem (2026) represents repeated experience as incremental residual deltas and consolidates high-frequency paths, independently supporting delta/consolidation as a memory design pattern.
- Work on short-term-to-long-term KG transfer (2026) shows that explicit selective memory retention can outperform indiscriminate insertion under constrained memory.
- A 2026 bitemporal graph-memory system explicitly keeps immutable memory identity plus valid/transaction time and reports different retrieval strengths/failures across question types.
- Older incremental graph-view work establishes the general systems principle that affected-region maintenance can avoid full recomputation when updates are local.

None of these proves G1d or FRANK transfer. They reduce the risk that the design is purely project-internal intuition.

## 8. G1d architecture

### Exact truth
Authoritative event/state stores remain exact. Graph epochs are rebuildable projections.

### Semantic base + delta epochs
The current graph is a validated immutable view. Small changes may publish as overlays; large/read-heavy overlays compact to a new base according to measured cost.

### Latent activation field
Fast events/goals/self-state/workspace outcomes may update sparse salience without invoking the LLM. Activation uses lazy decay, bounded propagation, inhibition/saturation and hard budgets. It cannot change evidence status, invent edges or mint capabilities.

### Assembly compiler
When a model-facing cognitive cycle occurs, the Assembly freezes:

`graph_epoch_id + activation_epoch_id + CognitiveFrame/basis_frame_id`.

It then selects bounded roots/assertions/conflicts/evidence families and exact anchors. This makes memory influence causally inspectable and prevents one answer from silently spanning incompatible graph revisions.

### Graph escalation
Graph traversal remains conditional. Exact/local facts use cheaper paths; associative/multihop questions can exploit the latent field as a seed prior and escalate relationally when needed.

## 9. FRANK feedback

`M.MEMORY_FABRIC` should experimentally add:

- `M.MEMORY_SEMANTIC_EPOCHS`;
- `M.MEMORY_LATENT_FIELD`;
- `OP.MEMORY_EPOCH_PUBLISH`;
- `OP.MEMORY_FIELD_UPDATE`;
- `OP.MEMORY_ASSEMBLY_COMPILE`;
- optional `OP.MEMORY_GRAPH_ESCALATE`;
- `OP.MEMORY_EXACT_VALIDATE`.

Proposed event path:

`authoritative event -> projector -> validated graph epoch -> latent field update -> later trigger -> Assembly compile -> optional graph escalation -> exact validation -> workspace candidate`.

Hard non-changes: Durable Event State remains authority; CognitiveFrame remains the current causal contract; GWT owns competition/ignition; activation is not ignition; K0/Capability Gateway owns external effects.

## 10. Migration

No new live store enumeration exists. The 71-store physical migration remains unchanged:

- `consciousness.db` -> PROJECT;
- `world_experience.db` -> PROJECT;
- Thalamus/Titan-Ego -> DEFER;
- safety/invariant authority if current -> KEEP_ISOLATED preferred;
- unresolved stores -> UNKNOWN/DEFER;
- MERGE -> none.

Cycle 4 adds shadow phases for base epoch, delta projector and latent field before any model visibility or read cutover.

## 11. Highest-information next experiment

The decisive next test is no longer merely retrieval quality. It is the original Clay hypothesis in causal form:

**no latent field vs truthful latent field vs relation-shuffled/temporal-shuffled latent field**, with final visible facts, token count and order matched at the model boundary.

Use events specifically selected so a query-only agent may fail to initiate a memory lookup. Measure operation/answer quality, recall, false association, latency, Assembly size and whether a previously latent relation changes the selected next action. Repeat on target 4B and a larger model to test the predicted small-model interaction.

Separately, implement actual graph epochs and stress concurrent publish/read/crash/replay before any FRANK integration.

## 12. Decision

**HOLD.** G1d is the preferred research candidate but does not replace `CLAYGRAPH_LATEST`.

Cycle 4's main contribution is conceptual and mechanistic:

> **ClayGraph should not force the AI to query memory on every thought. A cheap, sparse latent field can let committed events continuously reshape what is likely to enter the next Assembly, while immutable semantic epochs and exact anchors keep that changing salience from becoming changing truth.**

This recovers the strongest older Synthetic Clay intuition while remaining compatible with the newer negative result that current graph activation is not ready as a universal hot-path retriever.