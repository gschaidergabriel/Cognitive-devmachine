<!-- RAE_META
{"packet_id":"FRANK_REAL_QWEN4B_FIRST_EXECUTION_20260810","title":"First successful real Qwen3-4B Q8_0 execution on Hostinger Ubuntu","domains":["frank","harness","gwt","model_runtime"],"topics":["Qwen3-4B","llama.cpp","CPU inference","confidence calibration","tool call","adaptive recurrence"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT","origin_class":"REMOTE_EXECUTION_RECEIPT","origin_actor":"concurrent-research-entity-worker","created_at":"2026-08-10T00:33:00+07:00","updated_at":"2026-08-10T00:33:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/real_qwen4b_shadow_latest.json","research_entity/reports/20260810T0032p0700_FRANK_REAL_QWEN4B_FIRST_EXECUTION_ADDENDUM.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger@c9d06222643aa9028940cbba24b0421f6ef45ad6"],"related_claim_ids":["FRANK-QWEN4B-REAL-EXEC-001","FRANK-QWEN4B-CONFIDENCE-NEG-001"],"related_experiment_ids":["FRANK_REAL_QWEN4B_SHADOW_DIFFERENTIAL"],"predecessor_packet_ids":["FRANK_QWEN4B_BOOT_NEGATIVES_20260810"],"supersedes_packet_ids":[],"confidence":"HIGH_FOR_EXACT_RUN_LOW_FOR_GENERALIZATION","verification_required":true,"falsifier_or_next_test":"Run conservative prebuilt V2 and a larger held-out/OOD calibration benchmark; test confidently-wrong stable trajectories against halt/escalate behavior.","search_terms":["Qwen4B 10.7 tok/s","100 confidence wrong","read_state Qwen","real_model_executed true","Hostinger Qwen3 4B"]}
RAE_META -->

### Core
The pinned Qwen3-4B-Instruct-2507 Q8_0 model successfully executed under pinned llama.cpp on the real Hostinger Ubuntu runner. The four-task fixed pilot scored 3/4, mean decode throughput was ~10.705 tok/s and mean prompt throughput ~39.941 tok/s. The real tool case selected `read_state` with valid arguments and persisted no hidden reasoning field.

### Critical negative observation
On `2^10 mod 7`, the model returned `4` instead of `2` while reporting `CONFIDENCE=100`. This directly shows that raw visible self-confidence is not a calibrated correctness probability for this exact model/task and must not become Frank truth or control authority.

### Boundary
The successful receipt used V1 offline recurrence accounting. Its 20% recurrence/latency reduction remains diagnostic only because current V2 counts savings only for `HALT_CANDIDATE_CONVERGED` and falls back to the full fixed budget for route/escalate/rollback/abort/uncertain decisions.

### Next test
Conservative V2, then a larger calibration/OOD set comparing verbalized confidence, stability, self-consistency/logit-based signals where available, and external verification.
