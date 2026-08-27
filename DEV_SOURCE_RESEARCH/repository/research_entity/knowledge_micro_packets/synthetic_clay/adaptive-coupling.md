<!-- RAE_META
{"packet_id":"KMP-CLAY-ADAPTIVE-COUPLING","title":"Fast/slow coupling should be adaptive and guarded against overcoupling","domains":["frank-gwt","synthetic-clay","emergence"],"topics":["coupling","fast-slow-loops","overcoupling","control"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:COUPLING/coupling_sweep.csv","RAE83_G1:GWT_GRF_MATHEMATICAL_OPERATIONALIZATION.md","RAE83_G1:STATE.json"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["EXP-C2-COUPLING-SWEEP"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Sweep coupling in live or high-fidelity FRANK with utility, noise amplification, recovery and re-entry latency measured jointly.","search_terms":["adaptive coupling","overcoupling","fast slow loops","reentry coupling","kappa sweep"]}
RAE_META -->

### Core
More coupling is not automatically better. The G1 synthetic sweep produced an interior optimum in its constructed regime and explicitly warned that coupling coefficients are control parameters rather than objectives.

### Evidence / boundary
The source run reported a positive difference for 0.9 versus 1.0 in one proxy environment. Later work found different preferred values, weakening any universal numeric coefficient while strengthening the adaptive-coupling principle.

### Implication
FRANK/Clay should tune coupling from outcome, noise and recovery signals rather than hard-code maximal interconnection.

### Next test
Run a preregistered live/high-fidelity sweep with task utility, directed information flow, error amplification and recovery as co-primary metrics.
