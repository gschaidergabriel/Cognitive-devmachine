<!-- RAE_META
{"packet_id":"KMP-CLAY-HYPERPOSITION-SEMANTICS","title":"Hyperposition preserves contextual alternatives without destructive collapse","domains":["synthetic-clay","memory-state","emergence"],"topics":["hyperposition","conflict","unknown","bitemporal-state"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:FORMALIZATION/HYPERPOSITION_H0_H10_DECISION.md","RAE83_G1:HYPERPOSITION/hyperposition_H0_H10_complete_summary.csv","RAE83_G1:STATE.json"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["EXP-C1-HYPERPOSITION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Replicate contextual reconstruction on live FRANK state with independently implemented temporal-log and faceted backends.","search_terms":["hyperposition","faceted state","set-valued state","conflict preservation","unknown preservation"]}
RAE_META -->

### Core
The G1 synthetic tests supported a semantic rule: context-bound alternatives, conflict, revocation and unknown should coexist until a query/projection resolves what is relevant. Destructive scalar overwrite lost information; information-preserving temporal/faceted forms reconstructed the tested contextual states much better.

### Evidence / boundary
The source run reports scalar exact reconstruction around 0.387 in the expanded H0-H10 test while its indexed hyperposition candidate reached 1.0. This is synthetic evidence about semantics, not proof that a particular graph backend is uniquely required.

### Implication
Hyperposition is better treated as a query/state invariant than as a storage-engine claim.

### Next test
Run equal-semantics implementations on real FRANK histories and compare correctness, update cost, query latency and recovery.
