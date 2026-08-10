<!-- RAE_META
{"packet_id":"UNIFIEDDB_PULSE_V0_LAST_KNOWN_GOOD_RECOVERY_GAP_20260810","title":"Database Pulse v0 last-known-good recovery gap","domains":["unifieddb","frank","recovery","replay"],"topics":["checkpoint fallback","delta acknowledgement rollback","receipt rollback","replay","last known good"],"epistemic_class":"SOURCE_AUDIT_COUNTERHYPOTHESIS","claim_status_hint":"BLOCKER_CANDIDATE","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T07:28:00+07:00","source_refs":["research_entity/runtime/database_pulse_v0.py","research_entity/runtime/RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql"],"confidence":"HIGH_FOR_CODE_PATH_GAP_UNTIL_EXECUTED_FALSIFIER","verification_required":true,"falsifier_or_next_test":"Execute multi-pulse rollback with a corrupted newest checkpoint; prove fallback to newest older valid checkpoint, reversal of all post-checkpoint internal acknowledgements/receipts/checkpoints/invalidations, and deterministic replay without pulse-index collision."}
RAE_META -->

### Finding

`DatabasePulseV0.recover_last_known_good()` currently orders checkpoints newest-first but selects exactly one row with `LIMIT 1`. It then raises on a hash mismatch rather than scanning backward for the newest cryptographically self-consistent checkpoint. This is weaker than the function contract expressed by its own docstring and by the project continuity requirement for last-known-good recovery.

A second coupled risk exists if recovery ever selects an older checkpoint: the current method restores only `frank_database_pulse_state`. It does not atomically rewind internal post-checkpoint state that was committed by later Pulse transactions, including delta `applied_pulse_id` acknowledgements, later Pulse receipts/checkpoints, and Pulse-generated U10 possibility invalidations when that table exists. That can make later deltas appear already consumed after the state has moved backward, and retained receipt `pulse_index` uniqueness can collide when replay tries to recreate a rolled-back index.

This packet is a **blocker candidate**, not an executed failure receipt. The existing test that corrupts only the live state and restores the newest still-valid checkpoint does not discriminate these older-checkpoint cases.

### Required falsifier

1. Bootstrap Pulse v0 with U12 and U10 possibility invalidations enabled.
2. Admit and commit at least two distinct Pulse batches.
3. Corrupt the newest checkpoint payload/hash pair without modifying the previous checkpoint.
4. Corrupt live state so recovery is required.
5. Recover and require selection of the newest older self-consistent checkpoint.
6. In the same recovery transaction require:
   - all Pulse receipts after the chosen checkpoint are removed/quarantined from the active lineage;
   - all later Pulse checkpoints are removed/quarantined;
   - all delta acknowledgements belonging only to rolled-back Pulse IDs become unapplied again;
   - Pulse-generated possibility invalidations for rolled-back deltas are removed or deterministically rebuilt;
   - state hash verifies before commit.
7. Replay the reopened deltas and require deterministic post-state hash and no `pulse_index` collision.
8. Inject a fault during recovery and require complete rollback to the pre-recovery broken/quarantined state rather than a partially rewound database.

### Architecture consequence

Do not promote Pulse v0 recovery as full last-known-good semantics until this falsifier passes. A safer implementation should discover the newest internally consistent checkpoint by descending scan, compute the rollback cut from checkpoint `pulse_index`/`last_applied_delta_seq`, and rewind all **endogenous Pulse bookkeeping** atomically. It must not roll back external effects or canonical truth by inference; effect reconciliation remains outside Pulse authority.

If Database Pulse v1/v2 supersedes v0 before this is repaired, the same falsifier should be carried forward as a successor recovery obligation rather than silently dropped.
