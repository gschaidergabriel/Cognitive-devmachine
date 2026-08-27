<!-- RAE_META
{"packet_id":"KMP-NVIDIA-EMBEDDING-ROLE-NULL","title":"Dense embedding similarity can erase directed role identity","domains":["emergence","hyperposition","claygraph"],"topics":["role-recurrence","embedding-null","E-CERT2"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_METHOD_SUPPORT","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-role-class-embedding-similarity-20260808T2010p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-EMBED-ROLE-004"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.94,"verification_required":false,"falsifier_or_next_test":"Repeat across multiple embedding models and role structures; regardless, recurrence identity must preserve explicit roles unless a calibrated role-sensitive metric is validated.","search_terms":["emergence embedding role reversal","E-CERT2 role recurrence","NVIDIA embeddings"]}
RAE_META -->

### Core
With NVIDIA `nv-embedqa-e5-v5`, directed role reversals were more similar than role-preserving paraphrases in two constructed relation pairs: 0.9918 vs 0.9362 and 0.9860 vs 0.9685.

### Evidence / boundary
This is a semantic-geometry counterexample, not evidence about FRANK emergence. It shows only that dense similarity can collapse a causally important role distinction.

### Implication
E-CERT2 recurrence/organization matching must preserve directed role identity and cannot use embedding similarity alone to declare the same assembly/organ recurring.

### Next test
Use explicit role-preserving candidate identity in prospective OOD recurrence and lesion/rescue experiments.
