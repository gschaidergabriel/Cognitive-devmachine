<!-- RAE_META
{"packet_id":"KMP-CC9-COMPILED-READER-SURFACE","title":"Small models should consume certified ClayCode projections, not re-derive safety semantics","domains":["xeno_claycode","model_runtime","security_capabilities"],"topics":["Groq 8B","reader projection","Qwen 4B","authority","token efficiency","projection receipt"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"CURRENT_WITH_8B_PROXY_BOUNDARY","origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1723p0700-chatgpt-secondary","affected_branches":["frank","clay","gwt","claygraph","claycode"],"falsifier_or_next_test":"Pinned Qwen3-4B factorial raw semantic reasoning vs certified compiled reader surface on OOD schemas and unknown/conflict/revoked states."}
RAE_META -->

## Result
New CC9 Groq `llama-3.1-8b-instant` proxy: a raw ten-case epoch/op-hash/capability/effect classification task scored **1/10 exact**. The same model relaying decisions precompiled by a deterministic kernel scored **10/10 exact**. Prompt tokens fell **327 -> 152 (-53.5%)**; one-run total time fell 0.1007 s -> 0.0837 s, which is not a stable latency estimate.

Fresh contemporaneous Clay G9 data independently within the same provider/worker family points the same way: raw graph selection 5/10 vs trusted compiled candidate projection 9/10, prompt tokens 487 -> 324 (-33.5%). This is supporting shared-family evidence, not independent provider/model replication.

## Architecture implication
High-stakes ClayCode semantics should be deterministically compiled into bounded facts/decisions before small-model consumption. The model may reason over or relay that projection, but cannot turn its interpretation into authority. Bind the reader surface with separate `semantic_hash`, `projection_schema_hash`, and `projection_hash` so transport/read success is not confused with semantic reconstruction.

## Boundary
Groq 8B is a proxy only. This does not establish Qwen3-4B performance, LoRA internalization, local latency/energy, or production safety.
