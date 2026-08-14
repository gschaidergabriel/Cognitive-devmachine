# v0.3.1 Live-Refresh Addendum — State Adequacy and Auditability

## Why this addendum exists

A final live primary-source refresh found two method papers that materially
extend the v0.3 gate rather than merely restating it:

- *Conditioning-Depth Diagnostics for Hidden Memory in Temporal Causal
  Discovery* tests whether an inferred graph stabilizes as observed history is
  added.  It explicitly treats instability as a warning for state inadequacy,
  not as identification of the hidden mechanism.
- *AutoCause* records method choice, lag horizon, conditional-independence
  tests, sample adequacy, false-discovery control, surrogate diagnostics and
  method support.  Its majority-supported links improve precision on synthetic
  benchmarks but not against the river-topology reference; consensus is not
  truth.

FlowMSM additionally supplies a possible latent-regime route, but its
identifiability result is conditional on a declared model class, temporal regime
structure, nonlinear lagged/instantaneous effects and independent
exponential-family noise.  It is a candidate method, not a universal repair.

## New synthetic discriminator

A persistent binary source was used in two models:

1. true direct candidate: `Y[t] = X[t-1] XOR noise`;
2. omitted-history candidate: `Y[t] = X[t-3] XOR noise`, while testing the
   apparent `X[t-1] -> Y[t]` link.

For each conditioning depth `d`, the test added source lags `2..d+1` and target
lags `1..d`.  Twenty seeds with 20,000 samples each were executed.

| Candidate | Unconditioned information | Depth-1 conditional information | Retention |
|---|---:|---:|---:|
| True lag-1 path | 0.53157 bits | 0.17353 bits | 0.32645 |
| Apparent lag-1 path from omitted lag 3 | 0.24303 bits | 0.000090 bits | 0.000372 |

The omitted-history edge almost vanished when one additional history layer was
conditioned, while the true path retained a stable nonzero conditional signal
through depths 1–4 (0.1735–0.1758 bits).

## Gate revision

Insert `STATE_ADEQUACY_STABILITY` after context closure and before causal edge
promotion:

1. Predeclare a comparable conditioning-depth sequence and fixed candidate lag.
2. Record estimator, conditioning variables, effective samples and bootstrap or
   surrogate calibration at every depth.
3. A materially unstable edge yields `ABSTAIN_STATE_INADEQUATE`.
4. Stability only survives this falsifier; it does not establish causal
   sufficiency, identify the missing process or close latent confounding.
5. Adaptive parent-selection methods must not be forced into a nominal depth
   comparison that changes a different object at each depth.

Insert `AUDITABLE_MULTI_METHOD_SUPPORT` as a diagnostic, not a voting rule:

- Record all method/configuration decisions, support counts and FDR handling.
- Non-causal reference models and surrogate controls remain mandatory.
- Majority support can increase confidence only inside a calibrated regime.
- Consensus cannot override violated assumptions, pathwise counterevidence or
  a registered-target failure.

## New hypotheses and counterhypotheses

### H-UDB-EM-014

Hypothesis: conditioning-depth stability distinguishes a direct temporal edge
from an edge created by omitted predictive history.

Counterhypotheses:

- a real but weak or highly predictable edge can lose conditional information;
- CMI bias grows with conditioning dimension;
- stable edges can still be confounded;
- instability diagnoses state inadequacy but not its cause.

Adjudication: `SUPPORTED_AS_ONE_FALSIFIER_ONLY`.

### H-UDB-EM-015

Hypothesis: auditable multi-method support tiers reduce configuration-specific
false promotion.

Counterhypotheses:

- methods may share assumptions and correlated failure modes;
- majority support failed to improve precision against AutoCause's real river
  topology reference;
- support count does not supply causal identification.

Adjudication: `OPEN_DIAGNOSTIC_POLICY_NOT_VOTING_TRUTH`.

## Non-claim boundary

This addendum is synthetic method evidence.  It is not live FRANK validation,
not registered Andreas Ubuntu execution, not causal-emergence truth and not a
consciousness result.

## Fresh primary sources

- AutoCause: https://arxiv.org/html/2608.00198v1
- Conditioning-Depth Diagnostics: https://arxiv.org/html/2606.01214v2
- Identifiable Markov Switching Models / FlowMSM:
  https://arxiv.org/html/2606.02231v1

