<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-THERMAL-LIFECYCLE-SCHEDULER","title":"Android FRANK scheduling must treat thermal headroom and lifecycle as control inputs","domains":["android_edge_runtime","scheduling_concurrency","model_runtime","performance_economics"],"topics":["Android","thermal scheduling","background execution","Qwen-4B","edge inference"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_class":"PRIMARY_DOCS_AND_PREPRINT_SYNTHESIS","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T05:20:00+07:00","updated_at":"2026-08-08T05:20:00+07:00","source_refs":["https://developer.android.com/reference/android/os/PowerManager","https://developer.android.com/about/versions/oreo/background","https://docs.pytorch.org/executorch/stable/using-executorch-android.html","https://docs.pytorch.org/executorch/stable/android-vulkan.html","https://arxiv.org/abs/2603.23640","research_entity/trigger_runs/frank/20260808T0520+0700-chatgpt-secondary-r2/FINAL_REPORT.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Run 30-60 minute device factorial comparing fixed and thermal-headroom-aware inference cadence across CPU/Vulkan/vendor delegate while recording useful work, energy, thermals and process lifecycle recovery.","search_terms":["Android thermal headroom LLM","FRANK edge scheduler","ExecuTorch Vulkan QNN","background service limits","sustained inference"]}
RAE_META -->

### Core
An Android FRANK runtime should treat thermal headroom, power state and process lifecycle as scheduler inputs. Continuous systemd-style daemon assumptions do not transfer unchanged to Android.

### Evidence / boundary
Android exposes thermal status/headroom APIs and limits background execution. ExecuTorch documents CPU, Vulkan and vendor NPU Android backends. A 2026 preprint reports strong sustained-load thermal effects for one Qwen2.5-1.5B mobile benchmark, but those measurements are platform/model specific and cannot be generalized to FRANK’s Qwen3.5-4B target.

### Implication
Port the deterministic semantic core first, add process-kill checkpoint/replay, then benchmark CPU before device-specific acceleration. Peak tokens/s alone is not the optimization objective; sustained useful work under thermal/energy policy is.

### Next test
On representative phones, run fixed-vs-headroom-aware scheduling for 30–60 minutes across available backends and include cold-start, battery, thermal status and kill/restart recovery metrics.
