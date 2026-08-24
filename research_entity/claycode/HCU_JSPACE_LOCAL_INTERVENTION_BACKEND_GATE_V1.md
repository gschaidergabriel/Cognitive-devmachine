# HCU J-SPACE LOCAL INTERVENTION BACKEND GATE v1

Status: SOURCE / RESEARCH CONTRACT ONLY — NO MODEL-RUNTIME CREDIT
Authority epoch at creation: 8.68
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Mode: FREE_ONLY

## Problem

The new zero-cost local `llama.cpp`/Qwen research server is useful as a provider-independent inference surface, but a successful HTTP completion does not establish model-specific Global J-Space/GWT causality. J-Space promotion requires an instrumentable local execution path that can bind exact model/runtime identity to observed intermediate activations and controlled interventions.

## External donor principles

Current external implementations reinforce two useful principles:

- TransformerLens activation patching performs a clean/corrupted comparison and causally intervenes by replacing selected intermediate activations, then measures the output change.
- NNsight tracing exposes intermediate activations during a model forward pass and permits controlled modification of those activations in the trace context.

These are donor mechanisms only. EntityOS/HCU must preserve its own canonical state/evidence/effect boundaries and exact causal identity chain.

References:
- https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.patching.html
- https://github.com/ndif-team/nnsight/blob/main/docs/usage/trace.md

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
14. explicit classification of every recorded field as observed, derived, candidate or unknown.

## Required control structure

Minimum causal family:

- `BASELINE_CLEAN`
- `BASELINE_CORRUPTED`
- `INTERVENTION_TARGET`
- `SHAM_CONTROL`
- `OFF_TARGET_CONTROL`

A target effect is not promoted from one successful intervention alone. The target intervention must change the declared target metric relative to appropriate controls while off-target regressions remain inside a predeclared bound.

## Fail-closed boundaries

The backend must reject or downgrade to noncausal candidate evidence when any of these is unknown or mismatched:

- checkpoint/tokenizer/runtime/build identity;
- loader-consumed bytes;
- activation site identity;
- event/admission/route/generation binding;
- intervention identity;
- control-run identity;
- output identity;
- trace-to-InferenceReceipt binding.

An OpenAI-compatible completion endpoint that exposes only final text/logits is therefore `LOCAL_INFERENCE_CAPABLE` but not automatically `JSPACE_INTERVENTION_CAPABLE`.

## Cheapest next discriminator

On an authorized zero-cost local or `clay-direct-dev` surface, select the smallest already-available local model/backend that can expose one deterministic residual-stream or equivalent intermediate activation. Execute one clean/corrupted pair plus one target patch and one sham patch, binding exact model/runtime/loader identities and output metric deltas into a receipt.

Do not start with scale. One exact causal intervention is higher information than many opaque completion calls.

## Track classification

`GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS`: ADVANCED_AT_SOURCE_CONTRACT_LEVEL_ONLY.

No J-Space model-runtime, HCU full-runtime, training or whole-product credit is granted by this document.
