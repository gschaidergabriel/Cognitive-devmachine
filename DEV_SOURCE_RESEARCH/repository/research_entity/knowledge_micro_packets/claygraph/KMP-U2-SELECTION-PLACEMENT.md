<!-- RAE_META
{"packet_id":"KMP-U2-SELECTION-PLACEMENT-CLAYGRAPH","title":"UnifiedDB U2: ClayGraph selection integrity and graph placement are separate from record truth","domains":["claygraph","unifieddb","gwt"],"epistemic_class":"OPEN_CROSS_BRANCH_FEEDBACK_WITH_RUNTIME_CALIBRATION","status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/STORE_ROLE_MATRIX.json"],"verification_required":true}
RAE_META -->

ClayGraph remains a derived/rebuildable associative substrate by default. U2 separates graph data placement, graph index placement and graph compute placement, and requires an explicit selection/search-space receipt when graph structure can reallocate candidate membership.

In a constructed 700-case PPR-like calibration, changing untrusted structure changed naive selection in 516 cases while trusted-structure reselection restored the baseline in 700/700. This supports a live ClayGraph selector-integrity experiment; it does not promote G1d.
