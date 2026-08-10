# UnifiedDB F-V01-04 Storage Continuity — Target VPS Receipt — 2026-08-10

Status: TARGET_TEST_SUPPORTED / NOT_PROMOTED
Origin actor: chatgpt-secondary
Provider/model: OpenAI / GPT-5.6 Sol
Target repository: gschaidergabriel/Dr.-Unterweger
Target PR: #189
Target branch: chatgpt/unifieddb-current-main-wal-safety-20260810
Workflow run: 31408547133
Workflow job: 93520768416
Evidence class: TARGET_COMPATIBLE_SELF_HOSTED_CURRENT_MERGE_CONTEXT_COMPONENT_TEST

## Exact tested merge context

The self-hosted GitHub Actions checkout fetched and executed:

- PR merge ref: `b78e1b19209a44add01ac681cd15041a79b7205f`
- candidate head: `d4ae24f6e9bc898e4f704ee15a47b3bd676591b5`
- merge base/current-main context used by GitHub: `f2ec9ae063352a95eca3123f650b66304a195c3f`

This matters because main advanced after #189 was first created. The target job therefore did not merely execute the branch against the older creation base; GitHub rebuilt the PR merge ref against the then-current `f2ec9ae...` main context before checkout.

## Target environment

- runner name: `clay`
- machine: `digital-retina`
- platform: `Linux-6.8.0-117-generic-x86_64-with-glibc2.39`
- Python: `3.12.3`
- SQLite: `3.45.1`
- git: `2.43.0`

The SQLite runtime remains in an affected release family for the upstream 2026 WAL-reset corruption defect, so the candidate policy selects rollback journal DELETE + synchronous=FULL instead of WAL for migration on this runtime.

## Executed tests

All seven tests passed:

1. `test_full_current_schema_chain_uses_safe_policy_and_passes_integrity`
2. `test_fixed_runtime_accepts_preexisting_wal_full`
3. `test_vulnerable_runtime_accepts_delete_full`
4. `test_vulnerable_runtime_rejects_preexisting_wal`
5. `test_fixed_runtime_keeps_wal_full_policy`
6. `test_known_vulnerable_and_fixed_release_families`
7. `test_target_vps_observed_3451_falls_back_to_delete_full`

Result: `Ran 7 tests in 0.048s` / `OK` / process exit status 0.

## Resource receipt

GNU `/usr/bin/time -v` for the test process:

- user time: 0.10 s
- system time: 0.02 s
- elapsed wall time: 0.14 s
- CPU: 86%
- maximum RSS: 29140 kB
- major page faults: 0
- minor page faults: 4872
- voluntary context switches: 73
- involuntary context switches: 0
- swaps: 0
- filesystem inputs: 0
- filesystem outputs: 3304
- socket messages sent/received: 0/0
- exit status: 0

## Supported claims

This target-compatible merge-context run supports the following component claims:

- the candidate version-family classifier treats target SQLite 3.45.1 as unfixed;
- the candidate migration path selects DELETE + FULL on that target runtime;
- the full currently resolved UnifiedDB + ClayGraph schema chain can be materialized under that fail-safe policy in disposable state;
- integrity_check and foreign_key_check remain clean in the disposable full-schema migration test;
- normal runtime open rejects a pre-existing WAL store when the observed SQLite family is vulnerable;
- normal runtime open accepts DELETE state on the vulnerable target family and enforces FULL;
- the fixed-family branch still admits WAL + FULL in the controlled regression.

## Claims explicitly NOT supported

This receipt does NOT establish:

- the current persistent/canonical target UnifiedDB or ClayGraph journal mode;
- that persistent target state has already been migrated from WAL to DELETE;
- power-loss durability;
- simultaneous multi-process writer/checkpointer safety on SQLite 3.45.1;
- whole Frank v0.1 acceptance;
- ClayCode-only cognition completion;
- provider-effect completion/reconciliation;
- F-V01-04 terminal completion;
- V17 canonical migration inclusion;
- any universal superiority claim over SQLite/PostgreSQL/graph databases.

The GitHub-hosted sibling job for the same workflow completed in the current repository-wide no-step failure class and supplied no executable counterevidence. This receipt therefore credits only the successful self-hosted target-compatible job.

## Next falsifier / recovery gate

Before promotion or merge credit can close F-V01-04:

1. refresh current main and check overlap again;
2. read-only audit the actual persistent target `FRANK_UNIFIED.sqlite` and `FRANK_CLAYGRAPH.sqlite` journal modes and SQLite runtime identity;
3. if either persistent DB is WAL on an unfixed runtime, take verified last-known-good backup first;
4. perform only a separately authorized Research-Entity migration to the safe policy or upgrade SQLite to a fixed family;
5. restart/reopen normal Frank state and require repository/materialization truth, V15 lease continuity, V16 execution continuity and integrity/FK checks to pass;
6. rerun crash/restart/idempotency/stale-epoch tests against the actual current product schema;
7. keep V17 canonical-inclusion adjudication separate unless current main explicitly resolves it.

## Disposition

Architecture delta: SUPPORTED_COMPONENT_CANDIDATE
Canonical promotion: NO
F-V01-04 status change: NO — remains OPEN pending persistent-state audit/recovery/replay evidence.
