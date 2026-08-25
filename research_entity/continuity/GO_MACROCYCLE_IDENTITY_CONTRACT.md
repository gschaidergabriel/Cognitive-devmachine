# GO macrocycle identity contract

Status: engineering coordination contract. This file does not replace owner product directives.

## Problem

The `go` law allows exactly one bounded unusual experiment per **user-triggered macrocycle**, shared across any parallel organs spawned for that same trigger. Repository history can contain many independent `go` triggers at the same wall-clock time. `date`, `trigger`, `organ`, branch-name timestamps, source SHA, PR number, or commit time are therefore **not sufficient macrocycle identity**.

Without an explicit shared identifier, two receipts cannot safely be adjudicated as belonging to the same user-triggered `go`.

## Required identity

Before spawning parallel organs for a new `go`, the orchestration layer SHOULD mint one opaque `macrocycle_id` and propagate the exact same value to every organ in that macrocycle.

New `go` receipts SHOULD contain:

```json
{
  "trigger": "go",
  "macrocycle_id": "<opaque orchestrator-issued id>",
  "unusual_experiment": {
    "count_for_this_macrocycle": 0,
    "id": null
  }
}
```

If an unusual experiment is consumed, exactly one receipt/claim inside that `macrocycle_id` may set `count_for_this_macrocycle` to `1`; all other work in the same macrocycle must be ordinary regression, replication, source review, or fusion.

## Fail-closed adjudication law

- Compare unusual-experiment claims **only when `macrocycle_id` matches exactly**.
- Never infer a shared macrocycle from equal timestamps, equal `trigger`, equal organ/model name, similar branch prefixes, nearby commits, or same-day receipts.
- Receipts without `macrocycle_id` are `LEGACY_MACROCYCLE_ID_UNRESOLVED` for cross-receipt slot adjudication. Preserve their measured observations and local classifications; do not rewrite one because another no-ID receipt also says `count=1`.
- If a worker did not receive an upstream `macrocycle_id`, it must not invent one after the fact to claim cross-organ uniqueness. It may report its own local intervention count and mark global uniqueness `UNRESOLVED_NO_UPSTREAM_ID`.
- A correction that changes historical experiment classification solely by grouping no-ID receipts is invalid coordination evidence and must be superseded explicitly rather than silently erased.

## Why the ID must be upstream

A worker cannot distinguish concurrent separate user `go` triggers from parallel organs of one `go` using GitHub timing alone. A locally generated UUID would separate true siblings instead of joining them. Therefore the shared identity must originate at, or be propagated by, the trigger/orchestration boundary.

## Ordinary repeatable dispatch identity is a different axis

`macrocycle_id` MUST NOT be used to make a reusable ordinary infrastructure probe unique. Multiple organs and multiple independent `go` macrocycles can request the same still-pending measurement; creating one trigger per macrocycle causes issue/workflow fan-out without adding information.

Before creating any repeatable ordinary Issue/workflow/runtime trigger, every `go` organ MUST follow:

`research_entity/continuity/ORDINARY_DISPATCH_IDEMPOTENCY_PROTOCOL.md`

In particular:

- read the canonical dispatch spec;
- derive its current semantic `dispatch_key` from dispatch class + explicit retry generation;
- atomically CREATE-ONLY the canonical claim **before** creating the external trigger;
- if the claim already exists, create **zero** additional issues/workflow triggers for that dispatch generation;
- never include `go`, macrocycle id, timestamp, issue/run id, unrelated `main` movement, or organ identity in the reusable probe identity;
- never increment retry generation merely because another `go` arrived;
- preserve pending/queued as pending/queued rather than manufacturing another probe.

This law is independent of the unusual-experiment lease. Ordinary dispatch singleton coordination does not consume or create an unusual-experiment slot.

## Evidence boundary

This contract fixes bookkeeping/causal identity only. It creates no product PASS, runtime PASS, provider admission, training authorization, or model-quality evidence.
