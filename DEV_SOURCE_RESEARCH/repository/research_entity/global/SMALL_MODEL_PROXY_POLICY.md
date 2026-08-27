# RAE Small-Model Target / Proxy Policy

## Current target route

When a model-side experiment specifically targets Qwen3-4B and does **not** require local hardware/runtime identity, prefer the registered OpenRouter capability:

- provider: OpenRouter
- model: `qwen/qwen3-4b`
- parameter class: 4B
- evidence role: `direct_qwen3_4b_external_runtime`
- capability registration: `research_entity/global/OPENROUTER_RESEARCH_CAPABILITY.json`

This is direct evidence about the hosted Qwen3-4B model behavior exposed by OpenRouter. It is **not** local-device evidence and must not be used to close experiments whose scientific variable is Android/edge runtime, local tokenizer/runtime behavior, KV-cache layout, energy, thermal profile, LoRA internalization or live-FRANK integration.

## Fallback proxy

If the verified Qwen3-4B route is unavailable, quota-limited or provider-blocked, eligible small-model semantic-reader experiments MAY fall back to:

- provider: Groq
- model: `llama-3.1-8b-instant`
- parameter class: 8B
- evidence role: `8b_proxy_for_4b`

The Groq result is a practical proxy, not a relabeling. It MUST NOT be cited as actual 4B evidence.

## Applies to the hosted Qwen3-4B target route

Use the verified OpenRouter Qwen3-4B route for model-side experiments that do not depend on target-host hardware, including:

- ClayCode/XENO reader exactness and representation comparisons;
- JSON/raw state vs deterministic COVE/ClayCode projections;
- Gamma/TCC/CBCC basis and authority-decision parsing;
- ClayGraph matched-context answer-quality experiments;
- GWT/FRANK matched-content winner/order/projection sensitivity;
- Hyperposition n-ary/role-binding representation tests;
- other semantic decoding/classification experiments where actual Qwen3-4B behavior is the missing variable.

## Does not substitute for

Keep the local target experiment OPEN when it requires:

- local Qwen3-4B latency, memory, KV cache, energy, thermal or Android/edge measurements;
- exact local inference-engine behavior when provider-side routing/transforms could matter;
- LoRA training/internalization on the target model;
- live FRANK state, live GWT causal interventions, or target capability/runtime effects.

## Evidence discipline

Every result records separately:

- `requested_target_class`;
- `executed_model_class`;
- provider + exact model slug;
- evidence role;
- whether the result is hosted-model behavior or local-runtime behavior.

For OpenRouter `qwen/qwen3-4b`, record `requested_target_class = Qwen3-4B`, `executed_model_class = 4B`, `evidence_role = direct_qwen3_4b_external_runtime`.

For Groq fallback, record `executed_model_class = 8B`, `evidence_role = 8b_proxy_for_4b`.

## Default routing

1. If the scientific variable is hosted Qwen3-4B semantic/model behavior and the OpenRouter capability is runtime-verified, use OpenRouter Qwen3-4B.
2. If OpenRouter is unavailable, use Groq 8B as an explicitly labeled proxy when the experiment remains informative.
3. If the variable is local hardware/runtime identity, neither hosted route closes the target experiment.
4. Compare OpenRouter Qwen3-4B directly against historical Groq 8B proxy arms where a matched protocol exists; do not treat agreement as independent replication when prompts/scorers share ancestry.
