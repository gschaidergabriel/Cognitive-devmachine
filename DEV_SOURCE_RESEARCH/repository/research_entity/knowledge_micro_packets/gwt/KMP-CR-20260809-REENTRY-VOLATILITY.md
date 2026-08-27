<!-- RAE_META
{"packet_id":"KMP-CR-20260809-REENTRY-VOLATILITY","title":"Fixed re-entry gain fails under high process volatility","domains":["gwt","frank","emergenz","clayresearch"],"topics":["reentry","loop-dynamics","negative-result","adaptive-control"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"NEGATIVE_RESULT","origin_class":"EXECUTED_SYNTHETIC_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T17:16:00+07:00","updated_at":"2026-08-09T17:16:00+07:00","source_refs":["research_entity/trigger_runs/clay/clayresearch_20260809T1716p0700_chatgpt-secondary/EXPERIMENTS.md"],"evidence_refs":["EXP-REENTRY-002"],"related_claim_ids":["H-CR-019","H2-CR-006"],"related_experiment_ids":["EXP-REENTRY-001","EXP-REENTRY-002"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"MEDIUM_SYNTHETIC","verification_required":"LIVE_H1_REPLAY","falsifier_or_next_test":"Matched fixed-vs-adaptive re-entry on frozen H1 episodes across measured innovation/volatility regimes.","search_terms":["reentry volatility","fixed gain","process noise","GWT reentry","loop dynamics"]}
RAE_META -->

### Core
A fixed truthful re-entry gain is not monotonically beneficial. In the synthetic volatility sweep, raising process noise made truthful recurrent state worse than no re-entry across most tested autocorrelation settings, including high `rho`.

### Evidence / boundary
This is a synthetic state-estimation result, not live Frank/GWT evidence. A lower-volatility regime showed strong benefit, so the result refutes the fixed-gain generalization rather than re-entry itself.

### Implication
Re-entry/recurrence control should be conditioned on innovation, process-vs-observation volatility, residual pressure and marginal utility. Low state delta alone must not be read as successful convergence.

### Next test
Instrument H1 episodes and compare fixed gain, no re-entry, shuffled re-entry and an adaptive volatility-aware controller at matched compute.
