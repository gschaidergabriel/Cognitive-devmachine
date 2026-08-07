# Reserved Trigger: `fusion`

`fusion` is the Research Entity's global scientific feedback loop. It is not a scientific branch itself. It researches across the entire current RAE knowledge/evidence graph and returns explicit deltas to every registered scientific branch.

## Purpose

When the complete trimmed user message equals `fusion` (case-insensitive), execute a full cross-branch research cycle using all currently reachable RAE research classes:

- canonical state and active agenda;
- all currently registered scientific branches — at this revision: `clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`;
- completed and newer in-progress trigger runs;
- global/domain claim, hypothesis, experiment and negative-result ledgers;
- Topic Packets and Knowledge Micro-Packets;
- contradiction/supersession lineage;
- tool/provider health and prior tool results;
- promoted dump-derived material and source/provenance references;
- current runtime/code evidence when accessible;
- raw/source evidence reached by active claims, contradictions or research questions.

Branch membership is authoritative in `RESEARCH_TRIGGER_REGISTRY.json`; do not hard-code an older six-branch assumption. `tools/fusion_research_contract.py` derives its branch set from the registry.

`all data` means coverage of the complete current research graph/evidence classes, not blindly placing every raw byte into one model context. Use indexes, hashes, manifests and staged retrieval.

## Relationship to Clay and ClayGraph

- `clay` is the integrated Synthetic Clay architecture/research foundry.
- `claygraph` is the iterative memory/knowledge-graph/database-substrate research branch.
- `fusion` is the global meta-research and feedback cycle over both plus all other branches.

## Mandatory phases

### F0 — Canonical boot and corpus coverage

1. Verify canonical state, actor membership and trigger registry.
2. Materialize `GLOBAL_COVERAGE_MANIFEST.json` before Fusion 1.
3. Enumerate every registered scientific branch with status `FULL_INDEXED`, `REFERENCED_RAW_ON_DEMAND`, `MISSING`, `BLOCKED`, or `STALE`.
4. Scan newer in-progress material, not only final reports.
5. Preserve source/evidence ancestry.

A fusion run is incomplete if any registered scientific branch is silently omitted.

### F1 — Whole-mesh graph synthesis

Build a global working graph of active/current claims, open hypotheses, critical negative results, active/proposed experiments, architecture candidates, ClayGraph versions/migration results, cross-branch dependencies, contradictions/supersessions, unknowns and reusable methods.

Deduplicate equivalent mechanisms across terminology without deleting local names/provenance.

### F2 — Global hypothesis generation and anti-echo gate

Generate hypotheses arising from branch combinations. For each important synthesis identify upstream branches/evidence, ancestry, counterhypothesis, falsifier, highest-information experiment and affected branches.

Run Goodman anti-echo logic whenever support flows through shared FRANK/ClayCode/Clay/ClayGraph/GWT ancestry. Cross-branch repetition is convergence, not replication.

### F3 — External research and empirical work

Use quota/health-aware research tools with explicit fallbacks. Run local/remote experiments where feasible. Preserve `synthetic`, `proxy`, `independent_runtime`, `live`, and `formal` evidence classes.

### F4 — Fusion 2 / global model revision

State what is strengthened, weakened/refuted, reinterpreted, unresolved, what new mechanism/architecture follows and what should be tested next.

### F5 — Mandatory branch feedback closure

Every fusion run MUST write a feedback result for each registered scientific branch, including `NO_CHANGE` where appropriate.

At this revision `BRANCH_FEEDBACK_MANIFEST.json` therefore contains one entry each for:

- `clay`
- `frank`
- `gwt`
- `emergenz`
- `claycode`
- `hyperposition`
- `claygraph`

Each entry contains effect (`SUPPORT | CHALLENGE | REVISE | SUPERSEDE | NEW_EXPERIMENT | NO_CHANGE`), source fusion/evidence refs, affected claims/hypotheses/packets, confidence/evidence class, ancestry/contradiction lineage, next experiment/falsifier and durable write-back refs.

Write branch-discoverable feedback packets/micro-packets for substantive deltas. ClayGraph feedback must be discoverable by subsequent `claygraph`, `frank`, `claycode`, `hyperposition` and `gwt` runs when relevant.

### F6 — Global agenda update / promotion gate

Rank experiments by expected information gain across the whole mesh. Fusion has no special authority to promote weak evidence.

## Required outputs

Under `research_entity/trigger_runs/fusion/<run_id>/` write at minimum:

- `INTERCONNECT_MANIFEST.json`
- `GLOBAL_COVERAGE_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `GLOBAL_HYPOTHESIS_MATRIX.md` or `.json`
- `CONTRADICTION_MAP.md` or `.json`
- `EXPERIMENT_RESULTS.json` when experiments run
- `BRANCH_FEEDBACK_MANIFEST.json`
- `RUN_MANIFEST.json`
- `FINAL_REPORT.md`

## Completion gate

A fusion run cannot report 100% completion unless:

1. every branch currently registered as scientific was covered;
2. current/in-progress material was checked;
3. contradiction/shared-ancestry scan was performed;
4. research/tool work was executed or blockers recorded;
5. every scientific branch has a feedback receipt, including `NO_CHANGE`;
6. durable artifacts were written/reread;
7. `tools/fusion_research_contract.py` passes;
8. mandatory RAE status footer is present.

## Scientific boundary

Global synthesis increases coherence and may reveal interactions, but does not manufacture independent evidence. GWT/emergence/self-model/ClayGraph sophistication is not by itself evidence of phenomenal consciousness.
