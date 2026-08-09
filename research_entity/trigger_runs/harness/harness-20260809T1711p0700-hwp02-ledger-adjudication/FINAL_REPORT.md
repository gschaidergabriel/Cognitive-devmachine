# Harness H-WP-02 — State-Ledger Adjudication

Run: `harness-20260809T1711p0700-hwp02-ledger-adjudication`

## Result

Two live H-WP-02 state-ledger implementations were found to encode incompatible identity contracts. A deterministic source-contract differential probe therefore adjudicates **NEITHER_AS_IS**.

### Executable findings

- Changed payload with the same `event_id` and idempotency key: `research_entity/harness/reference_state_ledger.py` accepts 10,000/10,000 tested mutations as `IDEMPOTENT_REPLAY` under its current precheck; `research_entity/harness/reference/state_ledger.py` distinguishes all 10,000/10,000 through its payload/provenance-bound fingerprint.
- Same materialized state with different history/version basis: the first implementation preserves the same content root in 2,000/2,000 matched cases; the second produces a different `semantic_state_hash` in 2,000/2,000 because global/domain epochs and semantic history are included.

### Adjudication

Do not select either implementation unchanged. Split state identity into an explicit lattice:

1. `StateContentHash`
2. `SemanticEventHash`
3. `SemanticHistoryHash`
4. `VersionedStateRoot`
5. `ExecutionChainHash`
6. `TraceRootHash`

Retain the first implementation's history-independent content identity, explicit recovery provenance and tamper verification. Retain the second implementation's semantic/execution decomposition, domain epochs, lifecycle state, typed collection canonicalization and stronger idempotency fingerprint.

### Boundaries

This is local synthetic/source-contract evidence. It is not live Frank evidence, not target-host Ubuntu evidence, does not PASS H1, and does not advance the staged program. BASE ClayCode release remains the active gate.

### Next discriminating work

Implement one merged candidate contract with the identity lattice and strict idempotency fingerprint, then run both original implementations and the merged candidate over the same replay/crash/concurrency/tamper corpus. Once BASE permits H1 integration, bind those identities to captured frankv0.1 transitions, Run ClayGraph deltas and effect dependency envelopes.

## Sync state

The main repository changed concurrently during two safe write attempts. To avoid overwriting peer work, this run was preserved on isolated branch `chatgpt/harness-hwp02-adjudication-20260809-1711` from exact parent `5eba088131133a59b52236fc5de23ca75be88f1c`. Main integration remains pending; no canonical promotion is claimed.
