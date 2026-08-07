# Reserved Trigger: `claycode`

Research ClayCode as an internal language/IR for a system that is itself represented and partially implemented in Synthetic Clay. Use the Master Research Trigger Protocol.

Core research questions:
- Can the language faithfully represent the same state, relations, authority, provenance, assemblies and transitions that constitute its own runtime?
- Which semantics belong in the canonical IR versus reader-specific projection/wire syntax?
- Can a Clay-written runtime interpret/transform ClayCode without circular ambiguity or hidden authority escalation?
- What must remain deterministic outside the model: parser, schema, canonicalization, capability checks, commit gateway, rollback and receipts?
- Can a Qwen-class 4B model be trained/simulated to operate on the internal state language rather than merely imitate surface syntax?

Required research dimensions:
- self-description/reflection without conflating representation with authority;
- canonical AST/IR and deterministic roundtrip;
- state/version/provenance/unknown/conflict semantics;
- activation/assembly/workspace primitives;
- outcome/re-entry/credit primitives;
- external capability/commit boundary;
- parser/validator/compiler fuzzing;
- context/token/repair cost versus JSON/key=value/natural-language baselines;
- reader-specific projections and live-reader break-even;
- Qwen-4B simulation or live tests, explicitly labeled `simulation_only` when no target model is actually run;
- bootstrapping/self-hosting path: host runtime -> ClayCode runtime -> Clay-represented system.

A language candidate is not promoted because it looks compact or alien. Promotion requires semantic preservation, bounded repair cost, target-reader performance and safety/authority invariants.

Write the final report to `research_entity/trigger_runs/claycode/<run_id>/FINAL_REPORT.md` and finish with the mandatory status footer.
