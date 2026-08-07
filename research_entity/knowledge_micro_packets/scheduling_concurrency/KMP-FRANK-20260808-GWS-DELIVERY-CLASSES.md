<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-GWS-DELIVERY-CLASSES","title":"Workspace callbacks need explicit delivery classes, not a global sync/async switch","domains":["scheduling_concurrency","frank_gwt","observability_recovery","systems_architecture"],"topics":["backpressure","callback scheduling","workspace delivery"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN","origin_class":"CODE_PLUS_SYNTHETIC_EXPERIMENT_PLUS_EXTERNAL_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:51:00+07:00","updated_at":"2026-08-08T05:51:00+07:00","source_refs":["EXP-FRANK-GWS-CALLBACK-BACKPRESSURE-R2","ROS2 Executors documentation","NATS Slow Consumers documentation"],"evidence_refs":[],"related_claim_ids":["H-G3-005","H-G3-006"],"related_experiment_ids":["EXP-FRANK-GWS-CALLBACK-BACKPRESSURE-R2"],"predecessor_packet_ids":["KMP-FRANK-20260808-GWS-SYNC-CALLBACK"],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Implement instrumentation-only callback timing first; then compare current sync delivery against typed delivery classes on target-host traces with identical semantic outcomes.","search_terms":["GWS callback backpressure latest wins must apply best effort queue slow consumer"]}
RAE_META -->

### Core
FRANK should not replace synchronous GWS dispatch with one undifferentiated async queue. Each event/effect should declare a delivery semantic such as `MUST_APPLY`, `LATEST_WINS/COALESCE`, or `BEST_EFFORT`, while deterministic hot reducers may remain synchronous under a measured budget.

### Evidence / boundary
A synthetic lesion made publisher latency track injected subscriber delay approximately one-for-one; async queuing removed publisher delay but a small drop queue discarded 32/40 events. ROS 2 explicitly separates callback groups/executors and permits priority separation; NATS treats slow consumers and bounded pending data as first-class failure/backpressure concerns. These analogies support the mechanism but do not establish the optimal FRANK thresholds.

### Implication
The workspace event envelope needs queue/delivery semantics and receipts: enqueue/start/finish times, drop/coalesce reason, causal parent and outcome/reentry identity. Otherwise async execution can improve latency while destroying causal traceability.

### Next test
Instrument existing callbacks without changing semantics. Only migrate callbacks whose measured p99 violates a declared hot-path budget, then lesion overflow policies by event class.
