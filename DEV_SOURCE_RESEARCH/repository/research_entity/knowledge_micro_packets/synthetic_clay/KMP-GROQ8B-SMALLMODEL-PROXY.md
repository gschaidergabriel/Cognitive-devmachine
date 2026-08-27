<!-- RAE_META
{"packet_id":"KMP-GROQ8B-SMALLMODEL-PROXY","title":"Small-model proxy adds reader cost, reconstruction integrity and graph-selection constraints to Synthetic Clay","domains":["synthetic_clay","model_runtime","claycode","claygraph","frank_gwt","hyperposition"],"topics":["small_model","8b_proxy_for_4b","reader_projection","semantic_ir","reconstruction","active_context","role_binding","authority"],"epistemic_class":"CROSS_BRANCH_EXPERIMENT_SYNTHESIS","claim_status_hint":"CURRENT_WITH_8B_PROXY_BOUNDARY","origin_class":"GROQ_8B_PROXY_EXPERIMENT_SUITE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T07:45:00+07:00","updated_at":"2026-08-08T07:45:00+07:00","source_refs":["research_entity/runtime/groq_8b_proxy/SCIENTIFIC_SYNTHESIS.json","research_entity/topic_packets/groq-8b-small-model-proxy/PACKET.json"],"evidence_refs":["GROQ8B-F1-CLAYCODE-ZEROSHOT","GROQ8B-F2-TCC-GAMMA-SAFETY","GROQ8B-F3-GWT-RECONSTRUCTION","GROQ8B-F4-GWT-WINNER-ORDER","GROQ8B-F5-HYPERPOSITION-ROLE-PROJECTION","GROQ8B-F6-CLAYGRAPH-SELF-USE"],"related_experiment_ids":["EXP-GROQ8B-XENO-REPRESENTATION-FACTORIAL-V4","EXP-GROQ8B-OTCC-GAMMA-SEMANTIC-V2","EXP-GROQ8B-GWT-RECONSTRUCTION-UPTAKE-PROXY","EXP-GROQ8B-HYP-ROLE-BINDING-V4","EXP-GROQ8B-CLAYGRAPH-FACTUAL-QA-V3"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Use actual Qwen3-4B/live FRANK to test whether reader-specific projection, deterministic authority semantics and optimized ClayGraph packet selection preserve these proxy directions.","search_terms":["Synthetic Clay Groq 8B","small model proxy","reader projection cost","ClayGraph HOLD","reconstruction integrity"]}
RAE_META -->

### Cross-branch delta
The Groq 8B proxy suite changes Synthetic Clay's objective from **semantic compactness alone** to **semantic compactness × reader success × safety × context-selection cost**. A representation can be smaller yet functionally worse for an untrained small reader; a graph can be relationally richer yet too slow/noisy for the hot path; a successful transport can carry a wrong projection; and compact safety syntax can increase unsafe model decisions.

### Architecture consequences
1. Canonical state/ClayCode IR remains explicit and deterministic; reader-facing projections are separately optimized and measured.
2. Authority/freshness/effect closure is host-derived rather than entrusted to model interpretation.
3. GWT episodes distinguish transport, semantic reconstruction, uptake and effect.
4. ClayGraph remains a semantic/associative substrate candidate but its current activation implementation stays `HOLD` for hot-path use.
5. Role-aware relation-instance projections are a promising small-reader surface for n-ary semantics.
6. Every small-model experiment counterbalances presentation/order and preserves the executed model class separately from the requested target class.

### Boundary
The suite is `8b_proxy_for_4b`. It guides the next Synthetic Clay architecture iteration but does not promote a 4B/live-FRANK claim.
