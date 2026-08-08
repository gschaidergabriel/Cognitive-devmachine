<!-- RAE_META
{"packet_id":"KMP-CC13-001-MCAAT-BOUNDARY","title":"ClayCode MCAAT separates information role, causal stage and authority","domains":["claycode","frank","unifieddb","gwt","claygraph","hyperposition"],"topics":["type system","capabilities","admissibility","causal stages","effect authority"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:34:00Z","updated_at":"2026-08-08T17:34:00Z","source_refs":["claycode-20260808T1934p0200-chatgpt-secondary-r4/FINAL_REPORT.md","FRANK C8","UnifiedDB U2","GWT R5","WebAssembly/WASI capability docs","arXiv:2606.24322"],"evidence_refs":["EXECUTABLE_RESEARCH_RECEIPT.json","FRANK_CLAYCODE_GOODMAN_REVIEW.json"],"related_claim_ids":["H-CC13-001","H-CC13-002","H-CC13-003"],"related_experiment_ids":["EXP-CC13-MCAAT-TYPEFLOW-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.74,"verification_required":true,"falsifier_or_next_test":"Red-team a real WASI/Wasmtime lowering and target-Qwen-generated MCAAT corpus; any model-forgeable EffectPermit or implicit salience-to-authority cast falsifies the boundary.","search_terms":["MCAAT","EffectPermit","EffectIntent","admissibility","causal stage","ClayCode authority"]}
RAE_META -->

### Core
CC-RC1.8 MCAAT proposes that ClayCode type information carry three independent axes: collection semantics, information admissibility, and causal stage. Model output may create an `EffectIntent`, but actual `EffectPermit` authority remains an opaque host-minted capability and is not serializable/model-constructible.

### Evidence / boundary
The current randomized checker matched its separate declarative rule set in 120,000 cases and rejected 60,000 destructive/authority-injection mutations. Independent WASI capability and 2026 memory-IFC work support the architecture class. This is not a formal proof or target-FRANK/Qwen validation.

### Implication
Salience, candidate rank, workspace selection and model-internal uptake cannot silently become truth or execution authority simply because they share one Clay representation.

### Next test
Compile a frozen MCAAT corpus to a real capability sandbox and attack indirect authority paths, adapter label loss, stale/replayed permits and overbroad resource handles.
