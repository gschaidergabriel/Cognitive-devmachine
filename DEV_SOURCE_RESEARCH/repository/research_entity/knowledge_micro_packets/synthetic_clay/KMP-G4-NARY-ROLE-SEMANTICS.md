<!-- RAE_META
{"packet_id":"KMP-G4-NARY-ROLE-SEMANTICS","title":"Role-aware n-ary semantics are the invariant; hypergraph storage is optional","domains":["synthetic-clay","storage-state-memory","hyperposition"],"topics":["n-ary-relations","role-binding","hypergraph","reification"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"CLAY_G4_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T04:05:00+07:00","updated_at":"2026-08-08T04:05:00+07:00","source_refs":["research_entity/trigger_runs/clay/clay-20260808T0354p0700-chatgpt-secondary/FINAL_REPORT.md#exp-g4-nary-role-001","https://arxiv.org/abs/2506.05626"],"evidence_refs":["EXP-G4-NARY-ROLE-001","N-G3-001"],"related_claim_ids":["H-G3-001","H-G3-002"],"related_experiment_ids":["EXP-G4-NARY-ROLE-001","EXP-LIVE-HYPERPOSITION-BACKEND"],"predecessor_packet_ids":["KMP-HYPERPOSITION-SEMANTICS"],"supersedes_packet_ids":[],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Compare role-aware relation-node, temporal relational and native hypergraph implementations on identical n-ary queries, updates, crash recovery and revocation semantics.","search_terms":["n-ary relation","role binding","hypergraph","relation reification","hyperposition semantics"]}
RAE_META -->

### Core
Clay should make **role-aware n-ary relation semantics** first-class without committing the ontology to a specific hypergraph backend. In a 20,000-case G4 synthetic role-binding test, naive unlabeled pairwise decomposition reconstructed exact giver/recipient orientation only 50.11% of the time, while role-labelled reification reconstructed 100%.

### Evidence / boundary
This is a deliberately simple semantic-loss test, not a database benchmark. It aligns with G3's negative result that hyperposition does not require one storage form and with current n-ary knowledge-representation research emphasizing role/position awareness.

### Implication
The portable Clay contract should expose relation identity, arity, participant roles, context and temporal/provenance metadata. Hyperedges, relation nodes or temporal tables can then compete on performance and recovery while preserving identical semantics.

### Next test
Run equal-semantics backend replay under real FRANK relation patterns including role swaps, conflicts, revocations, concurrent updates and OOD query shapes.
