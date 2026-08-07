<!-- RAE_META
{"packet_id":"KMP-G8-EXACT-ANCHORED-SEMANTIC-ZOOM","title":"Resolution-adaptive memory should zoom from exact-backed projections, not summary-only truth","domains":["model-runtime","memory-state","synthetic-clay"],"topics":["semantic-memory","SeKV","summary-drift","reconstruction","rebase"],"epistemic_class":"SYNTHESIS_WITH_PROXY_AND_IMPLEMENTATION_SUPPORT","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","run_id":"clay-20260808T0605p0700-chatgpt-secondary","canonical_parent":"r2:04234efd","confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Compare exact-backed zoom, eviction and heavy-hitter/recency policies at equal memory on pinned FRANK/Qwen traces."}
RAE_META -->

### Core
G8 retains G7 multi-resolution memory but adds a drift firewall: canonical exact state remains immutable/replayable; summaries, low-rank forms, zoomed detail and materialized arrangements are replaceable projections with basis root, approximation/error estimate and rebase policy.

### Evidence / boundary
`EXP-G8-DRIFT-006` accumulated mean error ~1.56 under repeated approximate updates, versus ~0.105 with an error-triggered exact rebase in the constructed state process. SeKV (`arXiv:2606.31145`) independently demonstrates resolution-adaptive semantic zoom over hierarchical backing for KV inference. Neither result proves Clay memory quality on live FRANK.

### Implication
Compression may change resolution but not authority. Approximate layers need explicit provenance to exact backing and bounded drift/reconstruction depth.
