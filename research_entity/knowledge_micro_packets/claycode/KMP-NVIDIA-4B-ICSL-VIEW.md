<!-- RAE_META
{"packet_id":"KMP-NVIDIA-4B-ICSL-VIEW","title":"Actual 4B intent-view test separates canonical typing from compact native representation","domains":["claycode","frank","clay"],"topics":["ICSL","intent-view","4B-reader"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_SUPPORTED_WITH_NEGATIVE_RESULT","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cc10-raw-20260808T2000p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cc10-typed-20260808T2000p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-cc10-compact-20260808T2000p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-CC10-4B-002"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.87,"verification_required":true,"falsifier_or_next_test":"Repeat on exact Qwen full-FT Clay model and compare trained native discrete rail against raw and canonical views.","search_terms":["CC10 NVIDIA 4B","ICSL 4B","compact Clay negative result"]}
RAE_META -->

### Core
On Nemotron-Mini-4B, the matched CC10 policy task scored 12/16 from raw intent and 13/16 from verbose typed intent; the compact symbolic arm failed to produce the required 16 outputs.

### Evidence / boundary
Typed L1 used 733 prompt tokens versus 405 raw (+81%). This is an untrained generic 4B, not the owner-target Qwen full-FT Clay model.

### Implication
ICSL's canonical contract may aid correctness, but canonical L1 and efficient CLAY_MODEL/P2 representations must remain separate compiler targets. Compactness alone is not AI-native fluency.

### Next test
Full-model target adaptation with matched L0/P1/P2 arms and explicit adequacy scoring.
