# TRIGGERWORT 4 — Voice on VPS: Text/Event-Driven Build and Acceptance Addendum

Status: OWNER-DIRECTED BUILD/TEST BOUNDARY
Date: 2026-08-28
Applies with:
- `TRIGGERWORD_4_GRID10_COGNITIVE_RUNTIME_DIRECTIVE.md`
- `TRIGGERWORD_4_FRANKENSTEIN_2_VPS_ASSEMBLY_AND_CORTEX_DIRECTIVE.md`
- `TRIGGERWORD_4_FRANKENSTEIN_2_MASTER_ARCHITECTURE_AND_ASSEMBLY_WORKFLOW.md`
- `TRIGGERWORD_4_DEFERRED_CAUSAL_RETURN_RETRIEVAL_VOICE_FUSION_ADDENDUM.md`

## 1. Owner decision

Voice **shall be built as part of Frankenstein 2.0 on the VPS**, but the VPS is not required to prove the physical microphone/speaker/audio-hardware path.

The Voice organ must therefore expose and use a **text/event-driven test seam** that exercises the same session/control logic used by the real Realtime voice path wherever possible.

Do not postpone Voice architecture merely because the VPS lacks a meaningful physical audio environment.

## 2. What the VPS text/event harness must exercise

The harness must drive the real Voice/Realtime control plane with typed synthetic or recorded events rather than replacing it with a toy parallel implementation.

At minimum test:

- GRID/GWT `VoiceIntent` -> VoiceSessionCapsule compilation;
- session create/open/close state machine;
- proactive opportunity/reason/convenience gates;
- injected fresh/stale/unavailable PresenceSnapshot;
- soft addressee-confidence state where enabled;
- user text/transcript input;
- assistant text output intent;
- function/tool-call request and result return;
- deictic transcript -> `VisualNeed`;
- disagreement -> optional re-look request;
- silence/no-response events and the bounded retry/fallback ladder;
- interruption/barge-in event semantics;
- response cancellation and prevention of canceled-turn tool execution;
- structured `VoiceOutcome` re-entry;
- HOLD/WAKE interaction;
- CompletionGate interaction;
- failure/reconnect/timeout state transitions;
- exact causal IDs/generations across the voice episode.

Where the Realtime provider supports text events through the same session protocol, prefer that path because it exercises the real model/session/function-call surface without requiring physical audio I/O.

## 3. Required architecture shape

Do not create a second `TextVoice` brain.

Target:

```text
                 +---------------- physical audio adapter ----------------+
                 |                                                       |
GRID -> VoiceIntent -> Voice Session Core -> Realtime session -> VoiceOutcome -> GRID
                 |                                                       |
                 +--------------- text/event test adapter ----------------+
```

The physical-audio adapter and text/event adapter must converge on the same Voice Session Core, tool routing, causal state, cancellation, policy and outcome-reentry logic.

A test-only adapter may synthesize protocol events, but it must not silently bypass the production session state machine.

## 4. Evidence classes

### `VOICE_CONTROL_PLANE_VPS_PASS`

May be claimed when exact-source VPS tests prove the shared Voice Session Core, policy, model/session text-event path, tool routing, cancellation, outcome re-entry and integration with GRID/UnifiedDB/CompletionGate.

### `VOICE_REALTIME_TEXT_PROTOCOL_PASS`

May be claimed when the real Realtime endpoint/model is exercised through text/event input and returns expected session/function/output behavior without physical audio.

### `VOICE_AUDIO_HARDWARE_PASS`

May **not** be claimed from VPS text tests. It requires a host with meaningful physical audio I/O or an equivalent separately justified audio-device test setup.

Hardware/audio-only questions include:

- real microphone capture;
- real speaker playback;
- acoustic echo/feedback;
- environmental noise behavior;
- actual VAD/turn-detection quality on microphone audio;
- true speech barge-in timing;
- audible truncation alignment;
- codec/audio packet behavior under real streams;
- end-to-end acoustic latency and intelligibility.

These remain a later host-specific acceptance layer and do not block building the rest of Voice on the VPS.

## 5. Interpretation law

If VPS text/event acceptance is green, it is reasonable to treat the **software/control side of Voice as integrated at that scope**.

It is not correct to say "Voice is physically perfect" until audio-hardware evidence exists.

Use precise language:

```text
VOICE SOFTWARE/CONTROL INTEGRATION: PASS at VPS text/event scope
PHYSICAL AUDIO I/O: DEFERRED / NOT TESTED ON VPS
```

## 6. Mandatory VPS Voice tests

