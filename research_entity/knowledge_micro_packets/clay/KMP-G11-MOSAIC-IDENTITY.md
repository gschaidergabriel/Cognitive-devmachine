<!-- RAE_META
{"packet_id":"KMP-G11-MOSAIC-IDENTITY","title":"MOSAIC makes identity operation-specific and multi-axis","domains":["clay","frank","claycode","unifieddb"],"topics":["MOSAIC-G11","identity","causal slice","receipts"],"epistemic_class":"OPEN_ARCHITECTURE_CANDIDATE_WITH_SYNTHETIC_AND_RUNTIME_SUPPORT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/MOSAIC_G11.claycode.json","research_entity/runtime/e2b_verification.json"],"verification_required":true}
RAE_META -->

### Core
COVE's smallest sound causal slice survives, but G11 adds separate identity axes for executable semantics, exact contract/provenance instance, basis/epoch, selection/query-plan and concrete reader view. One super-hash is rejected.

### Evidence
Fresh E2B compiler evidence separated semantic and contract identity. G11's 100k synthetic mutation calibration found 39,915 false semantic inequalities under a provenance-bound single hash and 24,781 view mutations unbound by semantic-only identity; separated axes had zero errors in the constructed family.

### Boundary
This is an OPEN mechanism/architecture result, not a collision-proof or production-security proof.

### Next test
Property/stateful tests over typed SET/ORDERED/MULTISET/WEIGHTED semantics plus live/twin handoff replay.