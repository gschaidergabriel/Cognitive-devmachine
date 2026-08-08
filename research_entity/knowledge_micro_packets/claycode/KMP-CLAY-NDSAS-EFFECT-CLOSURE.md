<!-- RAE_META
{"packet_id":"KMP-CLAY-NDSAS-EFFECT-CLOSURE","title":"ClayCode Safe-Effect Closure and Foreign-Code Non-Amplification","domains":["claycode","clay","frank","security"],"topics":["effect algebra","compiler soundness","capability closure","generated code","FFI","prompt injection"],"epistemic_class":"OPEN_COMPILER_ARCHITECTURE_HYPOTHESIS_FROM_PERMANENT_CLAY_RESEARCH_AXIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T23:05:00+07:00","source_refs":["research_entity/global/CLAY_SAFE_EFFECT_GEOMETRY_RESEARCH_FOUNDATION.md","research_entity/knowledge_micro_packets/clay/KMP-CLAY-SAFE-EFFECT-GEOMETRY.md"],"verification_required":true}
RAE_META -->

# ClayCode implication

The permanent Clay Safe-Effect research axis requires ClayCode to test an effect system in which protected-state destructive/irreversible effects are not ordinary model-constructible capabilities while normal programming remains available through reversible/versioned/sandboxed operations.

The critical compiler/runtime closure condition is:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`

for generated Python, Bash, C, Rust, WASM, FFI, plugins, tools and subprocesses.

## Required distinctions

- dangerous concept representation != dangerous execution capability;
- compiler correctness != effect-policy adequacy != runtime enforcement completeness;
- model proposal != capability;
- `Persistent`, `Rebuildable`, `Ephemeral`, `Secret` and `External` state require different effect rules;
- irreversible external action may be requested but not self-authorized by the model.

## Highest-value ClayCode experiment

Extend the MRSC/ICSL executable compiler lab with typed effect classes and generate adversarial foreign-code payloads whose semantic intent attempts delete/format/truncate/drop/raw-write/resource-exhaust/secret-exfiltration. Run them in E2B/local/Judge0-style sandboxes with parent capabilities pinned and verify that no child path exceeds the parent effect envelope.

A pass must preserve ordinary compile/test/refactor/deploy utility. Refusal-only behavior does not count as containment evidence.
