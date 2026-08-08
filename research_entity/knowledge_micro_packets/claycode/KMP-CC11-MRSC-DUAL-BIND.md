<!-- RAE_META
{"packet_id":"KMP-CC11-MRSC-DUAL-BIND","title":"Critical Clay projections require dual source/output binding","domains":["claycode","frank","hyperposition"],"topics":["ProjectionReceiptV2","translation validation","fuzzing"],"epistemic_class":"LOCAL_PROPERTY_FUZZ_PLUS_ARCHITECTURE_HYPOTHESIS","claim_status_hint":"OPEN_SUPPORTED","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","source_refs":["research_entity/trigger_runs/claycode/claycode-20260808T2015p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true,"falsifier_or_next_test":"Stateful/property fuzz plus target compiler translation validation over serialized/wire/model views."}
RAE_META -->

### Core
Binding a canonical source hash is not enough to prove which reader payload was actually emitted. `S.PROJECTION_RECEIPT_V2` therefore binds both `canonical_input_hash` and `projected_view_hash`, plus schema/compiler/reader/basis/role identity and semantic-coverage validation.

### Evidence / boundary
In CC11's 100,000-case constructed mutation fuzz, source-only binding left 20,112 unsafe accepts; the dual-bound reference rejected all tested mutations. This is not a formal or production-security proof.
