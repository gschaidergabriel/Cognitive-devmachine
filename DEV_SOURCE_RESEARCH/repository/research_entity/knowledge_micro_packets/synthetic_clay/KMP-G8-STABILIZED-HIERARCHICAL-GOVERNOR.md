<!-- RAE_META
{"packet_id":"KMP-G8-STABILIZED-HIERARCHICAL-GOVERNOR","title":"Hierarchical causal control needs hysteresis, dwell and hard-constraint priority","domains":["synthetic-clay","systems-architecture","model-runtime"],"topics":["governor","hysteresis","chattering","anti-windup","control"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_SUPPORT","origin_actor":"chatgpt-secondary","run_id":"clay-20260808T0605p0700-chatgpt-secondary","canonical_parent":"r2:04234efd","confidence":0.87,"verification_required":true,"falsifier_or_next_test":"Run flat vs hierarchical vs stabilized hierarchy on live FRANK/Android traces including controller overhead and recovery debt."}
RAE_META -->

### Core
G7's hierarchy is retained but no longer treated as stable by construction. CASK-G8 adds hysteresis/dwell, delayed-state handling/anti-windup and fast hard-constraint priority over slow semantic utility allocation.

### Evidence / boundary
`EXP-G8-GOV-STABILITY-002` reduced switch rate from ~0.694 to ~0.058 with hysteresis at similar proxy loss; a slow+fast policy reached lower constructed loss (~0.0333) and violation rate (~0.172). This is a designed workload and does not transfer numeric parameters.

### Implication
Controller switching, delayed telemetry and intervention cost must be first-class shadow metrics. Adaptivity itself can be an instability source.
