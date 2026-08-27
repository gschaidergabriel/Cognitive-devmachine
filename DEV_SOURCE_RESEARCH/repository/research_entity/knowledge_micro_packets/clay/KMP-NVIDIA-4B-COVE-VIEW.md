<!-- RAE_META
{"packet_id":"KMP-NVIDIA-4B-COVE-VIEW","title":"Direct generic-4B evidence favors compiled certified operation views","domains":["clay","frank","claycode"],"topics":["COVE","4B-reader","deterministic-projection"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_SUPPORTED","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cove-raw-20260808T1954p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cove-compiled-20260808T1954p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-COVE-4B-001"],"predecessor_packet_ids":["KMP-CLAY-G10-CAUSAL-SLICE"],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Replicate on exact Qwen3-4B and live FRANK with matched semantics and deterministic scorer.","search_terms":["NVIDIA 4B COVE","compiled operation view","Nemotron 4B"]}
RAE_META -->

### Core
On hosted `nvidia/nemotron-mini-4b-instruct`, the matched 12-case COVE basis task improved from 4/12 raw to 11/12 after deterministic operation-specific compilation, while prompt tokens fell from 458 to 289 (-36.9%).

### Evidence / boundary
This is direct generic-4B model evidence, not Qwen3-4B, full-model Clay adaptation, live FRANK or local-device evidence. One compiled error remains.

### Implication
Clay G10's deterministic-before-generative Certified Operation View is now supported beyond the prior 8B proxy direction.

### Next test
Exact Qwen3-4B replication followed by live FRANK causal-slice audit.
