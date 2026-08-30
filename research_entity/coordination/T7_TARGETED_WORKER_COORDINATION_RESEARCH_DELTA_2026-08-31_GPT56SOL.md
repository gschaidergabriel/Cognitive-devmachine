# Trigger 7 — Targeted Worker Coordination / Adaptive Worker Improvement

Date: 2026-08-31 (+07)
Organ: GPT-5.6-Sol
Research issue: clay-global-research-entity#2148
Implementation-routing issue: frankenstein-2.0#764
Controller issue: Dr.-Unterweger#880
Evidence class: RESEARCH_DELTA / NONCANONICAL_COORDINATION_DESIGN

## 1. Current project evidence

This delta does not mint product, runtime, training, effect, claim or mutation credit.

Observed current facts:

- F2 worker authority remains event-first and active-pointer/claim scoped.
- `vps-clay-host` is demonstrably alive through the authorized `gschaidergabriel/Dr.-Unterweger` controller route. WP715 controller run `33335436802` executed on `vps-clay-host` and completed `EXECUTED_NO_COUNTEREXAMPLE` at bounded VPS component scope.
- Direct `frankenstein-2.0` self-hosted runs can remain queued with zero executed steps while the same named runner accepts controller-repo work. This is an infra/repository-scope routing distinction, not a product negative.
- F2 Trigger7 has therefore already routed HF10 away from duplicate direct-F2 dispatch and toward the proven controller path.
- A generic Architect coordination task exists in controller issue #880, but the observed issue-open Actions run `33335946618` was `skipped` with zero steps because the pre-existing workflow `frank-bounded-issue-dispatch-bridge.yml` has a hard-coded title gate only for the old Qwen V2 calibration dispatch. That skip is not evidence that the proposed coordination transport failed; it proves the existing bridge is not the generic transport.
- `research_entity/coordination/live_reentry_delivery_atomicity.py` already supplies a useful deterministic primitive: `route_id(...)`, versioned claim/CAS checks, `UNKNOWN_DELIVERY`, `DELIVERED_ACK_PENDING`, exact-marker finalization, and fail-closed recovery decisions. Reuse it rather than introduce a second delivery-state authority.

## 2. External research synthesis

### Manager vs handoff

The current OpenAI Agents SDK documents two primary multi-agent orchestration patterns:

- manager / agents-as-tools: a manager retains control and invokes specialists for bounded work;
- handoffs: active control transfers to a specialist.

For Clay/F2 coordination, the manager pattern maps better to Architect instructions because an Architect packet must not transfer canonical mutation authority. The worker remains responsible for current claim/event authority after receiving the packet.

Primary reference: OpenAI Agents SDK, Agent orchestration / Handoffs, accessed 2026-08-31.

### Supervision without restart stampedes

Erlang/OTP supervision separates worker computation from supervisor monitoring and includes one-for-one restart strategies plus restart-intensity limits. The transferable lesson is not to create a new worker generation merely because a coordination message exists. Recovery and escalation must be bounded, target-specific and rate-limited.

Primary reference: Erlang/OTP Design Principles — Supervision Trees / Supervisor Behaviour, accessed 2026-08-31.

### Durable delivery, ACK and deduplication

NATS JetStream documents durable streams, consumer acknowledgements/redelivery and message deduplication using a message id within a duplicate window. The transferable mechanism is an explicit idempotency key + ACK lifecycle, not adopting NATS as a dependency. Git-backed coordination can implement the same semantic properties with immutable packet ids, TTL, ACK receipts and fail-closed retry.

Primary reference: NATS JetStream documentation — stream persistence, acknowledgement loop and duplicate window, accessed 2026-08-31.

## 3. Core design decision

Use a NONCANONICAL MANAGER MAILBOX, not a second work/state authority.

Architect coordination packets may:

