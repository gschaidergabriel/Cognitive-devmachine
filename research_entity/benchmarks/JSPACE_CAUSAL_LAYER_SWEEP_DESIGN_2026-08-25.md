# Global J-Space causal layer-sweep design — 2026-08-25

Status: **DESIGN / HYPOTHESIS ONLY**. No model execution, runtime promotion, J-Space credit, HCU credit, training credit, or whole-product credit is created by this document.

Program: EntityOS + HCU  
Current authority at design time: Supervisor 8.78 / FREE_ONLY  
Target lane: retained HCU / Global J-Space donor path  
Execution precondition: canonical unusual-experiment lease plus an admitted zero-cost local/sandbox surface.

## Why this successor discriminator exists

The current Qwen3-0.6B hidden-state steering source path is useful but a terminal/final-norm vector coupled to output-embedding or `lm_head` geometry can demonstrate direct readout steering without demonstrating a learned intermediate J-Space representation. The successor test therefore separates **linear decodability**, **causal controllability**, and **where an intervention happens to work best**.

Current external research strengthens that distinction:

- Srivastav, *Steering the Language Axis: From Linear Decodability to Causal Control* (arXiv:2608.12334, 2026) reports that causal steering sensitivity can be strongly layer- and task/language-pair-dependent and uses matched random perturbations as controls.
- Kramar et al., *AtP*: An efficient and scalable method for localizing LLM behaviour to components* (arXiv:2403.00745) shows important false-negative modes in attribution-style localization and motivates treating fast localization only as a prioritizer, not promotion evidence.
- Hase et al., *Does Localization Inform Editing?* (arXiv:2301.04213) finds that localization peaks need not predict the layers where an intervention/edit is most effective. Localization and intervention success therefore must remain separate measured variables.
- Wu et al., *pyvene* (arXiv:2403.07809) provides a general intervention framing in which model-internal activation changes are explicit counterfactual manipulations; Clay may reuse the methodological idea without adopting the library as an authority.

These papers are research inputs, not canonical Clay facts.

## Competing hypotheses

### H1 — intermediate causal J-Space feature

A representation-derived direction learned away from the output readout causally controls the target behavior at a bounded subset of intermediate layers. The effect generalizes to a disjoint semantic holdout, has directional sign behavior, survives nuisance controls, and is materially larger than equal-norm unrelated perturbations.

### H0 — terminal readout confound

The observed behavior is mostly direct movement of terminal logits/readout geometry. Steering succeeds near the final normalization/readout region but weakens or disappears for representation-derived intermediate-layer vectors once output-embedding coupling is removed.

### H2 — prompt/schema recurrence confound

The vector captures shared wording, token position, formatting, or demonstration schema instead of the intended latent coordination variable. Effects collapse under paraphrase, reorder, format, lexical, or family holdouts.

### H3 — nonspecific perturbation / gain effect

Any sufficiently large residual-stream perturbation moves the measured output. Orthogonal, permuted, or random same-norm directions produce comparable target movement or comparable collateral degradation.

### H4 — localization/intervention mismatch

A layer can be highly decodable or rank highly under an attribution/localization score without being the layer where direct intervention has the strongest causal effect. A single preselected layer is therefore insufficient evidence.

## Frozen identity before any execution

A future admitted run must bind at minimum:

- exact repository commit/tree and dirty state;
- exact Qwen checkpoint revision and every consumed checkpoint shard digest;
- tokenizer identity/digest;
- Python, Torch, Transformers and relevant runtime/build identities;
- exact hook/module names discovered from the loaded model rather than assumed from prose;
- exact input family identifiers and train/validation/holdout split manifest;
- exact vector derivation code/source digest;
- exact intervention coefficient schedule;
- exact output/inference receipt and J-Space trace identities;
- proof that the admitted run made zero paid-provider / Together calls.

Pre-load hashing alone is not loader-consumption attestation.

## Vector construction

