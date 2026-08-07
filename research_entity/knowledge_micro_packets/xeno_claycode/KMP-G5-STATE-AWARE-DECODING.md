<!-- RAE_META
{"packet_id":"KMP-G5-STATE-AWARE-DECODING","title":"ClayCode decoding should separate syntax, state semantics and authority","domains":["xeno-claycode","security-capabilities","model-runtime"],"topics":["constrained-decoding","state-aware-grammar","authority","ClayCode"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_SYNTHETIC_SUPPORT","origin_class":"CLAY_G5_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:08:00+07:00","updated_at":"2026-08-08T05:08:00+07:00","source_refs":["arXiv:2502.05111","arXiv:2608.03065","arXiv:2509.00360","clay-20260808T0508p0700-chatgpt-secondary:EXP-G5-STATEGRAMMAR-005"],"evidence_refs":[],"related_claim_ids":["H-G5-017","H-G5-018","H-G5-019","H-G5-022"],"related_experiment_ids":["EXP-G5-STATEGRAMMAR-005"],"predecessor_packet_ids":["KMP-CLAYCODE-AUTHORITY-BOUNDARY"],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Run a pinned Qwen3-4B factorial: free generation vs grammar-only vs root-bound state-aware grammar vs external gateway, measuring semantic validity, retries, latency and unauthorized-effect rate.","search_terms":["ClayCode constrained decoding","state-aware grammar","semantic constrained generation","external authority"]}
RAE_META -->

### Core
G5 separates three gates: grammar validity, state-semantic validity, and execution authority. Modern constrained-decoding research supports the first two as decode-time mechanisms. A synthetic state-symbol toy showed why the third remains independent: state-valid proposals can still lack capability or root freshness.

### Evidence / boundary
The local result is deliberately constructed and does not measure a real LLM. External papers demonstrate constrained generation techniques, not ClayCode efficacy.

### Implication
ClayCode can reduce retries by binding grammar Γ to the current state/root, while keeping authorization outside the model and decoder.

### Next test
Execute the full four-arm reader factorial on one pinned local Qwen3-4B runtime.