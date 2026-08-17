# UnifiedDB F-V01-04 Storage Continuity — 2026-08-10

Status: TESTING_CANDIDATE / NO_CANONICAL_PROMOTION
Origin actor: chatgpt-secondary
Provider/model: OpenAI / GPT-5.6 Sol
Trigger lens: unifieddb (owner input `unifiedb` interpreted as the intended registered branch command)
Target: current accepted Frank v0.1 Hostinger Ubuntu VPS body
Truth boundary: Clay is the research entity; Frank/self.root is the separate research subject.

## Question

What is the highest-value current F-V01-04 UnifiedDB state-continuity blocker after V15 single-instance presence, V16 execution continuity and the existing standalone epoch-sealed continuity probe?

## Current-state refresh

The active Frank v0.1 workspace still records F-V01-04 UNIFIEDDB-STATE-CONTINUITY as OPEN. Current target main already contains:

- authoritative semantic transactions/state epochs/materialized state;
- V14 effect lifecycle;
- V15 exclusive semantic presence/lease epoch;
- V16 execution/request continuity and restart-visible idempotency state;
- a separate V17 provenance-bound effect completion schema file whose canonical inclusion is a separate live integration question.

UnifiedDB remains semantic/persistence authority. ClayGraph remains derived/rebuildable topology. No physical co-location promotion is inferred here.

## Existing evidence found instead of duplicating it

Dr.-Unterweger PR #182 already implements the intended standalone F-V01-04 epoch-sealed discriminator. Its self-hosted target-VPS run 31407554177 / job 93517452110 executed on runner `clay`, machine `digital-retina`, Python 3.12.3, SQLite 3.45.1 and passed 11/11 boolean continuity checks.

Observed #182 receipt:

- durability policy: DELETE + synchronous=FULL fallback;
- reason: SQLite 3.45.1 classified outside fixed WAL-reset families;
- 300 commits;
- commit latency p50 1743.522 us;
- p95 2678.487 us;
- p99 3934.526 us;
- max 5205.964 us;
- stale epoch rejected;
- duplicate idempotency key rejected;
- derived-index lag detected;
- query receipt epoch-bound;
- hard child-process crash before commit left no transaction visible;
- integrity remained OK after restart;
- epoch chain remained valid after restart;
- verified outcome -> provenance re-entry link present.

The probe explicitly does NOT claim ClayCode-compiled execution, a real provider effect or whole Frank v0.1 acceptance.

## Strongest counterhypothesis

A green standalone continuity probe may not improve the product because it can reproduce desired semantics in a parallel mini-schema while the real canonical migration/open path remains unsafe or semantically different.

This counterhypothesis is SUPPORTED.

## Reproduced production-path mismatch

Current target `runtime/state/apply_current_schema.py` still unconditionally requests:

- `PRAGMA journal_mode=WAL`;
- `PRAGMA synchronous=FULL`;

for both UnifiedDB and ClayGraph migrations, and normal `_open_existing()` accepts the persisted journal topology without checking the SQLite WAL-reset fix family.

The accepted target-compatible VPS environment is currently observed on SQLite 3.45.1.

SQLite upstream documents the 2026 WAL-reset corruption defect for affected WAL deployments when multiple connections in separate threads/processes may write/checkpoint concurrently. The fix is present in mainline >=3.51.3 and documented backports 3.50.7 and 3.44.6. Primary-source references:

- https://sqlite.org/wal.html
- https://sqlite.org/releaselog/3_51_3.html

Therefore the product path cannot inherit the standalone #182 safety result merely because the probe selected DELETE+FULL.

## Architecture delta candidate

Target PR: Dr.-Unterweger #189
Branch: `chatgpt/unifieddb-current-main-wal-safety-20260810`
Status at this report write: OPEN / TESTING / NOT MERGED

Candidate behavior:

1. Parse SQLite version by release family rather than naive monotone version comparison.
2. Migration policy:
   - vulnerable/unknown family -> DELETE + synchronous=FULL;
   - fixed 3.44.x >=3.44.6 -> WAL + FULL;
   - fixed 3.50.x >=3.50.7 -> WAL + FULL;
   - >=3.51.3 -> WAL + FULL.
