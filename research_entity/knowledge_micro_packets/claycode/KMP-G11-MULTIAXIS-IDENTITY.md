<!-- RAE_META
{"packet_id":"KMP-G11-MULTIAXIS-IDENTITY","title":"ClayCode identity expands from triple binding to operation-specific multi-axis binding","domains":["claycode","clay","frank","unifieddb"],"topics":["MRSC","E2B","semantic hash","query plan","basis"],"epistemic_class":"OPEN_REFINEMENT_WITH_EXECUTABLE_PRIOR_EVIDENCE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/knowledge_micro_packets/claycode/KMP-CC11-E2B-TRIPLE-BIND-IDENTITY.md","research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
CC11's E2B triple-bound candidate is retained and generalized. Critical handoffs distinguish semantic equality, contract/provenance instance, basis/epoch, query/selection plan and concrete emitted view. Typed collection algebra defines what semantic canonicalization may reorder/deduplicate.

### New evidence
In a 50k synthetic hybrid-selection test, a small query-plan weight change altered top-5 membership in 54.224% of cases while record bytes stayed unchanged. Plan identity therefore becomes a read dependency whenever selection changes the operation.

### Next test
Implement typed collection kinds and multi-axis receipt mutation/property tests in E2B ClayCode-Lab.