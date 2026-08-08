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
- executable general: local sandbox + Judge0 are verified fallbacks; E2B/Piston are used when operational;
- executable ClayCode/compiler/runtime: prefer registered `sandboxapi_sandbox` once it reaches `RUNTIME_VERIFIED`; until then use local sandbox/Judge0 and record the SandboxAPI blocker. SandboxAPI executions are research evidence only and every nontrivial ClayCode run must feed compile/runtime counterexamples and measurements back into the ClayCode research artifacts;
- target Qwen3-4B experiments: use a verified exact Qwen3-4B route when available; the currently tested OpenRouter and NVIDIA credential catalogs did not expose an executable exact Qwen3-4B route, so Qwen-specific claims remain OPEN;
- generic actual-4B model-behavior experiments: prefer verified NVIDIA `nvidia/nemotron-mini-4b-instruct` when Qwen identity is not itself the scientific variable; record it as direct generic-4B hosted evidence, never as Qwen evidence;
- proxy small-model experiments: use Groq `llama-3.1-8b-instant` as `8b_proxy_for_4b` only when a direct 4B model is unavailable or the historical matched protocol requires the proxy;
- embeddings / semantic-geometry / retrieval representation: NVIDIA `nvidia/nv-embedqa-e5-v5` is runtime-verified at 1024 dimensions and may be used for ClayGraph retrieval and geometry experiments; embedding similarity must never be treated as canonical relation identity, role identity, authority or causal identity;
- reranking: NVIDIA reranking is registered but its credential-valid hosted route is currently unresolved after HTTP 404 attempts; do not mark it available until a live successful call exists.

Provider registrations:
- OpenRouter: `research_entity/global/OPENROUTER_RESEARCH_CAPABILITY.json`;
- NVIDIA: `research_entity/global/NVIDIA_RESEARCH_CAPABILITY.json`;
- SandboxAPI/RapidAPI: `research_entity/global/SANDBOXAPI_RESEARCH_CAPABILITY.json` — gateway routing verified, current account state `BLOCKED_NOT_SUBSCRIBED` until an actual remote code execution succeeds.
Credential values remain only in the designated secret store and must never be copied into manifests, reports, packets or logs.

For ClayCode specifically, an executable research loop is part of the scientific method rather than optional implementation work: language hypotheses should be translated into real parser/compiler/interpreter/type/effect artifacts, executed against positive/negative/fuzz cases, and converted into durable `EXECUTABLE_RESEARCH_RECEIPT` evidence. A compiler pass or successful program output is not by itself semantic support; expected-vs-observed behavior and counterexamples must be tied to explicit hypotheses.

For experiments whose variable is local target model identity, tokenizer/runtime implementation, hidden-state/KV access, local memory, latency, energy/thermal behavior, LoRA/full-model internalization or live-FRANK integration, hosted inference does not close the local/runtime experiment. Hosted inference can close only the matching model-behavior arm. Every model result must preserve exact provider/model slug, requested target class, executed model class where known, and evidence role.

A required applicable provider may be skipped only for an explicit recorded reason such as quota exhaustion, rate limiting, provider/runtime/credential unavailability, connector blocking, missing provider subscription, or genuine non-applicability. Strong claim promotion must not silently bypass the tool plan.

Legacy fallback remains mandatory when a new provider cannot be used: native web research, direct primary sources, GitHub, public literature APIs, DDGS, local Python/container execution and archived RAE sources.
