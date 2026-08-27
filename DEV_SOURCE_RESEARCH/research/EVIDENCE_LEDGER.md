# Evidence ledger

Machine-readable companion: [`ARCHIVE_INDEX.json`](ARCHIVE_INDEX.json).

Status vocabulary used here:

`ATTEMPTED · SOURCE_READY · MEASURED · REPRODUCED · CONTRADICTED · BLOCKED · PREPARED_NOT_RUN · ADOPTED · RETIRED`

Confidence is an **engineering confidence score**, not a Bayesian probability and not evidence by itself.

| ID | Claim / mechanism | Evidence label | Status | Confidence | Exact source / evidence | Scope ceiling | Falsifier / next discriminator |
|---|---|---|---|---:|---|---|---|
| E01 | Clay persistent research identity; workers are organs | CURRENT_SOURCE | ADOPTED | 1.00 | `BOOTSTRAP_MINIMAL.json`, current authority surfaces | identity/coordination | newer explicit owner authority changes it |
| E02 | EntityOS current product; HCU current integrated cognition/compute architecture | CURRENT_SOURCE | ADOPTED | 1.00 | current authority surfaces | naming/architecture | newer explicit owner authority changes it |
| E03 | Project-Frankenstein Level-0 scope has 545 commit obligations from `e1a881…` inclusive to `abba90…` | HISTORICAL_SOURCE | MEASURED | 0.99 | `PROJECT_FRANKENSTEIN_LEVEL0_SCOPE_LAW.json` | scope denominator only | compare/scope artifact is proven wrong at exact identities |
| E04 | Project-Frankenstein history is completely reconstructed | HISTORICAL_SOURCE | BLOCKED | 0.99 | `PROJECT_FRANKENSTEIN_MANIFEST.json`, history interval manifest | no exhaustive claim | enumerate exact ordered obligation list + exact frozen-head tree and reconcile source lineages |
| E05 | Historical Frank used workspace, E-PQ/state, memory, perception, reward, goals, hypothesis/experiment and training services | HISTORICAL_SOURCE | MEASURED | 0.95 | 25 deep-read units in archive manifest | source architecture | exact frozen source contradicts indexed paths/classes |
| E06 | UnifiedDB-style single durable authority reduces fragmented-state ambiguity | OPEN_HYPOTHESIS | ADOPTED | 0.85 | current architecture + historical failure pressure | engineering hypothesis | matched failure/recovery comparison shows no benefit or worse ambiguity |
| E07 | Emergent Retrieval = query-time relevance from overlapping stored evidence dimensions | CURRENT_SOURCE | ADOPTED | 1.00 | project definition in Trigger-3 bootstrap / current curation | term definition | newer owner definition supersedes it |
| E08 | Reflection should terminate into ACT/ASK/WAIT/re-observe/measurable transition | CURRENT_SOURCE | ADOPTED | 0.95 | Trigger-3 contract | control design | workload study shows recursive reflection improves outcomes without fixation/latency cost and no exit gate is needed |
| E09 | Global J-Space is already proven as a model-specific causal semantic interface | CURRENT_SOURCE | CONTRADICTED | 0.98 | current supervisor credits + retained negative/shortcut controls | no J-Space promotion | exact model/runtime preregistered selective causal intervention passes all matched controls |
| E10 | Internal representation transport/readout alone proves semantic control | NEGATIVE_RESULT | CONTRADICTED | 0.97 | J-Space research lineage and current training guard work | methodology | selective behavior follows only semantic intervention and dominates nuisance controls on fresh holdout |
| E11 | GRID10 one torch thread/process is best for the measured 4-process/4-vCPU topology | PROJECT_MEASUREMENT | MEASURED | 0.94 | 9.13O thread A/B: 8.3197 s vs 23.1806 s; 4-thread arm timed out | exact measured topology only | matched rerun on same topology reverses result |
| E12 | One-thread result generalizes to every CPU/process topology | INFERENCE | BLOCKED | 0.99 | current supervisor explicitly forbids extrapolation | no generalization | matched tests across changed topologies establish stable rule |
| E13 | Raw Free-Swarm scale currently converts into accepted Distillery training tokens | PROJECT_MEASUREMENT | CONTRADICTED | 0.99 | 9.13O: 0 accepted / 88,774 source tokens | current measured conversion snapshot | exact-current evidence-qualified Forge→Distillery witness yields persistent >0 accepted tokens and replay +0 |
| E14 | 72h Frankenstein package/orchestrator/bugfix source exists | CURRENT_SOURCE | SOURCE_READY | 0.99 | main `854f6bc…`; three source files + tests | source/unit scope only | files absent or commit ancestry invalidated |
| E15 | 72h Frankenstein provider-calling orchestration is executable under current authority | CURRENT_SOURCE | BLOCKED | 1.00 | `SUPERVISOR_INBOX.json` + 9.13O steering | no provider execution | newer explicit authority re-enables route and exact caller gate passes |
| E16 | Together is currently available for the Frankenstein plan | CURRENT_SOURCE | CONTRADICTED | 1.00 | 9.13 HARD_OFF; zero paid runs; Together forbidden | no Together preflight/run | newer explicit owner/supervisor authority changes mode |
| E17 | Recent external Free-Pool concept advice matched real GRID10 source | NEGATIVE_RESULT | CONTRADICTED | 0.99 | `frankenstein-master-cognition-concept/CONCEPT.md` records invented InfluxDB/128-D/weighted graph details | advice quality finding | exact source actually contains those structures at cited identity |
| E18 | Source/unit PASS implies whole EntityOS/HCU PASS | CURRENT_SOURCE | CONTRADICTED | 1.00 | evidence law + zero whole-product credit | component only | full admitted integrated acceptance receipt exists at exact source/runtime identity |
| E19 | Whole EntityOS/HCU runtime acceptance | CURRENT_SOURCE | BLOCKED | 1.00 | selected supervisor promotion state | credit 0 | exact admitted full-path acceptance passes |
| E20 | Full HCU runtime acceptance | CURRENT_SOURCE | BLOCKED | 1.00 | selected supervisor promotion state | credit 0 | exact admitted HCU acceptance passes |
| E21 | Training acceptance | CURRENT_SOURCE | BLOCKED | 1.00 | selected supervisor promotion state | credit 0 | completed train + frozen eval + causal/retention/fail-closed gates pass at exact lineage |
| E22 | GWT literature proves consciousness/sentience in Frankenstein | EXTERNAL_PRIMARY | CONTRADICTED | 1.00 | external GWT is architecture/neuroscience literature, not project evidence | analogy only | no such inference is admissible from literature alone |
| E23 | GWT is useful as a distributed-workspace architecture analogy | EXTERNAL_PRIMARY | ADOPTED | 0.80 | Baars 2005 and related architecture literature | method analogy | project benchmarks show workspace pattern consistently harms coordination vs matched alternatives |
| E24 | NVIDIA Unified Memory proves UnifiedDB semantics | EXTERNAL_PRIMARY | CONTRADICTED | 1.00 | CUDA docs describe hardware/software memory coherence, not DB truth semantics | analogy only | not applicable: category error |
| E25 | NVIDIA Unified Memory is a useful ownership/copy-boundary analogy | EXTERNAL_PRIMARY | ADOPTED | 0.80 | CUDA programming guide | systems analogy | analogy misleads architecture decisions in concrete design review |
| E26 | SQLite WAL supports concurrent readers with a writer, but one writer at a time and same-host shared-memory constraints | EXTERNAL_PRIMARY | ADOPTED | 0.99 | SQLite WAL official docs | storage-mechanism fact | official SQLite docs change |
| E27 | Current root already satisfies the four-entry public topology | CURRENT_SOURCE | CONTRADICTED | 1.00 | main root tree at `854f6bc…` | topology | exact tree becomes only README + three target dirs |
| E28 | Moving all current root files immediately is safe | OPEN_HYPOTHESIS | BLOCKED | 0.95 | root contains authority/bootstrap/workflow compatibility entry paths | no mass move | full path-consumer/reference/workflow audit + staged compatibility tests pass |

## Promotion rule

A prettier story does not promote an item. Status changes require the named discriminator at the exact evidence scope.

When two sources disagree:

1. newest explicit owner authority;
2. inbox-selected current supervisor authority;
3. current canonical source/executable evidence;
4. older current-facing surfaces;
5. historical receipts/prose/cache.

Do not average incompatible authority epochs.
