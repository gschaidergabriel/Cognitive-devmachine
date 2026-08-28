# HCU J-SPACE LOCAL INTERVENTION BACKEND GATE v1

Status: SOURCE / RESEARCH CONTRACT ONLY — NO MODEL-RUNTIME CREDIT
Authority epoch at creation: 8.68
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Mode: FREE_ONLY

## Problem

The new zero-cost local `llama.cpp`/Qwen research server is useful as a provider-independent inference surface, but a successful HTTP completion does not establish model-specific Global J-Space/GWT causality. J-Space promotion requires an instrumentable local execution path that can bind exact model/runtime identity to observed intermediate activations and controlled interventions.

A second failure mode is equally important: an internal signal may be strongly decodable, recurrent, correlated with correctness, or useful to a probe while still not being a causal control variable. Therefore this gate separates **diagnostic readout** from **causal control** explicitly.

## External donor principles

Current external implementations and 2026 causal-intervention results reinforce five useful principles:

- TransformerLens activation patching performs a clean/corrupted comparison and causally intervenes by replacing selected intermediate activations, then measures the output change.
- NNsight tracing exposes intermediate activations during a model forward pass and permits controlled modification of those activations in the trace context.
- Multi-component causal tracing shows that causally important behavior can depend on sparse subsets of components rather than one privileged layer/component, so single-site success or failure must not be universalized without a declared search scope.
- Hidden-state probes can be highly diagnostic while attempted steering/patching remains noncausal or destructive; decodability is therefore not intervention evidence.
- Direction-based steering requires a matched placebo such as an equal-norm random direction because an arbitrary perturbation can itself move behavior or hidden-state metrics.

These are donor mechanisms only. EntityOS/HCU must preserve its own canonical state/evidence/effect boundaries and exact causal identity chain.

References:
- https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.patching.html
- https://github.com/ndif-team/nnsight/blob/main/docs/usage/trace.md
- https://aclanthology.org/2026.acl-long.154/
- https://arxiv.org/abs/2605.09502
- https://arxiv.org/abs/2608.12334

## Epistemic split: diagnostic readout is not causal control

Use these distinct evidence classes:

### `JSPACE_DIAGNOSTIC_READOUT`

May be supported by one or more of:

- linear/nonlinear probe performance;
- representational separation;
- hidden-state correlation with correctness or another target;
- recurrence/stability of a J-Space vector;
- token/layer localization;
- successful decoding of a latent property.

This class grants **zero causal-control credit** by itself. High AUROC, accuracy, mutual information, clustering quality, recurrence or cross-run stability cannot promote the signal to an intervention primitive.

### `JSPACE_CAUSAL_CONTROL_CANDIDATE`

Requires an actual intervention on the bound model execution plus method-matched controls, a predeclared target metric, off-target measurements and exact provenance. A successful candidate remains noncanonical until the current promotion/review gate accepts it.

The invariant is:

`DIAGNOSTIC_READOUT_PRESENT + INTERVENTION_NOT_PROVEN != CAUSAL_CONTROL_PRESENT`

## Gate

A local backend is `JSPACE_INTERVENTION_CAPABLE` only if one exact execution receipt binds all of:

1. exact checkpoint identity/digest;
2. exact tokenizer identity/digest;
3. exact runtime/backend build identity;
4. verified loader-consumption identity rather than pre-load hashing alone;
5. causal event identity + typed admission identity + route identity;
6. exact model execution identity;
7. named activation site identity (`layer`, `position`, and component/hook name or equivalent);
8. observed activation tensor metadata and digest before intervention;
9. intervention identity, operator, target and control condition;
10. observed activation tensor metadata and digest after intervention where applicable;
11. output identity and metric before/after intervention;
12. off-target regression metric for at least one unrelated behavior;
13. J-Space trace identity bound to `InferenceReceipt/v4` / current successor equivalent;
14. explicit classification of every recorded field as observed, derived, candidate or unknown;
15. the evidence class being tested (`JSPACE_DIAGNOSTIC_READOUT` or `JSPACE_CAUSAL_CONTROL_CANDIDATE`);
16. the declared intervention-family control policy and its exact control identities.

## Required control structure

Minimum causal family:

- `BASELINE_CLEAN`
- `BASELINE_CORRUPTED`
- `INTERVENTION_TARGET`
- `SHAM_CONTROL`
- `OFF_TARGET_CONTROL`

A target effect is not promoted from one successful intervention alone. The target intervention must change the declared target metric relative to appropriate controls while off-target regressions remain inside a predeclared bound.

### Method-matched placebo law

The sham/control must match the intervention family rather than being a generic extra run:

- **direction/vector steering**: require a `MATCHED_NORM_RANDOM_DIRECTION_CONTROL` (or a stronger predeclared placebo) at the same layer/position and intervention magnitude;
- **activation replacement/patching**: require a no-op, same-site sham, or a predeclared donor/control activation that preserves the tracing/replacement machinery while removing the hypothesized causal content;
- **ablation**: require a matched perturbation/control that distinguishes removal of the hypothesized feature from generic activation damage;
- **multi-component intervention**: declare the selected component set and include a size/energy-matched control subset or equivalent falsifier.

If the placebo changes the target metric as much as the target intervention, downgrade the result to `NONCAUSAL_OR_NONSPECIFIC_INTERVENTION` regardless of probe/readout quality.

### Localization and search-scope law

A single positive or negative activation site is evidence only for the declared site and search scope. Do not generalize one-site failure to “J-Space is noncausal,” and do not generalize one-site success to a global causal architecture claim.

When the hypothesis concerns distributed computation, use an explicitly bounded multi-component search/intervention method rather than repeatedly probing hand-picked sites until one succeeds. Any adaptive site selection must be recorded so the final holdout/control evaluation is not silently reused as the search set.

## Fail-closed boundaries

The backend must reject or downgrade to noncausal candidate evidence when any of these is unknown or mismatched:

- checkpoint/tokenizer/runtime/build identity;
- loader-consumed bytes;
- activation site identity;
- event/admission/route/generation binding;
- intervention identity;
- control-run identity;
- output identity;
- trace-to-InferenceReceipt binding;
- intervention-family placebo identity when required;
- target metric or off-target metric was selected after observing the intervention result.

An OpenAI-compatible completion endpoint that exposes only final text/logits is therefore `LOCAL_INFERENCE_CAPABLE` but not automatically `JSPACE_INTERVENTION_CAPABLE`.

## Promotion prohibitions

None of the following alone may mint causal J-Space credit:

- probe accuracy/AUROC;
- linear decodability;
- representation similarity or clustering;
- recurring vector direction;
- model self-report;
- textual coherence;
- clean/corrupted output difference without an internal intervention;
- an intervention effect without a method-matched placebo;
- an intervention effect whose off-target regressions exceed the predeclared bound.

## Cheapest next discriminator

On an authorized zero-cost local or `clay-direct-dev` surface, select the smallest already-available local model/backend that can expose one deterministic residual-stream or equivalent intermediate activation. Execute one clean/corrupted pair plus one target intervention and one **method-matched sham/placebo**, binding exact model/runtime/loader identities and output metric deltas into a receipt. For direction steering, the first placebo should be an equal-norm random direction at the same intervention locus.

Do not start with scale. One exact causal intervention with a discriminating placebo is higher information than many opaque completion calls or high-scoring probes.

## Track classification

`GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS`: ADVANCED_AT_SOURCE_CONTRACT_LEVEL_ONLY.

No J-Space model-runtime, HCU full-runtime, training or whole-product credit is granted by this document.
