<!-- RAE_META
{"packet_id":"KMP-G6-FRESHNESS-BOUND-GAMMA","title":"State-aware ClayCode grammars must be bound to a current state root or epoch","domains":["xeno-claycode","security-capabilities","synthetic-clay"],"topics":["decode-time-grammar","state-semantics","freshness","root-epoch"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_BOUNDARY","origin_class":"CLAY_G6_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:25:00+07:00","updated_at":"2026-08-08T05:25:00+07:00","source_refs":["clay-20260808T0525p0700-chatgpt-secondary:EXP-G6-STALE-GAMMA-003","arXiv:2607.18357","arXiv:2606.11817"],"evidence_refs":[],"related_claim_ids":["H-G6-031","H-G6-T04","H-G6-T05"],"related_experiment_ids":["EXP-G6-STALE-GAMMA-003"],"predecessor_packet_ids":["KMP-G5-STATE-AWARE-DECODING"],"supersedes_packet_ids":[],"confidence":0.89,"verification_required":true,"falsifier_or_next_test":"Pinned Qwen3-4B factorial over unconstrained, grammar-only, stale-Gamma, current-Gamma and Gamma+root validation.","search_terms":["ClayCode Gamma","state aware decoding","decode time grammars","stale root","epoch"]}
RAE_META -->

### Core
A grammar refined from runtime environment Γ can prevent undefined references only relative to that Γ. ClayCode proposals should therefore carry the canonical/materialized state root or epoch from which Γ was derived, and validation should fail closed if that root is stale or revoked.

### Evidence / boundary
In a dynamic-symbol proxy with 3% churn, grammar-only generation was invalid against current state 63.874% of the time; stale Γ reduced invalidity to 11.911%, while current Γ reached 0% in the toy. Root validation caught the stale remainder. Decode-Time Grammars provides external support for environment-indexed grammar refinement; separate security work warns grammar constraints are not themselves safety policy.

### Implication
Pipeline becomes `grammar -> Γ(root) -> semantic validation -> freshness/root check -> external authority`, not merely grammar -> execution.

### Next test
Run an end-to-end pinned-reader factorial and include stale/revoked-root adversarial cases.