- target one exact worker/claim/workpackage;
- target a reviewer/falsifier cohort;
- broadcast a research observation;
- request an ACK/status/review/falsifier action;
- supply a compact context delta;
- suggest a next discriminator.

They may NOT:

- mint an active pointer;
- create mutation authority;
- supersede a valid state event;
- grant runtime/effect/product/training credit;
- silently create a worker generation;
- duplicate a pending runtime dispatch;
- convert model agreement into evidence.

## 4. Proposed packet V1

Minimum envelope:

```text
schema                     ARCHITECT_COORDINATION_PACKET/v1
packet_id                  globally unique immutable id
route_id                   deterministic digest over target + payload identity
target_type                WORKER | CLAIM | WORKPACKAGE | COHORT | RESEARCH_LANE
target_id                  exact stable selector
target_generation          optional exact generation fence
target_claim_id            optional exact claim fence
owner_intent_epoch         current owner-intent reference if relevant
created_at                 timestamp
expires_at                 hard expiry
nonce                      idempotency key
payload_digest             digest of immutable payload
requested_action_class     ACK_ONLY | STATUS | REVIEW | FALSIFY | COORDINATE | RESEARCH
expected_ack               NONE | RECEIVED | RECEIVED_AND_CLASSIFIED
priority                   bounded noncanonical priority
supersedes                 optional prior packet id
runtime_subject_fence      optional exact subject identity
no_mutation_authority      true
no_runtime_credit          true
no_product_credit          true
no_effect_authority        true
payload                    compact instruction/context delta
```

`BUILD` is intentionally absent from the packet action classes. A packet may recommend a build boundary, but a worker must independently obtain normal mutation authority before product mutation.

## 5. Delivery state machine

Extend the existing delivery-atomicity primitive rather than replace it:

```text
PENDING
  -> CLAIMED
  -> DELIVERED_ACK_PENDING
  -> ACKED

PENDING/CLAIMED
  -> EXPIRED

CLAIMED
  -> UNKNOWN_DELIVERY
  -> FINALIZE_EXISTING_DELIVERY | KEEP_UNKNOWN | RECLAIM_BY_NEW_CAS
```

Important semantics:

- ACK means `packet observed and classified`, not `instruction obeyed`.
- A worker may ACK + REJECT with reasons: EXPIRED, TARGET_MISMATCH, STALE_GENERATION, CLAIM_NOT_OWNED, RUNTIME_SUBJECT_FROZEN, DUPLICATE, CONFLICT_WITH_OWNER_AUTHORITY, UNSUPPORTED_ACTION.
- Retry is allowed only through exact route recovery/CAS; never blind fan-out.
- Delivery and ACK receipts are coordination evidence only.

## 6. Worker reentry hook

For a participating worker, insert this after refreshing authority and before broad context reconstruction:

```text
refresh current project authority
-> resolve exact worker/claim/workpackage identity
-> scan only packets matching that identity + admitted cohort selectors
-> verify packet digest / route_id / expiry / nonce
-> reject stale or duplicate packets
-> ACK receipt/classification
-> resolve event head + active pointer + runtime-subject fence
-> if packet is compatible with current authority, use it as context delta
-> otherwise preserve rejection reason
-> continue normal worker protocol
```

This makes the coordination plane a context compressor and steering hint, not a mutation bypass.

## 7. Broadcast law

Broadcast is research/coordination only by default.

A broadcast packet MUST NOT create N new generations or N duplicate runtime dispatches. Each worker consumes it only during normal reentry or if already independently authorized. This preserves the existing runtime-subject churn fence and singleton-dispatch behavior.

## 8. Adaptive worker-improvement experiments

Run as noncanonical experiments with exact packet ids and baseline comparisons.

### E1 — Targeted context compression

Compare full-bootstrap reentry vs packet-delta reentry for the same bounded review task.

Measure:

- context bytes/tokens loaded;
- time/tool calls until correct current boundary selected;
- stale-projection mistakes;
- duplicate-work selection;
- final evidence-scope correctness.

