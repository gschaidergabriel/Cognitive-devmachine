<!-- RAE_META
{"packet_id":"KMP-G5-RDELTA-CHANGE-AMPLIFICATION","title":"R_delta operationalizes overcoupling as downstream change reproduction","domains":["synthetic-clay","performance-economics","scheduling-concurrency"],"topics":["incremental-computation","overcoupling","change-amplification","r-delta"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_SYNTHETIC_ONLY","origin_class":"CLAY_G5_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:08:00+07:00","updated_at":"2026-08-08T05:08:00+07:00","source_refs":["clay-20260808T0508p0700-chatgpt-secondary:EXP-G5-RDELTA-001","Differential Dataflow/Timely Dataflow external implementation evidence"],"evidence_refs":[],"related_claim_ids":["H-G5-009","H-G5-010","H-G5-012"],"related_experiment_ids":["EXP-G5-RDELTA-001"],"predecessor_packet_ids":["KMP-G4-INCREMENTAL-OVERCOUPLING"],"supersedes_packet_ids":[],"confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Instrument live FRANK events and measure actual invalidation/recompute cascade size versus fanout, propagation probability and edit rate.","search_terms":["R_delta","change reproduction number","change amplification","incremental recomputation","overcoupling"]}
RAE_META -->

### Core
G5 proposes `R_delta` as an engineering control variable: the expected number of consequential downstream state invalidations caused by one changed state. In a synthetic branching proxy, mean affected fraction was tiny near `R_delta=1.0` and rose rapidly above it, while stochastic extinction remained common.

### Evidence / boundary
This is synthetic mechanism evidence, not a universal theorem and not a live FRANK measurement. It sharpens the previous qualitative overcoupling warning by giving real traces a measurable target.

### Implication
Clay can regulate coupling using observed change amplification rather than raw graph density or one fixed global kappa.

### Next test
Measure `R_delta` on real FRANK traces and locate the workload-specific point where incremental maintenance ceases to beat rebuild.