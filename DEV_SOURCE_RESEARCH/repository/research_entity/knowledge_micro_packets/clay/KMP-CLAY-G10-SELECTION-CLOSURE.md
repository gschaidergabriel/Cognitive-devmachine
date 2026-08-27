<!-- RAE_META
{"packet_id":"KMP-CLAY-G10-SELECTION-CLOSURE","title":"Selection integrity is distinct from record provenance","domains":["clay","claygraph","frank","security"],"topics":["selection-integrity","retrieval","provenance","memory-poisoning"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T11:09:16Z","updated_at":"2026-08-08T11:09:16Z","source_refs":["clay-20260808T1751p0700-chatgpt-secondary-r2","arXiv:2606.12290"],"evidence_refs":["EXP-G10-SELECTION-INTEGRITY-002"],"related_claim_ids":[],"related_experiment_ids":["EXP-G10-SELECTION-INTEGRITY-002"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.84,"verification_required":true,"falsifier_or_next_test":"Run an authenticated-record structural redirection attack against live ClayGraph/FRANK shadow memory.","search_terms":["selection integrity","record provenance","AUTHSELECT","candidate set","selector provenance"]}
RAE_META -->

### Core
Authenticated memory records do not guarantee authentic selection. When writable graph/query structure can reallocate candidate membership or ranking, the selector and its authorized input view are authority-relevant dependencies.

### Evidence / boundary
Synthetic G10 selection attack preserved authentic records while redirecting the chosen result. Independently, Fei et al. 2026 (`arXiv:2606.12290`) formalize the same blindness class and report consequential misselection plus an `AUTHSELECT` mitigation. This corrects RAE novelty: Selection Integrity is independent convergence, not a globally novel G9 discovery. Live FRANK transfer is OPEN.

### Implication
Add `SelectionReceipt` / authorized selector replay before effect-bound memory can influence action authority or causal GWT measurement.

### Next test
Attack live ClayGraph candidate membership while keeping every returned record hash/provenance valid.