# EF-20260809-001 — Conformal Familiarity Metrology

Status: TESTED / READY_FOR_MESH_INTEGRATION
Trigger: `666`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Spawn seed: `18192266457284498906`
Seed material hash: `fc77e9f4c5b255da64478b2f0b75c7f5071503f33f80277fae24e4787773ecf9`
Program stage at spawn: `BASE_CLAYCODE_RELEASE`

## 1. Spawn decision

Candidate lens families were scored for novelty, orthogonality, cross-branch connectivity, falsifiability, information gain, milestone relevance, duplication and vague-metaphor risk. A seeded stochastic choice among the high-value candidates selected:

**Conformal Familiarity Metrology** — measurement/metrology + conformal/risk-control ideas applied to FRANK's adaptive visual familiarity gate.

This field does not claim that conformal prediction should replace the Micro Visual Classifier. It asks a narrower question:

> What statistical receipt is sufficient to justify the `KNOWN_HIGH_CONFIDENCE` fast path without laundering familiarity into sensor truth?

## 2. Internal grounding and cross-reads

Cross-read branches/artifacts:

1. `claycode` — `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
   - BASE is `NOT_PASS`; current rule is less semantic redesign, more compiler/runtime implementation.
   - ClayCode must still represent explicit epistemic/error states, provenance, replay and FRANK state transitions.

2. `gwt` — `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
   - measurement values must remain distinct from inferred claims, evidence status and architecture state;
   - observability must not silently gain cognitive/state authority.

3. FRANK/Retina — `research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md` and `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md`
   - `familiarity != evidence`, `confidence != authority`;
   - unknown/ambiguous/conflict must escalate;
   - MVC-E5 open-set rejection is mandatory.

## 3. External research

Primary/research sources consulted:

- Bates et al., **Distribution-Free, Risk-Controlling Prediction Sets** (2021), arXiv:2101.02703 — finite-sample risk control from held-out calibration under the method's assumptions.
- Angelopoulos et al., **Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control** (2021), arXiv:2110.01052 — explicit risk calibration including outlier/error-control examples.
- Angelopoulos, Barber & Bates, **Online conformal prediction with decaying step sizes** (ICML 2024) — online conformal methods for changing sequences.
- Podkopaev & Ramdas, **Distribution-free uncertainty quantification for classification under label shift** (UAI 2021) — ordinary coverage/calibration can degrade under shift; reweighting can restore guarantees for the modeled shift.
- Kasa et al., **Adapting Prediction Sets to Distribution Shifts Without Labels** (UAI 2025) — conformal prediction sets can degrade under distribution shift and can be adapted using unlabeled shifted-domain data.
- Almeida et al., **High Probability Risk Control Under Covariate Shift** (COPA 2025) — risk-control extensions explicitly model covariate shift rather than pretending calibration and target distributions are identical.

Evidence-class note: these papers support calibration/risk-control mechanisms and their assumptions. They do not establish FRANK-specific safety or performance.

## 4. Hypotheses and counterhypotheses

### H-CFM-1 — useful but limited calibration layer

A versioned calibration/risk receipt over the Micro Visual Classifier score can make the familiar fast path more measurable and falsifiable than an unqualified confidence threshold.

Status: `OPEN_SUPPORTED_AS_DESIGN_DIRECTION`.

### CH-CFM-1 — known-only conformal coverage is not open-set safety

A threshold calibrated to retain approximately 95% of known examples does **not** by itself bound false familiarity for unseen classes whose embeddings overlap the known manifold, especially under user-specific distribution shift.

Status: `SUPPORTED_BY_COUNTEREXAMPLE`.

### CH-CFM-2 — even explicit unknown-negative calibration is shift-scoped

A threshold calibrated on one unknown-negative distribution can fail on a shifted unknown distribution. Any risk receipt must therefore encode its calibration domain/version/age and a validity or drift state.

Status: `SUPPORTED_BY_COUNTEREXAMPLE + LITERATURE_CONSISTENT`.

## 5. Executed synthetic falsification

Artifact: `EXPERIMENT_SYNTHETIC_OPEN_SET.json`

Setup:
- two synthetic known prototype clusters in 2D;
- acceptance by distance to nearest known prototype;
- threshold calibrated for approximately 95% known acceptance;
- three unknown populations: far, midpoint, and a shifted near-confuser overlapping the known neighborhood.

Observed rates:

