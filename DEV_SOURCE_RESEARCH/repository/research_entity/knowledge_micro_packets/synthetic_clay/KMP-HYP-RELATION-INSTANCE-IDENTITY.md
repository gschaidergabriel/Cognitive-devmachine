<!-- RAE_META
{"packet_id":"KMP-HYP-RELATION-INSTANCE-IDENTITY","title":"Relation-instance identity preserves n-ary semantics that pairwise flattening loses","domains":["synthetic-clay","memory-state","systems-architecture"],"topics":["hyperposition","n-ary","role-binding","reification","event-identity"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"HYPERPOSITION_H2_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:50:00+07:00","updated_at":"2026-08-08T05:50:00+07:00","source_refs":["arXiv:2506.05626","arXiv:2606.03179","hyperposition-20260808T0550p0700-chatgpt-secondary:EXP-HYP-H2-RELATION-003"],"related_claim_ids":["H-HYP2-006","H-HYP2-007","H-HYP2-008"],"related_experiment_ids":["EXP-HYP-H2-RELATION-003"],"confidence":0.93,"verification_required":true,"falsifier_or_next_test":"Round-trip bitemporal, branched, revoked FRANK relation instances across relational/event-log, reified-graph and optional native-hypergraph backends."}
RAE_META -->

### Core
For general n-ary state, pairwise edges are a lossy projection unless they retain the identity of the relation instance that binds all roles together. H2 tested 5,000 ternary events: pairwise joins produced 92,690 plausible triples in a representative run, only 5,000 true (~5.39% precision); mean precision across ten seeds was ~5.31%. Explicit relation-instance identity + roles round-tripped exactly by construction.

### Evidence / boundary
This is a representation counterexample, not a performance benchmark. It does not require a native hypergraph store: a reified relation node in an ordinary graph can preserve event identity and role bindings.

### Implication
Canonical Hyperposition ABI should preserve `relation_instance_id`, roles, context/time, provenance, branch/conflict and revocation; pairwise edges/native hyperedges are derived indexes or storage optimizations.
