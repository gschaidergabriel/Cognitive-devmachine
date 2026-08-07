<!-- RAE_META
{"packet_id":"KMP-CLAY-ANTI-GOODHART-ACTIVE-CONTEXT","title":"High retrieval recall can destroy causal usefulness under an active-context budget","domains":["synthetic-clay","memory-state","research-methods"],"topics":["goodhart","retrieval","active-context","causal-path"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:ANTI_GOODHART/retrieval_goodhart_audit.json","RAE83_G1:GOODHART_CERTIFICATE.json","RAE83_G1:FINAL_SYNTHETIC_CLAY_CONCEPT.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["EXP-C3-GOODHART"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.89,"verification_required":true,"falsifier_or_next_test":"Repeat under real task traces with fixed token/compute budgets and compare recall, causal-path completeness and task success.","search_terms":["goodhart retrieval","broadcast all","causal path","active context budget","coarse to fine retrieval"]}
RAE_META -->

### Core
Optimizing retrieval recall alone can select a degenerate strategy. In the G1 synthetic audit, broadcast-all achieved maximal recall but failed to preserve complete causal paths under the active-context budget, while selective coarse-to-fine retrieval traded some recall for much better causal usefulness.

### Evidence / boundary
This is a synthetic anti-Goodhart result, not a universal retrieval benchmark.

### Implication
Clay/RAE retrieval metrics need shadow metrics: causal completeness, irrelevant bytes/tokens, contradiction preservation, task success and model-call cost.

### Next test
Recreate the comparison on real FRANK/RAE tasks under fixed active-context budgets.
