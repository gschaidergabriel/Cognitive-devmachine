<!-- RAE_META
{"packet_id":"KMP-FUSION-CTC-CLAYCODE","title":"Fusion extends CC-RC1.4 with origin and selector attestations","domains":["claycode","frank","claygraph","security"],"topics":["CBCC","origin_binding","selection_integrity","certified_basis","projection_receipt"],"epistemic_class":"FUSION_DERIVED_RESEARCH_DELTA","claim_status_hint":"OPEN_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T18:03:00+07:00","related_experiment_ids":["EXP-FUS-CTC-001"],"confidence":0.84,"verification_required":true}
RAE_META -->

### Fusion delta
CC-RC1.4's operation-specific Certified Basis and compositional closure are strengthened by the fusion experiment. The semantic envelope should additionally distinguish:
- immutable/write-time origin authority for memory inputs;
- selector/query-plan attestation when selection is structurally reallocatable;
- projection identity/integrity;
- capability/effect authority.

These are separate typed witnesses. The model may inspect them but cannot manufacture or upgrade them.

`EXP-FUS-CTC-001` shows in a constructed workload that a universal version lock creates many harmless rejects, while a complete operation-specific capsule preserves constructed safety; removing only selector validation reopens an unsafe channel. Numeric rates are not production estimates.

### Next test
Extend the executable CC-RC1.4 reference with origin and selector witness types; fuzz laundering, selection redirection, aliasing and projection substitution, with unknown closure failing broad.
