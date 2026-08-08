<!-- RAE_META
{"packet_id":"KMP-CG5-ROUTE-SELECTIVE-DUAL-PATH","title":"ClayGraph activation should be route-selective rather than universally blended","domains":["claygraph","frank","unifieddb","gwt"],"topics":["dual-path memory","activation routing","Assembly","exact retrieval"],"epistemic_class":"SYNTHETIC_MECHANISM_PLUS_STAGED_SELF_USE","status_hint":"OPEN_SUPPORTED_MECHANISM","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/claygraph/claygraph-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/claygraph/claygraph-20260808T2212p0700-chatgpt-secondary-r3/SELF_USE_BENCHMARK.json"],"verification_required":true}
RAE_META -->

### Claim
ClayGraph activation should not be blended into every query. High-confidence exact routes should normally BYPASS learned salience; associative/ambiguous routes may SUPPLEMENT; multihop/low-confidence routes may ESCALATE; stale/role/temporal/poison/unknown conditions should QUARANTINE.

### Evidence
Current-RAE staged self-use: truthful prior Recall@5 0.756944 vs explicit 0.583333 and shuffled 0.604167, reproduced in E2B. Mixed synthetic routing locally favored the adaptive router (0.95 top-1) while always-blend harmed exact queries and shuffled field harmed associative queries. Exact remote router subset was pending at the evidence cutoff, so the exact effect size remains proxy-only.

### Falsifier
A matched target-FRANK workload finds a universal retrieval/blend policy that equals or exceeds adaptive routing on correctness, false association, latency, recovery and rare cases.