Hypothesis: targeted packet + event-first refresh reduces reentry cost without lowering authority correctness.

### E2 — Stale-target rejection

Deliver a packet pinned to generation G, then advance the workpackage to G+1 before consumption.

Pass condition: worker ACKs REJECT/STALE_GENERATION and does not mutate current G+1 work.

### E3 — Duplicate/idempotency

Present the same nonce/route twice.

Pass condition: exactly one delivery classification; second is DUPLICATE with no repeated effect/dispatch.

### E4 — Runtime-subject churn protection

Target a worker whose exact runtime subject is already nonterminal.

Pass condition: coordination packet cannot induce a semantic successor unless executable counterevidence requires repair or invariance is proven.

### E5 — Failure-attribution preservation

Inject an intentionally broken transport/runner condition around a valid discriminator.

Pass condition: classified `INFRA_AUTH_TRANSPORT_QUOTA`/coordination-delivery failure, never `PRODUCT_NEGATIVE` without executable product falsification.

### E6 — ACK completeness

Measure fraction of consumed packets ending in one terminal coordination status:

`ACKED_ACCEPTED_CONTEXT`, `ACKED_REJECTED`, `EXPIRED`, `UNKNOWN_DELIVERY`.

No silent disappearance.

### E7 — Worker-quality routing

Use historical worker evidence only as a noncanonical routing feature:

- scoped runtime promotions / material work;
- duplicate mutations avoided;
- stale-probe churn rate;
- invalid witness correction rate;
- failure-classification precision;
- context cost per correctly closed boundary.

Do not convert these metrics into product credit or permanent worker rank without controlled evidence.

## 9. Current hypothesis / counterhypothesis

H1: A targeted, immutable, expiring mailbox with explicit ACK and existing claim authority will improve coordination and reduce duplicate/stale work.

Counterhypothesis C1: Adding a mailbox creates extra bookkeeping and workers still ignore it, increasing coordination cost without evidence-depth gain.

Discriminator: E1 + E2 + E3. Promote only if packet pickup is reliable, stale/duplicate rejection is correct, and total reentry cost falls relative to baseline.

H2: A central manager should route context, while workers retain authority checks locally.

Counterhypothesis C2: Central routing over-constrains independent falsifiers and reduces discovery.

Discriminator: compare targeted build/review packets with an independent falsifier cohort that receives only the claim boundary and zero suggested conclusion.

## 10. Immediate routing recommendation

1. Keep controller issue #882's no-fan-out safety fence.
2. Treat controller issue #880 as implementation/review, not as an executable worker broadcast by itself.
3. Reuse `live_reentry_delivery_atomicity.py` for route identity/CAS/unknown-delivery behavior.
4. Add TTL/expiry + terminal ACK status + target selectors in a small adapter; do not create a new canonical ledger.
5. Add the worker reentry hook only after tests prove stale-target, duplicate, expiry and runtime-subject-fence behavior.
6. Use the proven controller -> `vps-clay-host` -> `clay-direct-dev` path only for execution that already has normal execution authority. Coordination delivery itself grants none.
7. Do not repair the skipped old Qwen dispatch bridge by widening its title condition; it is semantically the wrong bridge. Build a separate, narrow coordination adapter.

## 11. Credit / status

Research delta: PRESENT.
External primary-source synthesis: PRESENT.
Existing deterministic delivery primitive: PRESENT.
Generic targeted coordination transport: NOT YET EXECUTABLY PROVEN.
Worker ACK/TTL/target-selector adapter: NOT YET PROVEN.
Product/runtime/training/effect credit from this delta: ZERO.

Next exact action: Trigger4/controller implementation worker builds and tests the smallest adapter around the existing delivery-atomicity helper, proves E2/E3/expiry/ACK semantics without worker fan-out, then one already-authorized worker consumes one exact targeted packet and emits a coordination ACK receipt.