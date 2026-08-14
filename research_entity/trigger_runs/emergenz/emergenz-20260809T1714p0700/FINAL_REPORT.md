# Emergenz Trigger Run — FINAL REPORT

Run: `emergenz-20260809T1714p0700`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: RAE-8.8 `r2` · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` / `IN_PROGRESS`  
Evidence scope: OPEN research delta + synthetic simulation; no target-runtime promotion.

## 1. Executive result

The strongest result of this run is not a new scalar for emergence. It is a stricter **causal triangulation requirement** for any FRANK/Synthetic-Clay emergent-mechanism candidate.

A candidate should not advance on transfer entropy, synergy, macro effective information, non-additivity, recurrence, graph irreducibility, or lesion alone. The minimum useful bundle is:

1. declared observational decomposition;
2. declared intervention distribution;
3. common-driver-conditioned directed-flow control;
4. higher-order decomposition / pairwise-reduction test;
5. matched factorial interaction;
6. mechanism lesion;
7. identity-preserving truthful rescue;
8. shuffled / temporally broken / provenance-broken rescue;
9. OOD and implementation-transfer test;
10. latency/compute/memory/instability cost shadow;
11. estimator-disagreement record.

This strengthens, rather than replaces, the current `GWT_EMERGENCE_READOUT_CONTRACT.md` and `HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`.

## 2. Internal grounding

Current repository law already rejects the following equivalences:

- novelty = emergence;
- recurrence = causal necessity;
- graph complexity = emergence;
- non-additivity = sufficient evidence;
- functional emergence = phenomenal consciousness.

The current GWT readout contract already requires factorial interaction, lesion/rescue, truthful-vs-shuffled re-entry, directed information flow, PID/PEID-style decomposition, macro-vs-micro contribution, multi-timescale coupling, OOD transfer and cost shadows.

The current Hyperposition contract adds pairwise-reduction error, n-ary/higher-order relation identity, topology interventions and H1/H2/H3 differential transfer.

The current program stage is BASE ClayCode. Therefore the immediate deliverable is semantic/measurement expressibility, not live causal promotion.

## 3. External evidence update

### 3.1 Effective information remains useful but intervention-distribution-sensitive

Hoel, Albantakis & Tononi (PNAS 2013, doi:10.1073/pnas.1314922110) formalized causal emergence as macro-scale effective information exceeding micro-scale effective information under interventions. Their result is directly relevant for FRANK's macro-vs-micro readout family.

However, EI depends on a specified intervention repertoire/distribution. Later critiques have emphasized that uniform/max-entropy intervention choices and coarse-graining choices can alter what the measure reports. Therefore FRANK must persist the intervention distribution as part of the measurement identity rather than storing an EI value without its intervention semantics.

### 3.2 Learned macro emergence creates an explicit Goodhart surface

Yang et al., *Finding emergence in data by maximizing effective information* (National Science Review 12(1), 2025, `nwae279`) learn coarse-grained latent dynamics while maximizing EI. The paper itself notes that unconstrained EI maximization admits trivial solutions such as collapsing states and therefore adds prediction/reconstruction constraints.

Implication for Clay: a learned macrostate is not evidence merely because it maximizes EI. Candidate macro variables require held-out/OOD validation, fixed comparison budgets, intervention validation and complexity/cost shadows. Search/optimization and evaluation data must be separated where feasible.

### 3.3 Dynamical independence is complementary, not equivalent

Barnett & Seth, *Dynamical independence: discovering emergent macroscopic processes in complex dynamical systems* (arXiv:2106.06511, updated 2026-03-22), define macro dynamical independence through conditional information flow from micro history to macro evolution. This supplies a useful autonomy/parsimony axis: a macro process may self-predict without extra micro history.

But this is not equivalent to intervention-sensitive causal necessity. Clay should treat dynamical independence as a complementary macro-autonomy measure, not as a replacement for lesion/rescue.

### 3.4 Higher-order information requires decomposition beyond pairwise graphs

Rosas et al., *Reconciling emergences* (arXiv:2004.08220), and the Integrated Information Decomposition line (Mediano et al., arXiv:2109.13186 and later journal work) formalize higher-order and temporally structured information phenomena that ordinary pairwise graph measures can collapse together.

Partial Entropy Decomposition work also shows that higher-order synergistic structure can be invisible to pairwise connectivity summaries.

Implication: ClayGraph/Hyperposition pairwise connectivity must never be used as a sufficient emergence proxy.

### 3.5 New 2026 PEID result adds a useful causal-synergy tool and a new bookkeeping requirement

Yang, Wang & Zhang, *Partial Effective Information Decomposition for Synergistic Causality* (arXiv:2605.03267, 2026-05-05), proposes PEID: an interventionist decomposition of multivariate source influence into unique and synergistic information under maximum-entropy interventions.

The key design consequence for Clay is subtle: under those max-entropy interventions, source correlations are removed, and the authors report that redundancy vanishes. This makes PEID useful for interventionist synergy, but it also means PEID and observational PID/PED answer different questions.

**Research delta:** Clay should not store `synergy` without the decomposition family and intervention regime. At minimum distinguish:

- `observational_synergy`;
- `interventional_synergy`;
- `intervention_distribution`;
- `redundancy_destroyed_by_intervention` / intervention-regime note.

PEID should therefore complement, not silently replace, observational decompositions.

## 4. Executable synthetic experiment

Artifact: `EXPERIMENT_SYNTHETIC_CAUSAL_GATES.json`

Design: 20 deterministic seeds, 50,000 samples per seed, two binary dynamical cases.

### Case A — common-driver false positive

A Markov environment `E` drives noisy copies `X` and `Y`; there is no direct X→Y mechanism.

Mean results:

- `TE_proxy(X[t-1] -> Y[t] | Y[t-1]) = 0.050016 ± 0.001988 bit`;
- conditioned additionally on measured driver `E[t-1]`: `0.000055 ± 0.000032 bit`.

Interpretation: an apparently directed information-flow signal can arise from a temporal common driver. Declaring the conditioning set is therefore part of measurement identity, not optional metadata.

### Case B — pairwise-blind higher-order causal synergy

`Y[t] = X[t-1] XOR E[t-1] XOR noise(0.05)`.

Mean results:

- pairwise `I(X;Y) ≈ 0.000013 bit`;
- pairwise `I(E;Y) ≈ 0.000017 bit`;
- pairwise TE-like signal X→Y ≈ `0.000028 bit`;
- joint `I(X,E;Y) = 0.713686 ± 0.003839 bit`;
- conditional directed information `I(X;Y | E, Ypast) = 0.713694 ± 0.003852 bit`;
- simple higher-order synergy proxy ≈ `0.713657 ± 0.003847 bit`.

Matched causal controls:

- full predictor accuracy: `0.950009 ± 0.000902`;
- X-only: `0.499348 ± 0.002082`;
- E-only: `0.500375 ± 0.002432`;
- neither: `0.501691 ± 0.001164`;
- factorial interaction Omega: `0.451977 ± 0.003267`;
- shuffled E rescue: `0.499776 ± 0.002615`.

Interpretation: pairwise flow can completely miss a genuine higher-order mechanism, while a common driver can create a false pairwise flow signal. The two failure modes are opposite and require a bundle of controls.

This is synthetic evidence only. It does not establish a FRANK emergent organ.

## 5. Hypothesis matrix

### H-EM-20260809-01 — Conditioning-set identity is mandatory

Mechanism: common drivers can generate nonzero directed prediction gain between channels without a direct mechanism.

Prediction: some candidate GWT/ClayGraph edges will lose most apparent TE/directed prediction gain when conditioned on body/goal/workspace/common-state drivers.

Counterhypothesis: pairwise TE plus temporal shuffle null is sufficient.

Falsifier: across preregistered H1 traces, common-driver conditioning never materially changes edge ranking or effect interpretation.

Status: `OPEN`, supported by synthetic simulation + information-theoretic literature.

### H-EM-20260809-02 — Higher-order causal paths require co-source-conditioned or multivariate decomposition

Mechanism: XOR-like/n-ary mechanisms can be pairwise invisible.

Prediction: some Hyperposition/GWT interactions will show low pairwise flow but high joint/conditional information plus matched lesion/rescue dependence.

Counterhypothesis: all functionally relevant FRANK interactions are adequately captured by pairwise edges.

Falsifier: best pairwise reduction reproduces predictions, interventions, outcomes and re-entry across H1/H2/H3 within preregistered tolerance.

Status: `OPEN`.

### H-EM-20260809-03 — PEID must be paired with observational decomposition

Mechanism: maximum-entropy intervention removes source correlation, changing redundancy structure by design.

Prediction: observational PID/PED and PEID will disagree systematically on some GWT/Hyperposition episodes; the disagreement will itself diagnose observational redundancy vs interventionist synergy.

Counterhypothesis: PEID alone is sufficient for all emergence-relevant decomposition.

Falsifier: on a representative benchmark battery, observational decomposition adds no discriminating information once PEID and intervention receipts are available.

Status: `OPEN`; motivated by 2026 PEID preprint.

### H-EM-20260809-04 — Macro-emergence search requires anti-Goodhart holdout

Mechanism: optimizing a representation for EI or another emergence objective can discover trivial/overfit coarse-grainings.

Prediction: macro candidates selected on training episodes will overstate emergence unless evaluated on held-out contexts/interventions/topologies.

Counterhypothesis: prediction/reconstruction constraints alone prevent practically important Goodhart failures.

Falsifier: preregistered search/evaluation splits show no measurable optimism gap across candidate macrostate searches.

Status: `OPEN`.

### H-EM-20260809-05 — Rescue identity is as important as rescue magnitude

Mechanism: generic added context can restore performance without restoring the claimed causal path.

Prediction: truthful, temporally aligned, provenance-bound rescue will outperform shuffled/provenance-broken content-matched rescue for genuine re-entry mechanisms.

Counterhypothesis: any content-equivalent rescue is sufficient to identify mechanism.

Falsifier: shuffled/provenance-broken rescue restores the same effect distribution as truthful rescue across frozen episodes.

Status: `OPEN`.

### H-EM-20260809-06 — Estimator disagreement is a useful first-class signal

Mechanism: EI, dynamical independence, TE, PID/PED/PEID, factorial Omega and lesion/rescue probe different failure modes and assumptions.

Prediction: high-value ambiguous episodes will exhibit structured estimator disagreement that points to confounding, higher-order interaction, coarse-graining sensitivity or intervention-regime dependence.

Counterhypothesis: a single carefully chosen emergence estimator dominates the rest and disagreement adds no value.

Falsifier: across benchmark fixtures and H1 traces, disagreement does not improve falsification/localization or prediction of lesion/rescue outcomes.

Status: `OPEN`.

## 6. Proposed ClayCode BASE delta

No semantic redesign is claimed necessary yet. First attempt to express these using existing type/effect primitives. If current semantics cannot encode them, the following are executable counterexample targets for `CC-WP-03-IR-TYPES` / `CC-WP-04-TYPE-EFFECT`:

```text
InterventionDistributionSpec {
  kind
  support_ref
  weighting_rule
  source_state_epoch
  hash
}

