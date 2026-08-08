# RAE Interconnected Research Mesh Protocol

## Core rule

No reserved scientific/research-center trigger is an isolated silo. Every run MUST begin from the current cross-trigger research mesh and MUST return its durable deltas to that mesh.

The authoritative peer branches are the branches registered as `domain_research` or `integrated_research_foundry` in `research_entity/global/RESEARCH_TRIGGER_REGISTRY.json`. At the current registry revision they are:

- `clay` — integrated Synthetic Clay foundry / master synthesis
- `frank` — FRANK whole-system cognitive/runtime architecture
- `gwt` — Global Workspace mechanisms and causal closure
- `emergenz` — emergence measurement and intervention
- `claycode` — semantic IR / internal language / self-representation
- `hyperposition` — contextual alternatives, higher-order codependencies and dynamic topology
- `claygraph` — XENO/Synthetic-Clay knowledge graph, associative memory substrate and graph/database-migration research
- `unifieddb` — Unified Database / unified Clay-native persistence, query, transaction, retrieval and state substrate research
- `harness` — executable FRANK convergence/integration/simulation, validation, ablation and falsification branch

`dump` is an intake/fusion command rather than a peer branch. `fusion` and `hypofusion` are global meta-research loops rather than peer silos.

The registry is authoritative for branch membership. `tools/research_interconnect_preflight.py` must fail closed if its explicit branch priorities no longer cover exactly the registered peer branch set. Governance drift must be surfaced, never silently resolved by using a stale branch list.

The FRANK↔ClayCode feedback edge additionally uses `research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md` so recursive agreement cannot manufacture evidential confidence. Harness execution of inherited FRANK/ClayCode assumptions also remains shared-ancestry evidence unless the test itself adds an independent discriminating intervention.

## Fixed FRANK Clay-native target

All nine peer branches MUST treat `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md` as a project-owner architecture directive, not as a hypothesis requiring repeated re-approval.

The target FRANK is Clay-native across model thought/generated symbolic language, memory, state, values/vector semantics, architecture IR, GWT/Assemblies, Hyperposition and internal semantic communication. Clay/ClayCode is the target semantic source of truth. ClayGraph is the specialist associative graph/memory substrate. UnifiedDB is the specialist whole-system persistence/query/transaction substrate. Harness is the specialist executable convergence layer that realizes and tests the current architecture without becoming an alternative semantic architecture.

Needle is the sole intentionally retained non-Clay semantic subsystem. It remains a fully used fast classifier/router according to the current FRANK/project contract. Human-language translation is outside the Clay-native model cognition boundary. Needle output is converted into typed provenance-bound Clay input and never becomes execution authority by itself.

Research MAY falsify proposed benefits, training recipes, representations, migration strategies, latency assumptions, memory mechanisms or safety mechanisms inside this fixed target. It MUST NOT silently convert the owner-fixed Clay-native target itself back into an open yes/no hypothesis.

Physical implementation encodings such as neural tensors, KV caches, numeric arrays, machine code, filesystem formats and database pages need not be literal Clay text. Where they cross a semantic boundary, their meaning/provenance must be represented by Clay-native typed contracts rather than an independent competing semantic architecture.

## Harness role and boundary

Harness is a full research-center member, but its special job is executable convergence.

It MUST:

- ingest every peer branch and fresh in-progress material;
- ingest live Harness workers before claiming work;
- implement the current compatible architecture rather than replace it with a mega-prompt;
- run parser/compiler/runtime/simulation/replay/ablation/fuzz/mutation/recovery/performance experiments;
- preserve implementation failures and counterexamples as research evidence;
- return feedback to all affected branches;
- distinguish inherited/shared-ancestry agreement from independent replication;
- pin exact architecture/artifact hashes at Test-1 release freeze.

Harness does not get epistemic priority merely because code executes. Synthetic or simulated execution remains synthetic/simulated evidence until promoted by the normal evidence gates.

The detailed protocol is `research_entity/triggers/HARNESS_BUILD_PROTOCOL.md`.

