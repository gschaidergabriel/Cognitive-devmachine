# Harness run — H-WP-02 concurrent idempotency race

Run: `20260809T1705p0700-hwp02-idempotency-race`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Trigger: `harness`

## Scope

This worker joined the current Harness branch as a review/falsification worker rather than creating another StateLedger implementation. The current workspace already had H-WP-02 claimed, and current repository history contained a tested H1 reference StateLedger plus a second competing H-WP-02 candidate lineage and a newer H-WP-11 TurnTraceEnvelope implementation.

The latest whole-mesh live-fusion closure was used as compact current coverage for all registered peer branches, then the relevant Harness artifacts were reread directly. See `INTERCONNECT_MANIFEST.json`.

## Current program boundary

`BASE_CLAYCODE_RELEASE` remains the active program stage. `H1_REFERENCE_HARNESS` remains blocked on BASE. Therefore this run may build/test component foundations and preserve counterexamples, but it does not claim H1 PASS or live-FRANK validation.

## Finding

The tested H1 reference ledger lineage performs an idempotency lookup before `BEGIN IMMEDIATE`. The visible control flow then acquires the write lock and proceeds with the write without a second idempotency lookup inside the transaction.

That ordering has a concrete concurrent-writer counterexample:

1. writer A checks idempotency key K -> absent;
2. writer B checks K -> absent;
3. writer A acquires `BEGIN IMMEDIATE`, inserts K, commits;
4. writer B later acquires `BEGIN IMMEDIATE`;
5. without a post-lock lookup, writer B attempts to insert K and receives the storage-level UNIQUE error instead of deterministic idempotent replay handling.

## Executed probe

A standalone deterministic SQLite mechanism probe was built and executed in the ChatGPT Python sandbox.

Observed vulnerable ordering:

- both preflight lookups missed;
- first writer committed;
- second writer raised `IntegrityError: UNIQUE constraint failed: events.idem`;
- exactly one row remained.

Observed guarded ordering:

- same preflight misses;
- after the first writer committed, the second writer acquired `BEGIN IMMEDIATE` and rechecked K;
- second writer returned `IDEMPOTENT_REPLAY`;
- exactly one row remained.

Artifact: `research_entity/harness/probes/hwp02_idempotency_prelock_race_probe.py`  
Receipt: `EXECUTION_RECEIPT.json`

Evidence class: `LOCAL_DETERMINISTIC_SYNTHETIC_MECHANISM_PROBE`.

This is not a project-host execution of the complete H1 StateLedger and does not upgrade to live-FRANK evidence.

## Negative result

`NR-HARNESS-HWP02-IDEMPOTENCY-PRELOCK-RACE-20260809` preserves the counterexample. It does not invalidate existing single-writer results: deterministic semantic hashes, stale-epoch rejection, explicit epistemic states, snapshot/restore, tamper checks and the earlier 7-test receipt remain intact within their tested scope.

## Repair hypothesis

Move or repeat idempotency identity/fingerprint validation inside the write transaction after `BEGIN IMMEDIATE`, then return replay only when the committed event is semantically the same. A reused idempotency key with a different event identity/fingerprint must remain a conflict.

The actual H1 code is intentionally not declared fixed by this run because this hosted ChatGPT surface cannot execute the full repository on the Ubuntu project host.

## Local execution handoff

Dynamic work `HWP02-IDEMPOTENCY-RACE-LOCAL-FIX` was queued for the local Claude Code organ. Completion requires:

- reread current H-WP-02 lineage/head;
- patch the actual reference StateLedger transaction boundary;
- add a real two-connection/process regression against the module;
- rerun existing tests and stress/snapshot/tamper suites on the Ubuntu project host;
- record exact local execution receipts;
- do not mark H1 PASS from component success alone.

Work event: `research_entity/state/work/events/20260809T1705p0700-hwp02-idempotency-race-local-fix.json`

## Mesh feedback

Material feedback was routed to Harness, UnifiedDB, FRANK, ClayCode and Clayresearch; the remaining branches received explicit NO_CHANGE receipts. See `BRANCH_FEEDBACK_MANIFEST.json`.

## Claim-state consequence

- New negative result: concurrent safety of the pre-lock-only idempotency pattern is **not supported**.
- No canonical scientific promotion.
- No H-WP-02 completion claim.
- No H1 PASS claim.
- No live-FRANK evidence claim.

## Next falsifier / discriminating test

Execute the patched actual H1 StateLedger on the Ubuntu project host with two concurrent connections/processes using the same idempotency key. Require deterministic replay/conflict semantics, no raw UNIQUE leakage, one committed event, stable epoch/root identity, and full regression-suite PASS.
