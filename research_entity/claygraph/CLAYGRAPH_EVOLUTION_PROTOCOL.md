# ClayGraph Iterative Evolution Protocol

## Core invariant

ClayGraph is a persistent evolving research artifact. A `claygraph` run MUST NOT reinvent the graph from scratch and MUST NOT absorb every new relation automatically.

Each run executes:

`accepted ClayGraph_n + complete current RAE research coverage -> candidate ClayGraph_n+1 -> self-use + adversarial/regression evaluation -> PROMOTE | REJECT | HOLD -> mesh feedback`.

The accepted architecture/schema source is:

`research_entity/claygraph/CLAYGRAPH_LATEST.claycode.json`

Historical accepted architecture snapshots live under `research_entity/claygraph/versions/`. The append-only promotion history is `research_entity/claygraph/CLAYGRAPH_EVOLUTION_LEDGER.jsonl`.

The current graph data materialization is derived/rebuildable and lives under `research_entity/claygraph/runtime/current/`. It never outranks canonical ledgers/raw evidence.

## Complete-research requirement

Every candidate is generated from indexed coverage of all currently reachable RAE research material, including all scientific branches, completed and in-progress runs, claims, hypotheses, experiments, negative results, Topic Packets, micro-packets, architecture artifacts, contradiction/supersession lineage, current FRANK evidence and relevant source/provenance references.

Complete coverage does not mean loading every byte into one model context. Build an index first and load raw evidence on demand where it can change graph meaning, a contradiction or an experiment.

## Two-layer architecture

ClayGraph separates:

1. **semantic/evidence graph** — typed entities, relations, events, provenance, versions, conflicts and evidence ancestry; deterministic/replayable where applicable;
2. **activation overlay** — transient relevance, salience, decay, spreading activation and bounded assembly state used to select what becomes model-visible.

Activation NEVER upgrades truth or evidence status. A highly active node is easier to think with, not more true.

## Mandatory evolution cycle

### E0 — Load parent

Read `CLAYGRAPH_LATEST.claycode.json`. If no accepted graph exists, generation 0 is created as `SEED_BASELINE`; it is a starting implementation, not a claim of superiority.

### E1 — Reindex complete current corpus

Rebuild the derived graph materialization from current repository evidence. Record source paths, SHA/content identity, branch/run lineage and missing/blocked regions.

### E2 — Generate candidate architecture

Research and write `CLAYGRAPH_CANDIDATE.claycode.json`. Candidate generation is parent generation + 1. Changes may affect node/edge semantics, activation, assemblies, indexing, migration mapping, storage layout or query strategy.

### E3 — Delta and contradiction analysis

Write `CLAYGRAPH_EVOLUTION_DELTA.json` containing added/removed/changed semantics, expected benefits, predicted regressions, research dependencies, shared-ancestry collapse and contradictions.

### E4 — RAE self-use experiment

The active ChatGPT/RAE worker MUST use ClayGraph itself for real research questions from the current run, not only synthetic unit tests. For each selected question compare at least:

- ClayGraph query/activation;
- existing SQLite/FTS/research-query baseline where available;
- direct repository/file search or staged retrieval baseline where available.

Measure:

- wall-clock retrieval latency in the executable environment;
- number of items/chars/tokens returned to the reasoning model;
- target-evidence recall/precision where a gold set can be defined;
- multi-hop relation recovery;
- irrelevant activation/false association;
- provenance/path explainability;
- whether the resulting answer/research decision changes.

These are environment-specific measurements. GitHub-runner or sandbox latency is not automatically live-FRANK latency.

Write `SELF_USE_BENCHMARK.json` and record the exact questions and gold/evaluation method so future generations can replay them.

### E5 — Adversarial/regression evaluation

Compare parent and candidate on applicable dimensions:

- research coverage;
- provenance/ancestry preservation;
- deterministic identity/replay;
- unknown/conflict/revoked/stale preservation;
- direct and multi-hop retrieval;
- false-association rate;
- assembly relevance/completeness;
- context/token cost;
- p50/p95/p99 latency;
- memory footprint;
- update amplification/write contention;
- hidden/stale dependency handling;
- crash/recovery equivalence;
- database migration parity/rollback;
- matched-budget small-model performance;
- capability/safety isolation.

Unmeasured dimensions remain `UNMEASURED`; they are never silently treated as unchanged.

### E6 — Decision

Write `CLAYGRAPH_EVOLUTION_DECISION.json` with one decision:

- `PROMOTE` — improves the evidence-backed objective set without violating hard invariants, or provides an explicit justified Pareto trade-off;
- `REJECT` — worse, unsafe, semantically lossy or unsupported;
- `HOLD` — promising but insufficient evidence.

Hard invariants include provenance/evidence ancestry, explicit unknown/conflict/revoked states, required replay/identity, model-output-is-not-authority, capability/effect isolation, migration rollback and no laundering of synthetic evidence into live evidence.

### E7 — Promotion/write-back

Only `PROMOTE` may replace `CLAYGRAPH_LATEST.claycode.json`. Archive the prior version, append the evolution ledger and rebuild the runtime graph. `REJECT`/`HOLD` preserve the candidate only inside the run.

Every run writes feedback to all materially affected branches. FRANK is the primary downstream architecture target.

## Anti-overfitting rule

A candidate must not be promoted solely because it performs better on benchmarks generated from its own graph structure. Include replayed questions from prior generations, adversarial queries, negative/contradictory cases and at least one evaluation whose expected answer is grounded independently of the candidate topology.

## Scientific boundary

ClayGraph self-use can establish engineering utility, not phenomenal consciousness. Better recall, continuity or self-reference remain functional measurements.