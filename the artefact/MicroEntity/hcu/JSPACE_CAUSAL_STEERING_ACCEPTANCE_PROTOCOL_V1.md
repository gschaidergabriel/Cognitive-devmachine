# J-Space Causal Steering Acceptance Protocol v1

Status: **SOURCE/RESEARCH PROTOCOL ONLY — ZERO MODEL/J-SPACE/TRAINING/WHOLE-PRODUCT RUNTIME CREDIT**

Schema: `ENTITYOS_HCU_JSPACE_CAUSAL_STEERING_ACCEPTANCE_PROTOCOL/v1`

Date: 2026-08-24

Authority: resolve current owner/supervisor authority from Research `main` at execution time. This document does not grant execution, spend, effect, state, model, or truth authority.

## Purpose

Define the minimum causal-control evidence needed before EntityOS/HCU may promote a model-specific Global J-Space steering claim above source plausibility or behavioral correlation.

This protocol deliberately reuses the existing single `JSPACE_VECTOR_CONTROL_ABI/v1` and `jspace_llamacpp_cvec_bridge_v1` path. It MUST NOT create a second vector wire, a second state authority, a second effect path, or a second persistent entity.

## Core hypothesis

For one exact model/runtime identity, an admitted J-Space direction causes a reproducible target-specific change when injected into a declared residual-layer range, and that change is stronger/more structured than equal-magnitude null interventions while remaining inside declared off-target regression bounds.

## Serious counterhypotheses

1. Apparent steering is caused by intervention magnitude rather than direction.
2. Apparent steering is a generic activation disruption effect.
3. Apparent steering is confined to one prompt family or leaks from direction-construction data.
4. Apparent steering is a layer-location artifact rather than a stable causal direction.
5. Apparent steering disappears under sign reversal, held-out families, repeated seeds, or exact replay.
6. Apparent steering is only output-level correlation; the claimed model-input intervention was not actually consumed at the bound runtime/source identity.

## Evidence identity required before a trial counts

Every counted trial MUST bind, at minimum:

- canonical causal event / Entry admission identity;
- entity generation;
- exact model checkpoint SHA-256;
- exact tokenizer SHA-256;
- exact runtime/build/source identity;
- verified loader-consumption identity, not pre-load hashing alone;
- exact `JSPACE_VECTOR_CONTROL_ABI/v1` packet SHA-256;
- exact basis id + basis SHA-256 + role;
- exact llama.cpp control-vector bridge binding SHA-256 where that backend is used;
- exact `il_start`, `il_end`, strength and emitted F32LE control-buffer SHA-256;
- exact GRID plan / output-producing cell identity where GRID10 is used;
- exact ModelExecution / InferenceReceipt identity;
- prompt/input family identity and split assignment;
- metric implementation/version and result digest.

If any required identity is ambiguous, the trial is `CAUSAL_STEERING_TRIAL_NOT_ADMITTED`.

## Phase 0 — no-intervention baseline

For every evaluation family, run an exact-source baseline with no steering applied. Preserve the same decoding parameters, model/runtime identity and evaluation metric used for intervention trials.

Baseline variance across repeated runs MUST be measured whenever decoding is nondeterministic. A single baseline sample is not sufficient for a stochastic claim.

## Phase 1 — currently representable null controls

Use the existing canonical ABI control conditions without inventing aliases:

- `NULL_VECTOR`: zero-vector intervention;
- `SIGN_FLIP`: opposite direction at matched absolute strength;
- `PERMUTED`: deterministic coordinate permutation of the same source direction, preserving the vector's coordinate multiset and therefore its exact L2 norm before q8 reconstruction;
- `ROLE_SWAP`: role-mismatched control where semantically meaningful;
- `LESION`: declared ablation control where the existing implementation admits it.

The `PERMUTED` control SHOULD use multiple deterministic seed-derived permutations across independent trial families. Record the seed derivation and permutation digest. Do not relabel a general random vector as `PERMUTED`.

### Why PERMUTED is useful but insufficient

A coordinate permutation is a magnitude-matched null direction and can falsify simple `effect == norm` explanations without changing the current ABI. It is not equivalent to an isotropically sampled random direction and therefore cannot by itself close the strongest generic-perturbation counterhypothesis.

## Phase 2 — stronger magnitude-matched random-direction control

Current `JSPACE_VECTOR_CONTROL_ABI/v1` does **not** declare a general magnitude-matched random control condition. Therefore a truly independent random-direction comparator MUST NOT be laundered through `BASELINE`, `PERMUTED`, or another existing label.

Before such a comparator can enter canonical model-input control, one of the following must happen under then-current authority:

1. the canonical ABI is successor-extended with one explicit, test-covered condition for an independently generated magnitude-matched random direction; or
2. a newer canonical protocol supplies an equally explicit nonambiguous representation without creating a second wire.

Until then, `ISOTROPIC_MATCHED_RANDOM_CONTROL = PROTOCOL_REQUIRED_BUT_CANONICAL_EXECUTION_BLOCKED_BY_ABI_LABEL`.

Any future random direction MUST be generated from a recorded deterministic seed/family identity, normalized to the same declared intervention norm/strength as the target direction, and independently hash-bound before model consumption.

