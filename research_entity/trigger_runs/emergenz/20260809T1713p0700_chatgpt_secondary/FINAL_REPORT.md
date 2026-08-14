# Emergenz Trigger Run — 2026-08-09

## Run identity

- run_id: `20260809T1713p0700_chatgpt_secondary`
- trigger: `emergenz`
- actor_id: `chatgpt-secondary`
- provider: OpenAI
- model: GPT-5.6 Sol
- canonical parent revision: `2`
- canonical parent state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- program stage: `BASE_CLAYCODE_RELEASE`
- evidence status of new claims: `OPEN`
- promotion: none

## Scope

Research measurable functional/causal emergence for FRANK/Synthetic-Clay with emphasis on intervention-sensitive GWT/Hyperposition readouts and what BASE ClayCode must represent now.

This run does not infer phenomenal consciousness from functional integration, synergy, recurrence, criticality, graph complexity or workspace ignition.

## Internal evidence used

Primary current contracts:

- `research_entity/triggers/EMERGENCE_RESEARCH_PROTOCOL.md`
- `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/global/RESEARCH_CENTER_PROGRAM_NARRATIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`

The current contracts already require a typed emergence vector, causal receipts, lesion/rescue, truthful-vs-shuffled re-entry, PID/PEID-style decomposition, directed information flow, macro-vs-micro causal contribution, OOD transfer, null controls and cost shadows.

Room pulse note: `research_entity/rooms/rooms/emergenz/state/ROOM_STATE.json` returned 404 on this connector surface, so this run does not claim a complete live-room pulse or full interconnect preflight. The run remains domain-loyal and records this coordination gap explicitly.

## External evidence

### E1 — Rosas et al. 2020, PLOS Computational Biology

`Reconciling emergences: An information-theoretic approach to identify causal emergence in multivariate data.`

Key relevance:
- formalizes causal emergence through irreducible dynamical information of supervenient features;
- separates downward causation and causal decoupling;
- provides practical criteria derived from PID / PhiID;
- observational predictive criteria should not be confused with intervention-proven causality.

Source: https://doi.org/10.1371/journal.pcbi.1008289

### E2 — Proca et al. 2024, PLOS Computational Biology

`Synergistic information supports modality integration and flexible learning in neural networks solving multiple tasks.`

Key relevance:
- ANN synergy increases in multi-source / multi-task learning settings;
- synergistic units can be important for integration and flexible learning;
- redundancy is associated with robustness under perturbation/noise.

Implication: synergy and robustness are not the same axis; both should remain separately measured in FRANK emergence readouts.

Source: https://doi.org/10.1371/journal.pcbi.1012178

### E3 — Varley 2024, npj Complexity

`A scalable synergy-first backbone decomposition of higher-order structures in complex systems.`

Key relevance:
- full PID has scaling limits;
- a synergy-first backbone provides a more scalable spectrum of higher-order synergistic structure;
- synergy is operationalized through information lost under minimally invasive perturbation of elements;
- the approach can extend from information measures to structural/network integration.

Implication: use a scalable synergy-first estimator for broad screening, then expensive PID/PhiID only on selected candidate assemblies/subgraphs.

Source: https://doi.org/10.1038/s44260-024-00011-1

### E4 — Zhang et al. 2025, npj Complexity

`Dynamical reversibility and a new theory of causal emergence based on SVD.`

Key relevance:
- classical EI-based causal emergence depends on coarse-graining choice;
- the paper proposes an SVD/dynamical-reversibility formulation intended to reduce dependence on a specific coarse-graining;
- theoretical and numerical examples connect reversibility and effective-information style causal emergence.

Implication: a FRANK macro-causal claim should carry an explicit macro-construction/coarse-graining identity and be challenged by at least one independent macro construction where feasible.

Source: https://doi.org/10.1038/s44260-025-00028-0

### E5 — Liardi et al. 2025, PLOS Computational Biology

`Null models for comparing information decomposition across complex systems.`

Key relevance:
- raw PID atoms can change strongly with total mutual information even when the underlying source-target relationship is otherwise fixed;
- naive normalization by total mutual information can still produce misleading cross-system conclusions;
- NuMIT compares PID atoms against null ensembles matched on total mutual information and reports relative position/quantile.

Implication: raw or MI-normalized synergy must not be used as a cross-condition emergence score without a null-model calibration strategy.

