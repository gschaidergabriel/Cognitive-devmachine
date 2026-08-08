<!-- RAE_META
{"packet_id":"MP-RETINA-HISTORICAL-METRIC-GOODHART","title":"Historical Retina coverage metrics contain a Goodhart trap","domains":["visual_perception_retina","formal_methods_testing","performance_economics"],"topics":["evaluation","CLIP threshold","test leakage"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"NEGATIVE_RESULT","origin_class":"HISTORICAL_SOURCE_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["Drive:digital-retina-emergent-readout.md","Drive:HONEST_REPORT.md","Drive:FINAL_REPORT.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["RET-E0","RET-E1"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.96,"verification_required":true,"falsifier_or_next_test":"Freeze a new held-out + realistic-negative benchmark before further tuning and reproduce current implementation.","search_terms":["retina 94.6 87.8 35.3 clip threshold 0.20 false positive hard set"]}
RAE_META -->

### Core
Historical high Retina coverage numbers must not be treated as final visual-truth accuracy. The source family contains two explicit traps: CLIP-lenient coverage of 94.6% used threshold 0.20, while an earlier calibration reported roughly 43.3% realistic-negative FPR at 0.20; and the later 87.8% strict hard-set score followed targeted vocabulary/projection changes derived from the same hard-set misses.

### Evidence / boundary
The May-26 honest report initially measured 35.3% strict hard-set coverage and documented structural failures. Later engineering improved surfaceability dramatically, which is useful, but the final hard-set is no longer independent after miss-guided gap closing.

### Implication
Do not optimize Retina to phrase recall or one embedding threshold. Release metrics require frozen unseen images, realistic negatives, compositional binding, calibration, UNKNOWN/OOD and downstream causal tasks.

### Next test
E0/E1: reproduce current code then freeze a clean final set by hashes before any vocabulary, threshold or model tuning.
