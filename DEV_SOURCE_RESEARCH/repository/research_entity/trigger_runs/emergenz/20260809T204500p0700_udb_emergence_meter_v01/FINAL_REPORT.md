# Emergenz × UnifiedDB Research Delta — Evidence-Preserving Mutation Meter v0.1

- run_id: `20260809T204500p0700_udb_emergence_meter_v01`
- actor: `chatgpt-secondary`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- home_room: `emergenz`
- linked_rooms: `unifieddb`, `gwt`, `frank`, `harness`, `claycode`, `claygraph`, `hyperposition`
- program_stage: `BASE_CLAYCODE_RELEASE`
- mode: `SOLO_RESEARCHER`
- evidence_class: `REAL_REPO_DB_SNAPSHOT_OBSERVATION + SYNTHETIC_MECHANISM_INTERVENTION`
- claim_status: `OPEN_RESEARCH_DELTA_NOT_LIVE_VALIDATED`

## Outcome

An executable UnifiedDB emergence measurement and mutation laboratory now exists. It stores immutable source identities, derived episodes, transformations, held-fixed variables, channel samples, estimator receipts and vector assessments. It never changes the source database and never emits a scalar consciousness/emergence score.

The meter currently separates five preregistered calibration regimes:

| Regime | Correct disposition |
|---|---|
| independent null | `NOT_SUPPORTED` |
| additive/proxy-confounded | `INTERACTION_ONLY` |
| common driver | `NOT_SUPPORTED`; common-driver control fails |
| XOR + lesion/rescue but no truthful re-entry | `MECHANISM_SUPPORTED_NOT_EMERGENCE` |
| XOR + lesion/rescue + truthful re-entry | `CAUSAL_EMERGENCE_CANDIDATE_OPEN` |

All deterministic regression tests pass, including exact same-seed reproduction.
After an initial seed sweep exposed noisy raw-Omega warnings, the detector was
revised to require a dedicated factorial permutation test (`p <= 0.01`). A
second sweep over 20 independent seeds, 800 samples per regime and 100 total
regime runs classified all 100 as preregistered, with zero false causal-
emergence promotions on negative controls.

## Real copied FRANK database evidence

The copied repository database surface contains at least:

- 21,443 `aura_analyzer.snapshots` rows;
- 704 `thought_aura_correlations` rows;
- 1,123 `acc_monitor.conflict_log` rows;
- 208 `consciousness.workspace_state` rows;
- 200 `attention_log` rows;
- 15 `action_outcomes` rows.

Five thousand ordered Aura snapshots were imported into the lab and transformed into three parent-linked episodes:

1. unchanged baseline copy;
2. joint time permutation preserving row count and marginals;
3. entropy-source shuffle preserving target order, other channels and marginals.

The lab database contains 60,000 channel samples for one probe invocation and passes SQLite `PRAGMA integrity_check`.

### Negative/confounder result N-UDB-EM-20260809-01

`global_density` and `global_entropy` are effectively duplicate sources in the sampled trace:

- Pearson correlation: approximately `0.999701`;
- quartile-discretized normalized mutual information: `1.0`.

They MUST NOT be counted as two independent integration/synergy axes. This is a concrete anti-double-counting rule for the estimator bank.

### Observational lag result

Peak conditional mutual information toward `coherence`, conditioning on target history, is small:

- `density -> coherence`: about `0.012905 bit` at tested lag 8;
- `entropy -> coherence`: about `0.012905 bit` at tested lag 8;
- `change_rate -> coherence`: about `0.009654 bit` at tested lag 8.

The peaks generally shrink under time/source shuffling, but this remains directed-prediction proxy evidence, not intervention causality. No emergence claim is promoted from it.

## Architecture finding

The current `services/global_workspace.py` is a synchronous in-process broadcast bus with a 100-event ring buffer. It records event type, source, data and salience, but does not provide stable WorkspaceEpisode identity or separate receipts for:

`addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`.

Therefore the current repository databases cannot finish live causal emergence validation without new observability hooks. Existing data can calibrate nulls and confounders; future runtime data must supply the missing causal chain.

## Measurement contract delta

Add the following mandatory controls to `EmergenceEstimatorBank`:

