<!-- RAE_META
{"packet_id":"KMP-G6-INVARIANT-CONFLUENT-CLOSURE","title":"Selective closure must combine authority boundaries with invariant-confluence risk","domains":["systems-architecture","ipc-distributed-systems","synthetic-clay"],"topics":["coordination","invariant-confluence","local-first","effect-gateway"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_NEGATIVE_RESULT","origin_class":"CLAY_G6_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:25:00+07:00","updated_at":"2026-08-08T05:25:00+07:00","source_refs":["clay-20260808T0525p0700-chatgpt-secondary:EXP-G6-INVCONFLUENCE-001","arXiv:1402.2237","github:automerge/automerge"],"evidence_refs":[],"related_claim_ids":["H-G6-021","H-G6-022","H-G6-T03"],"related_experiment_ids":["EXP-G6-INVCONFLUENCE-001"],"predecessor_packet_ids":["KMP-G5-SELECTIVE-DISTRIBUTED-CLOSURE"],"supersedes_packet_ids":[],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Classify real/twin FRANK state transitions by invariant and effect class, then partition-test strict, effect-only and invariant-aware closure.","search_terms":["invariant confluence","selective closure","coordination avoidance","CRDT","effect authority"]}
RAE_META -->

### Core
G6 weakens G5's effect-only synchronization boundary. A transition may require coordination even when it is purely internal if independently executed states cannot merge without violating an application invariant. Conversely, invariant-confluent state can often remain local.

### Evidence / boundary
In a 200k-pair capacity-invariant toy, treating all internal updates as coordination-free caused 34.8425% merged invariant violations. An invariant-aware classifier coordinated exactly the risky pairs and left 65.1575% local. Bailis et al.'s invariant-confluence framework supplies the external formal analogue. This is not a FRANK partition benchmark.

### Implication
Closure decision should approximate `authority/freshness risk OR non-invariant-confluent merge risk`, with CRDT/local-first methods reserved for compatible state classes.

### Next test
Replay FRANK/twin transitions under partitions and compare correctness, availability and latency across strict-global, effect-only and invariant-aware closure.
