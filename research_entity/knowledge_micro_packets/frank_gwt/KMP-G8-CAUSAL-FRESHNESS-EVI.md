<!-- RAE_META
{"packet_id":"KMP-G8-CAUSAL-FRESHNESS-EVI","title":"FRANK workspace freshness should be value-at-use and coverage aware","domains":["frank-gwt","synthetic-clay","systems-architecture"],"topics":["freshness","value-of-information","workspace","coalescing","fanout"],"epistemic_class":"SYNTHESIS_WITH_PROXY_SUPPORT","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","run_id":"clay-20260808T0605p0700-chatgpt-secondary","canonical_parent":"r2:04234efd","confidence":0.88,"verification_required":true,"falsifier_or_next_test":"Shadow fixed-60s, dirty-hybrid and EVI/coalesced scheduling on real FRANK reads with channel revisions, p99 and downstream outcomes."}
RAE_META -->

### Core
FRANK Cycle 3 and GWT R2 correctly move beyond fixed wall-clock age. G8 refines the decision to expected downstream value at use versus refresh/fanout cost, conditioned on dependency coverage and effect/deadline criticality. Heartbeat, dirty events, pre-read pull and full-broadcast fallback remain different modes.

### Evidence / boundary
In `EXP-G8-VOI-FRESHNESS-004`, dirty-immediate had zero constructed query error at send rate ~0.0726; coalesced query/EVI had error ~0.00248 at send rate ~0.0312. External query-AoI/event-triggered work independently distinguishes age from use/value. This does not set FRANK thresholds.

### Implication
Freshness optimization needs communication/recompute shadow costs and cannot assume `dirty => refresh now` or `old => stale`.