Source: https://doi.org/10.1371/journal.pcbi.1013629

### E6 — Murphy, Yin & Bassett 2024, arXiv

`Which bits went where? Past and future transfer entropy decomposition with the information bottleneck.`

Key relevance:
- transfer entropy can be decomposed to localize which parts of source past and target future carry transferred information;
- useful as a candidate-edge / temporal localization tool;
- consistent with current Clay rule that directed prediction/information flow does not itself prove causality without intervention.

Source: https://arxiv.org/abs/2411.04992

## Synthetic falsification-oriented check

A small analytic Gaussian check was run locally to test the NuMIT-motivating failure mode.

Model:

`X,Y,N ~ independent N(0,1)`

`T = X + Y + g*N`

The coupling coefficients from X and Y to T remain fixed; only noise scale `g` changes.

Using the Gaussian MMI-PID relation:

- at `g = 5`, `synergy / total_MI ~= 0.510`
- at `g = 1`, `synergy / total_MI ~= 0.631`
- at `g = 0.1`, `synergy / total_MI ~= 0.870`

Thus even the simple `synergy / total_MI` ratio changes substantially under a pure SNR manipulation while the source coefficients remain fixed. This reproduces the qualitative failure mode highlighted by Liardi et al. and supports a null-normalized comparison requirement.

Epistemic class: `SYNTHETIC_LOCAL_CHECK`.
It is not evidence that any FRANK mechanism is emergent.

## Fusion 1

The existing FRANK emergence contract is directionally strong but underspecifies three anti-Goodhart details:

1. cross-condition information-decomposition normalization;
2. scalable screening before expensive full PID/PhiID;
3. explicit coarse-graining / macro-construction robustness.

These are measurement-contract gaps, not evidence that emergence exists.

## Hypothesis matrix

### H-EM-20260809-01 — Null-normalized synergy is a safer cross-condition discriminator

Mechanism:
Raw or MI-normalized PID atoms confound structural information mode with changes in total information/SNR. A matched-null quantile should reduce this confound.

Prediction:
Across replay conditions that preserve mechanism but alter noise/sample entropy, NuMIT-style quantiles are more stable than raw/NMI synergy; true structural intervention changes shift the null-normalized statistic.

Counterhypothesis:
Null matching may remove biologically/computationally meaningful SNR-driven changes and hide a real mechanism.

Falsifier/test:
Use synthetic ground-truth systems with known mechanism + independent SNR sweeps, then FRANK frozen-episode replay with noise-only vs coupling interventions.

Status: `OPEN`.

### H-EM-20260809-02 — Two-stage synergy estimation reduces cost without losing useful candidates

Mechanism:
Use scalable synergy-first backbone measures to screen many module/Assembly sets, then run full PID/PhiID only on top candidates and controls.

Prediction:
On small systems where exhaustive PID is feasible, screening recall for truly high-order candidates remains high while estimator cost falls sharply as dimensionality grows.

Counterhypothesis:
The backbone loses element-specific structure and misses important candidates that full PID detects.

Falsifier/test:
Benchmark candidate recall/precision against exhaustive PID on small synthetic and H1 Golden traces; require explicit false-negative bounds before adopting as a gate.

Status: `OPEN`.

### H-EM-20260809-03 — Macro-causal claims should be robust to macro-construction family

Mechanism:
If a macro effect only exists under one hand-selected coarse-graining, it may be an analyst artifact rather than a stable system property.

Prediction:
Strong candidates retain sign/order or intervention conclusions under at least two independently motivated macro constructions, e.g. semantic Workspace/Assembly states versus a data-driven dynamical-reversibility/SVD family.

Counterhypothesis:
Some genuine emergent features are task-semantic and only visible under the correct macro variable; demanding cross-graining agreement could reject them incorrectly.

Falsifier/test:
Compare semantic macro, learned macro and SVD/reversibility-derived macro views on systems with known emergent macrostates and on null systems. Permit justified single-graining survival only with stronger intervention evidence.

Status: `OPEN`.

### H-EM-20260809-04 — Re-entry specificity requires truthful causal identity, not extra context

Mechanism:
A recurrent effect attributed to re-entry should depend on content + temporal/provenance identity, not merely on the presence of extra tokens/state.

