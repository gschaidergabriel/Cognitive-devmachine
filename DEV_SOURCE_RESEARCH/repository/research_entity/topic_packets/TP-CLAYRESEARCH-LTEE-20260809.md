# Topic Packet — Recurrent Decision Freshness and Effect Commit

**packet_id:** TP-CLAYRESEARCH-LTEE-20260809  
**status:** OPEN / NOT PROMOTED  
**origin:** `clayresearch-20260809T1655p0700-loop-txn-effect-envelope`

## Problem

FRANK loop-of-loops research, ClayCode recurrence, UnifiedDB transaction isolation and Safe-Effect capability boundaries meet at one concrete question: **may an effect decision formed at one state/authority basis still commit after recurrent delay?**

## Current evidence

Exact synthetic discriminator:

- 16 exhaustive schedules: retained permit 14 unsafe; global epoch 0 unsafe/1 false abort; dependency envelope 0 unsafe/0 false abort.
- 100,000 fuzz cases / 350,618 attempts: retained permit 143,298 unsafe; global epoch 0 unsafe/48,090 false abort; dependency envelope 0 unsafe/0 false abort.

This is not live FRANK evidence.

## Candidate mechanism

At effect commit, validate:

- exact effect-critical decision dependency versions;
- current capability identity/epoch/validity;
- resource identity and relevant budget;
- protected information-flow/declassification constraints where applicable;
- idempotency/recovery identity.

Do not invalidate solely because unrelated state changed when dependency closure is complete.

## Non-collapses

`semantic program != decision snapshot != authority grant != physical resource`

`recurrence != authority`

`GWT selection != authority`

`ClayGraph activation != authority`

## Cross-branch implications

- ClayCode: runtime ABI/compiler dependency metadata before new syntax.
- UnifiedDB: explicit semantic/capability epochs and retry receipts.
- Harness: compare whole-ledger CAS vs scoped versions on frozen Ubuntu H1 replay.
- GWT/Hyperposition: preserve decision/dependency identity through recurrence/alternatives without authority promotion.
- Safe-Effect: count false-abort/recompute cost as utility evidence; retain child-code/FFI closure as an open falsifier.

## Concurrent convergence

A same-time ClayCode DB transaction/broker run reached a compatible stdlib/FFI/runtime-first conclusion and explicitly linked this envelope work. Treat this as shared-ancestry convergence, not independent replication.

## Next discriminator

H1 Ubuntu replay with unrelated churn, critical-state change, capability revoke/regrant, queue delay, crash/restart and generated child-code effects; then H2 ClayCode differential reproduction.