## ClayGraph / UnifiedDB boundary

The two database-related branches are connected but not duplicates:

- `claygraph` researches associative graph memory, graph topology, relation identity, activation/spreading, graph epochs, Assemblies, graph self-use and migration of graph/state stores;
- `unifieddb` researches whether all FRANK data classes can share one logical semantic identity/query/transaction plane, how exact/event/temporal/relational/graph/vector/FTS/activation/effect data interact, and whether any of those stores should physically consolidate.

UnifiedDB MUST distinguish **semantic unification**, **logical API/query unification** and **physical storage merge**. `KEEP_ISOLATED` remains a valid evidence-based outcome. ClayGraph MUST not claim whole-database unification merely from graph-retrieval success. UnifiedDB MUST not erase graph-specific higher-order semantics merely to simplify storage.

Harness must preserve this distinction in simulation: a unified semantic/query contract is not permission to fake physical colocation or collapse distinct failure/authority domains.

## Mandatory preflight

Before Fusion 1, every peer research trigger MUST:

1. identify the newest material from every registered peer branch, including fresh/in-progress artifacts newer than the latest final report;
2. load relevant final reports, hypotheses, experiments, negative results, architecture deltas, Topic Packets and micro-packets;
3. preserve evidence status and provenance — synthetic/proxy evidence never becomes live evidence through reuse;
4. identify cross-branch dependencies, contradictions, duplicate hypotheses, equivalent mechanisms and unresolved interfaces;
5. materialize `INTERCONNECT_MANIFEST.json`;
6. cite that manifest in the run manifest/final report.

A run that omits a registered branch or the preflight is incomplete and cannot strongly promote architecture/scientific claims.

`fusion`, `claygraph`, `unifieddb` and `harness` are coverage-first. Harness additionally reads live worker claims/receipts and recent commits because its correctness depends on current implementation state.

## Branch dependency priorities

All branches ingest every other registered peer branch. Priority controls depth, not inclusion.

### `fusion`

Coverage-first across all nine peer branches. It must write one `BRANCH_FEEDBACK_MANIFEST.json` receipt for each of:
`clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`, `harness`.

### `clay`

Clay is the integrated master foundry and must jointly fuse all nine peer branches. It is responsible for detecting incompatible local optimizations between architecture, language, graph memory, unified persistence, workspace, emergence, topology and executable Harness research.

### `frank`

Mandatory priority:

`clay -> claycode -> harness -> claygraph -> unifieddb -> gwt -> hyperposition -> emergenz -> frank history`

Clay is the primary scientific/architectural foundation. ClayCode is the primary architecture/implementation IR. Harness is the primary executable integration/falsification feedback surface. ClayGraph is the deep associative memory/graph foundation. UnifiedDB is the deep persistence/query/transaction foundation.

Every FRANK run MUST deeply ingest the newest completed and in-progress ClayGraph, UnifiedDB and Harness research, including architecture candidates, inventories, execution/replay results, migration results, negative results and explicit FRANK feedback. A FRANK architecture that ignores a newer substrate/execution branch is invalid unless it records why that evidence is inapplicable or superseded.

The architecture source artifact remains `FRANK_ARCHITECTURE.claycode.json`; findings must be represented as ClayCode state contracts, relations, persistence/query/migration semantics and module boundaries where applicable.

### `claycode`

Mandatory priority:

`frank -> clay -> harness -> claygraph -> unifieddb -> gwt -> hyperposition -> emergenz -> claycode history`

ClayCode treats newest FRANK architecture/runtime research as primary target feedback and must apply the Goodman anti-echo protocol to materially imported FRANK assumptions.

ClayCode MUST deeply ingest Harness compiler/runtime/simulation evidence in addition to ClayGraph and UnifiedDB. Missing language primitives or semantic ambiguities exposed by executable Harness work must be tested and integrated/refuted rather than treated as downstream implementation details.

### `hyperposition`

Mandatory priority:

`clay -> harness -> claygraph -> unifieddb -> frank -> claycode -> gwt -> emergenz -> hyperposition history`

