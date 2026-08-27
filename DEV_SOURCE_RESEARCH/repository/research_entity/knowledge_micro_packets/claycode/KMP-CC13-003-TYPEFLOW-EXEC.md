<!-- RAE_META
{"packet_id":"KMP-CC13-003-TYPEFLOW-EXEC","title":"MCAAT reference checker separates typed authority flows in finite randomized tests","domains":["claycode","compiler","security"],"topics":["type checker","effect system","fuzzing","semantic identity"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:34:00Z","updated_at":"2026-08-08T17:34:00Z","source_refs":["claycode-20260808T1934p0200-chatgpt-secondary-r4/FINAL_REPORT.md"],"evidence_refs":["EXECUTABLE_RESEARCH_RECEIPT.json","claycode_mcaat_checker.py"],"related_claim_ids":["H-CC13-001","H-CC13-002","H-CC13-009"],"related_experiment_ids":["EXP-CC13-MCAAT-TYPEFLOW-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.72,"verification_required":true,"falsifier_or_next_test":"Independent implementation or real lowering finds accepted forbidden flow, semantic-hash alias, or physical-layout-dependent meaning missed by the checker.","search_terms":["MCAAT checker","authority flow","semantic hash","type fuzz","ClayCode compiler"]}
RAE_META -->

### Core
A CC-RC1.8 MCAAT reference checker was executed against randomized policy, injection and identity-property corpora. It treats admissibility class, causal stage and host authority as separate compiler-visible dimensions.

### Evidence / boundary
Observed: 0/120,000 disagreements with a separately specified declarative policy oracle; 0/60,000 destructive/model-authority injection accepts; 0 logical mismatches across 40,000 versioned create/edit/rename/hide operations; 0 semantic-axis aliases and 0 physical-lowering-induced semantic-hash changes across 30,000 identity cases. Generated-code smoke exited 0. These finite tests are not a proof and do not exercise real syscalls or target Qwen.

### Implication
The proposed distinction is implementable as an executable compiler contract rather than only documentation.

### Next test
Build an independent second checker/lowerer, then differential-test both over frozen adversarial corpora and a real Wasm capability runtime.
