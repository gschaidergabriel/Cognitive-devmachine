<!-- RAE_META
{"packet_id":"FRANK_QWEN4B_BOOT_NEGATIVES_20260810","title":"Real Qwen4B VPS lane blocked by build-tool assumptions before inference","domains":["frank","harness","model_runtime"],"topics":["Qwen3-4B","llama.cpp","CMake","Ninja","Hostinger","negative result"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"NEGATIVE_RESULT","origin_class":"REMOTE_EXECUTION_RECEIPT","origin_actor":"unknown-concurrent-worker","created_at":"2026-08-10T00:10:00+07:00","updated_at":"2026-08-10T00:10:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/real_qwen4b_shadow_latest.json","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger@ed5d35e60105dc9ad12496833c219c8f0b36d3c5","gschaidergabriel/Dr.-Unterweger@5092752f2c100d9d23ca7f7015e4ecb57c4db55c"],"related_claim_ids":["FRANK-QWEN4B-BOOT-NEG-001","FRANK-QWEN4B-BOOT-NEG-002"],"related_experiment_ids":["FRANK_REAL_QWEN4B_SHADOW_DIFFERENTIAL"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"HIGH_FOR_FAILURE_CAUSE_ON_EXACT_RUNS","verification_required":true,"falsifier_or_next_test":"Obtain a receipt with pinned build tools resolved, model hash verified, real_model_executed=true and a non-null benchmark.","search_terms":["Qwen4B","MISSING_REQUIRED_COMMAND cmake","BOOTSTRAPPED_NINJA_MISSING","real_model_executed false"]}
RAE_META -->

### Core
Two real Hostinger Ubuntu attempts at the pinned Qwen3-4B-Instruct-2507 Q8_0 + llama.cpp shadow lane failed **before model inference**. Attempt 1 stopped at `MISSING_REQUIRED_COMMAND:cmake`; after a build-tool bootstrap repair, attempt 2 stopped at `BOOTSTRAPPED_NINJA_MISSING`. In both receipts `benchmark=null` and `real_model_executed=false`.

### Evidence / boundary
These failures directly falsify two runner-toolchain assumptions. They do not refute Qwen4B viability, llama.cpp viability, Frank's adapter, or adaptive recurrence quality. Model/runtime pins remained explicit.

### Implication
Treat toolchain provisioning as reproducible job-local infrastructure and preserve failed attempts as regression evidence rather than deleting them after repair.

### Next test
Use the current absolute-path/Make fallback lane and require actual model execution plus a non-null benchmark before any performance claim.
