# Reserved Trigger: `claygraph`

Research the XENO/Synthetic-Clay knowledge graph, associative memory substrate and migration/transcendence of FRANK's distributed databases/state stores. Use the Master Research Trigger Protocol, Interconnected Research Mesh Protocol, quota/health-aware research-tool orchestration and the scientific boundaries in `research_entity/global/CLAYGRAPH_RESEARCH_FOUNDATION.md`.

## Role in the RAE

`claygraph` is a full scientific branch, not a storage-maintenance command.

Its purpose is to discover whether FRANK can move from many explicitly queried stores toward a persistent relational cognitive substrate where:

- canonical events/state remain exact and replayable;
- semantic relations remain incrementally available;
- current cues activate bounded relevant assemblies;
- self, memory, goals, consequences, conflicts and provenance can participate in one relational state model;
- a small model reasons over active structure instead of repeatedly reconstructing state from scattered text;
- existing databases are migrated only when evidence supports semantic and operational equivalence or improvement.

## Mandatory corpus coverage

A `claygraph` run is coverage-first. Before Fusion 1 it MUST index and synthesize the current research material from **all scientific branches**:

`clay -> frank -> claycode -> hyperposition -> gwt -> emergenz -> claygraph history`

This means coverage of completed and in-progress trigger runs, hypotheses, experiments, negative results, architecture deltas, Topic Packets, micro-packets, contradiction/supersession lineage and relevant source/provenance references. Use indexes/manifests first; load raw evidence on demand where it can change a claim or experiment. Do not attempt to put every byte into one context.

The run must materialize `INTERCONNECT_MANIFEST.json` before Fusion 1 and preserve shared evidence ancestry so cross-branch repetition is not counted as replication.

## Mandatory database/state-store inventory

Every serious ClayGraph architecture/migration run must establish or refresh a machine-readable inventory of the reachable FRANK stores. Materialize:

`DATABASE_INVENTORY.json`

For every database/store/schema where evidence is available record at minimum:

- stable store id/path/service ownership;
- evidence/source/version/timestamp;
- authoritative truth vs derived/cache/projection role;
- entity/state types;
- identity/key semantics;
- temporal/event/replay semantics;
- read/write patterns and latency sensitivity;
- transaction/consistency requirements;
- provenance/causal dependencies;
- retention/forgetting rules;
- capability/privacy/safety boundary;
- failure/recovery behavior;
- candidate ClayGraph mapping;
- migration disposition: `MERGE | PROJECT | LINK | KEEP_ISOLATED | DEFER | UNKNOWN`;
- open falsifier/measurement needed before changing disposition.

Unknown stores or unavailable live data must be recorded as `UNKNOWN/BLOCKED`, never invented.

## Research phases

### CG0 — Boot, mesh and inventory

1. Verify current RAE state and actor/provenance.
2. Run `tools/research_interconnect_preflight.py --trigger claygraph --run-id <run_id>`.
3. Cover the complete current scientific research mesh.
4. Build/refresh `DATABASE_INVENTORY.json` from current FRANK architecture/code/runtime evidence.
5. Identify which stores are currently authoritative versus accidental process/storage boundaries.

### CG1 — Semantic graph model

Research a Clay/XENO graph model able to preserve:

- canonical event/state identity;
- entities and typed relations;
- time/version/epoch;
- provenance and causal lineage;
- unknown/conflict/revoked/stale states;
- assemblies/activation and decay;
- SELF/goal/memory/consequence relationships;
- GWT episode/read/effect/outcome/re-entry receipts;
- ClayCode semantic operation/transition closure;
- Hyperposition alternatives and incompatible states without premature collapse;
- capability/effect authority references without embedding bearer secrets.

Produce `CLAYGRAPH_SCHEMA.claycode.json` as the semantic design source. It is a ClayCode semantic-IR projection, not merely a generic graph JSON dump.

### CG2 — Hypothesis generation

Generate falsifiable first-generation hypotheses and counterhypotheses across at least these families:

- associative activation versus explicit retrieval;
- assembly selection/propagation dynamics;
- multi-hop recall and false-association control;
- active/latent memory scaling;
- small-model reasoning benefit under matched token/compute budget;
- self-reference/continuity without self-report confounds;
- incremental graph maintenance versus repeated context reconstruction;
- exact-state plus semantic-activation separation;
- graph conflict/unknown/staleness semantics;
- persistence/replay and crash recovery;
- SQL/vector/event-store parity;
- migration/dual-write/cutover safety;
- query/update latency and memory footprint;
- write contention and hot-path isolation;
- graph growth, forgetting and edge decay;
- privacy/capability boundaries;
- failure cases where conventional isolated stores should remain.