## Layer-sweep discriminator

Do not select a favorable layer range after inspecting final evaluation results and then report it as if pre-specified.

For a model with `n_layer` transformer layers, define the sweep before evaluation. At minimum include:

- early range;
- early-middle range;
- middle range;
- late-middle range;
- late range;
- full admitted controllable range;
- no-intervention baseline.

When compute permits, prefer a single-layer or narrow-window scan around any coarse-range peak, followed by a fresh held-out confirmation run.

Every layer-range trial binds its exact `il_start`, `il_end`, control-buffer digest, strength and trial family. A layer peak discovered on one family is a hypothesis until reproduced on held-out families.

## Strength sweep

For each promoted direction/layer candidate, test at least three nonzero absolute strengths plus zero, including one weak perturbation and one stronger but still admitted perturbation. Include sign reversal where applicable.

A causal claim is weakened if target behavior changes only at strengths that also produce broad off-target degradation.

## Target and off-target metrics

A trial MUST define before execution:

- one primary target metric;
- one or more off-target capability/regression metrics;
- direction of desired change;
- acceptable regression bounds;
- aggregation rule across prompt families;
- deterministic/stochastic repeat policy.

Do not promote on target gain alone. Broad capability collapse, format corruption, repetition, refusal inflation, language drift, or other non-target degeneration must remain visible in the result.

## Split / leakage law

Direction construction, hyperparameter/layer discovery, threshold tuning and final confirmation MUST use family-level separated data where practical.

At minimum maintain:

- construction/train families;
- discovery/validation families;
- untouched holdout families.

Derived variants of one causal family must remain in the same split. A prompt paraphrase is not automatically an independent family.

## Minimum promotion gate

A model-specific J-Space steering claim may become `CAUSAL_STEERING_COMPONENT_PASS` only when all of the following are true at one exact model/runtime identity:

1. real model-input control consumption is evidenced at the bound source/runtime identity;
2. target intervention beats no-intervention baseline by the predeclared metric;
3. target intervention is distinguishable from at least the currently canonical magnitude-preserving `PERMUTED` null distribution across declared trial families;
4. sign/null controls behave consistently with the causal hypothesis rather than generic disruption;
5. the effect reproduces on held-out families;
6. a predeclared layer sweep shows reproducible layer dependence or a reproducible broad-range effect;
7. off-target regressions remain within predeclared bounds;
8. replay/provenance/generation/source identities validate exactly;
9. no effect, state, truth, whole-HCU, whole-EntityOS, or training credit is inferred beyond this exact component claim.

### Stronger promotion gate after random-control ABI support

Once an explicit canonical magnitude-matched random-direction condition exists, replace item 3 with the stronger requirement that the target-direction effect exceed the predeclared matched-random control distribution at the declared confidence/effect-size threshold on held-out families.

## Recommended statistics

Do not hard-code a universal p-value threshold into protocol semantics. The evaluation plan SHOULD predeclare:

- number of independent prompt families;
- number of repeated seeds/samples where stochastic;
- effect size and confidence interval or bootstrap interval;
- family-level aggregation rather than treating correlated tokens/samples as independent;
- correction strategy if many layers/strengths are searched;
- exact rule used to select a candidate for holdout confirmation.

The holdout confirmation is the promotion-bearing run; discovery sweeps are not independent confirmation.

## Failure classifications

Use explicit outcomes:

- `PASS_COMPONENT_CAUSAL_STEERING_EXACT_IDENTITY`
- `FAIL_TARGET_EFFECT_NOT_REPRODUCED`
- `FAIL_MATCHED_NULL_NOT_SEPARATED`
- `FAIL_OFF_TARGET_REGRESSION`
- `FAIL_LAYER_EFFECT_NOT_REPRODUCED`
- `FAIL_HOLDOUT_GENERALIZATION`
- `BLOCKED_MODEL_INPUT_CONSUMPTION_UNVERIFIED`
- `BLOCKED_MATCHED_RANDOM_ABI_CONDITION_UNAVAILABLE`
- `BLOCKED_EXECUTION_SURFACE_UNAVAILABLE`
- `BLOCKED_AUTHORITY_OR_RESOURCE_GATE`
- `INVALID_IDENTITY_OR_PROVENANCE`

Infrastructure/auth/quota/bridge failure is not scientific negative evidence.

## Current external-prior-art fusion

The protocol adopts only causal-testing principles, not external authority:

- current llama.cpp control-vector support exposes scaled vectors and layer ranges, and its adapter implementation applies a layer-specific additive control direction;
- recent activation-steering work reports strong layer dependence and uses equal-magnitude random perturbations to distinguish directional control from generic perturbation effects.

These observations motivate the layer sweep and magnitude-matched null/random controls. They do not prove that EntityOS/HCU J-Space works on the current candidate model.

## Acceptance boundary

Passing this protocol establishes only a **model-specific causal steering component result at exact identity**. It does not establish consciousness, a universal latent geometry, whole Global J-Space/GWT causality, EntityOS/HCU runtime acceptance, canonical truth, real-effect authority, or training benefit.

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT` remains mandatory.
