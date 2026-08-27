# UnifiedDB Emergence Meter v0.3 — Adversarial Concordance Gate

## Decision

The v0.2 synthetic five-regime classifier may remain as a scenario generator,
but its claim to be a reliable emergence instrument is rejected.  v0.3 is a
fail-closed measurement contract, not a promoted scalar and not a validated
FRANK detector.

Current evidence class: `SYNTHETIC_METHOD_FALSIFICATION` plus
`SYNTHETIC_PARAMETER_SURFACE_AND_COUNTEREXAMPLE`.

Current scientific promotion: `NONE`.

Live FRANK validation: `false`.

Phenomenal-consciousness inference: prohibited.

## Falsified assumptions

| Assumption in or near v0.2 | Adversarial observation | Adjudication |
|---|---:|---|
| Ticks can be sign-flipped as independent paired units | Null false-positive rate 0.84 at tick level versus 0.06 at the episode level | `FAIL_V02_INDEPENDENT_TICK_ASSUMPTION` |
| Full time shuffle is a safe default null for persistent series | Across phi 0.95–0.985, full-shuffle false-positive rates were 0.467–0.833 | `REJECT_AS_DEFAULT_FOR_DEPENDENT_TICKS` |
| One autocorrelation-preserving surrogate repairs the problem | Circular-shift null was better calibrated in the tested stationary AR cells, but showed 0.067–0.20 false-positive rates at phi 0.985 and failed under a shared regime | `ONE_DIAGNOSTIC_ONLY` |
| Searching for a high-EI/MI macrostate in-sample is valid discovery | At 2,500 candidate partitions, median selected train MI was 0.0622 bits while held-out MI was 0.000073 bits; 0.90 met the predefined false-discovery pattern | `REQUIRE_PREREGISTERED_OR_CROSSFIT_SELECTION` |
| Pairwise MMI synergy estimates can be summed | Duplicating one XOR source produced a 2-bit pairwise sum for a 1-bit target | `FAIL_OVERLAPPING_ADDITIVE_SYNERGY` |
| Endpoint agreement plus visible lesion/rescue validates the path | An unmapped XOR backup was endpoint-equivalent at baseline and still had intervention effect 0.5 | `REQUIRE_PATH_AND_EXCLUDED_VARIABLE_TESTS` |
| Concordant unconditional nulls identify a direct path | Under a shared persistent regime and no direct path, full shuffle rejected in 1.00 and circular shift in 0.975 of seeds; conditioning reduced median lag information from 0.7349 to 0.00063 bits | `CONDITION_ON_CONTEXT_OR_ABSTAIN` |

## Fail-closed state machine

No arithmetic average across gates is allowed.  Gates are conjunctive and a
strong result in one dimension cannot compensate for a failed causal gate.

1. `RECEIPT_COMPLETE`
   - Exact code hash, data hash, model/build/host identity, clock basis,
     graph/state epoch, seed, episode, context and intervention identifiers.
   - Any missing field yields `INVALID_RECEIPT`.
2. `INDEPENDENCE_UNIT_VALID`
   - Predeclare the independent sampling unit and the dependence hierarchy.
   - Tick replication cannot increase the independent sample count.
   - Exchangeability, symmetry, stationarity and mixing assumptions must be
     tested or bounded; otherwise `INVALID_ASSUMPTIONS`.
3. `NULL_CONCORDANCE`
   - Run at least two scientifically relevant null families, including a
     dependence-preserving null where appropriate.
   - A null family is admitted only with its exact invariance assumptions.
   - Disagreement yields `ABSTAIN_NULL_DISAGREEMENT`, not selection of the more
     favorable p-value.
4. `CONTEXT_CLOSURE`
   - Condition on known persistent regimes, common drivers and build/context
     changes, or run explicit context interventions.
   - Residual shared-context risk yields `ABSTAIN_CONTEXT_OPEN`.
