<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-AUTHORITY-BOUNDARY","title":"ClayCode/XENO output is a proposal, never execution authority","domains":["claycode","security-authority","synthetic-clay"],"topics":["capabilities","commit-gateway","provenance","rollback"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"CURRENT_SAFETY_INVARIANT","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:CLAYCODE_MANUAL.md","RAE83_G1:XENO_TO_CLAYCODE_MIGRATION.md","RAE83_G1:FINAL_SYNTHETIC_CLAY_CONCEPT.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["EXP-C3-CLAYCODE-RC1"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.96,"verification_required":false,"falsifier_or_next_test":"Attempt adversarial model-generated commit requests and verify that no effect occurs without external capability, invariant, root and rollback checks.","search_terms":["claycode","xeno","capability gateway","commit request","authority","rollback"]}
RAE_META -->

### Core
A model-generated ClayCode or XENO record may describe/propose a transition but must not grant itself authority. Critical effects require an external deterministic capability/policy/invariant gateway with current-root and rollback checks plus effect receipts.

### Evidence / boundary
G1 materialized parser/validator/compiler prototypes and intentionally kept `COMMIT_REQ` as a gateway request. This is a safety architecture invariant rather than evidence that the current prototype is production secure.

### Implication
Self-representing or self-hosted ClayCode can remain evolvable without making model text equivalent to OS authority.

### Next test
Red-team proposal paths for stale roots, revoked capabilities, deceptive provenance, missing rollback and indirect tool invocation.
