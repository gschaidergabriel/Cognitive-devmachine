<!-- RAE_META
{"packet_id":"KMP-CLAY-G10-CAUSAL-SLICE","title":"Certified operation-specific causal slices","domains":["clay","frank","claycode"],"topics":["causal-basis","epochs","concurrency"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T11:09:16Z","updated_at":"2026-08-08T11:09:16Z","source_refs":["clay-20260808T1751p0700-chatgpt-secondary-r2","FoundationDB Developer Guide"],"evidence_refs":["EXP-G10-BASIS-SCOPE-001"],"related_claim_ids":[],"related_experiment_ids":["EXP-G10-BASIS-SCOPE-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.68,"verification_required":true,"falsifier_or_next_test":"Live FRANK concurrent audit including negative/predicate dependencies and cross-store skew.","search_terms":["causal slice","certified basis","operation-specific epochs","consistency domains"]}
RAE_META -->

### Core
For consequential operations, compile the smallest sound set of state, selector and projection dependencies and validate those dependencies rather than imposing a universal global version lock.

### Evidence / boundary
Synthetic `EXP-G10-BASIS-SCOPE-001` rejected 4.137% with operation-specific dependencies versus 16.1431% under a universal lock, with zero constructed invalid accepts in either reference validator. FoundationDB provides an independent systems analogue via narrow conflict ranges. This is not a live FRANK incidence/performance estimate.

### Implication
FRANK C5 Certified Basis becomes a compiler/runtime contract mapping trusted operation semantics to native consistency domains plus explicit cross-domain witnesses.

### Next test
Instrument live FRANK for dependency declarations, cross-store skew, negative/predicate reads, retries and invalid accepts.