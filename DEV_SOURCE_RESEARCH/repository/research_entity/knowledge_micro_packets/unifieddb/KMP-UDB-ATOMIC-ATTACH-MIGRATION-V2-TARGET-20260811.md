# KMP-UDB-ATOMIC-ATTACH-MIGRATION-V2-TARGET-20260811

packet_id: `KMP-UDB-ATOMIC-ATTACH-MIGRATION-V2-TARGET-20260811`
domains: `unifieddb, claygraph, sqlite, migration, recovery`
epistemic_class: `ACCEPTED_TARGET_VPS_MECHANISM_EVIDENCE`
status_hint: `SUPPORTED_TARGET_PRECOMMIT_ATOMIC_MECHANISM_POWERLOSS_COMMIT_OPEN`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Target receipt

Candidate lived on research/fusion PR #286 branch `chatgpt/unifieddb-storage-pair-fused-main-20260811` at head `baa43b4a0025c8a3cd1a790b6b7bd4982ca4501f`.

Target workflow: `Frank UnifiedDB attached atomic pair migration V2 VPS`
Run: `31436807365`
Result: `SUCCESS`
Artifact: `frank-atomic-pair-v2-31436807365`
Artifact id: `9081378050`
Artifact digest: `sha256:4d2fb12cba510a7e981d555f4f4057a38981f5eb3c70bd658944075f46e56579`
Environment:
- Linux `6.8.0-117-generic` x86_64;
- Python `3.12.3`;
- SQLite `3.45.1`.

Mechanism result: `PASS_ATOMIC_PAIR_MIGRATION_V2_MECHANISM`.

## What was proved

The candidate compiler converted the current real migration surface into one attached rollback-journal transaction:
- 188 UnifiedDB statements;
- 52 ClayGraph statements;
- both `journal_mode=delete`;
- both physical integrity `ok`;
- zero FK violations.

Resulting live schema identities exactly matched the existing reference migrator:
- UnifiedDB `430d77b0f169c1cb3ba4e956ef06ddecaa14c72f88dbe622e6bb79cc362fc541`;
- ClayGraph `381d26b997973520cb1d3ae6a2161f1d561213b841a0d509b5be9d15f6441468`.

Target timing for the disposable full mechanism:
- fresh attached pair migration ~46.984 ms;
- remigration ~19.600 ms;
- max RSS for whole probe ~25,324 KiB.
These are not production throughput measurements.

Remigration preserved application sentinels on both databases and preserved logical schema identity.

Three explicit pre-COMMIT failure windows were injected independently:
1. `AFTER_GRAPH_DDL`;
2. `AFTER_UNIFIED_DDL`;
3. `AFTER_CERT_STAMP`.

For every injected exception:
- both logical schemas remained equal to their pre-run state;
- both sentinels remained unchanged;
- both SQLite integrity checks remained `ok`;
- both FK checks remained clean.

## External mechanism basis

SQLite documents that transactions spanning multiple ATTACHed databases are atomic as a set when the main database is file-backed and journal mode is not WAL. In rollback-journal mode SQLite coordinates multi-file commit using rollback journals plus a super-journal.

That mechanism aligns with the current target-safe SQLite 3.45.1 storage direction: rollback journal DELETE + FULL rather than unproven WAL.

## Strong remaining falsifier

This target receipt proves:
- current Frank migrations can be compiled into one ATTACHed transaction;
- schema equivalence;
- ordinary transaction rollback for failures before COMMIT completes.

It does **not** directly execute abrupt process/power loss during SQLite's multi-file COMMIT/super-journal recovery window. That is the required next discriminator before using this as production cross-file migration atomicity evidence.

Required crash test:
- child process enters attached transaction and commits under DELETE/FULL;
- parent kills/power-loss-simulates at controlled commit windows where feasible;
- reopen both files after SQLite recovery;
- result must be exactly PRE or POST on both files, never split Graph/Unified state;
- integrity/FK/live-schema identities must remain admissible;
- repeat enough times to hit super-journal recovery states rather than treating absence of a split in one run as proof.

## Architecture consequence

DELETE/FULL is no longer just a compatibility fallback. It is a genuine architecture candidate because it can offer a property fixed-WAL cannot: cross-file attached transaction atomicity for bounded UnifiedDB+ClayGraph writes/migrations.

This does not imply all Graph updates should become synchronous or that DELETE automatically beats fixed WAL. The physical A/B remains:
- `SYSTEM_SAFE_DELETE`: attached atomic bounded pair updates; more lock/fsync serialization;
- `PRIVATE_FIXED_WAL`: better concurrency candidate; Graph remains asynchronous/rebuildable because multi-ATTACH WAL is not jointly crash-atomic.

Choose by correctness first, then target latency/concurrency/recovery/I/O measurements.

## Promotion boundary

`SUPPORTED_TARGET_PRECOMMIT_ATOMIC_MECHANISM_POWERLOSS_COMMIT_OPEN`.

No canonical migration, product merge, R1C Graph freshness, semantic rollback authority, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
