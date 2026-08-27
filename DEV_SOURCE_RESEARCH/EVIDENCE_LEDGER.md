# Frankenstein evidence ledger

Frozen curation base: `854f6bc87780f4a5242489a6c807d186b16a8c3d`.

This ledger answers four questions for each material claim: **what is observed, what is its current state, what would falsify it, and what credit does it earn?**

| Claim | Evidence class | State | Engineering confidence | Falsifier / next discriminator | Credit boundary |
|---|---|---|---:|---|---|
| UnifiedDB is intended as the single canonical durable state/evidence authority | `CURRENT_SOURCE` | implemented in source | 0.95 | Show a second persistent store that can change canonical outcome without declared admission/gating | Source semantics only; no whole-product runtime credit |
| ClayGraph / retrieval outputs are derived rather than a second truth authority | `CURRENT_SOURCE` | implemented in source | 0.95 | Demonstrate a derived projection mutating canonical truth independently | Source semantics only |
| Emergent Retrieval fails closed on stale epoch / invalid resolution / missing current UnifiedDB binding | `CURRENT_SOURCE` | implemented | 0.92 | Unit/integration case where propagation occurs despite a failed gate | Component scope only |
| Emergent Retrieval creates relevance by overlap of stored dimensions, not information ex nihilo | `CURRENT_SOURCE` + `INFERENCE` | adopted framing | 0.90 | Find an admitted assembly item with no source/evidence lineage | Concept + source architecture only |
| Historical Project-Frankenstein scoped Git denominator is 545 commits from `e1a881…` inclusive to `abba90a…` inclusive | `HISTORICAL_SOURCE` | scope law frozen | 0.98 | Git compare/identity evidence disproves merge-base or count | Historical lineage only |
| The earlier Project-Frankenstein deep-read manifest fully enumerated the repository | `NEGATIVE_RESULT` | contradicted by manifest itself | 0.99 | The manifest says `exact_tree_enumerated: false`, `exact_history_enumerated: false` | Zero repository-completeness credit |
| Current Hyperposition/GWT/GRF is fully validated | `NEGATIVE_RESULT` | not supported | 0.99 | Current cache itself says `PARTIAL_COMPONENT_EVIDENCE` and physical-grid re-entry blocked | Zero full-mechanism credit |
| Hyperposition can preserve unresolved alternatives without consensus minting truth | `OPEN_HYPOTHESIS` + source design | partial | 0.72 | Replay/serialization collapses branches without evidence; majority recurrence changes truth status | No causal-runtime credit yet |
| Global J-Space controls model behavior causally | `OPEN_HYPOTHESIS` | model-specific evidence incomplete | 0.60 | Lesion/shuffle/rescue has no preregistered effect beyond prompt/schema leakage | Zero general causal credit |
| GRF gives a privileged causal representation | `OPEN_HYPOTHESIS` | research only | 0.45 | Simpler matched features equal/beat GRF under held-out causal tests | Zero universal-law credit |
| Reflection helps practical agency | `OPEN_HYPOTHESIS` + historical engineering evidence | plausible, not universal | 0.70 | Equal-budget system with explicit reflection performs no better or loops more | No consciousness implication |
| Useful reflection must terminate into ACT/ASK/WAIT/re-observe/measurable transition | `INFERENCE` + failure-driven design | adopted engineering constraint | 0.90 | Non-terminating reflection demonstrably improves task outcomes without unacceptable cost/loops | Control-policy claim only |
| The new Frankenstein package/orchestrator/bugfix code exists and had 29 reported tests green at base commit | `CURRENT_SOURCE` | source-tested | 0.99 | Re-read commit/source or rerun tests and observe mismatch | Source/unit-test scope only |
| The new 72h provider-calling Frankenstein orchestration is currently admitted to run | `NEGATIVE_RESULT` | blocked/quarantined | 0.99 | A newer explicit legitimate authority re-enables exact routes and closes caller gate | Zero current runtime authority |
| Under current 9.13 HARD_OFF, provider routes are false and Together/paid fallback are forbidden | `CURRENT_SOURCE` / current supervisor authority | active at frozen base | 0.99 | Newer explicit owner/supervisor authority supersedes it | Current execution policy only |
| The external free-pool caller boundary was fully contained under HARD_OFF | `NEGATIVE_RESULT` | not yet closed | 0.99 | Executable receipt proves `provider_calls=0` and `secret_lookups=0` before boundary under current source | Zero provider-path runtime pass |
| GRID10 1 thread/process beat 2 threads/process on measured 4-process/4-vCPU topology | `PROJECT_MEASUREMENT` | measured counterexample | 0.95 | Matched rerun on same topology reverses result | Topology-specific diagnostic only |
| The GRID10 thread result generalizes to every CPU/topology | `NEGATIVE_RESULT` | unsupported | 0.99 | Different topology produces different optimum | No generalized performance credit |
| Lower private dirty memory alone proves lower physical RAM use | `NEGATIVE_RESULT` | rejected by current supervisor | 0.99 | Proper RSS/PSS/full smaps accounting demonstrates actual reduction | Zero RAM-efficiency promotion from private-dirty alone |
| Distillery has produced accepted training data at the last confirmed base state | `NEGATIVE_RESULT` | zero accepted dataset tokens | 0.99 | Exact-current evidence shows accepted tokens >0 with provenance and idempotent replay | Training credit zero at base |
| Completed training by itself is a pass | `NEGATIVE_RESULT` | forbidden inference | 0.99 | Behavioral/causal/holdout tests required beyond job completion | No training pass from completion alone |
| Logical HCU/GRID cell count equals resident model count or physical decode concurrency | `NEGATIVE_RESULT` | explicitly false as reporting rule | 0.99 | Direct physical measurement is required | No physical concurrency credit from logical count |
| An effect request proves an external effect happened | `NEGATIVE_RESULT` | explicitly false | 0.99 | Verified external outcome required | Zero effect credit without verification |
| Unknown external outcome may be blindly replayed | `NEGATIVE_RESULT` | prohibited | 0.99 | Must first disambiguate outcome | Safety/effect invariant |
| Current public-root topology can be reduced without changing source bytes | `CURRENT_SOURCE` + this branch tree construction | prepared | 0.95 | Blob/tree identity mismatch for relocated source | Topology curation only; path-sensitive runtime unverified |

## Evidence promotion rules

1. `source-ready` -> `measured` requires execution at the claimed source identity.
2. `measured` -> `reproduced` requires a genuinely independent or at least explicitly same-family repeat; do not count identical pipeline consensus as independent evidence.
3. `component PASS` -> broader integration PASS requires tests at broader scope.
4. `prepared-not-run` never becomes `measured` by prose.
5. Current authority can block execution even when source tests are green.
6. Negative results remain indexed; deleting them would erase the reason later architecture exists.

## Current P0 contradiction preserved by this curation

The strongest current contradiction is intentional and visible:

- source commit `854f6bc8…` contains a real, tested Frankenstein Bauleiter/Bugfix implementation that calls external provider tiers;
- current supervisor state says the direct provider orchestration is non-operative under 9.13 HARD_OFF and identifies the still-ungated external caller boundary as P0 critical.

The correct synthesis is **not** to choose whichever story sounds more advanced. The code exists; the runtime authority does not. Both facts belong in the record.

## Acceptance state at the frozen base

- whole EntityOS runtime: not accepted / credit `0`
- full HCU runtime: credit `0`
- Physical-GRID10 runtime promotion: credit `0`
- canonical semantics promotion: credit `0`
- training credit: `0`
- current work remains `IN_PROGRESS`

Refresh the current authority before reusing these values after the frozen base.