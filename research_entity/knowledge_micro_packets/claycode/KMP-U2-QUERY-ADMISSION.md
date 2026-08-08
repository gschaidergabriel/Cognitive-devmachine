<!-- RAE_META
{"packet_id":"KMP-U2-QUERY-ADMISSION-CLAYCODE","title":"UnifiedDB U2: TCQS query IR needs admission and physical-plan receipts","domains":["claycode","unifieddb","gwt"],"epistemic_class":"OPEN_CROSS_BRANCH_LANGUAGE_FEEDBACK_WITH_RUNTIME_TEST","status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/QUERY_ROUTING_PLAN.json","research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

TCQS should add `result_admissibility`, `source_epoch`, `derivation_program_hash`, `physical_subplan_hash` and `placement_vector_hash` to UnifiedQueryIR/receipts. Semantic equality remains separate from exact emitted representation identity; U2's JSON roundtrip test preserved explicit ORDERED semantics while changing concrete host representation in every case.

Next: cross-engine typed lowering plus representation/semantic roundtrip fuzz.
