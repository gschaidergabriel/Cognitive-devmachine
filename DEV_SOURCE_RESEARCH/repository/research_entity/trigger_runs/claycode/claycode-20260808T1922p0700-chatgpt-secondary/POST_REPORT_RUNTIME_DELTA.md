# CC10 late runtime delta — OpenRouter Qwen3-4B target route

A new OpenRouter Qwen3-4B capability/policy was committed concurrently while CC10 was finalizing, so the run rechecked it before completion rather than relying on the older Groq-only state.

Results:
- `qwen/qwen3-4b` smoke test: **FAILED** — exact model not exposed by current OpenRouter account/catalog.
- `qwen/qwen3-4b:free` smoke test: **FAILED** — exact free model not exposed either.
- account catalog enumeration: **SUCCESS**, but no exact `qwen/qwen3-4b` slug was present.

Evidence refs:
- `research_entity/runtime/tool_results/openrouter-qwen3-4b-smoke-20260808T1942p0700.json`
- `research_entity/runtime/tool_results/openrouter-qwen3-4b-free-smoke-20260808T1945p0700.json`
- `research_entity/runtime/tool_results/cc10-1922-openrouter-list-models.json`

Consequence for CC10:
- no direct Qwen3-4B evidence is claimed;
- the newly registered capability remains **pending runtime verification** for the exact target model;
- Groq `llama-3.1-8b-instant` remains a correctly labeled `8b_proxy_for_4b` fallback for the reader comparison;
- target full-model Clay internalization remains open regardless, because hosted Qwen behavior would not close LoRA/full-FT/local-FRANK evidence anyway.

A concurrent Fusion r4 interconnect appeared after CC10 began and explicitly lists this CC10 run as an upstream run; it contains no completed downstream result that supersedes CC10.