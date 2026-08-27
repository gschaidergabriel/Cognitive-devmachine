# Live Re-entry Delivery Atomicity Protocol

**Status:** bounded coordination repair derived from `LIVE_FUSION_HYPOFUSION_WORKER_REENTRY_DIRECTIVE.md`  
**Scope:** research/worker feedback delivery only; no ClayVerse truth, state, effect, identity, runtime or acceptance authority.

## Problem

The first live worker re-entry exposed a real coordination race: several temporary organs independently reconstructed the same `github:pull/611` route and posted semantically duplicate GitHub comments before all of them observed the already-persisted delivery state.

The existing manifest deduplicates the **meaning** after the fact, but `refresh -> see pending -> post external comment -> persist delivered` is not atomic. Two workers can both pass the same stale preflight and produce duplicate external side effects.

This protocol closes that gap without creating a second bus or authority.

## Invariants

1. One semantic route has one deterministic `route_id`.
2. External delivery is forbidden until one worker owns a canonical delivery claim.
3. Claim acquisition is compare-and-swap (CAS) against the current canonical manifest blob/state; two workers observing the same prior state cannot both acquire the claim.
4. A delivered target marker is idempotency evidence for recovery; a worker must search for it before retrying an expired/uncertain claim.
5. Delivery, acknowledgement, plan revalidation, use, local effect and causal credit remain distinct states.
6. A duplicate/superseded delivery never receives causal credit and must not create another work obligation.
7. Unknown claim/delivery outcome stays explicit `UNKNOWN_DELIVERY`; never guess success.

## Deterministic route identity

For each routed envelope compute a stable digest over canonical JSON containing at least:

- `run_id`;
- `receiver`;
- `message_kind`;
- `decision`;
- canonical summary/revalidation payload digest.

Represent it as `route_id = sha256(canonical_route_json)`.

The external message must carry a compact marker such as:

`LIVE_REENTRY_ROUTE_ID:<route_id>`

The marker is coordination metadata only; it grants no semantic authority.

## Claim-before-effect state machine

Allowed route delivery states:

`PENDING -> CLAIMED -> DELIVERED_ACK_PENDING -> ACKED/PLAN_REVALIDATED/...`

Exceptional states:

`CLAIMED -> UNKNOWN_DELIVERY` when the worker cannot determine whether the external write happened;

`CLAIMED|UNKNOWN_DELIVERY -> DELIVERED_ACK_PENDING` only after the exact route marker is observed on the intended receiver;

`CLAIMED|UNKNOWN_DELIVERY -> PENDING` only after lease expiry **and** a target scan proves the route marker absent.

### Claim acquisition

Before posting any external worker feedback:

1. refresh current canonical `main` and the exact current `WORKER_REENTRY_MANIFEST.json` blob;
2. if the route is already `CLAIMED`, `DELIVERED_*`, `ACKED` or later, do not post;
3. write a `delivery_claim` containing `route_id`, `claim_id`, organ provenance, claim time and bounded expiry;
4. perform that manifest write using the current blob SHA as a CAS precondition;
5. if the write conflicts or the canonical claim after refresh is not yours, stop with `DUPLICATE_CLAIM_REJECTED` and do not post;
6. only the worker that re-reads its own canonical claim may perform the external delivery.

GitHub Contents blob-SHA preconditions are the current repository mechanism for serialization. A future transport may replace the mechanism, but it must preserve the same single-winner contract.

### Delivery finalization

After an external comment/message succeeds:

1. record the external message/comment identity and exact `route_id` marker;
2. CAS-update the same route to `DELIVERED_ACK_PENDING`;
3. if finalization is uncertain, classify `UNKNOWN_DELIVERY` rather than reposting;
4. recovery scans the intended target for the exact route marker before any retry.

A successful external API response followed by a failed manifest update is therefore recoverable without blind duplicate delivery.

## Lease recovery

A claim may be reclaimed only when all are true:

- its expiry is exceeded under the canonical coordination clock contract;
- no later canonical owner/claim supersedes it;
- target inspection finds no exact `route_id` marker;
- reclaim is itself acquired by CAS before delivery.

If target inspection is unavailable, remain `UNKNOWN_DELIVERY`; do not trade uncertainty for duplicate effects.

## Live Hypofusion requirement

Duplicate delivery or competing claims automatically trigger Live Hypofusion.

Record:

- whether the duplicates share one semantic `route_id`;
- whether any receiver action occurred between deliveries;
- whether duplicate comments created divergent work plans;
- the canonical retained delivery identity;
- anti-entropy action taken.

Do not delete historical evidence merely to make the timeline look clean. Mark later duplicates as superseded/no-new-action.

## Bounded discriminator

A deterministic two-worker CAS model has the following required outcome:

- both workers observe the same `PENDING` version;
- worker A wins the CAS claim;
- worker B's CAS against the stale version fails;
- only A is authorized to deliver;
- if A crashes after external delivery but before finalization, recovery finds the exact route marker and finalizes the same delivery instead of reposting.

This is a coordination-mechanism obligation, not ClayVerse product runtime evidence.

## Product boundary

This protocol must never become:

- a second UnifiedDB/state authority;
- a second EffectGate path;
- a second Clay identity;
- a truth-by-consensus mechanism;
- a reason to infer product/runtime PASS.

Its only purpose is to make live research/worker re-entry less duplicative and more causally auditable while the canonical ClayVerse product path remains unchanged.
