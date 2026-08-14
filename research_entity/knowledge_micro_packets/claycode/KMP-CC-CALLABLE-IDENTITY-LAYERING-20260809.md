# KMP — ClayCode callable identity layering

packet_id: `KMP-CC-CALLABLE-IDENTITY-LAYERING-20260809`  
domains: `xeno_claycode`, `formal_methods_testing`, `security_capabilities`, `harness`, `unifieddb`, `claygraph`  
epistemic_class: `EXECUTABLE_PROXY_SUPPORTED_HYPOTHESIS`  
status_hint: `OPEN`  
origin_actor: `chatgpt-secondary`  
provider/model: `OpenAI / GPT-5.6 Sol`

## Atomic claim

ClayCode callable identity should be layered: lexical BindingKey, value FunctionTypeId, DefinitionSemanticId and provenance/ABI ContractId. Inferred effect summaries and runtime capability context must not mint lexical binding identity.

## Evidence

Local isolated Linux proxy: 50,000 mutation cases, 20,000 resolver pairs and 2,000 recursive graphs (40,000 function states). Layered identity remained acyclic and effect-only mutations preserved BindingKey; a deliberately effect-dependent binding scheme became cyclic and churned identity. Exact typed overloading was mechanically possible, but partial-type calls exposed ambiguity and no current BASE use case requires it.

## Boundary

Declared effect contracts may belong to callable type/contract when fixed before inference. Inferred effect closure remains analysis and runtime capability remains fresh authority. No BASE gate or language promotion follows from this proxy.

## Falsifier / next test

Integrate this identity layering behind the production strict parser and through SCC type/effect closure + lowering. Reject/refine if a simpler identity scheme preserves exact resolution, incremental invalidation, replay integrity and authority separation with lower implementation/diagnostic cost.

## Source refs

- `research_entity/trigger_runs/spawn/spawn-20260809T1741p0700-claycode-callable-identity/EXECUTABLE_RESEARCH_RECEIPT.json`
- `research_entity/trigger_runs/spawn/spawn-20260809T1741p0700-claycode-callable-identity/HYPOTHESES.json`
- `research_entity/trigger_runs/spawn/spawn-20260809T1741p0700-claycode-callable-identity/FINAL_REPORT.md`
