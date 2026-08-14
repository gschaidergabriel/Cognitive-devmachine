# Harness Run — H-WP-02 Crash / Restart Atomicity

Run: `harness_20260809T1703p0700_wp02_crash_recovery_chatgpt_secondary`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Target: H1 Reference Harness state/event ledger

## Why this continuation was selected

The live Harness workspace still had exactly one active claim: `H-WP-02-STATE-LEDGER` by this worker. The previous run had already implemented deterministic semantic state hashing, epoch CAS, idempotency, provenance-bound event chaining, explicit epistemic states and snapshot recovery, but process-crash behavior remained an explicit open test. Starting a second package would have left the claimed package partially falsified at a high-risk boundary.

## Executable delta

Added:

- `research_entity/harness/reference_state_ledger_crash_probe.py`
- `tests/test_reference_state_ledger_crash_recovery.py`
- `research_entity/harness/H_WP_02_CRASH_RECOVERY_EXECUTION_RECEIPT.json`

The crash probe opens the ledger database in WAL mode with `synchronous=FULL`, begins an immediate transaction, crosses one of three write boundaries, and terminates the process through `os._exit(137)` without COMMIT or Python cleanup.

Tested boundaries:

1. `AFTER_STATE` — canonical state row mutated but no event/epoch publication;
2. `AFTER_EVENT` — state + event receipt inserted but no epoch publication;
3. `AFTER_EPOCH` — state + event + epoch rows written inside the still-uncommitted transaction.

## Execution result

Combined original + crash suite:

`11 passed in 5.27s`

At all three abrupt-death points after restart:

- epoch remained at the last committed value;
- semantic root hash remained unchanged;
- mutated state did not leak;
- synthetic crash event did not survive;
- synthetic next epoch did not survive;
- full ledger verification returned PASS.

A recovery retry after the crash then committed epoch 2 successfully. Repeating the same retry returned `IDEMPOTENT_REPLAY` and did not increment the epoch again.

## Interpretation

The tested SQLite transaction boundary provides atomic rollback for the H1 reference-ledger state/event/epoch bundle under abrupt process termination in the local Linux execution surface.

This closes one important failure mode from the previous run: a reader should not see a mixed state in which semantic state changed but the authoritative epoch/receipt did not, or vice versa, after this class of process crash.

It does **not** yet prove:

- physical power-loss durability;
- filesystem/controller durability on Andreas' Ubuntu developer host;
- live `frankv0.1` schema/behavior equivalence;
- distributed/networked effect atomicity;
- ClayGraph publication atomicity;
- H1 release readiness.

## Cross-branch feedback

### Harness

`H-WP-02` advances but remains ACTIVE. Crash/retry semantics are now executable evidence rather than an untested requirement.

### UnifiedDB

The current `state_epochs` / `semantic_transactions` / snapshot family is compatible in principle with atomic SQLite publication, but a direct mapping/differential test against current `frankv0.1` remains mandatory. No schema migration is promoted from this result alone.

### ClayGraph

Dynamic Run ClayGraph publication should bind to committed epochs. A crash inside an uncommitted ledger transition should produce no published semantic-state graph delta; crash/recovery provenance may be recorded separately.

### GWT / Emergenz / Hyperposition

No scientific claim changes. Future replay/intervention measurements should consume committed epochs only so partial state cannot masquerade as a causal transition.

### ClayCode

No language counterexample was found. H2 remains blocked on the current BASE ClayCode release.

### FRANK authority boundary

Frank did not change its own Harness. This Research Entity worker independently implemented and tested the Harness research component under the proposal-only self-observation boundary.

## Concurrency receipt

The first GitHub write attempt returned a CAS 409 because the repository advanced concurrently. The worker reread the current Harness workspace, confirmed no new worker had taken or changed H-WP-02, and then committed on the fresh repository head. No blind overwrite was used.

## Next highest-information H-WP-02 work

1. Build a structural/differential adapter against the current `frankv0.1` `state_epochs`, `semantic_transactions`, transaction ops and snapshots.
2. Run the crash suite on the actual Ubuntu developer host, including true process kill and filesystem/restart scenarios where safely feasible.
3. Couple committed pre/post semantic hashes into dynamic Run ClayGraph/replay receipts while preserving semantic-state identity separately from provenance/event-chain identity.

## Release state

- `H-WP-02-STATE-LEDGER`: ACTIVE / materially advanced, not COMPLETE.
- `H1_REFERENCE_HARNESS`: NOT PASS; staged program still blocks H1 on `BASE_CLAYCODE_RELEASE`.
- Paid/final model training: not started and not authorized by this run.
