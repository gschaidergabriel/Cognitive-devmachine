<!-- RAE_META
{"packet_id":"KMP-GWT-RECONSTRUCTION-UPTAKE","title":"Workspace transport does not establish receiver reconstruction or uptake","domains":["frank_gwt","observability_recovery","model_runtime"],"topics":["gwt","broadcast","reconstruction","uptake","receipts","qwen"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"GWT_TRIGGER_RUN_3","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T06:08:00+07:00","updated_at":"2026-08-08T06:08:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T0608p0700-chatgpt-secondary/FINAL_REPORT.md","SRC-GWT-VR-KANAI-2021","SRC-GWT-FRANK-RUNTIME-20260805"],"evidence_refs":["E-GWT-R3-RECON-005"],"related_claim_ids":["C-GWT-R3-003","C-GWT-R3-005"],"related_experiment_ids":["EXP-GWT-RECONSTRUCTION-LESION-005","EXP-LIVE-GWT-RECONSTRUCTION-UPTAKE"],"predecessor_packet_ids":["KMP-GWT-CAUSAL-EPISODE"],"supersedes_packet_ids":[],"confidence":0.91,"verification_required":true,"falsifier_or_next_test":"Hold current FRANK workspace row/read constant while perturbing receiver semantic projection; measure Core inclusion, Qwen uptake and downstream effect independently.","search_terms":["GWT reconstruction","workspace uptake","broadcast receipt","semantic projection","Qwen uptake"]}
RAE_META -->

### Core
A successful workspace transport/read is not sufficient evidence that a receiver reconstructed or used the intended semantic content. The receiver contract should be `transport_receipt → projection_receipt → uptake_receipt → effect_receipt`.

### Evidence / boundary
In `EXP-GWT-RECONSTRUCTION-LESION-005`, transport remained successful for every sample while one receiver's reconstruction transform was removed. Across 120 synthetic seeds the target's semantic action accuracy fell to `0.433735 ± 0.090740`; five unlesioned receivers remained at 1.0 mean accuracy. This validates the diagnostic separation only; it is not a live FRANK result.

### Implication
For current FRANK, the important receiver boundary is persisted workspace semantic state → Core `[INNER_STATE]` → Qwen. Deterministic projection checks and an eventual validated latent model probe should be kept distinct from downstream behavioral/effect receipts.

### Next test
Perturb semantic projection after successful workspace read while holding transport constant, then measure receiver-specific uptake and effects.
