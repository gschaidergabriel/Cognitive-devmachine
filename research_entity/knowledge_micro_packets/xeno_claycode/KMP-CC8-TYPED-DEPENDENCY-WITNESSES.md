<!-- RAE_META
{"packet_id":"KMP-CC8-TYPED-DEPENDENCY-WITNESSES","title":"ClayCode freshness needs typed object, predicate, invariant and temporal witnesses","domains":["xeno_claycode","storage_state_memory","formal_methods_testing","frank_gwt"],"topics":["ClayCode","freshness","predicate-dependency","phantom","invariants","temporal-dependency","workspace-revision"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_COUNTEREXAMPLE_AND_EXTERNAL_SUPPORT","origin_class":"CLAYCODE_CC8_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T06:06:00+07:00","updated_at":"2026-08-08T06:06:00+07:00","source_refs":["claycode-20260808T0606p0700-chatgpt-secondary:EXP-CC8-PREDICATE-001","PostgreSQL18:transaction-iso","arXiv:1208.4179","arXiv:2607.27074"],"evidence_refs":[],"related_claim_ids":["H-CC8-001","H-CC8-002","H-CC8-T02","H-CC8-T04","H-CC8-T07"],"related_experiment_ids":["EXP-CC8-PREDICATE-001","EXP-CC8-VOLATILE-003"],"predecessor_packet_ids":["KMP-CC7-SCOPED-FRESHNESS","KMP-G6-FRESHNESS-BOUND-GAMMA"],"supersedes_packet_ids":[],"affected_branches":["claycode","clay","frank","gwt","hyperposition"],"confidence":0.91,"verification_required":true,"falsifier_or_next_test":"Extract real FRANK/Clay predicates, channel revisions and n-ary invariants; replay concurrent mutations and compare whole-root, object-only and typed-witness validation for misses, false rejects and cost.","search_terms":["predicate witness","phantom dependency","serializable snapshot isolation","temporal effect","ClayCode freshness"]}
RAE_META -->

### Core
A ClayCode transition cannot generally reduce freshness to an object `read_set`/`write_set`. Semantic dependencies may be **negative predicates/ranges**, cross-object or n-ary **invariants**, and **temporal/environment inputs** such as workspace/channel revisions or regime tags. CC8 therefore proposes typed dependency witnesses rather than one flat read set.

### Evidence / boundary
`EXP-CC8-PREDICATE-001` constructs a create-if-absent race where two transactions insert different object IDs after both observe an empty predicate: object-only OCC misses the conflict by construction, while a predicate/invariant epoch catches it. PostgreSQL Serializable/SSI independently requires predicate/dependency monitoring for serialization anomalies. Current 2026 type-and-effect work shows temporal dependencies/stale reads can also be tracked as effects. Numeric CC8 results remain synthetic.

### Implication
CC-RC1.3 should distinguish object versions, predicate/range witnesses, invariant epochs, volatile/temporal receipts, capability handles and causal workspace/episode revisions. Whole-root validation remains a safe fallback when scope is unknown.

### Next test
Instrument actual FRANK workspace reads and state transitions to derive the smallest sound witness classes under concurrency/replay.