ConditioningSetSpec {
  variables[]
  lag_binding[]
  rationale_class
  hash
}

EstimatorReceipt {
  family
  version
  parameters_hash
  sample_count
  bias_correction
  uncertainty
  conditioning_set_ref
  intervention_distribution_ref
  null_family_ref
  result_hash
}

RescueReceipt {
  lesion_id
  rescue_id
  content_hash
  temporal_alignment
  provenance_integrity
  identity_integrity
  recovery_fraction
}

EstimatorDisagreement {
  episode_id
  compared_receipts[]
  disagreement_type
  unresolved_assumption
  next_discriminating_test
}
```

Hard semantic rule:

`measured_value != estimator_interpretation != evidence_status != execution_authority`

## 7. Harness benchmark fixtures to add before live emergence claims

Two tiny Golden fixtures should become mandatory H1/H2/H3 measurement conformance tests:

1. **COMMON_DRIVER_FALSE_POSITIVE** — pairwise directed-flow proxy is nonzero; common-driver conditioning must collapse it.
2. **XOR_PAIRWISE_FALSE_NEGATIVE** — pairwise flow is near zero; multivariate/conditional decomposition plus lesion/rescue must reveal the joint mechanism.

These fixtures test the measurement plane itself before it is trusted on FRANK.

Additional fixture:

3. **CONTENT_MATCHED_FALSE_RESCUE** — truthful rescue vs temporally shuffled/provenance-broken rescue have matched marginal content but different causal alignment.

## 8. Cross-branch feedback

- **GWT:** make conditioning-set identity and estimator disagreement explicit in `EmergenceReadout`; retain causal chain separation `addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`.
- **Hyperposition:** require higher-order intervention evidence in addition to representation irreducibility.
- **ClayCode:** verify BASE can encode intervention regimes, conditioning sets, estimator versions and rescue integrity without opaque host prose.
- **Harness:** add common-driver false-positive and XOR false-negative Golden traces before H1 emergence promotion.
- **FRANK:** observability plane must expose plausible common drivers (goal/body/salience/workspace/global state) so conditional flow is estimable.
- **ClayGraph:** preserve edge/hyperedge measurement ancestry; graph presence/activation is not causal evidence.
- **UnifiedDB:** persist estimator/intervention/conditioning/null identities transactionally with replay hashes; do not store an unqualified `emergence_score` as canonical truth.

## 9. What failed / what remains open

No live FRANK/Harness traces were available in this execution surface, so the synthetic result cannot promote any emergent organ or architecture mechanism.

The repository preflight CLI/provider-router CLI could not be directly executed from this ChatGPT connector surface. Native web + primary sources + connected GitHub + local Python were used; this is explicitly recorded in `TOOL_EXECUTION_MANIFEST.json`. Strong promotion is therefore disabled.

The newest 2026 PEID paper is a preprint. Treat its framework as promising external evidence, not settled consensus.

No claim about subjective or phenomenal consciousness is made.

## 10. Highest-information next experiment

On a frozen H1 `WorkspaceEpisode`, select one claimed re-entry/coupling mechanism and preregister:

- baseline outcome;
- lesion;
- truthful identity-preserving rescue;
- temporally shuffled rescue;
- provenance-broken content-matched rescue;
- common-driver conditioning set;
- pairwise TE/directed prediction gain;
- multivariate PID/PEID or nearest executable decomposition;
- factorial Omega;
- cost shadows;
- OOD replay context.

Advance the mechanism only if the predicted lesion matters, truthful rescue restores it materially more than shuffled/provenance-broken rescue, higher-order evidence survives nulls, and the result transfers to held-out episodes.

## 11. Final synthesis

The Emergenz branch should move from a **vector of interesting metrics** to a **vector of metrics plus explicit estimator assumptions and discriminating causal controls**.

The central new design rule from this run is:

`emergence evidence = measurement + intervention regime + conditioning set + null family + lesion/rescue identity + higher-order test + transfer + cost + provenance`

not:

`emergence evidence = high score`.

This is a research delta, not canonical promotion.