A migration hypothesis must always include a rollback condition.

### CG3 — External research and executable tests

Use mandatory provider tools while quota/health permits, with automatic fallback under the global tool policy. Search relevant work on temporal/knowledge graphs, associative/activation memory, graph databases, event sourcing, incremental view maintenance, CRDT/conflict models, graph neural retrieval where relevant, cognitive architectures, agent memory, provenance and database migration.

Run executable experiments where feasible. Useful baseline arms include:

- current SQL/store-specific retrieval;
- vector/RAG retrieval;
- property/RDF/temporal graph baseline where practical;
- ClayGraph incremental activation;
- hybrid graph + explicit retrieval.

Measure accuracy/relevance, false positives, missing dependencies, latency, p95/p99, token/context cost, memory, update amplification, replay equivalence and rollback success. Synthetic/proxy results stay labeled synthetic/proxy.

### CG4 — Migration architecture

Materialize `MIGRATION_PLAN.json` containing phased, reversible migration steps:

1. `INVENTORY`
2. `SEMANTIC_MAPPING`
3. `SHADOW_GRAPH`
4. `PARITY_AND_REPLAY`
5. `DUAL_READ`
6. `DUAL_WRITE_WHERE_SAFE`
7. `CONTROLLED_CUTOVER`
8. `ROLLBACK_WINDOW`
9. `DEPRECATE_OR_KEEP_ISOLATED`

No destructive migration is authorized merely by running this research trigger. Physical consolidation is evidence-driven; logical organs/timescales/authority boundaries may remain separate.

### CG5 — FRANK feedback closure

FRANK is the primary downstream architecture consumer. Every completed `claygraph` run MUST materialize:

`FRANK_CLAYGRAPH_FEEDBACK.json`

with:

- originating ClayGraph run;
- newest FRANK run/architecture consumed;
- architecture effects: `SUPPORT | CHALLENGE | REVISE | SUPERSEDE | NEW_EXPERIMENT | NO_CHANGE`;
- exact FRANK modules/state contracts/transitions affected;
- proposed ClayCode architecture changes;
- database/store boundaries to merge/project/link/keep isolated;
- evidence class and ancestry;
- contradictions and negative results;
- migration prerequisites and rollback conditions;
- highest-information next live FRANK experiments.

A later `frank` run must ingest the newest ClayGraph feedback before finalizing architecture.

Write substantive deltas back to all affected branches, especially `frank`, `clay`, `claycode`, `hyperposition`, `gwt` and `emergenz`. If there is no substantive branch delta, record explicit `NO_CHANGE` rather than silently omitting feedback.

### CG6 — Promotion boundary

Do not promote the thesis "all databases should become one graph" as a goal in itself. Promote only narrower mechanisms/boundaries supported by evidence. A valid outcome may be a hybrid architecture in which ClayGraph is semantic/cognitive substrate while selected transactional, model-resource, authority or durability stores remain physically isolated.

## Required outputs

Under `research_entity/trigger_runs/claygraph/<run_id>/` write at minimum:

- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `DATABASE_INVENTORY.json`
- `CLAYGRAPH_SCHEMA.claycode.json`
- `HYPOTHESES.md` or `.json`
- `EXPERIMENT_RESULTS.json` when experiments are run
- `NEGATIVE_RESULTS.md` or `.jsonl` when applicable
- `MIGRATION_PLAN.json`
- `FRANK_CLAYGRAPH_FEEDBACK.json`
- `RUN_MANIFEST.json`
- `FINAL_REPORT.md`

The final report must distinguish source-derived concepts, current FRANK evidence, external evidence, model inference and synthetic/live experiments.

## Completion gate

A ClayGraph run cannot report 100% completion unless:

1. all current scientific branches were covered/indexed;
2. current/in-progress research was checked;
3. database inventory gaps are explicit;
4. hypotheses/counterhypotheses/falsifiers were generated;
5. research tools/experiments were attempted or valid fallbacks recorded;
6. migration plan is reversible and preserves `KEEP_ISOLATED` as a legitimate outcome;
7. `FRANK_CLAYGRAPH_FEEDBACK.json` exists;
8. durable outputs were written/reread;
9. mandatory RAE status footer is present.

## Scientific boundary

The branch studies functional memory, continuity, activation and agent architecture. Associative memory, persistent self-model, GWT integration or graph continuity do not by themselves establish phenomenal consciousness.