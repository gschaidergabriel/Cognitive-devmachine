<!-- RAE_META
{"packet_id":"KMP-FUS-F5-C3F-GWT","title":"Fusion F5: GWT candidate identity includes collection semantics and authentic-misleading controls","domains":["gwt","clay","claycode","claygraph","unifieddb"],"epistemic_class":"OPEN_METHOD_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T14:16:10Z","source_refs":["research_entity/trigger_runs/fusion/fusion-20260808T2114p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Delta
CSOC should bind collection/multiplicity/order semantics in candidate-set provenance. Authenticated records are insufficient if storage/query lowering changes `SET/ORDERED/MULTISET` meaning.

Fusion also separates stale-invalid activation from authentic-but-misleading activation. The former can be rejected by ancestry/epoch integrity; the latter requires stage-orthogonal semantic/cognitive controls.

### Next test
`FIELD {OFF,true,stale,role-shuffled,temporal-shuffled} x WORKSPACE_SELECTION x RAIL`, with final visible facts/order/token budget pinned.