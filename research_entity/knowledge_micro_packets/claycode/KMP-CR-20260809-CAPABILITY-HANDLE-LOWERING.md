<!-- RAE_META
{"packet_id":"KMP-CR-20260809-CAPABILITY-HANDLE-LOWERING","title":"Lower Clay capability tokens to opaque scoped host handles","domains":["claycode","harness","frank","clayresearch"],"topics":["capabilities","safe-effect","ffi","lowering","authority"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"RESEARCH_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T17:16:00+07:00","updated_at":"2026-08-09T17:16:00+07:00","source_refs":["research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay","research_entity/trigger_runs/clay/clayresearch_20260809T1716p0700_chatgpt-secondary/SAFE_EFFECT_GEOMETRY_DELTA.md","bytecodealliance/cap-std:README.md"],"evidence_refs":["EXP-SAFE-001","cap-std capability-based security"],"related_claim_ids":["H-CR-003","H-CR-010","H2-CR-002","H2-CR-005"],"related_experiment_ids":["EXP-SAFE-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"MEDIUM_MECHANISM_LOW_END_TO_END","verification_required":"UBUNTU_COMPILER_RUNTIME","falsifier_or_next_test":"Compile CapabilityToken to a real Ubuntu scoped resource handle and attempt nested child/FFI authority widening.","search_terms":["CapabilityToken","opaque handle","authority non-amplification","child effect closure","cap-std"]}
RAE_META -->

### Core
The leading BASE Safe-Effect lowering hypothesis is `CapabilityToken -> opaque scoped host resource handle -> typed adapter -> receipt`. Model-visible names, paths and tool labels remain descriptive and do not mint authority.

### Evidence / boundary
G9 already encodes capability tokens and narrower-or-equal delegation. Synthetic set-intersection fuzzing produced zero authority-amplification violations, and cap-std provides an independent implementation analogue. Neither establishes complete Linux/FFI mediation.

### Implication
Child processes, generated code, tools and FFI must inherit no stronger effective effect set than the parent Clay contract unless an external grant is recorded.

### Next test
Implement the minimal Ubuntu adapter and run Python/Bash/C/Rust/Wasm/FFI/subprocess escape attempts plus resource-budget negatives.
