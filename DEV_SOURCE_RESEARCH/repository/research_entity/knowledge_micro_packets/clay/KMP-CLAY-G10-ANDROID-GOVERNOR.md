<!-- RAE_META
{"packet_id":"KMP-CLAY-G10-ANDROID-GOVERNOR","title":"Hard-constraint-first multi-timescale edge governor","domains":["clay","frank","android-edge"],"topics":["governor","thermal","memory","latency","goodhart"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T11:09:16Z","updated_at":"2026-08-08T11:09:16Z","source_refs":["clay-20260808T1751p0700-chatgpt-secondary-r2","MLC Android SDK","Qwen3-4B-GGUF"],"evidence_refs":["EXP-G10-GOVERNOR-TRIPWIRE-006"],"related_claim_ids":[],"related_experiment_ids":["EXP-G10-GOVERNOR-TRIPWIRE-006"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.60,"verification_required":true,"falsifier_or_next_test":"Run sustained target-device Qwen3-4B traces over quantization, context, prefill, fanout and speculation.","search_terms":["Android governor","Qwen3 4B","thermal hysteresis","hard constraints Pareto"]}
RAE_META -->

### Core
An edge governor should first enforce hard safety/recovery/authority constraints, then optimize a Pareto surface using sustained multi-timescale device state and hysteresis rather than one soft scalar reward.

### Evidence / boundary
In synthetic `EXP-G10-GOVERNOR-TRIPWIRE-006`, the best naive scalar configuration crossed the constructed security-risk tripwire while a feasible constrained configuration existed. MLC exposes Android memory/context/prefill controls, making adaptive policy technically plausible. No target-device sustained measurement was run.

### Implication
FRANK/Clay should treat model/quantization/context/retrieval fanout/speculation as a dynamic constrained control problem on Android, with reader identity pinned in experiments.

### Next test
30–60 minute target-device sweeps measuring thermals, memory, energy, p50/p95/p99 and task quality under hysteretic versus static policies.