# UnifiedDB Emergence Meter v0.2 Research Delta — OOD Robustness and Abstention

- run_id: `20260809T213500p0700_udb_emergence_meter_robustness_v02`
- actor: `chatgpt-secondary`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- evidence class: `SYNTHETIC_OOD_STRESS_TEST + SOFTWARE_EXECUTION`
- status: `OPEN_RESEARCH_DELTA_NOT_LIVE_VALIDATED`

## Result

The frozen v0.1 decision logic was stress-tested across 4 episode sizes (100, 200,
400, 800), 4 independent measurement-corruption rates (0, 5, 10, 20%), 20 seeds
and 5 preregistered regimes. This produced 1,600 regime runs.

- false causal-emergence promotions on null/additive/common-driver controls: **0**;
- 10/16 cells met the conservative calibrated-region rule;
- 6/16 cells were forced to `INSUFFICIENT_POWER_OR_ROBUSTNESS`;
- at 20% corruption, exact five-regime classification was only 72–78% across all
  tested sample sizes;
- larger n did not restore semantic validity under high corruption.

The calibrated-region rule requires all three:

1. zero causal promotions in negative controls;
2. at least 95% exact expected classification across all regimes;
3. at least 95% sensitivity for the causal XOR + truthful re-entry candidate.

The fast screen uses fewer permutation/bootstrap draws and cannot promote a live
claim. Boundary cells require the full-draw confirmation test.

## Negative result N-UDB-EM-20260809-02

Sample size cannot compensate for corrupted measurement semantics. At 20%
independent channel/outcome corruption, even n=800 retains only 76% exact regime
classification. Therefore `sample_count` must not be used as a surrogate for
measurement quality, receipt completeness or intervention fidelity.

## Hypotheses

### H-UDB-EM-005 — Quality-gated emergence readout

A data-quality vector containing missingness, corruption estimates, clock alignment,
receipt completeness and provenance continuity will predict whether an emergence
assessment lies inside a calibrated region better than sample size alone.

Falsifier: held-out corruptions show no improvement in calibration/error prediction
after adding these quality dimensions.

### H-UDB-EM-006 — Selective confirmation efficiency

A two-stage estimator (fast null/OOD screen followed by full-draw confirmation only
for boundary/candidate cells) preserves the full estimator's false-promotion bound at
materially lower compute cost.

Falsifier: fast screening misses a boundary that the full estimator promotes or the
cost reduction is negligible under representative FRANK traces.

### H-UDB-EM-007 — Corruption topology matters

Independent random corruption is not the worst case. Clock drift, receiver-selective
missingness, duplicated provenance and intervention leakage will produce different
and potentially more dangerous error surfaces.

Next test: block-correlated, receiver-dependent and provenance-preserving adversarial
mutations on copied episodes.

## Literature fusion

The result is consistent with multivariate transfer-entropy work requiring explicit
conditioning and hierarchical statistical testing, and with causal-emergence work
that compares intervention-relevant macro/micro descriptions rather than treating
observational information as causal power. Recent PEID/interventional-causality
preprints strengthen the case for decomposing causal effects, but do not eliminate
finite-sample, estimator or data-quality validation.

Primary/source links:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC6663300/
- https://arxiv.org/html/2501.11447v2
- https://arxiv.org/html/2605.03267v1
- https://arxiv.org/html/2503.13395v3

## Contract delta

Add `data_quality` to every `EmergenceReadout`:

`sample_power`, `missingness`, `estimated_corruption`, `clock_alignment`,
`receipt_completeness`, `provenance_continuity`, `intervention_fidelity`,
`calibration_region_id`, `screening_stage`, `confirmation_required`.

Decision law:

`outside calibrated region -> UNKNOWN / INSUFFICIENT_POWER_OR_ROBUSTNESS`.

Never translate that state to `NOT_SUPPORTED`, and never permit sample count to
override failed receipt/intervention quality.

## Branch feedback

- `unifieddb`: persist calibration-region and data-quality receipts beside metrics.
- `gwt`: every episode/receiver stage must expose receipt completeness and clock basis.
- `emergenz`: add abstention as a first-class evidence state.
- `harness`: add block corruption, clock drift, selective missingness and leakage tests.
- `claycode`: type `UNKNOWN` and `INSUFFICIENT_POWER_OR_ROBUSTNESS`; forbid implicit zero.
- `frank`: measurement plane stays read-only and cannot authorize behavior.
- `claygraph`: provenance continuity and topology epoch are measured inputs, not truth.
- `hyperposition`: test n-ary readouts under receiver-selective missingness.

## Evidence boundary

This is a reproducible synthetic OOD result, not live FRANK validation. The live gate
still requires stable episode/receiver receipts, copied-episode factorial replay,
lesion/rescue, truthful-vs-shuffled re-entry and implementation/OOD transfer.

