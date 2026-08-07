<!-- RAE_META
{"packet_id":"KMP-G4-INCREMENTAL-OVERCOUPLING","title":"Incremental recomputation advantage collapses as coupling density rises","domains":["synthetic-clay","performance-economics","scheduling-concurrency"],"topics":["incremental-recomputation","overcoupling","active-projections","dependency-amplification"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"CLAY_G4_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T04:05:00+07:00","updated_at":"2026-08-08T04:05:00+07:00","source_refs":["research_entity/trigger_runs/clay/clay-20260808T0354p0700-chatgpt-secondary/FINAL_REPORT.md#exp-g4-incremental-002"],"evidence_refs":["EXP-G4-INCREMENTAL-002"],"related_claim_ids":[],"related_experiment_ids":["EXP-G4-INCREMENTAL-002","EXP-LIVE-HYPERPOSITION-BACKEND"],"predecessor_packet_ids":["KMP-CLAY-ADAPTIVE-COUPLING"],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Replay sparse real FRANK updates over instrumented active projections at multiple dependency densities and compare delta work, tail latency and correctness against full reconstruction.","search_terms":["incremental recomputation","overcoupling","dependency amplification","active projection","delta propagation"]}
RAE_META -->

### Core
In a new G4 synthetic DAG test, sparse incremental recomputation touched only 0.237% of a 4,000-node graph at indegree 1, rising to 21.363% at indegree 8. The theoretical work advantage versus a full pass fell from about 421x to 4.68x as dependency density increased.

### Evidence / boundary
This is controlled synthetic proxy evidence, not a live FRANK latency benchmark. It supports two linked mechanisms: incremental active projections can be extremely cheap for sparse changes, and excessive coupling destroys that locality.

### Implication
Overcoupling can be operationalized partly as change/descendant amplification under a propagation budget. Clay should maintain only causally useful hot projections and monitor fan-out rather than maximize interconnection.

### Next test
Instrument a real FRANK/Clay dependency graph and sweep coupling while jointly measuring affected-state fraction, p50/p95 latency, task utility, recovery and energy.
