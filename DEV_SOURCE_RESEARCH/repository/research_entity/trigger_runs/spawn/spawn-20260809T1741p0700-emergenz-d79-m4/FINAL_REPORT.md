# SPAWN Research Run — Adaptive Compensation Confounds Lesion/Rescue

Run: `spawn-20260809T1741p0700-emergenz-d79-m4`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: RAE-8.8 `r2` · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Origin branch: `emergenz` (OS-CSPRNG draw 79/100)  
Selected microdirection: `adaptive_compensation_confounds_lesion_rescue` (OS-CSPRNG draw 4/5)  
Program stage: `BASE_CLAYCODE_RELEASE` / IN_PROGRESS  
Evidence scope: OPEN research delta + primary external evidence + executed synthetic proof-of-principle; **no live FRANK/H1 promotion**.

## 1. Executive result

Lesion/rescue is not history-invariant in an adaptive system. The experiment must declare **what is allowed to learn, when the effect is measured, and which state is restored during rescue**.

A small chronic lesion effect does not imply that the lesioned mechanism was unnecessary in the pre-lesion state: function may have rerouted during the measurement interval. Likewise, restoring only the lesioned mechanism after compensation is not a clean rescue because the adapted alternative route remains changed and can make the restored system worse.

Hard distinctions:

`acute_mechanism_necessity != adaptation_compensated_performance`

`rescue_magnitude_without_state_lineage != mechanism_restoration`

`intervention_schedule != incidental_metadata`

## 2. Novelty relative to current Emergenz

The preceding Emergenz run already strengthened common-driver conditioning, higher-order controls, observational/interventional decomposition, truthful-vs-shuffled rescue, estimator disagreement and anti-Goodhart holdout. This Spawn does not repeat those results.

It targets a separate confound already hinted by Hyperposition: **online credit/plasticity can change the system while the intervention is being used to measure it**. This changes the causal estimand itself.

A concurrent ClayCode spawn (`9b044a9be6128201e4fbc6fb6831ae3cce21ff4e`) was observed before writeback. It concerns adaptive visual learner state/promotion/rollback semantics and is adjacent but not a duplicate of this emergence-causal lesion/rescue direction.

## 3. External primary evidence

Bredenberg, Savin & Kiani, *Recurrent Neural Circuits Overcome Partial Inactivation by Compensation and Re-learning* (Journal of Neuroscience 2024; DOI `10.1523/JNEUROSCI.1635-23.2024`) show in recurrent neural-network models that plastic networks can reconfigure during inactivation and regain pre-inactivation performance. Continuous inactivation permits faster compensation than intermittent inactivation, and the paper emphasizes transient effects before relearning for causal interpretation.

Fetsch et al., *Focal optogenetic suppression in macaque area MT biases direction discrimination and decision confidence, but only transiently* (eLife 2018; DOI `10.7554/eLife.36523`) report that behavioral effects of MT suppression attenuated over tens of minutes and also showed sub-second compensation.

These are mechanistic analogues and experimental-design evidence, not direct FRANK evidence.

## 4. Executed synthetic discriminator

Experiment: `EXP-SPAWN-EM-ADAPTIVE-LESION-001`  
Script SHA-256: `deb74941b800219344a7894f622752d0e558f641386dbfe324e2c43b63c65ec5`  
Result SHA-256: `511ae649f164153977c065d6952327e565f0dc22cde5540fcd874510ee9f66ca`

Exact Git commits on the main-based integration branch:

- experiment source: `19315017daa5fd31a6f2b28482d0d3a81efb0f95`;
- experiment result: `803046b9c281b01f540cfb0f0335353b01d2dc52`;
- execution receipt: `edcbbcee8256a0875990de4bb3d5ab5732208874`;
- evidence manifest: `2714fbc5ccfa51139501833df4c1b7de4374e3cd`;
- mesh feedback: `097afa0f0edb208bfb6f9bda2763970f01d661cf`.

### A — Same lesion, different plasticity history

The toy system has two redundant paths, A=0.8 and B=0.2, whose intact sum exactly solves the task. A is lesioned.

Across 50 deterministic seeds:

- frozen-learning delayed lesion MSE: **0.642002 ± 0.092250**;
- truthful online-adaptation delayed MSE: **3.69e-17**;
- shuffled-credit delayed MSE: **1.013704 ± 0.193766**;
- learned B after truthful adaptation: **~1.0**.

Thus the same originally important path looks strongly necessary when learning is frozen and nearly irrelevant when measured only after adaptation.

### B — Rescue is history-dependent

After B compensates for the A lesion:

- restoring A alone while keeping adapted B gives MSE **0.642002 ± 0.092250**;
- restoring the full pre-lesion learner state gives MSE **~6.95e-33**;
- mechanism-only rescue was worse than the already-adapted lesioned state in **50/50 seeds**.

Therefore `Lesion -> Adapt -> RescueMechanism` is not equivalent to a counterfactual fork from the same pre-intervention state.

### C — Perturbation schedule changes compensation

With continuous lesion duty cycle 1.0, B converged to ~1.0 and lesion-state error approached zero. At duty cycles 0.5, 0.25 and 0.1, compensation was progressively weaker. Perturbation schedule is therefore part of causal measurement identity in adaptive systems.

