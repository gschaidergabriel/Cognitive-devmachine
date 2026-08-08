<!-- RAE_META
{"packet_id":"KMP-CLAY-G10-PROJECTION-PROOF","title":"Projection identity is not projection semantic correctness","domains":["clay","claycode","gwt","frank"],"topics":["projection","reader-abi","semantic-validation","prompt-order"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T11:09:16Z","updated_at":"2026-08-08T11:09:16Z","source_refs":["clay-20260808T1751p0700-chatgpt-secondary-r2","ACL 2026 Lost in the Prompt Order"],"evidence_refs":["EXP-G10-8B-CAUSAL-SLICE-007"],"related_claim_ids":[],"related_experiment_ids":["EXP-G10-8B-CAUSAL-SLICE-007"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.73,"verification_required":true,"falsifier_or_next_test":"Target Qwen3-4B raw-vs-compiled projection factorial plus compiler mutation/reference tests.","search_terms":["projection proof","reader abi","semantic compiler","prompt order"]}
RAE_META -->

### Core
A projection hash/schema receipt proves which projection was used, not that the trusted projection compiler preserved the intended semantics. Projection semantics therefore need reference/differential/mutation validation.

### Evidence / boundary
Prompt-order research supports projection as a causal variable. In `EXP-G10-8B-CAUSAL-SLICE-007`, the registered Groq 8B proxy improved from 6/12 raw to 12/12 compiled while prompt tokens fell 410 to 241. This is not target Qwen3-4B evidence and does not prove compiler semantic correctness.

### Implication
`ProjectionProofReceipt` should bind semantic input, projection schema/order/wire identity, reader identity and a trusted validation/reference version.

### Next test
Run target Qwen3-4B matched projections and deliberately mutate compiler rules while keeping identity metadata internally consistent.