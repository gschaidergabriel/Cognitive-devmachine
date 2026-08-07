<!-- RAE_META
{"packet_id":"KMP-CC8-DURABLE-EFFECT-INTENT","title":"Externally irreversible ClayCode effects should use durable intent plus idempotent capability-gated release","domains":["xeno_claycode","security_capabilities","storage_state_memory","observability_recovery"],"topics":["effect-gateway","transactional-outbox","idempotency","effect-receipt","rollback"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN_WITH_EXTERNAL_IMPLEMENTATION_SUPPORT","origin_class":"CLAYCODE_CC8_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T06:06:00+07:00","updated_at":"2026-08-08T06:06:00+07:00","source_refs":["claycode-20260808T0606p0700-chatgpt-secondary:EXP-CC8-EFFECT-ESCAPE-004","claycode-20260808T0606p0700-chatgpt-secondary:EXP-CC8-OUTBOX-006","Azure-Transactional-Outbox-2026","AWS-Transactional-Outbox","WIT-resources"],"evidence_refs":[],"related_claim_ids":["H-CC8-015","H-CC8-016","H-CC8-T05","H-CC8-T06"],"related_experiment_ids":["EXP-CC8-EFFECT-ESCAPE-004","EXP-CC8-OUTBOX-006"],"predecessor_packet_ids":["KMP-CLAYCODE-AUTHORITY-BOUNDARY"],"supersedes_packet_ids":[],"affected_branches":["claycode","frank","clay","gwt"],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Implement a durable effect-intent queue behind the FRANK capability gateway; inject crashes before/after commit and relay, duplicate delivery, capability revocation and stale roots; measure lost/duplicate real effects and replay fidelity.","search_terms":["ClayCode effect intent","transactional outbox","idempotent effect receipt","capability gateway"]}
RAE_META -->

### Core
For irreversible external effects, ClayCode should not treat rollback as if an already executed network/device/tool action can always be undone. Commit internal state plus a **durable effect intent** atomically; a separate external capability gateway validates freshness/scope/revocation and releases the effect with an idempotency key and effect receipt.

### Evidence / boundary
CC8's constructed pre-effect interposition proxy blocked every deliberately unauthorized external effect before release; post-hoc monitoring necessarily observed those effects only after they had occurred. The crash/retry proxy reproduced the transactional-outbox tradeoff: state+intent avoided the modeled lost-intent dual-write failure while at-least-once relay created duplicate deliveries that idempotency must absorb. Azure and AWS document the same durable-outbox pattern for distributed state+event reliability. Numeric rates are proxy parameters, not FRANK reliability measurements.

### Implication
`EFFECT_PROPOSAL` becomes `prepare/validate -> durable intent commit -> capability-gated release -> effect receipt`, while pure/reversible state work can remain local/speculative when other invariants permit.

### Next test
Fault-inject a real gateway/outbox prototype with replay and revocation between intent commit and effect release.
