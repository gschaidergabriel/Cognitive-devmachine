<!-- RAE_META
{"packet_id":"KMP-G11-IDENTITY-AXES","title":"Hyperposition firebreaks should declare identity comparison axis","domains":["hyperposition","clay","claycode","unifieddb"],"topics":["identity axes","firebreaks","epoch","physical topology"],"epistemic_class":"OPEN_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/trigger_runs/hyperposition/hyperposition-20260808T1806p0700-chatgpt-secondary-r2/FINAL_REPORT.md","research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/MOSAIC_G11.claycode.json"],"verification_required":true}
RAE_META -->

### Core
A Hyperposition equality/cast/firebreak check should declare which axis it compares: semantic meaning, exact instance/provenance, basis/epoch, selection/query plan or reader view. Physical topology may change without changing semantic identity, and semantic equality may hold while provenance or representation differs.

### Runtime implication
Compact handles may carry only operation-required witnesses, with missing coverage forcing broader validation. One overloaded identity token is rejected.

### Next test
Packed Rust/C MOSAIC handles with axis-specific mutation fuzz and witness-coverage/fallback measurements.