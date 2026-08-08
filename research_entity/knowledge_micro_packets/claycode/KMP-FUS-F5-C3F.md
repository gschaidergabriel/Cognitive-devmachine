<!-- RAE_META
{"packet_id":"KMP-FUS-F5-C3F-CLAYCODE","title":"Fusion F5: typed collection algebra is part of executable query identity","domains":["claycode","unifieddb","clay","gwt"],"epistemic_class":"OPEN_MECHANISM_SUPPORT_FROM_LOCAL_SQLITE_EXECUTION","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T14:16:25Z","source_refs":["tools/claycode_query_semantics_lab.py","research_entity/trigger_runs/fusion/fusion-20260808T2114p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Result
Fresh CC12 direction is strengthened. Local SQLite differential execution over 30,000 seeded cases produced 0 mismatches for type-correct lowering, while a type-erased DISTINCT route mismatched 16,947 cases and a bag/ordered route mismatched 16,609.

### Consequence
`SET/ORDERED/MULTISET/WEIGHTED/PRIORITY` belongs in ClayCode executable/query identity and UnifiedDB selection-plan receipts. Storage adapters must prove or test semantic preservation rather than infer collection meaning from container shape.

### Boundary
This replicates the declared mechanism locally; it is not independent conceptual evidence and does not yet validate every engine or weighted/priority semantics.