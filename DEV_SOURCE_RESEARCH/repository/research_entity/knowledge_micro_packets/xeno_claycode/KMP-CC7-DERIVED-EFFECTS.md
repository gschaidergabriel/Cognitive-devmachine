<!-- RAE_META
{"packet_id":"KMP-CC7-DERIVED-EFFECTS","title":"ClayCode effect and dependency footprints must be derived by trusted operation semantics","domains":["xeno-claycode","security-capabilities","formal-methods-testing"],"topics":["effect-system","read-set","write-set","capabilities","authority","compiler"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_REPLICATED_PROXY_SUPPORT","origin_class":"CLAYCODE_CC7_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:49:00+07:00","updated_at":"2026-08-08T05:49:00+07:00","source_refs":["claycode-20260808T0549p0700-chatgpt-secondary:EXP-CC7-DERIVED-EFFECT-003","claycode-20260808T0549p0700-chatgpt-secondary:EXP-CC7-DERIVED-EFFECT-JUDGE0-004","arXiv:2507.10301","MLIR ODS/interfaces"],"evidence_refs":[],"related_claim_ids":["H-CC7-003","H-CC7-006","H-CC7-007","H-CC7-016"],"related_experiment_ids":["EXP-CC7-DERIVED-EFFECT-003","EXP-CC7-DERIVED-EFFECT-JUDGE0-004"],"predecessor_packet_ids":["KMP-CLAYCODE-AUTHORITY-BOUNDARY"],"supersedes_packet_ids":[],"confidence":0.91,"verification_required":true,"falsifier_or_next_test":"Implement a pinned ClayCode op registry; mutation-test derived footprints against dynamic instrumentation including indirect/dynamic operations."}
RAE_META -->

### Core
A model may choose a typed ClayCode operation and arguments, but it must not be trusted to declare the operation's own safety-relevant footprint. A trusted parser/compiler/interpreter should derive at least `read_set`, `write_set`, `invariant_set`, `effect_class`, `required_caps`, and the pinned operation-semantics version/hash.

### Evidence / boundary
A 100k local constructed test with deliberately incomplete model claims produced a 10.748% missed-conflict rate when claims were trusted and zero misses for the derived footprint. An independent 50k Judge0 execution reproduced the direction: 7.398% missed conflicts for trusted claims and zero for derived footprints. These are typed-operation proxies, not proof that all real Clay operations have statically complete effects.

### Implication
Effect typing and capability authority remain separate: the type/semantics describes what the operation can touch or cause; the external gateway decides whether the invocation is authorized now.

### Safety rule
Dynamic/unknown effects are never interpreted as an empty footprint. They conservatively escalate.
