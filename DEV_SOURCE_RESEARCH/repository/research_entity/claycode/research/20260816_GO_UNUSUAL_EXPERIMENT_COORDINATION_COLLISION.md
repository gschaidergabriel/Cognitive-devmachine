# GO 2026-08-16 — unusual-experiment coordination collision

## Status

NEGATIVE_RESULT / COORDINATION_INVARIANT_NOT_PROVEN

Active program: `CLAYVERSE_CLAY_MACHINE_ONLY`.
Trigger: exact `go`.
This record adds no experiment and changes no product bytes.

## Observed anchors

One temporary Clay worker executed and durably recorded the bounded unusual experiment `CYCLIC_SIBLING_QUARANTINE` while reviewing PR #596. Its local result was PASS: `A -> Pair<B,C>`, `B -> A`, `C -> Int` canonicalized to `Pair<<TYPE_ERROR>, Int>` with exactly one alias-cycle diagnostic and the healthy sibling retained.

After canonical promotion and re-entry, the live `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` instead reports:

- `current_go_unusual_experiment.count = 1`
- `name = RECURSION_LIMIT_PINCH`
- instruction: the unusual-experiment slot is consumed; do not execute another.

Therefore the shared macro-cycle cannot honestly claim that exactly one unusual experiment occurred globally. At least two distinct unusual-experiment receipts are visible across concurrent workers unless a future coordinator proves they belong to distinct macro-cycle identities.

## Counterevidence / interpretation

This is not a TypeRef semantic failure. It is a concurrency/coordination failure in enforcing a cardinality invariant across parallel Clay workers. A per-worker interpretation of “exactly one” is weaker than the project protocol, which describes the `go` macro-cycle as the unit.

No second unusual experiment is executed by this record.

## Required repair

Before future parallel `go` workers execute an unusual experiment, allocate the slot through a shared CAS/lease keyed by canonical macro-cycle id. Minimal state should bind:

- macro_cycle_id
- holder / provenance
- experiment_name
- claimed_at revision
- state: RESERVED | EXECUTED | RELEASED | INVALIDATED
- evidence/receipt pointer after execution

Acquisition must fail closed if a live reservation/execution already exists for that macro-cycle. Crash recovery may release only an unexecuted reservation under an explicit stale-lease rule; an executed slot is immutable for the cycle.

## Claim boundary

- Does not invalidate PR #596 or #598.
- Does not prove either unusual experiment was semantically wrong.
- Does prove that the global `exactly one` cardinality claim is currently ambiguous / not enforceably serialized under concurrent workers.
- No whole Clay Machine completion claim.