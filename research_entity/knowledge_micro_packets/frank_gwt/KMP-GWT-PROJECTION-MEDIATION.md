<!-- RAE_META
{"packet_id":"KMP-GWT-PROJECTION-MEDIATION","title":"Reader projection order can mediate apparent GWT winner effects","domains":["frank_gwt","model_runtime","claycode"],"topics":["projection","prompt-order","winner","uptake","causal-attention"],"epistemic_class":"8B_PROXY_PLUS_EXTERNAL_MECHANISTIC_CONTEXT","claim_status_hint":"CURRENT_WITH_PROXY_BOUNDARY","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:35:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T1721p0700-chatgpt-secondary/EXPERIMENT_RESULTS.json","KMP-GROQ8B-GWT-RECONSTRUCTION-ORDER"],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"On actual Core/Qwen hold WorkspaceEpisode fixed and counterbalance neutral vs winner-first projection while measuring uptake/effect."}
RAE_META -->

### Core
Projection is a causal stage rather than cosmetic serialization. Run 4's metadata-free Groq 8B proxy scored 10/12 in one candidate order and 8/12 after reversal. A separate earlier GWT proxy measured 87.5% neutral vs 62.5% reversed-order accuracy. ACL 2026 independently reports >14 percentage-point MCQA prompt-order effects in decoder LMs caused by causal-attention information availability.

### Implication for FRANK
Do not credit a winner-first/full-detail reader prompt to workspace selection unless semantic WorkspaceEpisode, candidate facts, token budget and projection ordering are held fixed/counterbalanced. Persist `projection_hash`, `projection_order_policy`, `reader_version`, and uptake/effect receipts.

### Boundary
Groq 8B is a proxy, not Qwen3-4B. The target Core/Qwen mediation experiment remains open.
