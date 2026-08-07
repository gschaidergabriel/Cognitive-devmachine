<!-- RAE_META
{"packet_id":"KMP-GWT-BROADCAST-OVERCOUPLING","title":"Broadcast utility needs a perturbation-amplification shadow","domains":["frank_gwt","observability_recovery","synthetic_clay"],"topics":["gwt","broadcast","overcoupling","noise","capacity"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"GWT_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-07T22:29:00Z","updated_at":"2026-08-07T22:29:00Z","source_refs":[],"evidence_refs":["E-GWT-RUN-ADAPTIVE-001","N-G3-003"],"related_claim_ids":["C-GWT-RUN-004","C-GWT-RUN-006"],"related_experiment_ids":["EXP-GWT-RUN-ADAPTIVE-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.92,"verification_required":true,"falsifier_or_next_test":"Inject bounded workspace corruption in a FRANK twin while sweeping fanout/coupling; measure task utility, downstream state divergence, recovery cost and latency.","search_terms":["global workspace broadcast","overcoupling","noise amplification","fanout","selective multicast"]}
RAE_META -->

### Core
Maximizing workspace broadcast/coupling is not a safe universal objective. In `EXP-GWT-RUN-ADAPTIVE-001`, stronger coupling improved clean synthetic performance but monotonically increased the immediate propagation of injected workspace corruption. Under 5% corruption, `beta=0.4` beat `beta=1.0` by mean MSE `0.02211` across 60 paired seeds; bootstrap 95% interval for `beta0.4 - beta1.0` was `[-0.02554,-0.01865]`.

### Evidence / boundary
This is a constructed nonstationary modular proxy, not FRANK. It demonstrates a counterexample to universal maximum coupling, not a transferable optimum.

### Implication
Every GWT broadcast score should carry a noise/perturbation-amplification and recovery-cost shadow. Logical global availability may be implemented with selective physical multicast rather than unconditional maximal fanout.

### Next test
Repeat the corruption/fanout sweep on synchronized FRANK twin traces.
