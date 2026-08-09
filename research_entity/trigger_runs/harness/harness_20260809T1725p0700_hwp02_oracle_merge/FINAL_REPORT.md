# Harness H-WP-02 Oracle Merge Run

Run: `harness_20260809T1725p0700_hwp02_oracle_merge`  
Actor: `chatgpt-secondary`  
Work package: `H-WP-02-STATE-LEDGER`  
Status: **EXECUTABLE CANDIDATE BUILT / LOCAL TESTS PASS / NO H1 PROMOTION**

## Why this run

The current H-WP-02 lineage adjudication established two incompatible but complementary state-ledger implementations. Lineage A preserved history-independent semantic current-state identity plus verify/snapshot/restore; Lineage B preserved typed set/order canonicalization, domain epochs, stronger semantic idempotency and explicit execution/trace separation. The adjudicated next step was one merged candidate rather than selecting either lineage wholesale.

During this run the live Harness mesh also landed `e77de62e5aa784f90fdee1541ac8f2449478cb0b`, independently hardening A-lineage semantic idempotency under `BEGIN IMMEDIATE`. That delta was incorporated as an invariant rather than duplicated as a competing fix.

## Built artifacts

- `research_entity/harness/reference/oracle_state_ledger.py`
- `research_entity/harness/tests/test_oracle_state_ledger.py`
- `INTERCONNECT_MANIFEST.json`
- `EXECUTION_RECEIPT.json`
- `BRANCH_FEEDBACK_MANIFEST.json`

The candidate separates three identities:

1. `semantic_state_hash` — history-independent canonical current semantic content;
2. `state_version_hash` — global/domain epochs plus semantic event-chain/version identity;
3. `trace_root_hash` — version identity bound to execution-attempt chain.

It also implements typed `$kind=set` / `$kind=ordered` canonicalization, global CAS plus domain epochs, request-fingerprint semantic idempotency under the write lock, append-only receipts, replay verification, atomic rollback fault injection and exact event-log snapshot restore.

## Executed tests

Local deterministic ChatGPT Python sandbox execution:

- 9/9 regression tests PASS;
- two-writer same-request race => exactly one `COMMITTED` plus one `IDEMPOTENT_REPLAY`, one event row;
- semantic same-state/different-history => equal semantic hash, unequal version hash;
- changed semantic payload under same idempotency key => `IdempotencyConflict`;
- stale epoch => fail closed;
- injected fault after event insertion => full rollback;
- exact replay => semantic/version/trace roots equal;
- exact snapshot restore => roots equal;
- tampered exported snapshot => rejected;
- stress: 5,000 typed-set permutations, 5,000 ordered mutations, 1,000 events => PASS.

Stress roots:

- semantic: `30dc67a93c7dd35688c908dac5a71b3fe2d63f99d5f84d0ac021162038aec24a`
- version: `b5f53def94718ca73b6abc08d2ddd328ce2ee2cf637d517ad4aead655c35e3fc`
- trace: `5381096c15158dfa8b08e03e1780e15b6df0dd9478f4142b6e1b8f013035ed38`

## Interpretation

The executable result supports the adjudicated layered-identity design: semantic equivalence, state/version equivalence and execution-trace equivalence are different questions and should not be forced into one hash. Transactional semantic idempotency is compatible with this separation: writer/timestamp/attempt metadata may change across retries while the semantic request fingerprint remains fixed.

This is not independent scientific replication of upstream FRANK/ClayCode assumptions. It is Harness execution of a merged oracle derived from shared project evidence.

## Negative results / unresolved gates

- No Ubuntu developer-host execution in this run.
- No live `frankv0.1` captured golden-corpus differential.
- No exact crash-process/power-loss matrix on the target host.
- No dynamic Run ClayGraph binding test yet.
- No Reference Harness release gate change.
- No LoRA/training authorization change.
- Candidate does not supersede A or B until target-host differential evidence and adjudication.

## Next highest-information test

On the Ubuntu developer host, execute the committed oracle candidate plus regressions against captured `frankv0.1` transaction fixtures. Differentially compare hardened A, typed/domain-epoch B and merged candidate for:

1. same final semantic state under different transaction grouping;
2. set/order canonicalization;
3. global and domain/read-set stale writers;
4. idempotency payload collisions and concurrent retries;
5. crash between state/event/version publication;
6. checkpoint restore and continuation;
7. dynamic Run ClayGraph bindings;
8. schedule/retry/recurrence execution receipts.

Only those target-host results can justify freezing the H-WP-02 oracle contract.
