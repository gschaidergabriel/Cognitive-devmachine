# TRIGGERWORT 4 — Deferred Causal Return / Retrieval + Voice Fusion Addendum

Status: CURRENT SOURCE-GROUNDED ARCHITECTURE CANDIDATE + REQUIRED DISCRIMINATORS
Date: 2026-08-28
Donor: `gschaidergabriel/frankenstein@5641dc6b2df6ebed1df246ee7533134324f6c427`
Source delta: `research_entity/frankenstein_architecture_ingest/ARCHITECTURE_DELTA_2026-08-28T1054Z_DEFERRED_CAUSAL_RETURN_FUSION_GPT56SOL.json`

## 1. Shared failure shape

Latest Triggerword-5 source cross-checks found a common causal-return problem across otherwise different subsystems:

- deferred retrieval relevance feedback can be attached through context/session-local ordering rather than one immutable retrieval origin;
- reactive Voice activation starts Realtime without a dedicated activation-event identity/generation and preserves stale wake-word status wording beside the newer activation semantics;
- immediate Realtime tool output retains the original `call_id`, while later asynchronous completion is logged with a task/auftrag identifier but re-enters the model-facing conversation as a new `role=user` text item without the original typed call/task/result join.

The shared architecture principle is:

`DEFERRED_OR_ASYNC_RESULT -> REPLAY_STABLE_ORIGIN_ID + GENERATION -> TYPED_REENTRY`

not:

`SESSION + TIMESTAMP + QUEUE_ORDER + TRANSPORT_ROLE -> CAUSAL_JOIN`.

## 2. Candidate common envelope

Triggerword 4 may test a shared `DeferredCausalReturnEnvelope/v1` with minimum fields:

```text
origin_event_id
origin_kind
origin_generation
request_or_call_id
producer_class
producer_runtime_or_build_identity
result_status
result_payload_digest_or_ref
evidence_class
completion_receipt_id
reentry_id
created_at
```

This is a candidate abstraction, not mandatory universal ontology. Keep it only if measurement shows that it reduces duplicate identity/reentry logic without erasing subsystem-specific semantics.

Counterhypothesis: three explicit bindings may be simpler and more auditable than one generalized envelope.

## 3. Required specializations

### RetrievalRelevanceCandidate

Must preserve:

```text
retrieval_id
turn_id / causal_id
retrieval_generation
candidate_id(s)
judge/runtime identity
model-derived evidence class
result status
reentry id
```

`NEWEST_SESSION_RETRIEVAL != RETRIEVAL_CAUSAL_JOIN`.

### VoiceActivationBinding/v1

Must preserve:

```text
activation_event_id
enable/session generation
audio segment identity or immutable digest
transcript identity/digest where present
Realtime invocation identity
activation policy/version
created_at
```

Two distinct non-empty `speech_end` events must never collapse to one activation identity merely because they share a session.

### VoiceAsyncReturnBinding/v1

Must preserve:

```text
original call_id
task/auftrag_id
task generation
submission receipt
completion receipt
result status
payload digest/ref
conversation reentry id
source/provenance class
```

The model-facing transport representation may be `role=user` if required by the provider protocol, but that transport role must not change provenance to `HUMAN_ORIGINATED_SPEECH`.

`TRANSPORT_ROLE != ORIGIN_SEMANTICS`.

## 4. GRID/UnifiedDB integration

Deferred results do not write canonical world truth merely by re-entering a model context.

```text
Deferred result
 -> typed causal-return record
 -> evidence classification
 -> GRID/UnifiedDB reentry
 -> compare against active goal/prediction/effect/completion state
 -> update only through the appropriate deterministic reducer/gate
```

Model-derived relevance remains candidate evidence. Async task completion is not verified world effect unless the exact task/effect/completion receipts establish that state.

## 5. Required discriminators

1. Two same-session retrieval episodes complete in reverse order; relevance attaches only to exact `retrieval_id + generation`.
2. Stop/retrieval cognition disabled/warm/cold/slow/unreachable; later deterministic Stop bookkeeping remains complete and tail latency is measured.
3. Two overlapping background Voice/tool tasks complete in reverse order; each reentry retains original `call_id + task generation`.
4. Two distinct `speech_end` activations in one enabled session create two distinct activation identities and Realtime invocations.
5. Provider-transport test: internal system-generated async result transported as `role=user` remains provenance-classified as internal/system result, never human speech.
6. Retry/replacement test: old generation cannot satisfy the newer request.
7. Shared-envelope ablation: compare common `DeferredCausalReturnEnvelope` against three specialized bindings for code/identity duplication, attribution error, latency and auditability.

## 6. Telemetry binding

Every test records in the canonical data spine:

- origin event and generation;
- retrieval/activation/call/task IDs;
- producer runtime/build;
- submission/completion/reentry receipts;
- source/provenance class;
- result status including UNKNOWN/FAILED;
- all queue/compute/model/network/DB/reentry latency spans;
- concurrency and reverse-completion order;
- any attribution mismatch as a bug event.

Map primarily to `communications.sqlite`, `system_telemetry.sqlite`, `performance.sqlite`, `bugs.sqlite`, `hypotheses.sqlite`, and where GRID consumes the return, `grid10_telemetry.sqlite`.

## 7. Seeded migration defects / hypotheses

When the Frankenstein-2.0 data spine is available, seed:

- `F2-BUG-0005`: Voice activation lacks a dedicated replay-stable activation identity/generation in the pinned donor reactive listener path; stale wake-word status wording survives beside reactive activation semantics.
- `F2-BUG-0006`: asynchronous Voice/tool completion loses original `call_id` typed binding at model-facing reentry and can be represented as a fresh `role=user` transport item.

Hypothesis pair:

- `F2-HYP-0005`: one shared DeferredCausalReturn envelope lowers identity/reentry duplication and attribution defects across retrieval and Voice.
- `F2-HYP-0005-C1`: subsystem-specific Retrieval/Activation/AsyncReturn bindings are simpler, faster and more auditable; a generalized envelope adds abstraction without measurable value.

No runtime credit follows from source cross-check alone.

## 8. Final laws

`SESSION_ID_IS_CONTEXT_NOT_CAUSAL_JOIN_KEY`

`TIMESTAMP_OR_QUEUE_ORDER_IS_NOT_CAUSAL_JOIN_KEY`

`NEWEST_OPEN_ROW_IS_NOT_SUFFICIENT_UNDER_OVERLAP`

`TRANSPORT_ROLE_DOES_NOT_REWRITE_ORIGIN_PROVENANCE`

`RETRY_OR_REPLACEMENT_REQUIRES_EXPLICIT_GENERATION`

`MODEL_DERIVED_RELEVANCE != WORLD_FACT`

`ASYNC_COMPLETION != VERIFIED_WORLD_EFFECT_WITHOUT_BOUND_RECEIPTS`

Triggerword 4 must preserve this as a measured architecture question: adopt the shared envelope only if reverse-order overlap tests and implementation/telemetry cost show net benefit.