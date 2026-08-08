# RAE Small-Model Proxy Policy

## Current operational proxy

Until a verified bare/Qwen-class 4B runtime is operational, model experiments that require a small approximately-4B reader MAY and, when decision-relevant, SHOULD use:

- provider: Groq
- model: `llama-3.1-8b-instant`
- parameter class: 8B
- evidence role: `8b_proxy_for_4b`

This is a practical proxy, not a relabeling. Results MUST NOT be cited as actual 4B evidence.

## Applies to

Use the Groq 8B proxy for model-side experiments that do not require target-host weights/runtime, including:

- ClayCode/XENO reader exactness and representation comparisons;
- JSON vs compact/ClayCode projections;
- Gamma/TCC reasoning and authority-decision parsing;
- ClayGraph retrieval-context answer-quality experiments;
- GWT/FRANK matched-content winner/order sensitivity proxies;
- Hyperposition n-ary/role-binding representation tests;
- other small-model semantic decoding/classification experiments where model size is a variable but target hardware is not required.

## Does not substitute for

Keep the true target experiment OPEN when it requires:

- Qwen3-4B-specific weights/tokenizer/behavior;
- local 4B latency, memory, KV cache, energy, thermal or Android/edge measurements;
- LoRA training/internalization on the target model;
- live FRANK state, live GWT causal interventions, or target capability/runtime effects.

## Evidence discipline

Every proxy result records both:

- `requested_target_class` (for example `bare_4b` or `Qwen3-4B`), and
- `executed_model_class = 8B`, `evidence_role = 8b_proxy_for_4b`.

A positive 8B result can unblock architecture iteration and falsify some representation failures, but cannot prove a 4B model will match it. A negative 8B result is especially informative for a harder/smaller target, but still does not replace direct target replication.

## Default routing

For eligible pending small-model experiments, prefer Groq 8B while healthy/quota-available. If Groq is unavailable, fall back under the normal provider policy. When a verified 4B provider/runtime becomes available, rerun the target-sensitive subset and compare directly against the proxy.
