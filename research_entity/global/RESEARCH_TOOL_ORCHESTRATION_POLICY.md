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
- model experiments: local/target model plus Hugging Face when an independent model/embedding/inference comparison is decision-relevant.

A required applicable provider may be skipped only for an explicit recorded reason such as quota exhaustion, rate limiting, provider/runtime/credential unavailability, connector blocking or genuine non-applicability. Strong claim promotion must not silently bypass the tool plan.

Legacy fallback remains mandatory when a new provider cannot be used: native web research, direct primary sources, GitHub, public literature APIs, DDGS, local Python/container execution and archived RAE sources.