### VTX-01 — Reactive dialogue

Injected user transcript -> GRID/Voice handling -> response -> VoiceOutcome -> state re-entry.

### VTX-02 — Proactive gate fail

Meaningful reason exists but presence is false/stale -> no proactive session open; WAIT receipt.

### VTX-03 — Proactive gate pass

Fresh presence + meaningful reason + convenience pass -> exactly one proactive Voice episode opens.

### VTX-04 — Busy suppression

Presence true but interruptibility low -> ordinary proactive candidate suppressed or deferred according to policy.

### VTX-05 — No-response ladder

Attempt 1 -> no-response event -> fresh-condition recheck -> at most one retry -> quiet fallback/cooldown; no third voice attempt.

### VTX-06 — Barge-in/cancel semantics

Assistant response is in progress -> injected interruption event -> current response canceled/truncated in protocol state -> any tool call belonging solely to canceled continuation is rejected.

This proves control semantics, not acoustic timing.

### VTX-07 — Deixis

User transcript such as a visually deictic request -> typed `VisualNeed` -> sensing result -> grounded response path.

### VTX-08 — Disagreement/re-look

User contradicts a visually checkable current claim -> permitted re-look -> evidence update -> response/state re-entry.

### VTX-09 — Tool round trip

Voice-originated tool request -> EffectGate where required -> tool result -> CompletionGate -> VoiceOutcome/state update.

### VTX-10 — HOLD/WAKE

Deferred voice-worthy intent enters HOLD -> injected valid wake condition -> context rebuilt from checkpoint -> Voice candidate re-evaluated once.

### VTX-11 — Restart/recovery

Voice episode or pending intent state survives the intended restart boundary without duplicate execution or lost causal lineage.

### VTX-12 — Text/physical adapter equivalence contract

Static/integration test proves both adapters enter the same Voice Session Core and cannot maintain independent truth/effect/completion state.

## 7. Promotion rule inside Triggerword 4

Stage 7 Voice is allowed to reach `ACCEPTED_AT_SCOPE` on VPS when the text/event suite and exact-source integration tests pass, with the scope explicitly recorded as `VOICE_CONTROL_PLANE_VPS_TEXT_EVENT`.

This allows Triggerword 4 to continue into executor/effect/full-system assembly without waiting for physical audio hardware.

A later suitable host can add `VOICE_AUDIO_HARDWARE_PASS` without reopening the already-proven control-plane architecture unless audio testing reveals a real architectural defect.

## 8. Successor causal-return binding from latest Triggerword-5 forensics

The latest exact-donor source cross-check found that reactive activation and later asynchronous Voice/tool completion can lose replay-stable causal identity even though immediate tool output retains its original `call_id`.

Therefore this Voice acceptance addendum now requires the companion:

`TRIGGERWORD_4_DEFERRED_CAUSAL_RETURN_RETRIEVAL_VOICE_FUSION_ADDENDUM.md`

and adds these acceptance laws:

```text
SESSION_ID != ACTIVATION_EVENT_ID
SESSION_ID != ASYNC_TASK_CAUSAL_JOIN
TIMESTAMP_OR_QUEUE_ORDER != CAUSAL_JOIN
TRANSPORT_ROLE != ORIGIN_PROVENANCE
RETRY_OR_REPLACEMENT_REQUIRES_EXPLICIT_GENERATION
```

### VTX-13 — Activation identity / replay

Two distinct non-empty reactive `speech_end` inputs in the same enabled Voice session must create two distinct activation identities/generations and must not collapse merely because the session is shared.

Record audio/transcript identity or immutable digest where present, Realtime invocation identity and activation policy generation.

### VTX-14 — Async reverse-order return

Start two overlapping background Voice/tool tasks and complete them in reverse order. Each result must preserve its original protocol `call_id`, task/auftrag identity, task generation, completion receipt and reentry identity. No result may attach by chronology/newest-open-row/session proximity.

### VTX-15 — Transport-role provenance

If the provider protocol requires an internal asynchronous result to be transported as a `role=user` conversation item, the canonical provenance must remain system/internal result. It may not be classified as human-originated speech merely because of transport representation.

### VTX-16 — Deferred-return abstraction ablation

Compare one generalized `DeferredCausalReturnEnvelope` against specialized `RetrievalRelevanceCandidate`, `VoiceActivationBinding` and `VoiceAsyncReturnBinding`. Retain the generalized envelope only if it measurably reduces duplicated identity/reentry defects or implementation cost without adding attribution error, latency or lost subsystem semantics.

No source/docs evidence alone earns Voice runtime credit.