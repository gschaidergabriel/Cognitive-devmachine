<!-- RAE_META
{"packet_id":"KMP-G9-READ-AWARE-EPOCH-MAINTENANCE","title":"Epoch compaction should be read-aware, not one fixed change threshold","domains":["claygraph","synthetic_clay","scheduling_concurrency"],"topics":["epochs","delta_overlay","compaction","maintenance_debt"],"epistemic_class":"SYNTHETIC_ENGINEERING_PROXY","origin_class":"CLAY_G9_PLUS_CLAYGRAPH_C4","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:40:00+07:00","source_refs":["research_entity/trigger_runs/clay/clay-20260808T1716p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/claygraph/claygraph-20260808T1712p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
ClayGraph C4 measured a growing query tax as delta overlays grow. G9 used those costs in a seeded economics proxy: a noisy read-aware selector had ~2.4% regret versus oracle, compared with ~18.7% for a fixed 5% threshold and ~23.8% for 10% in that workload.

### Negative result
One scalar maintenance policy is not universally superior: G9's separate debt-aware proxy lowered p95 but raised mean cost by rebuilding more often. Optimize explicit mean/tail/write/space/recovery objectives.

### Next test
Fit compaction policy on actual RAE/FRANK update/read traces and evaluate held-out amortized latency, p99, write amplification, memory and crash/recovery debt.