3. Fail migration if the engine cannot actually enter the required journal mode.
4. Normal canonical state open:
   - vulnerable SQLite + persisted WAL -> fail closed as CONTINUITY_DEGRADED;
   - vulnerable SQLite + DELETE -> allow, enforce synchronous=FULL;
   - fixed SQLite + WAL -> allow, enforce synchronous=FULL;
   - unsupported canonical journal modes -> fail closed and require authorized migration.
5. Preserve all current schema ordering, Research-Entity-only canonical migration authority, integrity/FK validation, central state path and UnifiedDB/ClayGraph semantic authority separation.

This is a physical continuity guard. It does not widen truth/effect authority.

## Regression candidate

PR #189 adds:

- fixed/vulnerable family classification tests;
- exact 3.45.1 migration fallback test;
- fixed-runtime WAL route test;
- vulnerable pre-existing WAL runtime-open rejection;
- vulnerable DELETE runtime-open acceptance;
- fixed WAL runtime-open acceptance;
- complete disposable current UnifiedDB + ClayGraph migration-chain smoke with journal/synchronous/integrity/FK assertions;
- GitHub-hosted and self-hosted target-compatible workflow lanes.

At this report write, the self-hosted exact-byte job has not yet begun execution; no PASS is claimed. Repository-wide `Frank Deep Integrity` and hosted jobs are currently showing a separate no-step/absent-log infrastructure failure class and are not interpreted as scientific test failures.

## Supplementary local discriminator

A local Linux file-backed SQLite microprototype, explicitly NOT target evidence, tested a single-file epoch/head/projection transaction with BEGIN IMMEDIATE and synchronous=FULL. Fifteen real child-process hard exits were injected across three pre-COMMIT points (after event insert, after projection update, after head update), five repetitions each. All 15 reopened at the last committed epoch with `PRAGMA integrity_check=ok` and no partial event/projection/head visibility.

This supports the atomic-commit mechanism only. It is not power-loss evidence, target-VPS evidence or proof about the current Frank schemas.

## Negative results / non-selections

- Do NOT duplicate PR #182 as another parallel F-V01-04 mini-schema.
- Do NOT interpret the narrow effect-authority `runtime/vps_unifieddb` evidence as a general UnifiedDB acceptance.
- Do NOT merge physical UnifiedDB + ClayGraph merely for speed; logical authority separation remains fixed and physical co-location still needs recovery evidence.
- Do NOT promote WAL on target SQLite 3.45.1 merely because single-connection tests pass.
- Do NOT pull V17 canonical-inclusion work into the storage-safety patch; it is a separate effect/re-entry migration-authority question.
- Do NOT claim universal superiority over PostgreSQL, SQLite or graph databases from this repair.

## Next discriminating gates

1. Execute PR #189 exact merge bytes on the self-hosted target-compatible VPS lane.
2. Record exact platform/Python/SQLite/journal/synchronous/resource receipt.
3. Audit the actual persistent target UnifiedDB and ClayGraph journal modes read-only.
4. If either is WAL on an unfixed SQLite family, create verified backup/LKG first, then run the separately authorized safe migration to DELETE+FULL or upgrade SQLite to a fixed family.
5. Restart/reopen and require repository/materialization truth, V15 presence and V16 execution continuity to remain coherent.
6. Re-run crash/restart/replay and stale-epoch/idempotency tests against the actual current product schema, not a parallel mini-schema.
7. On a fixed SQLite family, run the multi-connection writer/checkpoint stress that is currently unsafe to claim on 3.45.1.
8. Compare safe DELETE+FULL and fixed-WAL+FULL on the real Frank workload for latency, jitter, write amplification, checkpoint behavior and recovery, while preserving the same semantic invariants.
9. Resolve V17 canonical inclusion independently.
10. Only then consider updating F-V01-04 completion evidence / terminal UnifiedDB receipt.

## Current conclusion

The major result is not another retrieval algorithm. It is a continuity mismatch between a successful standalone F-V01-04 probe and the real current product storage path.

PR #182 demonstrates the desired epoch/crash/re-entry mechanism on the accepted target-compatible VPS. PR #189 moves the same fail-safe storage premise into the actual current migration/open boundary. Until its target run and actual persistent-state audit pass, F-V01-04 remains OPEN and the architecture delta remains TESTING_CANDIDATE.
