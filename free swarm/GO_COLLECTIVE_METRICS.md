# GO Collective Recursive-Improvement Metrics — live baseline

Generated: `2026-08-24T11:59:40Z`  
Authority observed: `8.69`  
Generation class: `BOOTSTRAP_BASELINE_SOURCE_DERIVED_NOT_AGGREGATOR_RUNTIME`

The first full per-worker table will be generated from the `/artifacts` worker records by `free swarm/go_collective_metrics.py` on an authorized artifact-bearing local or `clay-direct-dev` surface. The connected GitHub surface currently exposes the persisted aggregate dashboard but not the runtime worker JSONL tree, so individual worker rows are not invented here.

## Aggregate baseline

| Metric | Current | Evidence status |
|---|---:|---|
| Free-Swarm worker records | 709 | observed persisted live metrics |
| exact-usage rows | 414 | observed |
| exact total tokens | 3,187,935 | observed |
| accepted architecture deltas | 0 / 1 adjudication records | observed current ledger |
| Token Quality Efficiency / 1k tokens | 0.000000 | verified-utility baseline only; not a claim that all tokens were useless |
| Code Quality Score / 100 | UNKNOWN | no accepted delta has enough evidence coverage |
| Verified Innovation Score / 100 | UNKNOWN | no accepted verified innovation delta |
| performance index | UNKNOWN | no matched benchmark family in new worker schema yet |
| p95 information-transfer latency | UNKNOWN | downstream consumption acknowledgement not yet instrumented |
| Capability / Information-Latency Ratio | UNKNOWN | requires both raw constituents |
| HCU_TARGET_100_GO forecast | **43.05%** | **UNCALIBRATED** model forecast, not completion percentage or canonical fact |
| HCU forecast uncertainty | **20–65%** | intentionally wide bootstrap interval |

## HCU forecast vector

| Milestone family | bootstrap p |
|---|---:|
| authority / truth / effect invariants | 90% |
| Typed Entry + causal identity | 75% |
| provider/runtime/effect boundaries | 35% |
| engine/load/consumed-byte identity | 45% |
| GRID10 + InferenceReceipt closure | 55% |
| canonical local model execution | 40% |
| model-specific J-Space observation | 45% |
| J-Space causal intervention/controls | 25% |
| dataset/training readiness | 35% |
| recovery/replay/fail-closed | 55% |
| performance/latency/scale | 20% |
| integration + independent reproducibility | 40% |

## Mandatory worker table from next `go`

| worker | tokens | TQE | CQS | VIS | performance index | p95 info latency | CILR | evidence lineage | HCU forecast contribution | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| pending artifact-bearing aggregator run | — | — | — | — | — | — | — | — | — | PENDING |

## Anti-Goodhart / Goodman-lineage protections

- no single scalar is the optimization target;
- use Pareto improvement plus hard correctness/provenance/security/effect gates;
- raw measurements are append-only; derived metrics are recomputable;
- shared model/source/prompt/orchestration ancestry is collapsed as correlated evidence;
- high-scoring changes require counter-metrics/holdout or random audit where practical;
- metric weights freeze for 10 macrocycles; definition changes shadow-run for 3 cycles;
- a score is allowed to decrease after stronger measurement or counterevidence;
- latency cannot be improved by skipping validation;
- token efficiency cannot be improved by deleting required evidence;
- HCU confidence is forecast and must be calibrated against resolved outcomes using Brier/log loss.

The goal is slow recursive improvement of the actual EntityOS/HCU system, not monotonic cosmetic score growth.
