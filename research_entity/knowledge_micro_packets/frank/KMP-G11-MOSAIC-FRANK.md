<!-- RAE_META
{"packet_id":"KMP-G11-MOSAIC-FRANK","title":"FRANK should consume operation-specific identity capsules over logical UnifiedDB","domains":["frank","clay","claycode","unifieddb"],"topics":["MOSAIC-G11","CNUCS","UnifiedDB","MRSC"],"epistemic_class":"CROSS_BRANCH_OPEN_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/MOSAIC_G11.claycode.json"],"verification_required":true}
RAE_META -->

### Core
FRANK C6 remains Clay-native, but its handoff boundary should track semantic, provenance-instance, basis/epoch, selection-plan and reader-view identity separately. UnifiedDB supplies one logical persistence/query plane while physical engines remain swappable; MRSC remains after the trusted causal slice.

### Safety
Capability/effect authority stays externally gated and physically isolatable. Neither UnifiedDB nor MOSAIC can mint authority.

### Next test
One full twin episode with independent basis, selector and reader-view mutations before effect commit.