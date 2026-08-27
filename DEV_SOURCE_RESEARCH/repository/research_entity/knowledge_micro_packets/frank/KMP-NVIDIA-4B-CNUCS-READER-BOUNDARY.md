<!-- RAE_META
{"packet_id":"KMP-NVIDIA-4B-CNUCS-READER-BOUNDARY","title":"Actual 4B reader evidence supports view routing but not native-Clay internalization","domains":["frank","claycode","clay"],"topics":["CNUCS","4B-reader","native-Clay"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_SUPPORTED_WITH_BOUNDARY","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cove-compiled-20260808T1954p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cc10-compact-20260808T2000p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-COVE-4B-001","NV-XB-CC10-4B-002"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Run full-model Clay adaptation and matched P1/P2 view tests on the owner-target Qwen-class 4B.","search_terms":["FRANK C6 NVIDIA 4B","CNUCS reader","native Clay compact failure"]}
RAE_META -->

### Core
A real hosted 4B reader strongly benefits from a deterministic compiled operation view, but an aggressive compact Clay-like CC10 serialization failed the 16-case output contract entirely.

### Evidence / boundary
This separates two C6 hypotheses: view routing has direct generic-4B support; native compact Clay internalization remains untested because the model was not Clay-adapted and was not Qwen.

### Implication
FRANK should retain a deterministic Clay View Router and not assume the canonical or shortest serialization is automatically the best model-facing rail.

### Next test
Owner-target full-model Qwen-class Clay adaptation with matched natural/canonical/discrete-native arms.