Prediction:
Truthful provenance-bound re-entry outperforms temporal shuffle, receiver shuffle, provenance-broken replacement and no-reentry controls on future causal-use/outcome metrics; lesion loss is rescued by faithful restoration.

Counterhypothesis:
The observed gain comes from generic extra context or compute rather than re-entry specificity.

Falsifier/test:
Matched frozen-model-output replay across the five re-entry conditions, with latency/token/compute shadows.

Status: `OPEN`.

## Fusion 2 — proposed measurement pipeline

For each candidate emergent mechanism:

1. freeze episode/state/provenance;
2. run additive/common-driver/graph-only/workspace-only controls;
3. broad screening with scalable higher-order/synergy estimator;
4. null-normalize information-decomposition comparisons across conditions;
5. selective full PID/PhiID on candidate assemblies plus matched nulls;
6. directed-flow/lag localization (TE or directed prediction gain) as candidate routing evidence;
7. matched lesion + rescue;
8. truthful vs shuffled/provenance-broken re-entry;
9. macro-vs-micro causal contribution with explicit macro-construction identity;
10. challenge with an independent macro-construction where feasible;
11. OOD/task/topology/implementation transfer;
12. retain cost, instability, recovery and estimator-uncertainty shadows.

No single scalar is promoted as `emergence`.

## BASE ClayCode research delta

Current-stage implication: ClayCode must be able to represent not only values but the comparison/normalization method and macro-construction provenance.

Recommended additions to the eventual executable measurement schema:

```text
measurement_role: SCREENING | CONFIRMATORY
estimator_family
estimator_version
normalization_method
null_model_family
null_ensemble_spec_hash
null_sample_count
null_quantile_or_pvalue
source_total_information
screening_candidate_rank
confirmatory_estimator_ref
macro_construction_id
macro_construction_family
coarse_graining_spec_hash
cross_graining_stability
intervention_receipt_refs
reentry_control_family
cost_shadow_ref
ood_transfer_ref
```

Hard semantic distinctions:

`raw_measure != normalized_measure != significance_vs_null != causal_claim != evidence_status`

`screening_signal != confirmatory_evidence`

`macro_representation != macro_causal_power`

This is a concrete input to `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT`, `CC-WP-11-FUZZ-CONFORMANCE`, and later H1 measurement implementation.

## Cross-branch feedback

- GWT: extend `EmergenceReadout.interaction` controls with estimator/normalization/null-ensemble identity.
- Hyperposition: higher-order irreducibility should use screening-vs-confirmatory estimator separation and matched nulls.
- ClayCode: represent null model specifications, macro-construction identity and evidence-status separation in executable IR.
- Harness: H1 replay surface should include noise-only/SNR controls in addition to coupling lesions so PID drift can be diagnosed.
- ClayGraph: attach estimator/null/macro-construction provenance to readout nodes/edges.
- UnifiedDB: retain raw values, normalized values, null distributions/quantiles and estimator versions separately; never overwrite raw evidence.
- FRANK: model-readable summaries may expose normalized readouts but cannot self-certify them.

## Negative results / non-results

- No live FRANK emergence mechanism was proven in this run.
- No target Harness replay was available/executed here.
- No phenomenal-consciousness inference is supported.
- Same-room live pulse state was unavailable at the expected materialized path on this connector surface.
- Full repository interconnect preflight and provider-router scripts were not executable on this connector surface; therefore no strong canonical promotion is claimed.

## Strongest surviving conclusion

The most actionable delta is methodological: FRANK's emergence readout should add **null-normalized information-decomposition semantics plus explicit macro-construction provenance**, and should use scalable synergy screening only as a precursor to intervention-backed confirmatory tests.

This improves anti-Goodhart protection without collapsing emergence into a scalar and directly serves the current BASE ClayCode gate.

## Next discriminating experiment

Create a small H1-compatible emergence benchmark matrix with four mechanism families:

1. pure additive;
2. redundant/robust;
3. synergistic integration;
4. recurrent provenance-specific re-entry.

For each, sweep SNR and sample size, then compare:

- raw PID;
- MI-normalized PID;
- NuMIT-style null quantile;
- synergy-first screening backbone;
- factorial Omega;
- lesion/rescue;
- truthful-vs-shuffled re-entry;
- macro causal gain under two macro-construction families.

Pre-register which signatures should and should not fire for each family. Use this as the Golden null/candidate corpus before any live FRANK emergence promotion.