Hyperposition must test how semantic, coordination and physical topology interact with graph epochs, unified logical/physical database layouts and Harness-measured coupling costs. Results that improve or falsify assumptions must be written back.

### `gwt`

Mandatory priority:

`clay -> harness -> claygraph -> unifieddb -> frank -> emergenz -> hyperposition -> claycode -> gwt history`

GWT must distinguish graph propagation, database/query selection, workspace competition/selection, projection/reconstruction, uptake, outcome and re-entry. Harness is the preferred executable intervention/replay surface when available, but simulated receiver effects remain simulated evidence.

### `emergenz`

Must use Clay architecture, GWT intervention surfaces, Harness replay/ablation surfaces, ClayGraph relational/activation substrate, UnifiedDB state/query instrumentation, Hyperposition higher-order structure, FRANK runtime observability and ClayCode causal/provenance representations. Database integration or Harness complexity alone is never emergence/consciousness evidence.

### `claygraph`

Mandatory priority:

`clay -> frank -> claycode -> harness -> unifieddb -> hyperposition -> gwt -> emergenz -> claygraph history`

ClayGraph is iterative. Every run starts from the current accepted graph version, covers all current research, builds a candidate, self-uses/benchmarks it against retrieval baselines, performs regression/ablation tests and promotes or rejects the candidate. It must exchange explicit store-role, query-routing and migration constraints with UnifiedDB and executable retrieval/Assembly counterexamples with Harness.

### `unifieddb`

Mandatory priority:

`clay -> frank -> claycode -> harness -> claygraph -> hyperposition -> gwt -> emergenz -> unifieddb history`

UnifiedDB is iterative and coverage-first. Every run must inventory current stores/data classes/authority roles; compare specialized-store baseline vs logically unified interface vs hybrid canonical-store/derived-sidecars vs physical consolidation where feasible; test correctness/replay/snapshot consistency, query equivalence, selection integrity, latency/amplification, crash/recovery and migration rollback; and explicitly classify physical store decisions. Harness replay/consistency results are a primary executable feedback source.

### `harness`

Mandatory priority:

`frank -> claycode -> clay -> gwt -> claygraph -> unifieddb -> hyperposition -> emergenz -> harness history/live workers`

Harness is coverage-first and execution-first. It MUST know the complete mesh, then materialize the current compatible architecture into executable/simulated state transitions. It must never treat an older FRANK snapshot as complete when later GWT/ClayGraph/ClayCode/etc. overlays materially change the system without an explicit freeze decision.

Harness work packages must coordinate through shared append-only claims/receipts, avoid duplicate work unless replication is intended, cross-read sibling results, execute tests in available sandboxes/CI, and return implementation/scientific feedback to affected branches.

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
- record provenance being mistaken for selection/query-plan integrity;
- Harness execution of a branch-derived oracle being mistaken for independent proof of the oracle;
- a model prompt emulation being mistaken for an externally executed FRANK module/state transition;
- successful replay being mistaken for causal validity without intervention.

Contradictions are retained, not averaged away.

## Mesh write-back

Every durable result should carry originating trigger/run, affected branches, evidence class/status, upstream dependencies, ancestry family, contradictions/supersessions and downstream architecture/experiment implications.

Create cross-links in Topic Packets/micro-packets where practical. A branch-specific result may remain local in confidence, but it must remain discoverable by all affected branches.

For `fusion`, write-back is mandatory for all nine peer branches. For `claygraph`, FRANK feedback is mandatory plus affected-branch feedback/NO_CHANGE. For `unifieddb`, FRANK + ClayCode + ClayGraph + materially affected Harness feedback is mandatory. For `harness`, explicit affected-branch feedback is mandatory for any architecture/compiler/runtime counterexample or validated execution constraint.

## Scientific boundaries

Interconnection increases information flow, not evidence strength. Repetition across branches from one underlying source/experiment is not independent replication. Graph connectivity, unified persistence, associative memory, GWT, emergence, self-reference, Harness executability or architectural sophistication do not by themselves establish phenomenal consciousness.
