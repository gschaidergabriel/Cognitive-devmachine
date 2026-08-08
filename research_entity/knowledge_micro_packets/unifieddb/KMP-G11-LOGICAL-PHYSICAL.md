<!-- RAE_META
{"packet_id":"KMP-G11-LOGICAL-PHYSICAL","title":"UnifiedDB should unify semantics and planning before physical storage","domains":["unifieddb","clay","frank","claygraph"],"topics":["logical unification","physical polyglot","query planner","common-mode risk"],"epistemic_class":"OPEN_ARCHITECTURE_REFINEMENT_WITH_SYNTHETIC_CALIBRATION","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:33:00Z","source_refs":["research_entity/global/UNIFIED_DATABASE_RESEARCH_FOUNDATION.md","research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
Start UnifiedDB as one Clay semantic identity/query/transaction plane over specialized physical engines. Decide physical colocation per subplan/workload using latency, serialization, contention, write amplification, recovery and common-mode risk.

### Evidence
CIDR/PVLDB work independently supports bridge/unified algebras and decoupled vector sidecars, while integrated graph-vector engines show physical consolidation is feasible. G11's synthetic sweep found no universal architecture winner.

### Next test
Dedicated four-baseline UnifiedDB benchmark with replay, query equivalence, p50/p95/p99, crash recovery and reversible migration.