<!-- RAE_META
{"packet_id":"KMP-CLAY-4B-TRANSFORM-KERNEL","title":"Qwen-class 4B should be an intermittent semantic transform kernel","domains":["model-runtime","synthetic-clay","frank-architecture"],"topics":["qwen-4b","semantic-transform","needle","small-nets"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:FINAL_SYNTHETIC_CLAY_CONCEPT.md","RAE83_G1:SYNTHETIC_CLAY_ARCHITECTURE_PROPOSAL.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Benchmark always-on 4B versus ignition/uncertainty-routed 4B with equal task quality, latency, energy and recovery metrics on Linux and Android targets.","search_terms":["qwen 4b","semantic transform kernel","model routing","needle","small networks","android inference"]}
RAE_META -->

### Core
Cheap continuous dynamics should preferentially run in deterministic code, classifiers/Needle and small networks; the 4B model should be invoked as a semantic transform operator when novelty, uncertainty or task complexity justifies it.

### Evidence / boundary
This is an architecture hypothesis from the G1 synthesis, not a measured universal optimum. No full-model training or live 4B end-to-end baseline was executed in that run.

### Implication
The design can reduce inference load and makes Android/edge deployment more plausible, while keeping canonical state outside model weights/context.

### Next test
Compare always-on versus routed 4B across task success, calls, latency, energy/thermal load, context size and recovery.
