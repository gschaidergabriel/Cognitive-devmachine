<!-- RAE_META
{"packet_id":"KMP-G8-COVERAGE-AWARE-FAST-PATH","title":"Selective validation and coordination require explicit coverage evidence","domains":["systems-architecture","ipc-distributed-systems","xeno-claycode"],"topics":["invariants","dependency-coverage","selective-closure","fail-closed"],"epistemic_class":"SYNTHESIS_WITH_SYNTHETIC_COUNTEREXAMPLE","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","run_id":"clay-20260808T0605p0700-chatgpt-secondary","canonical_parent":"r2:04234efd","confidence":0.92,"verification_required":true,"falsifier_or_next_test":"Compile real FRANK scopes from trusted op semantics and property/stateful fuzz hidden aliases, reorder and partition."}
RAE_META -->

### Core
CC7/H2 selective scopes are safe only to the extent their dependency/invariant closure is complete. G8 makes **coverage/unknown** first-class runtime state: verified complete scopes may use the fast path; incomplete/dynamic/unknown scopes broaden validation, coordination or rejection.

### Evidence / boundary
In `EXP-G8-COVERAGE-003`, a narrow observed-scope policy had nonzero unsafe rates even at 95% per-scope coverage; a fail-closed coverage-aware policy eliminated the constructed unsafe cases while coordinating more. Current sound invariant-synthesis work supports `learn/suggest -> verify -> use`, not learned invariants as authority.

### Implication
Latency wins are invalid if obtained by silently assuming scope completeness. Coverage debt must be measured alongside coordination cost.