1. source redundancy matrix before PID/PEID or interaction aggregation;
2. common-driver conditional-information control;
3. matched marginal-preserving time shuffle;
4. single-source/edge shuffle;
5. lesion loss plus bounded rescue recovery;
6. truthful vs shuffled/provenance-broken re-entry;
7. same-seed and cross-seed reproducibility;
8. estimator/version/sample/source/result hashes;
9. evidence ladder and explicit falsifiers;
10. UNKNOWN for missing causal stages rather than zero.

Factorial interaction specifically requires both a material effect and its own
permutation control. The first uncorrected threshold produced harmless but noisy
`INTERACTION_ONLY` warnings; that negative calibration result is retained as
method memory rather than hidden.

## Hypotheses and counterhypotheses

### H-UDB-EM-001 — Receipt-complete discriminability

A UnifiedDB meter using the full causal receipt chain plus redundancy/common-driver/null controls will distinguish higher-order re-entry mechanisms from additive, duplicated-source and common-driver systems across held-out seeds.

Falsifier: false-positive rate exceeds the preregistered bound on null/additive/common-driver controls, or true mechanisms fail under implementation-preserving replay.

### H-UDB-EM-002 — UDB counterfactual sufficiency

Parent-linked immutable episodes plus held-fixed intervention specifications are sufficient to reproduce every measurement decision independently of mutable runtime state.

Falsifier: the same source/contract/seed hashes produce a different metric receipt or a decision depends on unrecorded state.

### H-UDB-EM-003 — Redundancy inflation

Treating `density` and `entropy` as independent sources will inflate integration or synergy estimates without adding causal information.

Discriminating test: compare PID/PEID and candidate classification before and after redundancy collapse while preserving the outcome and all other channels.

### H-UDB-EM-004 — GWT receipt completion

Stable per-stage episode/receiver receipts will turn currently weak observational lag candidates into either lesion-sensitive paths or rejected correlations.

Counterhypothesis: the lag signal is entirely driven by shared update functions/quantization and disappears under frozen-output intervention.

## Literature fusion

- Rosas et al. provide practical information-theoretic criteria for causal emergence and distinguish irreducible macro features from parts.
- Hoel et al. motivate matched micro/macro effective-information comparison rather than assuming a coarse-graining is superior.
- Varley et al. show how partial entropy decomposition exposes higher-order structure but do not license causal interpretation without interventions.
- Novelli/Wollstadt et al. show why multivariate/conditional transfer-entropy inference and hierarchical statistical testing are needed to reduce pairwise false positives.
- Recent PEID work proposes intervention-based decomposition of unique and synergistic effective information; it is promising but remains a 2026 preprint and must be independently validated before becoming authoritative.

## Branch feedback

- `unifieddb`: adopt the receipt schema provisionally; do not freeze physical layout before H1-H3 access traces.
- `gwt`: instrument stable episode/receiver stages and Causal Ignition Concordance axes.
- `frank`: keep the measurement plane logically read-only relative to cognitive/authority state.
- `harness`: add immutable snapshot mutation, frozen-model-output replay, redundancy collapse and common-driver controls.
- `claycode`: needs first-class episode, intervention, estimator, uncertainty, evidence and hash types; current Python is H1-style reference semantics only.
- `claygraph`: attach exact topology epoch/path IDs; graph activation never substitutes for causal use.
- `hyperposition`: supply n-ary vs best-pairwise reduction candidates.
- `emergenz`: promote no candidate beyond its lowest missing causal gate.

## Evidence boundary and next cycle

The measurement instrument is now executable and calibrated on controlled cases, and it has found a real copied-data confounder. It is not yet "reliably validated in live FRANK" because the current runtime lacks receipt-complete GWT episodes and BASE/H1 remain unfinished.

The next highest-information experiment is a copied-episode factorial replay:

`broadcast intact/lesioned × re-entry truthful/shuffled × redundant sources kept/collapsed`,

with model output frozen, receiver-use/outcome recorded and cross-seed/OOD replication. Live promotion requires bounded false positives, lesion/rescue, truthful re-entry, implementation transfer and rollback evidence.

No paid training was started. Together was not used.
