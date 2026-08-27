<!-- RAE_META
{"packet_id":"KMP-U2-PLACEMENT-LATTICE","title":"UnifiedDB physical placement is multi-axis, not monolith-vs-polystore","domains":["unifieddb","frank","claycode","claygraph"],"epistemic_class":"OPEN_SYNTHESIS_WITH_RUNTIME_MECHANISM_TEST","status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EVIDENCE_LEDGER.md"],"verification_required":true}
RAE_META -->

## Claim
A UnifiedDB component should not be labeled only `COLOCATED` or `ISOLATED`. Transaction domain, data placement, index placement, compute placement, process placement and fault domain can vary independently.

External evidence points in both directions: AkasicDB demonstrates integrated vector/graph/relational query execution; PostgreSQL-V and DecoupleVS show important benefits from decoupling vector indexes/data. U2 E2B found same-process separate stores and a monolith essentially tied in one mixed-read mechanism test while JSON service boundaries were slower.

## Boundary
No target FRANK trace or Android placement benchmark exists. This is an OPEN architecture refinement, not a physical deployment decision.

## Next test
Replay real FRANK query traces across placement vectors with correctness/recovery fixed, then compare p50/p95/p99, write amplification, memory and failure radius.
