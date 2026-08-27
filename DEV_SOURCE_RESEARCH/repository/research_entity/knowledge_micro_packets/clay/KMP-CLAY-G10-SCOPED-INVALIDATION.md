<!-- RAE_META
{"packet_id":"KMP-CLAY-G10-SCOPED-INVALIDATION","title":"Dependency-scoped invalidation for latent activation","domains":["clay","claygraph","hyperposition"],"topics":["latent-activation","revocation","dependency-index","incremental-maintenance"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN","origin_class":"MODEL_AUTHORED_RESEARCH","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T11:09:16Z","updated_at":"2026-08-08T11:09:16Z","source_refs":["clay-20260808T1751p0700-chatgpt-secondary-r2"],"evidence_refs":["EXP-G10-SCOPED-INVALIDATION-004"],"related_claim_ids":[],"related_experiment_ids":["EXP-G10-SCOPED-INVALIDATION-004"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.62,"verification_required":true,"falsifier_or_next_test":"Add transitive derivation dependencies and test stale-support leakage under real ClayGraph revocations.","search_terms":["revocation dependency index","latent field invalidation","scoped rebase"]}
RAE_META -->

### Core
Semantic revocation should invalidate latent activation through reverse dependency links when possible rather than forcing every unrelated active item through a global rebase.

### Evidence / boundary
`EXP-G10-SCOPED-INVALIDATION-004` modeled 50k relations and reduced direct validation work from 1.5M checks to 53,016 (28.29x) while the reference validators left zero stale direct dependencies. Timestamp-only activation retained a small stale fraction. The test omitted transitive derivation chains, so the architecture remains OPEN.

### Implication
ClayGraph G1d should test `M.REVOCATION_DEPENDENCY_INDEX` and keep activation explicitly non-authoritative.

### Next test
Inject semantic revocations into a real derived activation field with direct and transitive dependencies, then compare scoped invalidation, negative-delta propagation and full rebase.