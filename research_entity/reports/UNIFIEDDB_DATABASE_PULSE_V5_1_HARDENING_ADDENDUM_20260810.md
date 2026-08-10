# UnifiedDB Database Pulse V5.1 hardening addendum

Date: 2026-08-10
Parent decision: `UNIFIEDDB_DATABASE_PULSE_V5_DIRECT_EVENT_FUSION_20260810.md`
Status: TESTING / NOT PROMOTED
PR: #136

## Hardening deltas after V5 fusion review

### 1. Ambiguous legacy U12 epoch migration now fails closed

Finding: a pre-V5 U12 `source_epoch` is an integer from a legacy execution plane. The integer alone
does not prove that its epoch namespace is identical to the authoritative StateLedger epoch
namespace. Automatically mapping a lagging legacy value to StateLedger event history would violate
the project rule `stale epoch/schema -> reject, do not guess`.

Preferred runtime: `DatabasePulseExecutionPlaneV51` in
`research_entity/runtime/database_pulse_execution_plane_v5_1.py`.

Rules:

- fresh V5.1 -> verified current StateLedger snapshot at current event head;
- already-V5 -> verify cursor/hash/epoch and continue;
- legacy U12 aligned with current StateLedger epoch -> start a new direct-event cursor at current
  verified reality, without claiming historical epoch equivalence;
- lagging legacy U12 -> fail closed by default;
- lagging legacy U12 may be mapped only with explicit
  `legacy_source_epoch_is_stateledger_epoch=True`, after which the runtime requires a verifiable
  StateLedger event/hash boundary and the catch-up tests must reproduce the remaining event stream.

This flag records migration authority/provenance. It is not scientific evidence that the legacy
epochs were equivalent.

### 2. True two-writer idempotency test materialized

`test_database_pulse_execution_plane_v5_1.py` opens two independent StateLedger/SQLite connections
against the same database, synchronizes two writer threads on a barrier, and sends the same V5
invocation id concurrently.

Required result:

- both calls terminate;
- one returns `RECORDED`, one `ALREADY_RECORDED`;
- both expose identical pulse id / pulse index / receipt hash;
- persistent Pulse count == 1;
- invocation registry rows for the id == 1;
- Pulse receipt rows == 1;
- non-bootstrap checkpoint rows for that Pulse == 1.

The implementation uses `BEGIN IMMEDIATE` plus the V5 invocation registry unique constraints and
re-checks the registry inside the write transaction. This is materially stronger than the earlier
sequential retry test, but remains TESTING until run receipts are observed.

### 3. V5.1 CI hardening lane

`.github/workflows/database-pulse-v5-1-hardening.yml` executes:

- compile checks;
- V5 direct-event suite;
- V5 source-boundary suite;
- V5.1 strict-migration / two-writer suite;
- inherited adaptive-rank tests;
- inherited authenticated focus-use tests;
- matched semantic-V4 vs direct-event-V5 benchmark;
- randomized authoritative-rank differential on Hostinger;
- hosted + self-hosted Ubuntu hard gates.

Execution truth remains separate from materialization truth. A workflow definition is not a PASS.
Promotion requires a real step-level receipt.

## Remaining strongest counterhypotheses

1. Keeping every Pulse receipt/checkpoint in SQLite may create unacceptable long-run storage/WAL
   amplification even after semantic self-churn is removed.
2. Periodic full-root audits plus per-focus auth guard may still be too expensive or too weak for
   the target failure model; target measurements must establish the correct cadence.
3. Direct StateLedger event consumption may need an explicit retention/compaction contract if the
   event log is pruned; cursor recovery across compaction is not yet promoted.
4. SQLite writer serialization may become a throughput bottleneck under real concurrent Frank
   subsystems even when idempotency is correct.
5. Adaptive compiled-rank economics may differ materially on Andreas' target hardware and real
   mixed read/write workload.

## Next promotion gates

No promotion before:

- hosted/self-hosted test steps actually execute and pass;
- concurrency test executes repeatedly, including restart/retry around the winning transaction;
- crash fault injection covers registry/state/receipt/checkpoint boundaries;
- long-run receipt/WAL/storage amplification is measured;
- event-log retention/compaction cursor recovery is specified and tested;
- target-like rank compile economics are measured;
- final Andreas Ubuntu system repeats required gates.
