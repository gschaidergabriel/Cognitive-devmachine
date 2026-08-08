<!-- RAE_META
{"packet_id":"KMP-NVIDIA-EMBEDDING-FIREBREAK-BOUNDARY","title":"Embedding geometry cannot enforce Clay semantic firebreaks","domains":["hyperposition","claygraph","frank"],"topics":["semantic-firebreak","role-binding","embedding-geometry"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT_METHOD_SUPPORT","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-role-class-embedding-similarity-20260808T2010p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-EMBED-ROLE-004"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.93,"verification_required":false,"falsifier_or_next_test":"Runtime-enforced cast factorial remains required; no similarity threshold should substitute without explicit calibrated proof.","search_terms":["Hyperposition NVIDIA embedding","semantic firebreak similarity","role binding"]}
RAE_META -->

### Core
NVIDIA embedding geometry assigned extremely high similarity to role-reversed relations, and the same surface sentence remained highly similar across `FACT_EXACT`, `ACTIVATION_PRIOR`, `PROPOSAL` and `AUTHORITY_CAP` labels.

### Evidence / boundary
Class tags lowered cosine from exact-surface fact to roughly 0.839-0.881, but this remains similarity, not type enforcement. Role reversal reached 0.992 in one pair.

### Implication
HYP-RC4's firebreak must remain a typed runtime/compiler property. Embeddings may retrieve candidates but cannot define legal casts, role identity or authority.

### Next test
Live semantic-cast fault factorial with runtime-enforced classes versus tag-only and similarity-based controls.
