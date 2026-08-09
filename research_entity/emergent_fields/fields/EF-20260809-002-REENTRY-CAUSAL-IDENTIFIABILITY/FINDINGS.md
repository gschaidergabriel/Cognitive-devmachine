# EF-20260809-002 — Re-entry Causal Identifiability

## Spawn

- Trigger: `666`
- Post-Level-0 emergent-field mode
- Seed: `8560758903970440746`
- Lens: dynamical systems × causal inference
- Program attractor: `BASE_CLAYCODE_RELEASE`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol

## Why this field exists

A concurrent `666` worker had already spawned **Proof-Carrying Adaptive State**, materially overlapping this worker's first adaptive-familiarity candidate. The duplicate was therefore not counted as a new independent field. This field is the orthogonal resample.

## Question

When FRANK observes recurrent information flow between workspace, memory, receiver and re-entry channels, when is that flow actually causal rather than a by-product of shared state, scheduler timing or another common driver?

## Core mechanism

Treat observational directionality as a **screening layer**, not causal certification:

`directed prediction / TE signal`
`-> explicit conditioning/common-driver audit`
`-> matched counterfactual replay`
`-> edge/re-entry lesion`
`-> targeted rescue`
`-> only then stronger causal evidence status`

This directly matches the existing GWT contract's distinction that directed estimators are not proof of causality and the Hyperposition requirement for edge/hyperedge lesions, delay perturbations and rescue.

## External primary evidence

- **Panayiotou & Simsek, CLeaR 2026 (PMLR 323)**: blocking interventions can identify causal structure in chain-reaction dynamical systems where observational heuristics fail under delayed/overlapping effects.
- **Bica et al., ICML 2020 (PMLR 119)**: hidden confounding in longitudinal systems can bias causal-effect estimates and requires explicit treatment.
- **Gunther, Ninad & Runge, UAI 2023 (PMLR 216)**: time-series causal discovery benefits from explicitly representing observed/latent contexts and common drivers.
- **Jahn, Karnik & Schulman, CLeaR 2025 (PMLR 275)**: causal effects in time-series graphs with latent confounding require identifiability analysis, not directional association alone.

These establish a scientific prior for intervention/deconfounding discipline, not FRANK-specific proof.

## Synthetic discriminating test

Two systems shared a lagged common driver C.

### No direct A -> B coupling

Adding lagged A to a B autoregression still produced about **32.2% directed prediction gain** and an apparent A coefficient of about **0.437**. After conditioning on C the A coefficient fell to about **-0.003**. With matched exogenous noise, clamping A to zero changed B by **0.0**.

### True A -> B coupling = 0.35

The conditioned A coefficient recovered about **0.346**. Clamping A produced downstream B change of about **1.156 MAE / 1.446 RMS**.

The important result is qualitative: a strong observational directional signal existed in the zero-causal-edge case. Intervention separated the two mechanisms.

Synthetic only; no FRANK claim is promoted.

## Cross-branch delta

### GWT / Emergenz

Do not advance a re-entry mechanism above observational/predictive evidence merely because TE or directed prediction gain is high. Require explicit common-driver controls and matched lesions/rescues for stronger causal status.

### Hyperposition

Scheduler/shared-state topology is itself a possible common driver. Preserve conditioning-set identity, active topology hash and intervention target so apparent coupling can be audited against shared causes.

### Harness

Add a Golden confound family where two channels have strong lagged predictive dependence caused only by a third shared state. The test should verify that observational estimators fire but lesion effect stays null. Pair it with a true-coupling twin where the same lesion produces the expected loss and rescue restores it.

### ClayGraph

Record the distinction between `PREDICTIVE_EDGE`, `CONDITIONED_FLOW`, `INTERVENTION_SUPPORTED_EDGE` and `RESCUE_SUPPORTED_EDGE`; graph connectivity must not silently imply causal use.

### ClayCode BASE

Current contracts already require enough semantic room to represent conditioning sets, intervention specs, estimator identity, lags, control results and provenance. No new primitive is justified unless a compiler/runtime counterexample appears.

## Next test

In H1, generate paired Golden traces with:

1. shared memory/scheduler common driver and no direct re-entry edge;
2. same observable lag pattern plus a true re-entry edge;
3. frozen model output;
4. matched seeds/input/state;
5. raw directed-flow estimator;
6. conditioned estimator;
7. edge lesion;
8. delay perturbation;
9. truthful-vs-shuffled re-entry;
10. rescue.

A valid measurement stack should assign materially different causal evidence despite superficially similar observational flow.

## Status

`SUPPORTED_WORKING_HYPOTHESIS_SYNTHETIC_PLUS_PRIMARY_CAUSAL_LITERATURE`

Not promotable until H1/Harness executes matched FRANK traces.
