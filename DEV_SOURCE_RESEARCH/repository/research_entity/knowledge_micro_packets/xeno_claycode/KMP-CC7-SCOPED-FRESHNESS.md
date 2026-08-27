<!-- RAE_META
{"packet_id":"KMP-CC7-SCOPED-FRESHNESS","title":"Separate snapshot identity from dependency-scoped commit freshness","domains":["xeno-claycode","storage-state-memory","security-capabilities","ipc-distributed-systems"],"topics":["state-root","freshness","dependency-closure","versions","invariants","ClayCode"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_AND_EXTERNAL_SUPPORT","origin_class":"CLAYCODE_CC7_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:49:00+07:00","updated_at":"2026-08-08T05:49:00+07:00","source_refs":["claycode-20260808T0549p0700-chatgpt-secondary:EXP-CC7-SCOPED-FRESHNESS-001","claycode-20260808T0549p0700-chatgpt-secondary:EXP-CC7-HIDDEN-DEP-002","KMP-G6-FRESHNESS-BOUND-GAMMA","PostgreSQL MVCC","etcd transactional revision comparisons"],"evidence_refs":[],"related_claim_ids":["H-CC7-001","H-CC7-002","H-CC7-004","H-CC7-005"],"related_experiment_ids":["EXP-CC7-SCOPED-FRESHNESS-001","EXP-CC7-HIDDEN-DEP-002"],"predecessor_packet_ids":["KMP-G6-FRESHNESS-BOUND-GAMMA"],"supersedes_packet_ids":[],"confidence":0.84,"verification_required":true,"falsifier_or_next_test":"Instrument real FRANK proposal lifetimes and dynamic read/write traces; compare whole-root rejection, object/version validation and invariant-aware scoped validation."}
RAE_META -->

### Core
The global `state_root` should identify and provenance the immutable basis snapshot, but need not be the sole commit-freshness predicate. When the trusted operation semantics yields a complete dependency/invariant closure, commit validation can compare the current versions/epochs of that closure and safely revalidate a proposal whose global basis root became stale only because unrelated state changed.

### Evidence / boundary
In a constructed sparse-key workload, whole-root mismatch rapidly approached universal rejection as unrelated churn increased, while complete scoped validation tracked actual conflicts. A counterexperiment deliberately injected hidden dependencies and immediately produced missed conflicts. Therefore scoped freshness is conditional on a complete or conservatively over-approximated closure.

### Safety rule
Unknown, reflective, indirect or dynamically unresolved effects escalate to broader validation/coordination. A global-root mismatch is never silently ignored.

### Next test
Real FRANK instrumentation with proposal delay, object versions, invariant epochs, dynamic access traces and crash/replay recovery.
