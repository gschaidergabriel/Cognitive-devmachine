<!-- RAE_META
{"packet_id":"KMP-G6-EDGE-FEEDBACK-GOVERNOR","title":"Edge FRANK runtime should adapt backend, thermal policy, KV budget and speculation from feedback","domains":["model-runtime","android-edge","frank-architecture"],"topics":["thermal-governor","speculative-decoding","kv-cache","backend-routing"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_BOUNDARY","origin_class":"CLAY_G6_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:25:00+07:00","updated_at":"2026-08-08T05:25:00+07:00","source_refs":["clay-20260808T0525p0700-chatgpt-secondary:EXP-G6-THERMAL-GOV-006","clay-20260808T0525p0700-chatgpt-secondary:EXP-G6-SPEC-GOV-007","arXiv:2606.23001","arXiv:2603.08727","arXiv:2604.04722","github:qualcomm/GenieX"],"evidence_refs":[],"related_claim_ids":["H-G6-039","H-G6-040","H-G6-041","H-G6-T08","H-G6-T16"],"related_experiment_ids":["EXP-G6-THERMAL-GOV-006","EXP-G6-SPEC-GOV-007"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.85,"verification_required":true,"falsifier_or_next_test":"Sustained Qwen3-4B Android benchmark across CPU/GPU/NPU, frequency, context/KV and speculation policies with quality shadows.","search_terms":["Android LLM thermal","Qwen3 4B","GenieX","adaptive KV","speculative decoding governor"]}
RAE_META -->

### Core
FRANK's edge runtime should optimize sustained task utility by feedback-controlling backend/frequency, context/KV allocation and speculative decoding rather than selecting a permanent fastest configuration.

### Evidence / boundary
Current mobile research reports thermal throttling as a first-order sustained-load constraint and adaptive energy/KV policies as viable. Qualcomm GenieX exposes CPU/GPU/NPU paths for Qwen3-4B-class execution. In G6 toys, a thermal governor sustained 46.23 normalized tok/s versus 42.0 static eco and 16.92 thermally collapsed static high; an acceptance-conditioned speculation controller slightly beat always-on speculation. These are not device measurements.

### Implication
Expose thermal state, memory/KV pressure, backend telemetry, task class and draft acceptance to a runtime controller; preserve task quality, energy and recovery as shadow objectives.

### Next test
Run sustained physical-device Qwen3-4B measurements across a representative Android fleet and preregister governor objectives.