1. Build contrastive activation differences from a **derivation family only**. Do not use holdout examples to choose a layer, coefficient, direction sign, token position, or score threshold.
2. Derive directions from intermediate representations themselves. Do not construct the successor vector from `lm_head` rows or output-embedding rows.
3. Normalize and record vector norm separately from direction.
4. Keep derivation families causally grouped so paraphrases/near-duplicates cannot leak across train/validation/holdout.
5. If PCA/SVD or another dimensionality reduction is used, bind the fitted transform to the derivation split and persist its digest.

## Layer sweep

Discover the model's actual candidate hook sites at runtime and sweep a preregistered set spanning early, middle, and late residual-stream locations. Do not choose one "magic" layer from localization alone.

For each candidate layer execute the same matched control family:

- BASELINE
- +VECTOR
- SIGN_FLIP
- NULL_VECTOR
- ORTHOGONAL_SAME_NORM
- PERMUTED_SAME_NORM
- RANDOM_SAME_NORM with frozen seed family
- SHAM_HOOK with hook plumbing active but zero intervention
- OFF_TARGET_LAYER using the same direction at a preregistered control layer where dimensionally valid

The layer index and hook site are independent experimental variables. Do not pool them post hoc until per-layer results are persisted.

## Holdouts and nuisance controls

At least one semantic holdout family must differ from vector-derivation examples in wording and surface form. Prefer multiple nuisance families:

- lexical paraphrase;
- formatting/order change;
- token-position shift;
- semantically adjacent off-target behavior;
- unrelated capability probes;
- prompt family held out as a unit.

Family-level split identity must be recorded in the trace so examples descended from the same causal source cannot cross the boundary.

## Measurements

Record, without silently converting them into truth:

- preregistered target-behavior score;
- baseline-to-intervention effect size per layer/control;
- sign-flip symmetry/asymmetry;
- random/orthogonal/permuted same-norm null distribution;
- general-output coherence/capability nuisance metrics;
- output-logit distribution shift or another bounded readout-drift measure;
- layer-localization/decodability score as a separate variable;
- intervention causal effect as a separate variable;
- confidence intervals or repeated-seed dispersion where the admitted execution budget permits.

Do not use model self-report as the causal target metric.

## Promotion gates

Model-specific J-Space causal component evidence requires all of the following at exact identity:

1. representation-derived intermediate vector, not terminal output-row construction;
2. positive target effect on disjoint holdout;
3. materially weaker NULL / ORTHOGONAL / PERMUTED / RANDOM same-norm controls;
4. direction-sensitive behavior under SIGN_FLIP or an explicit hypothesis explaining and predeclaring why symmetry is not expected;
5. bounded collateral degradation on nuisance/off-target probes;
6. layer-specific result persisted before cross-layer interpretation;
7. exact loader-consumption and inference-receipt binding;
8. JSPACE_VECTOR_CONTROL_ABI/v1-compatible causal trace;
9. no family leakage;
10. no promotion based solely on localization/decodability, textual coherence, recurrence, self-report, or steering-search score.

Even a positive result grants only the declared model-specific component scope. It does not establish whole HCU, whole EntityOS, consciousness, canonical truth, or training success.

## Cheapest high-information sequence after lease

1. Validate exact model/runtime/loader identity and hook discovery with zero intervention.
2. Run a small preregistered layer pilot using BASELINE, +VECTOR, NULL and RANDOM_SAME_NORM solely to detect plumbing failures and catastrophic nuisance effects. Pilot families are permanently excluded from confirmatory holdout.
3. Freeze candidate layer set and coefficient range before confirmatory evaluation.
4. Run the full matched control family on disjoint holdout.
5. Compare causal effect vs localization/decodability instead of assuming correlation.
6. Only if the causal gate survives, emit admitted TrainingTrace candidates for later leak-resistant dataset construction.

## Current macrocycle decision

No experiment is executed in this macrocycle because the current ChatGPT organ has no shared reproducible upstream macrocycle identity sufficient to claim the canonical unusual-experiment lease. The correct state is therefore:

`COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`

This document advances **training-readiness/falsifiability only**.
