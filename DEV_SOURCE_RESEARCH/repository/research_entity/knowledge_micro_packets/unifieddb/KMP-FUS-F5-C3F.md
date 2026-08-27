<!-- RAE_META
{"packet_id":"KMP-FUS-F5-C3F-UNIFIEDDB","title":"Fusion F5: UnifiedDB preserves collection algebra and canonical re-entry across adaptive placement","domains":["unifieddb","claycode","claygraph","frank","gwt"],"epistemic_class":"OPEN_ARCHITECTURE_SUPPORT_AND_REFINEMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T14:16:40Z","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2044p0700-chatgpt-secondary-r2/FINAL_REPORT.md","research_entity/trigger_runs/fusion/fusion-20260808T2114p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Delta
UD-RC1's logical-over-physical separation is strengthened. `UnifiedQueryIR` must carry exact collection algebra and bind it in selection/query-plan receipts; type-erased storage lowering can silently change candidate multiplicity/order.

Persistent graph/vector/FTS/activation updates should consume canonical event/effect/outcome commits. Physical placement remains per-subplan. Apache Arrow C Data Interface is a same-process zero-copy candidate only; cross-process CORF routes require an explicit IPC/shared-memory transport contract.

### Next test
Trace-driven multi-engine query lowering + crash/replay + Rust/Arrow/shared-memory benchmark with identical semantic/selection/view receipts.