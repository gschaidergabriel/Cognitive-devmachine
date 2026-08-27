<!-- RAE_META
{"packet_id":"KMP-G11-WORKSPACE-BASIS","title":"GWT causal attribution should bind UnifiedDB/MOSAIC basis and reader handoff","domains":["gwt","clay","unifieddb","claycode"],"topics":["CSOC","MOSAIC","basis","query plan","rail"],"epistemic_class":"METHOD_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T1721p0700-chatgpt-secondary/FINAL_REPORT.md","research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/MOSAIC_G11.claycode.json"],"verification_required":true}
RAE_META -->

### Core
CSOC is extended with explicit basis/query-plan/selection and reader-view/rail identity. A workspace lesion is invalidly bundled if retrieval plan, candidate set, physical snapshot or reader rail changes with it.

### Next test
Factorial `BASIS x QUERY_PLAN x WORKSPACE x RAIL/PROJECTION x REENTRY` with identical canonical content and independent receipts.