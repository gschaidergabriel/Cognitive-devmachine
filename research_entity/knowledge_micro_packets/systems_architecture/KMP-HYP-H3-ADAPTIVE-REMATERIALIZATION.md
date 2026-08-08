<!-- RAE_META
{"packet_id":"KMP-HYP-H3-ADAPTIVE-REMATERIALIZATION","title":"Hyperposition projections need workload-aware rematerialization","domains":["systems-architecture","hyperposition","claygraph"],"topics":["incremental-computation","rebuild-crossover","compaction","online-control"],"epistemic_class":"MEASURED_HYBRID_PROXY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_PROXY_SUPPORT","origin_class":"HYPERPOSITION_H3_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:22:00+07:00","source_refs":["ClayGraph EXP-CG4-DELTA-EPOCH-001","EXP-HYP-H3-REMAT-003","GraphOne","TEGRA","POEGA"],"related_experiment_ids":["EXP-HYP-H3-REMAT-003"],"confidence":0.84,"verification_required":true,"falsifier_or_next_test":"Replay actual current-corpus update/read traces with controller overhead, partial rebuild and crash recovery."}
RAE_META -->

### Core
Incremental versus rebuild is an amortized workload decision, not a fixed changed-node threshold. Relevant variables include update cost, expected reads before the next update, projection query tax, memory tax, cascade tails and recovery risk.

### Evidence
Using the measured ClayGraph C4 proxy cost table under a generated nonstationary workload, an EWMA controller cost 1.040x the hindsight oracle versus 1.194x always-incremental, 1.200x fixed 10% cutoff and 1.515x always-rebuild.

### Boundary
The workload was synthetic and the cost surface came from Python proxy measurements. The controller is therefore a research candidate, not a production threshold.
