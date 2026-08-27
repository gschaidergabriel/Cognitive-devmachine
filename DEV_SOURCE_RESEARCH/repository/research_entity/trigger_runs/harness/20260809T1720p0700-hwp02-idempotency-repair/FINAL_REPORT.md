# Harness run — H-WP-02 semantic idempotency repair

Run: `20260809T1720p0700-hwp02-idempotency-repair`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Trigger: `harness`

## Scope

This worker continued the already active `H-WP-02-STATE-LEDGER` lineage and repaired the two idempotency counterexamples established by the immediately preceding Harness runs. No competing StateLedger implementation was created.

The current staged program remains `BASE_CLAYCODE_RELEASE`; H1 remains blocked on BASE. This run is therefore component-level build/execute/falsification work and does not claim H1 PASS or live-FRANK validation.

## Repaired failure modes

The prior current reference implementation had two coupled failure modes:

1. duplicate/idempotency lookup occurred before `BEGIN IMMEDIATE`, leaving a TOCTOU window between two writers;
2. a found duplicate accepted replay based on matching `event_id` without establishing that the retry represented the same semantic request.

The current reference implementation was changed so that:

- normalized mutation and provenance representations are prepared deterministically;
- `BEGIN IMMEDIATE` is acquired before duplicate resolution;
- an existing idempotency key is replayable only when `event_id`, `base_epoch`, `event_type`, normalized mutations and provenance are identical;
- writer and timestamp remain execution-local retry metadata and do not by themselves change semantic retry identity;
- changed semantics under a reused key raise a deterministic `LedgerError` without state/epoch mutation;
- stale-epoch comparison remains fail-closed for new events.

Implementation commit: `e77de62e5aa784f90fdee1541ac8f2449478cb0b`  
Committed blob: `ed109c281f3d2139b0e5e59305f604a60e150c6d`

## Executed tests

Execution class: `LOCAL_CONTAINER_LINUX_EXECUTION_OF_EXACT_COMMITTED_GIT_BLOB`.

Observed PASS:

- changed semantic retry red probe: rejected, committed state unchanged, epoch unchanged;
- actual-module multiprocessing concurrent retry probe: one `COMMITTED`, one `IDEMPOTENT_REPLAY`, one event row, epoch 1;
- regression bundle: event-chain verification, stale-epoch rejection, semantic-root stability, snapshot/export/restore, explicit UNKNOWN/CONFLICT preservation and Python compilation;
- local executed source blob identity matched the GitHub committed blob exactly.

The new actual-module concurrency probe was committed at:

`research_entity/harness/probes/hwp02_actual_idempotency_concurrency_probe.py`

Commit: `41943b0b756eb65e93e51db6ce568bfcda88611f`

See `EXECUTION_RECEIPT.json`.

## Evidence boundary

This run does **not** upgrade the result to Ubuntu project-host validation. The connector surface did not provide execution inside the designated project checkout/host. The full historical H-WP-02 stress/crash/tamper suite therefore remains a required local-organ check.

Consequently:

- `H-WP-02-STATE-LEDGER` remains incomplete;
- H1 remains blocked on BASE and is not PASS;
- no live-FRANK claim is made;
- no canonical scientific promotion is made;
- no paid training is authorized or started.

## Mesh feedback

Material feedback was routed to `clayresearch`, `frank`, `claycode`, `unifieddb` and `harness`.

`gwt`, `emergenz`, `hyperposition` and `claygraph` received explicit `NO_CHANGE` receipts for this repair.

See `BRANCH_FEEDBACK_MANIFEST.json`.

## Next discriminating test

On the Ubuntu project host, at the exact repaired commit or a verified descendant:

1. run `hwp02_idempotency_payload_fingerprint_probe.py` against the actual reference module;
2. run `hwp02_actual_idempotency_concurrency_probe.py`;
3. rerun the complete H-WP-02 regression/stress/crash/snapshot/tamper test surface;
4. record host, commit, commands, outputs and test counts in a verified local execution receipt;
5. only then adjudicate whether H-WP-02 can advance toward completion.

## Decision trace

Evidence used: current canonical/program/workspace state, current H1 reference source, immediately preceding H-WP-02 negative results and executable probes, current Frank runtime-state lineage.  
Alternative rejected: create a parallel StateLedger implementation; this would violate the shared Harness lineage and obscure differential evidence.  
Intervention: repair the current active reference module at the duplicate-resolution boundary and execute semantic/concurrency regressions.  
Result: both known idempotency counterexamples are repaired in the committed component under container execution.  
Uncertainty: target Ubuntu host and complete H-WP-02 suite remain unverified.  
Next falsifier: any target-host run that produces duplicate commit, accepts changed semantic retry, mutates state on rejected conflict, regresses crash/snapshot/tamper behavior, or reveals another non-atomic retry path.
