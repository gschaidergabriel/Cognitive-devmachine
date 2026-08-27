<!-- RAE_META
{"packet_id":"KMP-FRANK-C7-LOGICAL-FABRIC","title":"FRANK C7 consumes UnifiedDB as logical fabric, not mandatory physical monolith","domains":["unifieddb","frank","storage-state-memory"],"topics":["logical query fabric","derived views","physical placement","replay"],"epistemic_class":"OPEN_ARCHITECTURE_CANDIDATE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:51:00Z","source_refs":["research_entity/trigger_runs/frank/20260808T2051p0700-chatgpt-secondary-r3/FRANK_ARCHITECTURE.claycode.json","research_entity/global/UNIFIED_DATABASE_RESEARCH_FOUNDATION.md"],"verification_required":true}
RAE_META -->

### Core
C7 requires one typed logical query/transaction plane across exact, relational, graph, vector, FTS and activation views while preserving physical specialization and hard isolation. Exact event/effect history remains authoritative; derived views carry source/epoch/derivation/rebuild receipts.

### Next test
Four-baseline UnifiedDB benchmark with replay equivalence, selection integrity, p99, write amplification, crash radius and rollback.