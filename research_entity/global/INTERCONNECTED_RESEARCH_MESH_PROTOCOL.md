# RAE Interconnected Research Mesh Protocol

## Core rule

No reserved scientific trigger is an isolated research silo. Every run MUST begin from the current cross-trigger research mesh and MUST return its durable deltas to that mesh.

The authoritative scientific branches are the branches registered as `domain_research` or `integrated_research_foundry` in `research_entity/global/RESEARCH_TRIGGER_REGISTRY.json`. At the current registry revision they are:

- `clay` — integrated Synthetic Clay foundry / master synthesis
- `frank` — FRANK whole-system cognitive/runtime architecture
- `gwt` — Global Workspace mechanisms and causal closure
- `emergenz` — emergence measurement and intervention
- `claycode` — semantic IR / internal language / self-representation
- `hyperposition` — contextual alternatives, higher-order codependencies and dynamic topology
- `claygraph` — XENO/Synthetic-Clay knowledge graph, associative memory substrate and graph/database-migration research
- `unifieddb` — Unified Database / unified Clay-native persistence, query, transaction, retrieval and state substrate research

`dump` is an intake/fusion command rather than a peer scientific branch. `fusion` is the global meta-research feedback loop rather than a ninth scientific silo.

The registry is authoritative for branch membership. `tools/research_interconnect_preflight.py` must fail closed if its explicit branch priorities no longer cover exactly the registered scientific branch set. Governance drift must be surfaced, never silently resolved by using a stale branch list.

The FRANK↔ClayCode feedback edge additionally uses `research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md` so recursive agreement cannot manufacture evidential confidence.

## Fixed FRANK Clay-native target

All eight scientific branches MUST treat `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md` as a project-owner architecture directive, not as a hypothesis requiring repeated re-approval.

The target FRANK is Clay-native across model thought/generated symbolic language, memory, state, values/vector semantics, architecture IR, GWT/Assemblies, Hyperposition and internal semantic communication. Clay/ClayCode is the target semantic source of truth. ClayGraph is the specialist associative graph/memory substrate. UnifiedDB is the specialist whole-system persistence/query/transaction substrate. Both remain subject to measured safety/performance constraints.

Needle is the sole intentionally retained non-Clay semantic subsystem. It remains a fully used fast classifier/router. Needle output is converted into typed provenance-bound Clay input and never becomes execution authority by itself.

Research MAY falsify proposed benefits, training recipes, representations, migration strategies, latency assumptions, memory mechanisms or safety mechanisms inside this fixed target. It MUST NOT silently convert the owner-fixed Clay-native target itself back into an open yes/no hypothesis.

Physical implementation encodings such as neural tensors, KV caches, numeric arrays, machine code, filesystem formats and database pages need not be literal Clay text. Where they cross a semantic boundary, their meaning/provenance must be represented by Clay-native typed contracts rather than an independent competing semantic architecture.

## ClayGraph / UnifiedDB boundary

The two database-related branches are connected but not duplicates:

- `claygraph` researches associative graph memory, graph topology, relation identity, activation/spreading, graph epochs, Assemblies, graph self-use and migration of graph/state stores;
- `unifieddb` researches whether all FRANK data classes can share one logical semantic identity/query/transaction plane, how exact/event/temporal/relational/graph/vector/FTS/activation/effect data interact, and whether any of those stores should physically consolidate.

UnifiedDB MUST distinguish **semantic unification**, **logical API/query unification** and **physical storage merge**. `KEEP_ISOLATED` remains a valid evidence-based outcome. ClayGraph MUST not claim whole-database unification merely from graph-retrieval success. UnifiedDB MUST not erase graph-specific higher-order semantics merely to simplify storage.

## Mandatory preflight

Before Fusion 1, every scientific research trigger MUST:

1. identify the newest material from every registered scientific branch, including fresh/in-progress artifacts newer than the latest final report;
2. load relevant final reports, hypotheses, experiments, negative results, architecture deltas, Topic Packets and micro-packets;
3. preserve evidence status and provenance — synthetic/proxy evidence never becomes live evidence through reuse;
4. identify cross-branch dependencies, contradictions, duplicate hypotheses, equivalent mechanisms and unresolved interfaces;
5. materialize `INTERCONNECT_MANIFEST.json`;
6. cite that manifest in the run manifest/final report.

A run that omits a registered branch or the preflight is incomplete and cannot strongly promote architecture/scientific claims.

`fusion`, `claygraph` and `unifieddb` are coverage-first. They index all discovered branch history/material before loading raw evidence on demand.

## Branch dependency priorities

All branches ingest every other registered scientific branch. Priority controls depth, not inclusion.

### `fusion`

Coverage-first across all eight branches. It must write one `BRANCH_FEEDBACK_MANIFEST.json` receipt for each of:
`clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`.

### `clay`

Clay is the integrated master foundry and must jointly fuse all eight branches. It is responsible for detecting incompatible local optimizations between architecture, language, graph memory, unified persistence, workspace, emergence and topology research.

### `frank`

Mandatory priority:

`clay -> claycode -> claygraph -> unifieddb -> gwt -> hyperposition -> emergenz -> frank history`

Clay is the primary scientific/architectural foundation. ClayCode is the primary architecture/implementation IR. ClayGraph is the deep associative memory/graph foundation. UnifiedDB is the deep persistence/query/transaction foundation.

