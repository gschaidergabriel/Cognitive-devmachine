<!-- RAE_META
{"packet_id":"FRANK_SQLITE_WAL_VPS_20260810","title":"Frank disposable SQLite WAL probe on Hostinger Ubuntu","domains":["unifieddb","frank","harness"],"topics":["SQLite","WAL","synchronous FULL","synchronous NORMAL","locking","checkpoint"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT","origin_class":"REMOTE_EXECUTION_RECEIPT","origin_actor":"claude-code-lead","created_at":"2026-08-10T00:09:00+07:00","updated_at":"2026-08-10T00:09:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/sqlite_wal_probe_latest.json","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger@2696a85eca3ccf916203b06f7d56f860a1e09a94"],"related_claim_ids":[],"related_experiment_ids":["FRANK_SQLITE_WAL_RUNTIME_PROBE"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"HIGH_FOR_DISPOSABLE_HOST_WORKLOAD","verification_required":true,"falsifier_or_next_test":"Run production-shaped concurrent state workload plus process-kill/restart and disposable crash/power-loss-equivalent durability tests before changing synchronous policy.","search_terms":["SQLite WAL","0.745 ms","SQLITE_BUSY","checkpoint","Frank UnifiedDB"]}
RAE_META -->

### Core
A disposable SQLite WAL workload on the real Hostinger Ubuntu runner measured 120 commits per mode: `synchronous=FULL` mean 0.745740 ms / p95 0.956806 ms versus `NORMAL` mean 0.025938 ms / p95 0.045 ms. A held reader did not block writes; WAL reached 650,992 bytes and truncated to zero after reader release. Competing-writer contention produced `SQLITE_BUSY` after ~100.861 ms and recovered after release.

### Evidence / boundary
Canonical Frank state was not mutated and integrity checks passed. The ~28.75x mean latency ratio is workload-specific. Normal process execution is not a power-loss test and gives no cross-file crash-atomicity guarantee.

### Implication
Keep WAL behavior and contention handling explicit, but do not switch Frank from FULL durability merely for latency.

### Next test
Use production-shaped state transitions, restart/kill recovery, checkpoint pressure and disposable durability fault injection.
