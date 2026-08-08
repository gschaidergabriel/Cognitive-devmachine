# RAE Research Tool Orchestration Policy

Substantive research runs must plan and record use of applicable registered research tools. If a provider is unavailable, rate-limited, out of quota, or lacks credentials, continue automatically with the best available legacy fallback and record the reason.

Executable enforcement:
- `tools/research_provider_router.py plan` creates the required provider plan for the task classes.
- `TOOL_EXECUTION_MANIFEST.json` records actual attempts, outcomes, sanitized usage/cost metadata and fallback reasons.
- `tools/research_provider_router.py validate-manifest` detects missing required attempts.
- `research_entity/runtime/TOOL_QUOTA_STATE.json` caches exhaustion/cooldown state to avoid repeated failed calls.

Default research bundles:
- scholarly: OpenAlex + arXiv; Semantic Scholar when operational;
- bibliographic: Crossref when DOI/publication identity matters;
- current web: Tavily + Exa, with DDGS/native web fallback;
- implementation: GitHub/source inspection;
- executable: local sandbox first, then E2B when operational, Piston/Judge0 as suitable fallbacks;
- target small-model experiments: when the scientific target is Qwen3-4B model behavior and local hardware identity is not required, use the registered OpenRouter `qwen/qwen3-4b` capability after runtime verification;
- proxy small-model experiments: if the target Qwen3-4B route is unavailable or the test only needs an approximate small-model proxy, use Groq `llama-3.1-8b-instant` as `8b_proxy_for_4b` under `research_entity/global/SMALL_MODEL_PROXY_POLICY.md`; Hugging Face is a fallback/independent provider when healthy and quota-available.

OpenRouter registration is stored in `research_entity/global/OPENROUTER_RESEARCH_CAPABILITY.json`; credential values remain only in the designated secret store and must never be copied into manifests, reports, packets or logs.

For an experiment whose scientific variable is specifically local target model identity, tokenizer/runtime implementation, local memory/KV behavior, energy/thermal profile, LoRA internalization or live-FRANK integration, a hosted OpenRouter Qwen3-4B call does not close that local/runtime experiment. It can close the model-behavior arm only. Every result must preserve `requested_target_class` separately from `executed_model_class`, exact provider/model slug, and evidence role.

A required applicable provider may be skipped only for an explicit recorded reason such as quota exhaustion, rate limiting, provider/runtime/credential unavailability, connector blocking or genuine non-applicability. Strong claim promotion must not silently bypass the tool plan.

Legacy fallback remains mandatory when a new provider cannot be used: native web research, direct primary sources, GitHub, public literature APIs, DDGS, local Python/container execution and archived RAE sources.
