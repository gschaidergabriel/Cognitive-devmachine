# PR1421 successor-current distillery admission re-entry receipt

Status: **SOURCE/CONTROL REENTRY — NO PROVIDER, MODEL, HCU, J-SPACE, TRAINING OR WHOLE-PRODUCT RUNTIME CREDIT**

Date: 2026-08-24
Product: EntityOS
Integrated cognition/compute architecture: HCU
Newest observed supervisor at this re-entry: `8.67 / FREE_ONLY`
Canonical main observed during the re-entry: `9d16b4ef028d1b98319e7cb876c5b6ea1ff3b2f8`
Retained admission convergence lane: PR1421

## R0 observed

1. Current `main` has landed a canonical typed FREE provider admission helper, an 8.67 provider-admission object, supervisor admission-before-secret ordering, wrapper-level live admission rechecks, shared provider quota coordination, and distillery integration.
2. Current canonical provider admission represents only `groq`, `mistral`, and `nvidia`; each is currently `UNKNOWN` / not admitted. Provider runtime credit remains zero.
3. The supervisor derives the global compatibility flag when any represented LLM provider is admitted and starts `run_research_distillery_entry.py` under the supervisor lifecycle.
4. The distillery entrypoint does not itself add typed provider admission. It can select provisional OpenRouter reviewer lanes.
5. The underlying distillery directly reads credentials for OpenRouter, NVIDIA, Mistral, Groq, Tavily and Exa. `tavily_collect()` and `exa_collect()` perform keyed provider requests through the generic request path. These providers are not all represented by the current canonical provider-admission object.
6. Public unauthenticated arXiv/GitHub research fetches are a distinct no-secret research-fetch class and should not be conflated with secret-bearing/metered model/search provider execution.
7. Current-main wrapper chat requests recheck typed provider admission immediately before provider execution. Direct `run_free_go_swarm.py` remains separately reachable; PR1421 has a useful direct-base hardening delta for that path.
8. The current-main tripwire tests introduced before the latest resolver change still reference the previous bootstrap-bound resolver surface. The current helper now resolves successor authority through `SUPERVISOR_INBOX -> steering`, so tests must follow that same current authority source rather than patch removed bootstrap resolver fields.

## Main hypothesis

The admission repair is only complete when every secret-bearing or potentially metered provider path performs a successor-current typed `cost_class=FREE` decision before its provider secret is read and again before provider network I/O, while public unauthenticated research fetches remain explicitly separate.

## Counterhypothesis

Gating the supervisor and the three original swarm providers is sufficient because the distillery runs under the same `CLAY_FREE_ONLY_ATTESTED` process envelope.

This is not sufficient as an authority mechanism: the global compatibility flag proves neither provider identity nor provider-specific monetary class. A provider omitted from the typed admission object can otherwise inherit a global flag minted by a different admitted provider.

## Required successor-current fusion

- preserve the live `free_swarm_quota` gate, distillery SQLite context and worker -> `OPEN_RESEARCH_QUESTIONS_JSON` feedback bridge;
- preserve PR1421 direct-base-controller admission hardening;
- extend one canonical typed admission surface to all secret-bearing/metered distillery providers that can create monetary entitlement risk;
- select a requested provider before any provider-specific secret lookup and read only that provider secret after FREE admission;
- recheck provider admission immediately before provider socket/network I/O;
- prove missing/UNKNOWN/PAID/SUBSCRIPTION/expired/revoked decisions produce zero provider-secret reads and zero provider-network attempts;
- keep public unauthenticated arXiv/GitHub fetches explicitly distinct from secret-bearing provider execution;
- update deterministic tripwires to derive expected authority from the current live supervisor resolver;
- preserve exact-source runtime credit at zero until the successor head is actually executed on an authorized zero-cost local-normal-user or `clay-direct-dev` surface.

## Track mapping

- Track A — `ENTITYOS_EXECUTABLE_CONVERGENCE`: advances by preventing a partial provider-admission fix from regressing current main or leaving a parallel distillery execution path.
- Track B — `HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT`: advances one reusable typed external-provider capability/cost admission boundary without creating a second state/effect authority.
- Track C — `GLOBAL_JSPACE_GWT_PROTOTYPE_AND_TRAINING_READINESS_FREE_ONLY`: external research-feed execution becomes admissible only after provider-specific FREE closure; J-Space/model/training runtime credit remains zero. Independently, PR1263 now contains a causal steering acceptance protocol requiring matched controls, holdout families, layer/strength sweeps, off-target metrics and exact model/runtime identity.

## External-prior-art transfer

SLSA/in-toto-style provenance reinforces separation of untrusted external parameters from trusted control-plane/executor identity and digest-bound artifact/run identity. This is a transferable method only, not canonical Clay authority.

Recent activation-steering work reports direction- and layer-specific causal effects and uses equal-magnitude random perturbations as a control. This supports matched-null/random controls and predeclared layer sweeps for future J-Space causal acceptance; it does not establish a J-Space fact for the current model.

## Non-claims

- no unusual experiment was executed;
- no provider secret was consumed by this ChatGPT organ;
- no provider network execution was performed by this ChatGPT organ;
- no provider runtime credit;
- no full HCU runtime credit;
- no J-Space model-runtime credit;
- no training credit;
- no whole EntityOS/HCU PASS.

## Next exact gate

Fuse PR1421 onto the live successor main, close the distillery provider boundary and successor-stale test fixture, then execute the exact resulting head with secret-access and socket tripwires on an authorized zero-cost execution surface before promotion.