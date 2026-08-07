<!-- RAE_META
{"packet_id":"KMP-G4-QWEN4B-CONTEXT-BUDGET","title":"Qwen-class 4B context/KV is a first-class mobile runtime budget","domains":["model-runtime","android-edge-runtime","synthetic-clay"],"topics":["qwen3-4b","kv-cache","context-budget","mobile-inference","routing"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN_ARCHITECTURE","origin_class":"CLAY_G4_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T04:05:00+07:00","updated_at":"2026-08-08T04:05:00+07:00","source_refs":["research_entity/trigger_runs/clay/clay-20260808T0354p0700-chatgpt-secondary/FINAL_REPORT.md#exp-g4-qwen-memory-008","https://huggingface.co/Qwen/Qwen3-4B","https://docs.pytorch.org/executorch/stable/using-executorch-android.html","https://llm.mlc.ai/docs/deploy/android.html"],"evidence_refs":["EXP-G4-QWEN-MEMORY-008"],"related_claim_ids":[],"related_experiment_ids":["EXP-LIVE-XENO-CLAY-FACTORIAL"],"predecessor_packet_ids":["KMP-CLAY-4B-TRANSFORM-KERNEL"],"supersedes_packet_ids":[],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Measure real Qwen3-4B RAM/KV, TTFT, tok/s, power and thermal throttling at 4k/8k/16k contexts across CPU, Vulkan and available NPU backends on target Android hardware.","search_terms":["Qwen3 4B KV cache","Android local LLM","context budget","mobile thermals","model routing"]}
RAE_META -->

### Core
For a Qwen3-4B-class local reader, context length is a major memory and thermal design variable rather than free persistent memory. From the official 36-layer, 8-KV-head, 128-head-dimension configuration, a simple full-attention cache estimate yields FP16 KV of about 0.5625 GiB at 4k tokens, 1.125 GiB at 8k, 2.25 GiB at 16k and 4.5 GiB at 32k.

### Evidence / boundary
The calculation is architecture-derived, not a measured allocator profile; real runtimes may quantize/compress/cache differently. Official ExecuTorch and MLC documentation confirms multiple Android execution backends, while community reports show device-specific bandwidth/thermal constraints.

### Implication
FRANK should externalize persistent state and compile bounded active context on demand. The 4B model should be routed as an intermittent semantic transform kernel, with context bytes, TTFT, thermals and recovery included in the routing objective.

### Next test
Benchmark a pinned Qwen3-4B quantization on Snapdragon and MediaTek devices over 4k–16k active contexts with CPU/Vulkan/NPU paths where available.
