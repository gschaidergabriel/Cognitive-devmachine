# FranKenstein Harness / ChatGPT Bridge Hardening Concept

Status: DESIGN ONLY / NO SWARM IMPLEMENTATION YET
Date: 2026-09-12
Branch: chatgpt/harness-bridge-hardening-concept-20260912

## 1. Scope

Stabilize the terminal -> GRID10 -> ChatGPT organ -> GRID10 path before adding any new swarm fan-out. Preserve the existing canonical cognitive/state authority and the existing Local Bridge. Do not create a side brain, duplicate watcher, duplicate turn loop, duplicate browser authority, or second production state path.

## 2. Evidence-driven defects found

### D1 Transport PASS can mask semantic failure
A Local Bridge exec receipt can be PASS/exit 0 while stdout reports MISSING/PY_COMPILE_FAIL. Therefore CLAY_LOCAL_RECEIPT/v1 status is transport/process status only and must never be treated as semantic acceptance of the audited subject.

Required fix: typed result layers:
- transport_status
- process_exit
- semantic_status
- acceptance_scope
- evidence/readback

### D2 stern.chatgpt_senden top-level ok is too weak
The legacy wrapper can return top-level ok=True after the loop even when individual runs failed. Exact adapters must not use only top-level ok as dispatch truth.

Required fix: semantic success predicate over each requested coordinator send, with sent-count/URL attribution/readback.

### D3 Exact backend pending state is volatile and cleared too early
ExactChatGPTBackend stores one in-memory `_pending` value and clears it before harvest completes. Timeout/browser failure can therefore create UNKNOWN_COMPLETION while the backend forgets the request locally.

Required fix: durable request journal and state machine:
PREPARED -> DISPATCHING -> DISPATCHED -> HARVESTING -> HARVESTED -> UPTAKEN
with terminal states FAILED / RECONCILE_REQUIRED / CANCELLED.
Never erase DISPATCHED identity until terminal reconciliation.

### D4 URL attribution is global-ledger-diff based
TargetedChatGPTHarness derives new URLs by diffing a shared `sent_urls_v2.txt` before/after snapshot. Concurrent senders can steal or mix attribution.

Required fix: request-scoped dispatch identity. Preferred order:
1. sender emits request_id/dispatch_id together with resulting URL atomically;
2. if sender cannot be changed yet, hold one dispatch lease around before/send/after ledger capture;
3. verify cardinality and timestamps; ambiguity => RECONCILE_REQUIRED, never guessed attribution.

### D5 Browser completion heuristic is UI-string fragile
Harvest currently uses rendered text plus strings such as `Stop answering` / `Worked for`. UI wording changes can generate false completion.

Required fix: multi-signal completion detector with explicit confidence and fail-closed ambiguity:
- result marker parse
- DOM generation-state signal where available
- stable text digest across N polls
- request URL identity
- timeout => UNKNOWN_COMPLETION, not FAILED unless product failure is proven.

## 3. Canonical state machine

One parent turn owns one coordinator dispatch.

TURN_PREPARED
  -> HOST_ADMITTED
  -> BRIDGE_LEASED
  -> DISPATCH_PREPARED
  -> DISPATCHED(request_id, dispatch_id, url_set)
  -> HARVESTING
  -> HARVESTED(response_digest, marker)
  -> GRID_UPTAKE
  -> CLOSED

Exceptional states:
- HOST_BLOCKED
- MAIN_ORGAN_UNAVAILABLE
- TRANSPORT_FAILED
- UNKNOWN_DELIVERY
- UNKNOWN_COMPLETION
- ATTRIBUTION_CONFLICT
- RECONCILE_REQUIRED

No state transition may be inferred only from shell exit 0 or a PASS string.

## 4. Collision model

Before any future swarm implementation, introduce the following ownership keys:

- canonical_turn_key = runtime_epoch_id + turn_event_id
- coordinator_key = canonical_turn_key + main_organ
- effect_key = machine_id + canonical subject + capability
- browser_dispatch_key = browser_profile + request_id
- worker_key = parent_turn + worker_id + scope_digest

Rules:
1. Exactly one coordinator lease per canonical turn.
2. Workers can fan out only after coordinator ownership is committed.
3. Worker mutation scopes must be disjoint or serialized by effect_key.
4. Same request_id with same payload digest is idempotent replay; same request_id with different digest is conflict.
5. Unknown delivery blocks blind replay until reconciliation proves no prior effect.
6. Workers never mint canonical state independently; all uptake goes through parent turn.
7. Existing Local Bridge machine_id+owner provenance remains mandatory.

## 5. Immune-system integration

The bridge/harness becomes an admitted organ behind a host-safety gate, not a bypass.

Pre-dispatch admission must read current telemetry and return a signed/hashed admission snapshot containing at least:
- timestamp/age
- machine_id/owner
- cpu_count/load1
- MemAvailable
- browser tab/process count if relevant
- active harness leases
- configured hard limits

Admission states:
GREEN -> execution allowed within budget
AMBER -> coordinator only / fan-out disabled
RED -> no new local execution
UNKNOWN/STALE -> fail closed

The admission snapshot id must be referenced by coordinator and every child worker/effect receipt. A worker cannot inherit an unlimited budget just because the parent was admitted.

## 6. Bridge hardening implementation order

B0 Observability only
- add semantic_status separate from transport status
- request/dispatch correlation envelope
- explicit UNKNOWN_* states

B1 Exactly-once dispatch core
- durable request journal
- coordinator lease
- CAS/idempotency by request_id + payload digest

B2 Robust targeted harvest
- persistent dispatched URL identities
- no clearing pending before terminal outcome
- reconciliation command for UNKNOWN_COMPLETION

B3 Immune-system binding
- telemetry admission snapshot
- budget token passed to coordinator/workers
- stale/red telemetry blocks fan-out

B4 End-to-end acceptance
- one real `frank --once` proves T1-T8
- inject controlled transport failure and verify no duplicate canonical turn / no duplicate dispatch
- restart terminal process between DISPATCHED and HARVESTED and prove reentry/reconciliation

Only after B0-B4 pass should new swarm logic be implemented.

## 7. Future swarm design boundary (NOT IMPLEMENTED IN THIS BRANCH)

Swarm will be proposal/execution fan-out under the single parent turn, not N independent agents sharing loose global state. Coordinator decides bounded tasks; scheduler allocates only disjoint scopes; immune system grants per-worker resource tokens; completion returns immutable worker receipts; parent performs deterministic merge/selection/uptake.

No worker starts without:
- parent_turn_id
- scope_digest
- lease/claim
- host admission token
- resource budget
- mutation boundary
- expiry/deadline

No worker may:
- call canonical turn recursively
- overwrite another worker's scope
- create a second DB/state authority
- silently become the owner-facing main organ
- replay an unknown-delivery effect

## 8. Promotion rule

This document is a design artifact only. Do not merge or implement swarm fan-out solely because this concept exists. Re-read current repo heads, live receipts, active claims/branches, and owner instruction immediately before implementation.
