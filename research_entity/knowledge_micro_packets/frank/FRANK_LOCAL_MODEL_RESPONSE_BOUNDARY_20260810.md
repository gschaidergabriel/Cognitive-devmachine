<!-- RAE_META
{"packet_id":"FRANK_LOCAL_MODEL_RESPONSE_BOUNDARY_20260810","title":"Frank local model response boundary is explicit fail-closed projection","domains":["frank","harness","security"],"topics":["local model","OpenAI-compatible","proxy","usage projection","tool calls","reasoning_content"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"CURRENT","origin_class":"CODE_PLUS_REMOTE_EXECUTION_RECEIPT","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T00:11:00+07:00","updated_at":"2026-08-10T00:11:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:runtime/model/frank_response_contract.py","gschaidergabriel/Dr.-Unterweger:runtime/model/frank_local_model_adapter.py","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger@07f9af41ca3f4b7add75d198bebf92887c3b52d3","gschaidergabriel/Dr.-Unterweger@5aa980244630d63f8ecbe6f2a5a31482ff12a19f","https://docs.python.org/3/library/urllib.request.html"],"related_claim_ids":["FRANK-LOCAL-TRANSPORT-002","FRANK-RESPONSE-PERSIST-003"],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"HIGH_FOR_TESTED_CONTRACT","verification_required":true,"falsifier_or_next_test":"Repeat against actual pinned llama.cpp/Qwen responses including tools, malformed fields, oversized bodies and backend-version drift.","search_terms":["ProxyHandler empty","reasoning_content","usage allowlist","strict response contract","Frank local model"]}
RAE_META -->

### Core
Frank's current local inference boundary treats the backend response as untrusted data. The adapter disables ambient proxy autodiscovery for the loopback path, while `frank_response_contract.py` accepts strict JSON, projects only visible content, validated function tool calls and known non-negative usage counters, and ignores unknown/private backend fields. Hidden `reasoning_content` is not part of the durable contract.

### Evidence / boundary
Python's official urllib docs confirm default proxy-environment discovery and document `ProxyHandler({})` as the way to disable it. The real Hostinger matrix passed a hostile dead-proxy regression and sentinel-field exclusion. This has not yet been differentially tested against every supported inference engine/version.

### Implication
Keep model cognition/diagnostics separate from execution authority and durable Frank state.

### Next test
Run the same boundary suite against the pinned real llama.cpp/Qwen lane and future engine candidates before admitting backend changes.
