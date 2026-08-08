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
- `claygraph` — XENO/Synthetic-Clay knowledge graph, associative memory substrate and database/state-store migration research

`dump` is an intake/fusion command rather than a peer scientific branch. `fusion` is the global meta-research feedback loop rather than an eighth scientific silo.

The registry is authoritative for branch membership. `tools/research_interconnect_preflight.py` must fail closed if its explicit branch priorities no longer cover exactly the registered scientific branch set. Governance drift must be surfaced, never silently resolved by using a stale six-branch list.

The FRANK↔ClayCode feedback edge additionally uses `research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md` so recursive agreement cannot manufacture evidential confidence.

## Fixed FRANK Clay-native target

All seven scientific branches MUST treat `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md` as a project-owner architecture directive, not as a hypothesis requiring repeated re-approval.

The target FRANK is Clay-native across model thought/generated symbolic language, memory, state, values/vector semantics, architecture IR, GWT/Assemblies, Hyperposition and internal semantic communication. Clay/ClayCode is the target semantic source of truth and ClayGraph is the target persistent semantic memory/knowledge substrate subject to measured safety/performance constraints.

Needle is the sole intentionally retained non-Clay semantic subsystem. It remains a fully used fast classifier/router. Needle output is converted into typed provenance-bound Clay input and never becomes execution authority by itself.

Research MAY falsify proposed benefits, training recipes, representations, migration strategies, latency assumptions, memory mechanisms or safety mechanisms inside this fixed target. It MUST NOT silently convert the owner-fixed Clay-native target itself back into an open yes/no hypothesis.

Physical implementation encodings such as neural tensors, KV caches, numeric arrays, machine code, filesystem formats and database pages need not be literal Clay text. Where they cross a semantic boundary, their meaning/provenance must be represented by Clay-native typed contracts rather than an independent competing semantic architecture.

## Mandatory preflight

Before Fusion 1, every scientific research trigger MUST:

1. identify the newest material from every registered scientific branch, including fresh/in-progress artifacts newer than the latest final report;
2. load relevant final reports, hypotheses, experiments, negative results, architecture deltas, Topic Packets and micro-packets;
3. preserve evidence status and provenance — synthetic/proxy evidence never becomes live evidence through reuse;
4. identify cross-branch dependencies, contradictions, duplicate hypotheses, equivalent mechanisms and unresolved interfaces;
5. materialize `INTERCONNECT_MANIFEST.json`;
6. cite that manifest in the run manifest/final report.

A run that omits a registered branch or the preflight is incomplete and cannot strongly promote architecture/scientific claims.

`fusion` and `claygraph` are coverage-first. They index all discovered branch history/material before loading raw evidence on demand.

## Branch dependency priorities

All branches ingest every other registered scientific branch. Priority controls depth, not inclusion.

### `fusion`

Coverage-first across all seven branches. It must write one `BRANCH_FEEDBACK_MANIFEST.json` receipt for each of:
`clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`.

### `clay`

Clay is the integrated master foundry and must jointly fuse all seven branches. It is responsible for detecting incompatible local optimizations between architecture, language, memory substrate, workspace, emergence and topology research.

### `frank`

Mandatory priority:

`clay -> claycode -> claygraph -> gwt -> hyperposition -> emergenz -> frank history`

Clay is the primary scientific/architectural foundation. ClayCode is the primary architecture/implementation IR. ClayGraph is the deep memory/state/database-substrate foundation.

Every FRANK run MUST deeply ingest the newest completed and in-progress ClayGraph research, including the accepted/latest graph candidate when present, self-use benchmarks, database inventory/migration results, negative results and `FRANK_CLAYGRAPH_FEEDBACK.json`. A FRANK architecture that ignores newer ClayGraph substrate evidence is invalid unless it explicitly records why that evidence is inapplicable or superseded.

The architecture source artifact remains `FRANK_ARCHITECTURE.claycode.json`; ClayGraph findings must be represented as ClayCode state contracts, relations, persistence/migration semantics and module boundaries where applicable.

### `claycode`

Mandatory priority:

`frank -> clay -> claygraph -> gwt -> hyperposition -> emergenz -> claycode history`

ClayCode treats newest FRANK architecture/runtime research as primary target feedback and must apply the Goodman anti-echo protocol to materially imported FRANK assumptions.

Every ClayCode run MUST also deeply ingest current ClayGraph research because ClayCode must be able to represent and execute the graph's typed entities/relations, activation assemblies, provenance, temporal/conflict states, migration semantics, replay boundaries and graph operations. If ClayGraph exposes a missing primitive or invalidates a ClayCode assumption, ClayCode must test and integrate/refute that requirement rather than treating the graph as an external storage detail.

### `hyperposition`

Mandatory priority:

`clay -> claygraph -> frank -> claycode -> gwt -> emergenz -> hyperposition history`

Every Hyperposition run MUST deeply ingest current ClayGraph architecture and experiments. It must test whether higher-order codependencies, contextual alternatives and dynamic topology are represented correctly in the graph, whether n-ary relations add information beyond pairwise projections, and how spreading activation/incremental recomputation interact with conflict, uncertainty, locality and overcoupling.

Hyperposition results that improve or falsify ClayGraph topology/activation assumptions must be written back to ClayGraph as branch-discoverable deltas.

### `gwt`

Mandatory priority:

`clay -> claygraph -> frank -> emergenz -> hyperposition -> claycode -> gwt history`

Every GWT run MUST deeply ingest current ClayGraph research. It must examine whether candidate generation, ignition, broadcast, reconstruction, outcome and re-entry can operate over ClayGraph assemblies/relations, and whether graph activation is a useful substrate or a confound for workspace causality. GWT experiments should distinguish graph propagation from genuine workspace selection/broadcast effects.

GWT findings that alter assembly selection, salience, receipt/re-entry or causal episode semantics must be written back to ClayGraph.

### `emergenz`

Must use Clay architecture, GWT intervention surfaces, ClayGraph relational/activation substrate, Hyperposition higher-order structure, FRANK runtime observability and ClayCode causal/provenance representations.

### `claygraph`

Mandatory priority:

`clay -> frank -> claycode -> hyperposition -> gwt -> emergenz -> claygraph history`

ClayGraph is iterative. Every run starts from the current accepted graph version, covers all current research, builds a candidate, self-uses/benchmarks it against retrieval baselines, performs regression/ablation tests and promotes or rejects the candidate. It must never assume that all databases should physically merge; `KEEP_ISOLATED` is a valid evidence-based outcome.

Every completed ClayGraph run writes explicit feedback especially to FRANK and to every other branch materially affected by its result.

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
- ClayGraph activation/retrieval success being mistaken for independent evidence for the content retrieved.

Contradictions are retained, not averaged away.

## Mesh write-back

Every durable result should carry originating trigger/run, affected branches, evidence class/status, upstream dependencies, ancestry family, contradictions/supersessions and downstream architecture/experiment implications.

Create cross-links in Topic Packets/micro-packets where practical. A branch-specific result may remain local in confidence, but it must remain discoverable by all affected branches.

For `fusion`, write-back is mandatory for all seven scientific branches. For `claygraph`, FRANK feedback is mandatory and all materially affected branches require feedback or explicit `NO_CHANGE`.

## Scientific boundaries

Interconnection increases information flow, not evidence strength. Repetition across branches from one underlying source/experiment is not independent replication. Graph connectivity, associative memory, GWT, emergence, self-reference or architectural sophistication do not by themselves establish phenomenal consciousness.