All of this is synthetic proof-of-principle only.

## 5. Proposed causal estimands

For adaptive FRANK/Harness interventions distinguish at least:

1. `acute_lesion_loss`: common pre-intervention snapshot, plasticity frozen, preregistered immediate window;
2. `chronic_lesion_loss`: same intervention after a declared adaptation budget and learning policy;
3. `compensation_gain = acute_lesion_loss - chronic_lesion_loss` plus a normalized form where useful;
4. `mechanism_only_rescue_effect`: restore mechanism, retain adapted learner state;
5. `state_rollback_rescue_effect`: restore mechanism and learner state from common snapshot;
6. `counterfactual_twin_effect`: compare sibling branches forked from exactly the same snapshot with explicit intervention histories.

A mechanism-necessity claim should be anchored to the acute common-snapshot estimand. Chronic recovery is evidence about compensation capacity, not retroactive evidence that the mechanism was never causal.

## 6. Receipt semantics needed for interpretable lesion/rescue

The intervention/readout representation should bind:

```text
pre_intervention_state_hash
intervention_epoch
measurement_delay_steps
measurement_window
plasticity_mode                 # FROZEN | ALLOWED | CONTROLLED
learning_policy_hash
credit_policy                   # truthful | shuffled | path-scoped | broadcast | ...
learner_state_hash_before
learner_state_hash_after
parameter_delta_hash
route_or_topology_delta_hash
adaptation_budget
perturbation_duty_cycle
rescue_mode                     # MECHANISM_ONLY | STATE_ROLLBACK | COUNTERFACTUAL_TWIN
counterfactual_sibling_ref
estimand_id
```

These fields support reproducibility and interpretation; they do not grant execution authority.

## 7. BASE ClayCode implication

This is first a **conformance/expressibility test**, not permission to redesign ClayCode.

Current BASE policy is “less change, more compile.” Therefore:

- first encode common-snapshot forks, ordered interventions, learning-policy identity, learner-state lineage and rescue modes with current ClayCode semantics;
- route executable failures to `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT`, `CC-WP-11-FUZZ-CONFORMANCE` and `CC-WP-13-HARNESS-HANDOFF`;
- change language semantics only if an executable counterexample proves that the current semantics cannot faithfully represent/lower the experiment.

## 8. H1/H2/H3 Golden fixture

Add `ADAPTIVE_LESION_COMPENSATION` from one frozen pre-intervention snapshot with sibling branches:

- baseline / no lesion;
- lesion + learning frozen;
- lesion + truthful learning for fixed budget;
- lesion + shuffled credit under the same update budget;
- adaptive lesion -> mechanism-only rescue;
- adaptive lesion -> full learner-state rollback rescue;
- continuous vs intermittent lesion schedules with declared exposure.

Compare immediate and chronic outcomes, parameter/route/topology deltas, cost shadows and replay hashes. H2/H3 should reproduce the intervention semantics, not merely the final score.

## 9. Mesh feedback

- **Emergenz — NEW_CONSTRAINT:** split acute necessity from chronic compensation; learner-state lineage is causal metadata.
- **GWT — NEW_CONSTRAINT:** lesion/rescue readouts need plasticity mode, time window, schedule, compensation gain and rescue mode.
- **Hyperposition — SUPPORTING_EVIDENCE:** strengthens the adaptive-credit confound and makes intervention schedule/topology lineage explicit.
- **ClayCode — NEW_HYPOTHESIS:** verify current semantics can encode ordered counterfactual branches and learner-state identity; no redesign without executable failure.
- **Harness — NEW_HYPOTHESIS:** add the Golden fixture above before any strong emergence promotion.
- **FRANK — NEW_CONSTRAINT:** observability must expose learning/route/topology changes during intervention.
- **ClayGraph — NEW_CONSTRAINT:** stable or rerouted topology after a lesion can be adaptation rather than causal proof; preserve branch lineage.
- **UnifiedDB — NEW_CONSTRAINT:** persist common-snapshot fork lineage, learner-state hashes and parameter/topology deltas with receipts.
- **ClayResearch — SUPPORTING_EVIDENCE:** recurrence/adaptation/intervention ordering is noncommutative and must remain visible in the integrated architecture.

## 10. Limits / negative-result discipline

No live FRANK or H1 episode was executed. None of H-SPAWN-EM-01..05 is promoted beyond OPEN and no emergent mechanism is certified.

The toy model intentionally makes the confound easy to isolate; it does not estimate its prevalence or magnitude in FRANK. The neuroscience evidence supports plausibility and experimental-design caution, not architectural equivalence.

## 11. Highest-information next experiment

When H1 is executable, freeze one real `WorkspaceEpisode` plus learner state and fork it into the seven Golden branches above. Freeze model outputs where technically appropriate to isolate architecture/plasticity effects. Preregister immediate and chronic windows and require exact learner/topology delta receipts.

The decisive question is:

> **Was the mechanism necessary before adaptation, what changed to compensate, and does a lineage-correct rescue restore the same causal state?**
