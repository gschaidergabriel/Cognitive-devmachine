# ClayGraph Iterative Evolution Protocol

## Core invariant

ClayGraph is a persistent evolving research artifact. A `claygraph` run MUST NOT reinvent the graph from scratch and MUST NOT absorb every new relation automatically.

Each run executes:

`accepted ClayGraph_n + complete current RAE research coverage + available privacy-approved external-use evidence -> candidate ClayGraph_n+1 -> self-use + external-use + adversarial/regression evaluation -> PROMOTE | REJECT | HOLD -> mesh feedback`.

The accepted architecture/schema source is:

`research_entity/claygraph/CLAYGRAPH_LATEST.claycode.json`

Historical accepted architecture snapshots live under `research_entity/claygraph/versions/`. The append-only promotion history is `research_entity/claygraph/CLAYGRAPH_EVOLUTION_LEDGER.jsonl`.

The current graph data materialization is derived/rebuildable and lives under `research_entity/claygraph/runtime/current/`. It never outranks canonical ledgers/raw evidence.

## Complete-research requirement

Every candidate is generated from indexed coverage of all currently reachable RAE research material, including all scientific branches, completed and in-progress runs, claims, hypotheses, experiments, negative results, Topic Packets, micro-packets, architecture artifacts, contradiction/supersession lineage, current FRANK evidence and relevant source/provenance references.

When available, also ingest privacy-approved external Frank founding-user evidence under:
`research_entity/external_users/founding_user_01/`
using `FRANK_USAGE_INGEST_PROTOCOL.md`.

External-user evidence is a distinct evidence class and must not be laundered into internal self-use evidence or population-level claims.

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

Also check the founding-user Frank export stream for new privacy-approved real-use observations and record the external-use ingestion cursor/coverage. Absence of new external evidence is valid and must be recorded rather than fabricated.

### E2 — Generate candidate architecture

Research and write `CLAYGRAPH_CANDIDATE.claycode.json`. Candidate generation is parent generation + 1. Changes may affect node/edge semantics, activation, assemblies, indexing, migration mapping, storage layout or query strategy.

### E3 — Delta and contradiction analysis

Write `CLAYGRAPH_EVOLUTION_DELTA.json` containing added/removed/changed semantics, expected benefits, predicted regressions, research dependencies, shared-ancestry collapse, contradictions and any relevant external Frank findings that motivated or challenge the candidate.

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

Write `SELF_USE_BENCHMARK.json` and record exact questions/evaluation method so future generations can replay them.

### E4B — Founding-user external-use evaluation

When sufficient new privacy-approved Frank evidence exists, evaluate the parent/candidate implications against the real Andreas deployment.

Applicable measures include:
- relevant-context misses and successful recalls;
- false/irrelevant activation;
- cross-project dependency usefulness;
- mail importance false alarms and missed-important incidents;
- graph growth versus context/latency cost;
- duplicate/stale/conflict failures;
- goal-level usefulness/adoption;
- snapshot/recovery outcomes;
- explicit user corrections;
- no-value/annoyance outcomes.

Do not require all metrics when not observable. Mark unavailable dimensions `UNMEASURED`.

A proposed schema change that would affect the external Frank consumer must include a rollback-capable migration plan. Only after PROMOTION and compatibility validation may a consumer update package be appended to:
`research_entity/external_users/founding_user_01/CLAYGRAPH_UPDATE_FEED.jsonl`.

If a high-information human answer would materially discriminate competing hypotheses and cannot be derived from existing evidence, Clay may append one concise question to:
`research_entity/external_users/founding_user_01/QUESTION_OUTBOX.jsonl`.
Do not interrogate the user for convenience.

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
- capability/safety isolation;
- external Frank regression risk where relevant.

Unmeasured dimensions remain `UNMEASURED`; they are never silently treated as unchanged.

### E6 — Decision

Write `CLAYGRAPH_EVOLUTION_DECISION.json` with one decision:

- `PROMOTE` — improves the evidence-backed objective set without violating hard invariants, or provides an explicit justified Pareto trade-off;
- `REJECT` — worse, unsafe, semantically lossy or unsupported;
- `HOLD` — promising but insufficient evidence.

Hard invariants include provenance/evidence ancestry, explicit unknown/conflict/revoked states, required replay/identity, model-output-is-not-authority, capability/effect isolation, migration rollback, no laundering of synthetic evidence into live evidence and no laundering of a single founding-user case into general-user proof.

### E7 — Promotion/write-back

Only `PROMOTE` may replace `CLAYGRAPH_LATEST.claycode.json`. Archive the prior version, append the evolution ledger and rebuild the runtime graph. `REJECT`/`HOLD` preserve the candidate only inside the run.

Every run writes feedback to all materially affected branches. FRANK is the primary downstream architecture target.

For a consumer-affecting promoted generation, append a compatible migration/update package to the founding-user ClayGraph update feed. Frank will consume it independently and read-only from its own repository context.

## Anti-overfitting rule

A candidate must not be promoted solely because it performs better on benchmarks generated from its own graph structure or solely because one founding user likes it. Include replayed questions from prior generations, adversarial queries, negative/contradictory cases and at least one evaluation whose expected answer is grounded independently of candidate topology.

## Scientific boundary

ClayGraph self-use and founding-user deployment can establish engineering utility evidence, not phenomenal consciousness. Better recall, continuity or self-reference remain functional measurements. A single-user longitudinal case is valuable for mechanism discovery/regression, not population-level validation.