- known acceptance: **95.37%**;
- far unknown accepted as familiar: **0.00%**;
- midpoint unknown accepted as familiar: **5.10%**;
- near shifted confuser accepted as familiar: **73.27%**.

A second threshold chosen to produce about 5% empirical acceptance on the midpoint-unknown calibration distribution still accepted **73.41%** of the shifted near-confuser population.

This is a synthetic counterexample, not an estimate of FRANK's real performance. It falsifies only the strong guarantee that calibration on known data or on one frozen unknown distribution is sufficient for general open-set safety.

## 6. New architecture constraint

The visual fast path should expose a typed, replayable measurement receipt such as:

```text
FamiliarityCalibrationReceipt {
  feature_backbone_version
  classifier_or_prototype_version
  calibration_version
  calibration_set_hash
  calibration_domain
  score_kind
  score_value
  threshold_or_prediction_set
  target_risk_or_alpha
  empirical_or_bounded_risk
  support_count
  calibration_age
  drift_status
  validity_status
  unknown_negative_coverage_status
  evidence_tier_summary
  source_receipts
}
```

Hard rule:

`calibrated_score != sensor_truth != semantic_authority`

Recommended bypass contract:

`KNOWN_HIGH_CONFIDENCE_FAST_PATH` is permitted only when the classifier result, calibration validity, open-set/unknown-risk evidence, provenance and conflict checks all pass. Any stale/invalid/shifted/unsupported state falls back to deeper Retina.

## 7. ClayCode implication

Current evidence does **not** justify a new ClayCode language primitive. The current BASE policy explicitly prefers implementation over semantic churn unless an executable counterexample proves the language cannot express the needed behavior.

Required BASE consequence instead:

- ensure ordinary typed records/enums can express the receipt above;
- preserve `UNKNOWN`, `CONFLICT`, invalid/stale calibration and version incompatibility;
- include hashes/provenance/version identities and deterministic replay hooks;
- keep measurement/risk state distinct from authority/effect state;
- add a conformance/application test showing candidate promotion/rollback and calibration invalidation can compile/lower/execute without opaque host semantics.

If current ClayCode cannot express this using existing core semantics, that becomes a concrete executable counterexample for `CC-WP-03/04/05/11/13`, not a speculative redesign request.

## 8. GWT / observability implication

The calibration receipt belongs to the same epistemic pattern as GWT emergence readouts:

`measured_value != inferred_claim != evidence_status != architecture_state`

Therefore the receipt should be readable by the model/Workspace when useful, but computed/validated in an observability/measurement path that cannot silently authorize the fast path without the runtime gate.

## 9. Harness / Retina test delta

Extend `MVC-E5` with at least:

1. far unknowns;
2. visually/embedding-near unknown confusers;
3. temporal/domain shift between calibration and test;
4. stale calibration after prototype/classifier update;
5. feature-backbone version migration;
6. candidate-vs-current false-familiarity risk comparison;
7. explicit abstention/escalation rate and resulting Retina compute cost;
8. adversarially selected near-manifold unknowns where feasible.

The acceptance metric should not be known-class accuracy alone. Track false familiarity, abstention/escalation, retained known coverage, calibration validity, and compute/task impact together.

## 10. Negative result preserved

`NEGATIVE_RESULT EF-CFM-N1`:

> Known-class confidence or known-only conformal coverage cannot be promoted to a general open-set safety guarantee for FRANK's user-adaptive visual learner.

This strengthens the existing architectural boundary rather than replacing it.

## 11. Mesh routing

Affected rooms:
- `claycode`: typed receipt/conformance requirement; no semantic redesign yet.
- `frank`: fast-path gate becomes explicitly calibration-validity + open-set-evidence dependent.
- `gwt`: preserve readout/claim/authority separation.
- `harness`: expand MVC-E5 with near-confuser and distribution-shift slices.
- `claygraph` / `unifieddb`: later persistence should retain calibration/version/domain/validity lineage, but no premature physical database decision is implied.

## 12. Best next falsifier

Run the same gate comparison on real frozen Retina embeddings collected from:
- recurring known user UI/layout classes;
- semantically different but visually/embedding-near confusers;
- time-separated sessions;
- feature-backbone/version changes.

Compare prototype distance, linear-head confidence, conformal/prediction-set calibration, and an explicit unknown-risk gate under identical replay. If the calibrated two-gate design does not reduce false familiarity at acceptable compute/escalation cost, this field should close as `NO_CHANGE` or be merged into the existing MVC confidence/open-set work rather than promoted.
