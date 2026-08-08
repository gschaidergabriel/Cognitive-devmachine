<!-- RAE_META
{"packet_id":"KMP-FUSION-CTC-CLAYGRAPH","title":"Fusion adds reallocatable-selector and origin-integrity tests to ClayGraph","domains":["claygraph","frank","synthetic_clay","security"],"topics":["selection_integrity","origin_binding","graph_poisoning","activation","authenticated_subgraph"],"epistemic_class":"FUSION_DERIVED_RESEARCH_DELTA","claim_status_hint":"OPEN_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T18:03:00+07:00","related_experiment_ids":["EXP-FUS-CTC-001"],"confidence":0.86,"verification_required":true}
RAE_META -->

### Fusion delta
ClayGraph G1d remains HOLD and activation remains non-authoritative. Fusion adds a separate attack surface: even when every returned fact is authentic, writable graph structure can redirect membership/ranking when the selector is **reallocatable**. Effect-bound selection should therefore either run over an authenticated/authorized structural view or carry a selector attestation with an equivalent guarantee.

This still does not justify universal authenticated-graph recomputation: current external evidence suggests exposure depends on selector mechanics. Content-fixed/non-reallocatable selectors may permit a cheaper certified path.

Write-time origin authority is prior to selection integrity; later graph validation cannot repair a memory item whose authority was already laundered.

### Next test
On the actual RAE/FRANK corpus, inject sourceless structural edges and relation-channel conflicts without modifying record bytes. Compare native selector, authenticated-subgraph recomputation and content-fixed reranking; then repeat with write-time origin laundering.