5. `MACRO_SELECTION_VALID`
   - Macro variables are preregistered, or learned only inside time-, episode-
     and context-aware training folds.
   - All intervention and causal estimates are computed on untouched folds or
     independent target episodes.
   - Report candidate count, optimizer family and all selection objectives.
6. `DECOMPOSITION_BOUNDED`
   - Report several estimator families/axiom choices and their finite-sample
     calibration.
   - Overlapping source sets are not additively aggregated.
   - Each claimed synergy is bounded by target information/entropy and checked
     against duplicate-source controls.
   - Material estimator disagreement yields `ABSTAIN_ESTIMATOR_DISAGREEMENT`.
7. `PATHWISE_CAUSAL_VALIDITY`
   - Test intermediate variables, not only endpoints.
   - Intervene on excluded/unmapped variables and alternative paths.
   - Use matched baseline, lesion, rescue, truthful re-entry, shuffled re-entry
     and absent re-entry conditions.
8. `GWT_RECEIVER_USE_CLOSED`
   - Persist the complete chain: selection → broadcast → delivery → receiver
     reconstruction → uptake → causal use → outcome → provenance re-entry.
   - Broadcast availability or decodability alone is insufficient.
9. `OOD_TARGET_REPLICATION`
   - Repeat across held-out seeds, contexts, workloads and a registered target
     runtime.  Local synthetic success does not substitute for Andreas Ubuntu
     target attestation.

Only if every gate passes may the status become
`CAUSAL_EMERGENCE_CANDIDATE_OPEN`.  This status remains a bounded research
hypothesis and never means consciousness, phenomenal experience, personhood or
scientific truth.

## Required null family policy

The instrument must record why each permutation/surrogate leaves the null
distribution invariant.  Full shuffle, circular shift, block permutation,
local permutation, episode sign-flip and model-based residual bootstrap are
separate families, not interchangeable implementations.

The default policy is:

- independent episodes: cluster-aware randomization or hierarchical model;
- stationary dependent ticks: dependence-preserving null plus a second
  calibrated family;
- nonstationary or regime-switching ticks: regime-local analysis, explicit
  context conditioning, or abstention;
- unknown dependence: no p-value promotion.

## Power policy

Correct inference can have low power.  The sweep showed episode-cluster power
of only 0.15–0.175 with six episodes for the tested effect, rising to
0.95–0.975 with 48 episodes.  More within-episode ticks did not repair the
shortage of independent episodes.  A low-power result remains `UNKNOWN`; it is
never replaced with a pseudoreplicated tick-level result.

## Immediate integration points

- UnifiedDB: store the receipt fields and gate states without a new scalar.
- GWT/Harness: project matched intervention runs onto receiver-complete episode
  receipts and the existing outcome/causal-credit spine.
- ClayGraph: bind every intervention to exact source, graph and state epochs.
- ClayResearch/Emergenz: retain every negative result and null disagreement.
- FRANK: do not promote until a registered Andreas Ubuntu target run supplies
  complete, rereadable receipts.

## Primary-method anchors

- Romano and Tirlea, *Permutation Testing for Dependence in Time Series*:
  https://arxiv.org/abs/2009.03170
- Shen et al., *Independence Testing for Temporal Data*:
  https://arxiv.org/html/1908.06486v5
- Ciganovic et al., *Double Machine Learning for Time Series*:
  https://arxiv.org/html/2603.10999v1
- Saggioro et al., *Reconstructing regime-dependent causal relationships*:
  https://arxiv.org/abs/2007.00267
- Méloux et al., *Validating Causal Abstraction Metrics*:
  https://arxiv.org/html/2607.00267v1
- Lyu et al., *Multivariate Partial Information Decomposition*:
  https://arxiv.org/pdf/2508.05530
- Gurnee et al., *Verbalizable Representations Form a Global Workspace*:
  https://arxiv.org/html/2607.15495v1
- Rahbar, *The Ignition Index*:
  https://arxiv.org/html/2608.05160v1

