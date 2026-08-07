<!-- RAE_META
{"packet_id":"KMP-GWT-GATE-VS-IGNITION","title":"Configured workspace gating must be separated from endogenous ignition evidence","domains":["frank_gwt","observability_recovery","formal_methods_testing"],"topics":["gwt","ignition","threshold","recurrence","hysteresis","goodhart"],"epistemic_class":"METHOD_MEMORY","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"GWT_TRIGGER_RUN_3","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T06:08:00+07:00","updated_at":"2026-08-08T06:08:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T0608p0700-chatgpt-secondary/FINAL_REPORT.md","SRC-GWT-MASHOUR-2020","SRC-GWT-DEL-CUL-2007","SRC-GWT-IGNITION-INDEX-2026","SRC-GWT-FRANK-RUNTIME-20260805"],"evidence_refs":["E-GWT-R3-FRANK-WORKSPACE","E-GWT-R3-IGNITION-004","E-GWT-R3-GNW-IGNITION","E-GWT-R3-IGNITION-INDEX"],"related_claim_ids":["C-GWT-R3-001","C-GWT-R3-002","C-GWT-R3-004"],"related_experiment_ids":["EXP-GWT-IGNITION-IDENT-004","EXP-LIVE-GWT-GATE-IDENTIFIABILITY","EXP-LIVE-GWT-RECURRENT-LESION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.94,"verification_required":true,"falsifier_or_next_test":"Replay identical current FRANK candidate traces under multiple shadow ZUENDSCHWELLE values while logging pre-gate dynamics; then lesion feedback/re-entry and test transition sharpness, persistence and hysteresis.","search_terms":["FRANK GWT ignition","configured threshold","ZUENDSCHWELLE","threshold shift","recurrent ignition","hysteresis"]}
RAE_META -->

### Core
FRANK's configured `ZUENDSCHWELLE=0.55` can create a sharp binary `gezuendet` transition by construction. Therefore `gate_event` must be recorded separately from scientific `ignition_evidence`. Endogenous ignition requires independent dynamical evidence such as a pre-gate nonlinear transition, threshold-shift invariance, ambiguity/bimodality, persistence or hysteresis, and sensitivity to recurrent/feedback lesions.

### Evidence / boundary
In `EXP-GWT-IGNITION-IDENT-004`, a synthetic hard gate produced transition-location anchoring slope `0.99817 ± 0.01116` as the configured threshold moved; an independently observed pre-gate transition remained invariant in that diagnostic toy. GNW literature associates ignition with nonlinear recurrent amplification. These facts define a measurement safeguard, not a live FRANK ignition result.

### Implication
A configured threshold must never automatically satisfy the metric used to evaluate GWT ignition. This blocks a direct measurement-Goodhart failure.

### Next test
Run shadow threshold sweeps on current FRANK traces, then feedback/re-entry lesions with compute-matched controls.
