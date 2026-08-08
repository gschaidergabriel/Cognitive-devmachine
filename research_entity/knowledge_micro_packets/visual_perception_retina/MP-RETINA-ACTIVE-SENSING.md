<!-- RAE_META
{"packet_id":"MP-RETINA-ACTIVE-SENSING","title":"Visual uncertainty should allocate sensing computation","domains":["visual_perception_retina","frank_gwt","agent_orchestration"],"topics":["active perception","information gain","compute routing"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"CROSS_DOMAIN_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["https://doi.org/10.1016/j.ophoto.2025.100098","research_entity/retina/RETINA_SECOND_GENERATION_HYPOTHESES.json"],"evidence_refs":["research_entity/retina/runs/retina-20260809T0615p0700-deep-foundry/SYNTHETIC_MECHANISM_RECEIPT.json"],"related_claim_ids":[],"related_experiment_ids":["RET-E9"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.72,"verification_required":true,"falsifier_or_next_test":"Compare always/never/fixed-threshold/information-gain sensing policies on ambiguous real visual tasks.","search_terms":["retina active sensing information gain uncertainty visual compute router"]}
RAE_META -->

### Core
Retina should be tested as an information router rather than a fixed all-model pipeline. When current evidence is insufficient and the uncertainty matters, FRANK can select the next evidence-producing operation — crop, higher resolution, OCR retry, open-vocabulary detector, new anchor, alternate source or camera action — using expected information/task/safety value relative to compute, latency and risk.

### Evidence / boundary
Active-perception/next-best-view literature establishes uncertainty/information-gain-based sensor action as a mature research family. The deep-run synthetic second-look test only shows that selective expensive operations can form a cost/accuracy frontier; it does not establish an optimal FRANK policy.

### Implication
Uncertainty becomes a compute-allocation state, not merely a confidence number. This connects Retina directly to GWT, budgets and action selection.

### Next test
E9 with ambiguous held-out cases and fixed operation costs; compare always-on, never, simple uncertainty threshold and information-gain policies.
