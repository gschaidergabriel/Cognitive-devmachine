<!-- RAE_META
{"packet_id":"KMP-HYP-NARY-ROLE-ABI","title":"Preserve n-ary relation-instance identity and roles across backends","domains":["memory-state","synthetic-clay","systems-architecture"],"topics":["hyperposition","n-ary relations","role binding","hypergraphs","reification"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_BOUNDED_FORMAL_SUPPORT","origin_class":"HYPERPOSITION_H1_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:26:00+07:00","updated_at":"2026-08-08T05:26:00+07:00","source_refs":["hyperposition-20260808T0526p0700-chatgpt-secondary:EXP-HYP-H1-NARY-001","Text2NKG arXiv:2310.05185","n-ary relation taxonomy arXiv:2506.05626","Clay G5 H-G5-025/H-G5-026"],"evidence_refs":[],"related_claim_ids":["H-HYP-002","H-HYP-003","H-HYP-004"],"related_experiment_ids":["EXP-HYP-H1-NARY-001"],"predecessor_packet_ids":["KMP-CLAY-HYPERPOSITION-SEMANTICS"],"supersedes_packet_ids":[],"confidence":0.90,"verification_required":true,"falsifier_or_next_test":"Round-trip identical live FRANK n-ary histories through relational/event-log, role-aware reified graph and native hypergraph backends and compare exact semantic reconstruction plus cost.","search_terms":["n-ary role ABI","hyper-relational","relation instance identity","pairwise projection loss","hypergraph reification"]}
RAE_META -->

### Core
A portable hyperposition ABI should retain a relation-instance identity plus explicit role→entity/value bindings. Pairwise projections are not generally sufficient: H1 constructed two disjoint ternary relations with identical projections on every role pair.

### Evidence / boundary
The counterexample is exact for its finite construction and establishes information loss from pairwise projection in general. It does not establish that native hyperedge storage is necessary; an ordinary graph can retain the same semantics by reifying each relation instance and its role edges.

### Implication
Treat role-aware n-ary semantics as canonical and storage form as replaceable. Benchmark native hyperedges only as a locality/query/update optimization.

### Next test
Run equal-semantics backend roundtrips including conflicts, revocation, bitemporal updates and recovery.