Every FRANK run MUST deeply ingest the newest completed and in-progress ClayGraph and UnifiedDB research, including current architecture candidates, inventories, migration results, negative results and explicit FRANK feedback. A FRANK architecture that ignores a newer substrate branch is invalid unless it records why that evidence is inapplicable or superseded.

The architecture source artifact remains `FRANK_ARCHITECTURE.claycode.json`; ClayGraph/UnifiedDB findings must be represented as ClayCode state contracts, relations, persistence/query/migration semantics and module boundaries where applicable.

### `claycode`

Mandatory priority:

`frank -> clay -> claygraph -> unifieddb -> gwt -> hyperposition -> emergenz -> claycode history`

ClayCode treats newest FRANK architecture/runtime research as primary target feedback and must apply the Goodman anti-echo protocol to materially imported FRANK assumptions.

ClayCode MUST deeply ingest ClayGraph and UnifiedDB because it must represent typed entities/relations, graph assemblies, provenance, temporal/conflict states, query/transaction semantics, migration/replay boundaries and database operations. Missing language primitives exposed by either substrate branch must be tested and integrated/refuted rather than treated as external storage details.

### `hyperposition`

Mandatory priority:

`clay -> claygraph -> unifieddb -> frank -> claycode -> gwt -> emergenz -> hyperposition history`

Hyperposition must test how semantic, coordination and physical topology interact with both graph epochs and unified logical/physical database layouts. Topology results that improve or falsify ClayGraph or UnifiedDB assumptions must be written back to those branches.

### `gwt`

Mandatory priority:

`clay -> claygraph -> unifieddb -> frank -> emergenz -> hyperposition -> claycode -> gwt history`

GWT must distinguish graph propagation, database/query selection, workspace competition/selection, projection/reconstruction, uptake, outcome and re-entry. Database or graph selection changes must not be mistaken for genuine workspace effects.

### `emergenz`

Must use Clay architecture, GWT intervention surfaces, ClayGraph relational/activation substrate, UnifiedDB state/query instrumentation, Hyperposition higher-order structure, FRANK runtime observability and ClayCode causal/provenance representations. Database integration alone is never emergence/consciousness evidence.

### `claygraph`

Mandatory priority:

`clay -> frank -> claycode -> unifieddb -> hyperposition -> gwt -> emergenz -> claygraph history`

ClayGraph is iterative. Every run starts from the current accepted graph version, covers all current research, builds a candidate, self-uses/benchmarks it against retrieval baselines, performs regression/ablation tests and promotes or rejects the candidate. It must exchange explicit store-role, query-routing and migration constraints with UnifiedDB.

Every completed ClayGraph run writes explicit feedback especially to FRANK and to every other branch materially affected by its result.

### `unifieddb`

Mandatory priority:

`clay -> frank -> claycode -> claygraph -> hyperposition -> gwt -> emergenz -> unifieddb history`

UnifiedDB is iterative and coverage-first. Every run must inventory current stores/data classes/authority roles; compare specialized-store baseline vs logically unified interface vs hybrid canonical-store/derived-sidecars vs physical consolidation where feasible; test correctness/replay/snapshot consistency, query equivalence, selection integrity, latency/amplification, crash/recovery and migration rollback; and explicitly classify each physical store decision as `KEEP_ISOLATED`, `UNIFY_LOGICALLY`, `COLOCATE_PHYSICALLY` or another justified hybrid.

Every completed UnifiedDB run writes explicit feedback to FRANK, ClayCode and ClayGraph and to every other materially affected branch.

## Cross-branch contradiction and anti-echo gate

Before final synthesis, every run MUST scan for:

- a new result contradicting an active hypothesis in another branch;
- a local optimization worsening another branch's hard constraint;
- duplicated concepts with different names;
- identical concepts with incompatible evidence status;
- representation claims mistaken for mechanism claims;
- architecture claims depending on synthetic evidence as though live;
- stale conclusions superseded by a newer run;
- apparent multi-branch agreement that collapses to shared evidence ancestry;
- ClayGraph activation/retrieval success being mistaken for independent evidence for retrieved content;
- UnifiedDB logical unification being mistaken for evidence that physical merge is beneficial;
- record provenance being mistaken for selection/query-plan integrity.

Contradictions are retained, not averaged away.

## Mesh write-back

Every durable result should carry originating trigger/run, affected branches, evidence class/status, upstream dependencies, ancestry family, contradictions/supersessions and downstream architecture/experiment implications.

Create cross-links in Topic Packets/micro-packets where practical. A branch-specific result may remain local in confidence, but it must remain discoverable by all affected branches.

For `fusion`, write-back is mandatory for all eight scientific branches. For `claygraph`, FRANK feedback is mandatory plus affected-branch feedback/NO_CHANGE. For `unifieddb`, FRANK + ClayCode + ClayGraph feedback is mandatory plus affected-branch feedback/NO_CHANGE.

## Scientific boundaries

Interconnection increases information flow, not evidence strength. Repetition across branches from one underlying source/experiment is not independent replication. Graph connectivity, unified persistence, associative memory, GWT, emergence, self-reference or architectural sophistication do not by themselves establish phenomenal consciousness.
