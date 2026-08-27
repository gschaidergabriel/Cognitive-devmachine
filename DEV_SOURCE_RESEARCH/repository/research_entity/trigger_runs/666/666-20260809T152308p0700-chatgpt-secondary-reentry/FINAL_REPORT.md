# 666 Run Report — Re-entry Causal Identifiability

## Run

- run_id: `666-20260809T152308p0700-chatgpt-secondary-reentry`
- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Level-0 gate observed: `PASS`
- program stage: `BASE_CLAYCODE_RELEASE`
- mode: post-Level-0 seeded stochastic emergent-field genesis

## Concurrency / duplicate handling

The first local candidate, `Familiarity Stability Control`, was built and tested after an initially empty field-registry read. Before registry commit, CAS detected a concurrent registry mutation. Re-read showed an earlier field, `Proof-Carrying Adaptive State`, whose scope materially overlapped continual adaptation, BRONZE/self-label poisoning, open-set health, provenance and rollback.

Per duplicate-avoidance law:

- the familiarity candidate is preserved as correlated replication material;
- it is not counted as an independent field spawn;
- its original cross-room event is corrected by an immutable INVALIDATE event;
- the worker resampled to an orthogonal field.

A later registry CAS conflict exposed another concurrent field, `Perceptual Cache Coherence`; all remote fields were preserved during the successful merge.

## Valid spawned field

- field_id: `EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY`
- name: **Re-entry Causal Identifiability**
- seed: `8560758903970440746`
- lens: dynamical systems × causal inference
- lifecycle: `SPAWNED -> ACTIVE -> CROSS_CONNECTED -> TESTED -> INTEGRATED`

## Research question

When FRANK observes transfer entropy, directed prediction gain or recurrent lagged activity between workspace/re-entry channels, how can it distinguish a true causal re-entry edge from spurious directionality induced by shared state, scheduler timing or a common latent driver?

## Internal evidence used

1. `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
   - already requires common-driver controls, matched counterfactual replay, lesion/rescue and warns that directionality estimators are not proof of causality.
2. `research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`
   - requires topology/delay interventions, lesions, rescue and separation of graph connectivity from causal use.
3. current `PROGRAM_STATE.json`
   - Level 0 PASS; current milestone BASE ClayCode release.

## External primary research

- Panayiotou & Simsek, CLeaR 2026, PMLR 323 — blocking interventions identify causal chain-reaction structure where observational heuristics can fail under delayed/overlapping effects.
- Bica, Alaa & van der Schaar, ICML 2020, PMLR 119 — hidden confounding biases longitudinal causal estimation unless explicitly addressed.
- Gunther, Ninad & Runge, UAI 2023, PMLR 216 — time-series causal discovery can require explicit observed/latent context handling.
- Jahn, Karnik & Schulman, CLeaR 2025, PMLR 275 — causal identifiability in time-series graphs with latent confounders requires formal identification conditions, not raw directional association.

Evidence class remains external analogue/theory, not FRANK runtime proof.

## Hypothesis matrix

### H1 — intervention-supported re-entry evidence

**Claim:** directed-flow metrics are screening signals; stronger re-entry causal status requires common-driver audit plus matched lesion/blocking and preferably rescue.

**Status:** `SUPPORTED_WORKING_HYPOTHESIS_SYNTHETIC_PLUS_PRIMARY_CAUSAL_LITERATURE`

**Falsifier:** observational estimators with practical FRANK conditioning sets reliably distinguish confounded and true-coupling twins across realistic delays/shared-state cases, at materially lower cost and without intervention evidence.

### C1 — observational sufficiency

Rich conditioning may make intervention receipts redundant for many deterministic Harness traces.

**Status:** OPEN.

### C2 — intervention distribution shift

Lesions may perturb the system so strongly that normal-operation observational metrics are sometimes more representative.

**Status:** OPEN; motivates lesion + rescue + graded gain/delay perturbations rather than binary ablation alone.

## Executed synthetic test

Artifact: `SYNTHETIC_COMMON_DRIVER_EXPERIMENT.json`

Two matched linear dynamical systems shared a lagged common driver C.

### Common-driver-only system; true A->B coupling = 0

Across 50 seeds:

- directed prediction gain from adding lagged A: ~0.3218
- apparent A coefficient without conditioning on C: ~0.4369
- A coefficient conditioned on C: ~-0.0034
- matched A-lesion downstream B MAE: 0.0
- matched A-lesion downstream B RMS: 0.0

### True coupling system; A->B = 0.35

Across 50 seeds:

- directed prediction gain: ~0.6252
- apparent A coefficient without C: ~0.8825
- A coefficient conditioned on C: ~0.3457
- matched A-lesion downstream B MAE: ~1.1563
- matched A-lesion downstream B RMS: ~1.4461

### Interpretation

The no-edge system produced a substantial lagged predictive signal despite zero direct causal effect. Conditioning removed the spurious coefficient only because the common driver was observed in this synthetic construction. The matched lesion separated the two systems unambiguously.

This is synthetic mechanism evidence only and cannot promote a FRANK causal claim.

## Cross-branch feedback

### GWT
Bind directed-flow measurements to conditioning-set identity and keep them below intervention-supported evidence status.

### Emergenz
Use confounded-vs-true-coupling twin traces as mandatory null/control pairs for re-entry and cross-timescale emergence claims.

### Hyperposition
Treat scheduler/shared-state topology as a possible common driver and preserve topology hash, delay and intervention identity in readouts.

### Harness
Add Golden traces containing strong lagged predictive dependence generated only by a shared state, paired with a true-coupling twin. Execute conditioned estimator, edge lesion, delay perturbation, truthful-vs-shuffled re-entry and rescue under matched replay.

### ClayGraph
Distinguish `PREDICTIVE_EDGE`, `CONDITIONED_FLOW`, `INTERVENTION_SUPPORTED_EDGE` and `RESCUE_SUPPORTED_EDGE`.

### ClayCode
The current contracts already require conditioning sets, estimator identity, intervention specs, controls, provenance and evidence status. No language-semantic change is justified without an executable compiler/runtime counterexample.

## Negative / non-promoted results

- Strong directed prediction gain alone was shown insufficient in the synthetic common-driver case.
- No FRANK runtime/hardware evidence was produced.
- No causal-emergence claim was promoted.
- No new ClayCode primitive was proposed as mandatory.
- The initial adaptive-familiarity candidate was explicitly not counted as an independent field due to concurrent overlap.

## Durable artifacts

- `research_entity/emergent_fields/fields/EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY/FIELD_STATE.json`
- `research_entity/emergent_fields/fields/EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY/FINDINGS.md`
- `research_entity/emergent_fields/fields/EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY/SYNTHETIC_COMMON_DRIVER_EXPERIMENT.json`
- `research_entity/emergent_fields/fields/EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY/common_driver_reentry_sim.py`
- `research_entity/rooms/center_events/CRD-20260809T152308-REENTRY-CAUSAL-IDENTIFIABILITY.json`
- `research_entity/rooms/center_events/INVALIDATE-20260809T152308-FAMILIARITY-DUPLICATE.json`

## Final synthesis

This 666 run contributes a concrete identifiability guardrail: FRANK should not let observational information-flow metrics silently harden into causal re-entry claims. The system already has the correct conceptual hooks in GWT/Hyperposition; the next high-information step is to turn those hooks into paired H1 confound-vs-causal Golden traces and require matched intervention receipts before causal-evidence promotion.

Research result remains a working hypothesis, not canonical architecture truth.
