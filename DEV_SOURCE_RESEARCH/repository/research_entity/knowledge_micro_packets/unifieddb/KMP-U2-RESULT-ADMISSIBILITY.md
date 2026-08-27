<!-- RAE_META
{"packet_id":"KMP-U2-RESULT-ADMISSIBILITY","title":"UnifiedDB results require explicit admissibility class","domains":["unifieddb","claycode","claygraph","gwt","hyperposition"],"epistemic_class":"OPEN_ARCHITECTURE_CONSTRAINT_WITH_EXECUTABLE_BOUNDARY_TEST","status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/QUERY_ROUTING_PLAN.json","research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

## Claim
Every UnifiedDB result should declare whether it is `AUTHORITATIVE_EXACT`, `EXACT_DERIVED`, `APPROXIMATE_CANDIDATE`, `SALIENCE_ONLY`, `MODEL_INTERNAL_ONLY`, `EXTERNAL_EVIDENCE` or a protected external reference.

This prevents one unified query language from silently flattening fact truth, derived exact values, ANN candidates, activation priors and model-internal state into one interchangeable value class.

U2 also separates typed semantic equality from exact emitted representation identity: 10,000 JSON roundtrips changed host tuple/list representation in every case while an explicit `ORDERED` semantic canonicalizer preserved meaning in every case.

## Boundary
The class set is an OPEN contract and still needs cross-engine/ClayCode integration tests.
