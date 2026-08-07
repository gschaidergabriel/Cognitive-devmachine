# Reserved Trigger: `fusion`

`fusion` is the Research Entity's global scientific feedback loop. It is not a seventh domain silo. It researches across the entire current RAE knowledge/evidence graph and returns explicit deltas to every scientific branch.

## Purpose

When the complete trimmed user message equals `fusion` (case-insensitive), execute a full cross-branch research cycle using all currently reachable RAE research classes:

- canonical state and active agenda;
- all six scientific branches: `clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`;
- completed and newer in-progress trigger runs;
- global/domain claim, hypothesis, experiment and negative-result ledgers;
- Topic Packets and Knowledge Micro-Packets;
- contradiction/supersession lineage;
- tool/provider health and prior tool results;
- promoted dump-derived material and source/provenance references;
- current runtime/code evidence when accessible;
- raw/source evidence reached by active claims, contradictions or research questions.

`all data` means **coverage of the complete current research graph and evidence classes**, not blindly placing every raw byte into one model context. Use indexes, hashes, manifests and staged retrieval so the run is exhaustive in coverage while loading raw evidence only where it can change the analysis.

## Relationship to `clay`

- `clay` is the integrated Synthetic Clay architecture/research foundry.
- `fusion` is the global meta-research and feedback cycle over the whole RAE.

`fusion` may produce architecture implications for Clay, but its primary product is cross-domain scientific synthesis, contradiction resolution, new hypotheses/experiments and explicit feedback into every branch.

## Mandatory phases

### F0 — Canonical boot and corpus coverage

1. Verify current canonical state, actor membership and trigger registry.
2. Materialize `GLOBAL_COVERAGE_MANIFEST.json` before Fusion 1.
3. The coverage manifest must enumerate every current research class/branch and record whether coverage is `FULL_INDEXED`, `REFERENCED_RAW_ON_DEMAND`, `MISSING`, `BLOCKED`, or `STALE`.
4. Scan newer in-progress material, not only latest final reports.
5. Preserve source/evidence ancestry. Reuse of one underlying experiment across branches never becomes independent replication.

A `fusion` run is incomplete if any scientific branch is silently omitted.

### F1 — Whole-mesh graph synthesis

Build a global working graph of:

- active/current claims;
- open hypotheses;
- critical negative results;
- active and proposed experiments;
- architecture candidates;
- cross-branch dependencies;
- contradictions and supersessions;
- unknowns and missing evidence;
- reusable methods/measurements.

Deduplicate equivalent mechanisms across branch-specific terminology without deleting local names or provenance.

### F2 — Global hypothesis generation and anti-echo gate

Generate hypotheses that arise only from combining branches. For every important synthesis, identify:

- upstream branches/evidence;
- whether the apparent agreement shares ancestry;
- counterhypothesis;
- falsifier;
- cheapest/highest-information experiment;
- affected branches.

Run the Goodman anti-echo logic whenever support flows through shared FRANK/ClayCode/Clay/GWT ancestry. Cross-branch repetition is convergence, not replication.

### F3 — External research and empirical work

Use the quota/health-aware research tool orchestration policy. Search external literature/code/data where it can discriminate hypotheses. Run local/remote experiments where feasible. Preserve `synthetic`, `proxy`, `independent_runtime`, `live`, and `formal` evidence classes exactly.

Do not promote synthetic results into live FRANK claims.

### F4 — Fusion 2 / global model revision

Produce a global synthesis that explicitly states:

- what is strengthened;
- what is weakened/refuted;
- what is merely reinterpreted;
- what remains unresolved;
- what new cross-domain mechanism or architecture follows;
- what research should happen next and why.

Prefer falsifiable mechanism statements over broad narratives.

### F5 — Mandatory branch feedback closure

Every `fusion` run MUST write a feedback result for **each** scientific branch, even when the result is `NO_CHANGE`.

Materialize `BRANCH_FEEDBACK_MANIFEST.json` with one entry each for:

- `clay`
- `frank`
- `gwt`
- `emergenz`
- `claycode`
- `hyperposition`

Each entry must contain:

- `effect`: `SUPPORT | CHALLENGE | REVISE | SUPERSEDE | NEW_EXPERIMENT | NO_CHANGE` (or a list);
- source fusion run and evidence refs;
- exact claims/hypotheses/packets affected;
- confidence/evidence class;
- contradiction or supersession lineage;
- next experiment/falsifier;
- durable write-back artifact refs.

Write branch-specific feedback packets/micro-packets into the existing mesh so a later domain trigger automatically ingests the fusion result. Do not create isolated `fusion` knowledge that other triggers cannot discover.

If a branch receives no substantive delta, record an explicit `NO_CHANGE` receipt. This is the proof that feedback closure was checked rather than forgotten.

### F6 — Global agenda update / promotion gate

Rank next experiments by expected information gain across the whole mesh, not by one branch's local optimization.

Canonical promotion/refutation is allowed only through normal claim lifecycle rules and evidence precedence. `fusion` has no special authority to promote weak evidence merely because it used more data.

## Required outputs

Write under `research_entity/trigger_runs/fusion/<run_id>/` at minimum:

- `INTERCONNECT_MANIFEST.json`
- `GLOBAL_COVERAGE_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `GLOBAL_HYPOTHESIS_MATRIX.md` or `.json`
- `CONTRADICTION_MAP.md` or `.json`
- `EXPERIMENT_RESULTS.json` when experiments are run
- `BRANCH_FEEDBACK_MANIFEST.json`
- `RUN_MANIFEST.json`
- `FINAL_REPORT.md`

Additionally write branch-discoverable feedback packets/micro-packets for every substantive delta.

## Completion gate

A `fusion` run cannot report 100% completion unless:

1. all six scientific branches were covered;
2. current/in-progress material was checked;
3. contradiction/shared-ancestry scan was performed;
4. research/tool work was executed or explicit blockers recorded;
5. every branch has a feedback receipt, including `NO_CHANGE` where applicable;
6. durable artifacts were written and reread;
7. the mandatory RAE status footer is present.

## Scientific boundary

Global synthesis can increase coherence and reveal interactions, but it does not manufacture independent evidence. In particular, GWT/emergence/self-model sophistication is never by itself evidence of phenomenal consciousness.
