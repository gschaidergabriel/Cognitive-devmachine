<!-- RAE_META
{"packet_id":"KMP-CC6-SEMANTIC-IR-PROJECTION-SEPARATION","title":"ClayCode canonical semantics should be separated from reader projections","domains":["xeno_claycode","model_runtime","formal_methods_testing"],"topics":["canonical-ir","reader-projection","state-aware-decoding","roundtrip","versioning"],"epistemic_class":"OPEN_ARCHITECTURE_WITH_SYNTHETIC_SUPPORT","claim_status_hint":"OPEN","origin_class":"CLAYCODE_CC6_TRIGGER_RUN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T05:29:00+07:00","source_refs":["claycode-20260808T0529p0700-chatgpt-secondary:EXP-CC6-PROJECTION-001","arXiv:2607.18357","arXiv:2608.03065","arXiv:2605.03353","MLIR:BytecodeFormat","Protobuf:SerializationNotCanonical"],"related_claim_ids":["H-G3-006","H-CC6-001","H-CC6-002","H-CC6-004","H-CC6-012"],"related_experiment_ids":["EXP-CC6-PROJECTION-001","EXP-CC6-EXTENSION-002"],"predecessor_packet_ids":["KMP-G5-STATE-AWARE-DECODING","KMP-CLAYCODE-AUTHORITY-BOUNDARY"],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Pinned Qwen3-4B projection factorial with semantic roundtrip, exact task quality, retries, token cost, latency and grammar/state-constraint overhead.","search_terms":["ClayCode semantic IR","reader projection","state-aware grammar","canonicalization","Qwen3-4B"]}
RAE_META -->

### Core
ClayCode should treat the durable language as a canonical semantic IR, while model/wire surfaces are compiled projections. A projection is accepted only if it round-trips to equivalent canonical semantics under the declared IR/dialect version.

### Evidence / boundary
CC6 falsified an ad-hoc pipe-delimited compact syntax with adversarial embedded delimiters. A positional-JSON projection then completed 50,000 fuzzed semantic roundtrips with zero failures and lower byte size than object JSON, but this is a local parser/byte proxy and does not establish Qwen token or reader performance. External state-aware grammar and typed-IR work supports the mechanism class, not ClayCode itself.

### Implication
Optimize surface syntax per reader/model without allowing projection accidents to define canonical state hashes, authority or schema evolution.

### Next test
Run `EXP-LIVE-XENO-CLAY-FACTORIAL` on pinned Qwen3-4B with verbose JSON, positional projection, grammar-only and state-aware Γ arms plus the external gateway.
