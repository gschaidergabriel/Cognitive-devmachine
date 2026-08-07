<!-- RAE_META
{"packet_id":"KMP-HYP-CASCADE-TAIL","title":"Overcoupling control needs cascade-tail metrics beyond mean R_delta","domains":["systems-architecture","synthetic-clay","emergence"],"topics":["R_delta","overcoupling","change amplification","incremental computation","tail risk"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_SUPPORT","origin_class":"HYPERPOSITION_H1_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:26:00+07:00","updated_at":"2026-08-08T05:26:00+07:00","source_refs":["hyperposition-20260808T0526p0700-chatgpt-secondary:EXP-HYP-H1-CASCADE-002","Clay G5 EXP-G5-RDELTA-001"],"evidence_refs":[],"related_claim_ids":["H-HYP-008","H-HYP-009","H-HYP-016"],"related_experiment_ids":["EXP-HYP-H1-CASCADE-002","EXP-G5-RDELTA-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.72,"verification_required":true,"falsifier_or_next_test":"Instrument live FRANK dependency invalidations and test whether q95/q99 cascade size predicts latency/recovery failures or incremental-vs-rebuild crossover beyond mean amplification.","search_terms":["change amplification tail","R_delta","cascade q99","overcoupling tripwire","incremental rebuild crossover"]}
RAE_META -->

### Core
H1 extends the G5 `R_delta` idea: mean change amplification is insufficient when cascade-size distributions are heavy-tailed. The synthetic proxy showed a regime with ~1.97% mean affected state but ~19.75% q95 affected state.

### Evidence / boundary
The topology and propagation law were deliberately synthetic, so the numerical thresholds are not live-FRANK evidence. The experiment demonstrates a measurement failure mode: a low mean can coexist with damaging tail cascades.

### Implication
Track mean affected fraction together with q95/q99 cascade size, touched-edge work, invalidation depth, recovery time and the measured incremental-vs-rebuild crossover.

### Next test
Collect these distributions on real/twin FRANK traces and fit workload-specific tripwires rather than freezing one coupling coefficient.
