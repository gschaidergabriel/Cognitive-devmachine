<!-- RAE_META
{"packet_id":"KMP-GWT-CAUSAL-FRESHNESS","title":"GWT re-entry should be freshness-gated at use time","domains":["frank_gwt","scheduling_concurrency","observability_recovery"],"topics":["gwt","reentry","freshness","age-of-information","adaptive-control"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN_WITH_SYNTHETIC_SUPPORT","origin_class":"GWT_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-07T22:49:00Z","updated_at":"2026-08-07T22:49:00Z","source_refs":["SRC-GWT-QAOI-2020","SRC-GWT-QAOI-2021"],"evidence_refs":["E-GWT-R2-FRESHNESS-003"],"related_claim_ids":["C-GWT-R2-002","C-GWT-R2-003"],"related_experiment_ids":["EXP-GWT-FRESHNESS-003","EXP-LIVE-GWT-LESION-FRESHNESS"],"predecessor_packet_ids":["KMP-GWT-CAUSAL-EPISODE"],"supersedes_packet_ids":[],"confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Replay FRANK with truthful/shuffled/removed re-entry across delays and regime/state changes; compare raw age against state-compatible predictive freshness.","search_terms":["GWT reentry freshness","age of information at query","stale feedback","causal freshness"]}
RAE_META -->

### Core
Truthful re-entry should not update active FRANK state merely because it is recent. Its usefulness should be evaluated when consumed using age-at-use, source-state compatibility/validity epoch and predictive causal value.

### Evidence / boundary
In synthetic AR(1) replay, the last beneficial delay grew strongly with process persistence; the tested crossover tracked process correlation half-life. Query-Age-of-Information literature independently shows that pull-based systems can require freshness metrics at query time. Neither result proves the FRANK mechanism.

### Implication
Add a causal-freshness gate to `reentry_receipt`; stale payloads may remain historical evidence without becoming active control input.

### Next test
Run paired live/twin FRANK re-entry lesions with delay, state-match and regime-change factors.
