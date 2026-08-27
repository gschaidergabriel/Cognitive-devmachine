# 666 Level-0 Run Report — PF Voice / Wake-Word Lineage

- Trigger: `666`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Exact Level-0 credit: **0.0%**

## Result

The wake-word contradiction is a real temporal supersession/reintroduction lineage:

1. Initial repository state declared wake-word + push-to-talk.
2. Feb-19 disabled the legacy `aicore-voice` wake listener and removed it from watchdog supervision.
3. Feb-19 through Feb-21 documentation/self-model moved to push-to-talk only.
4. Mar-19 unified `FrankVoice` reintroduced wake-word functionality internally, alongside CPU STT/VAD/TTS and WebSocket voice streaming.
5. Frozen HEAD still contains the OpenWakeWord detector, an explicit `wake_word` mode and WebSocket handling of a wake event.

Therefore the old component remains superseded, while the user function was later reintroduced in a different component generation.

## Current epistemic status

- Legacy `aicore-voice` wake daemon: `SUPERSEDED_DISABLED`.
- FrankVoice wake-word source capability: `CURRENT_SOURCE_REACHABLE`.
- End-user UI/default enablement on target build: `OPEN`.
- Working microphone-to-effect wake detection on Andreas target PC: `OPEN_UNVERIFIED_EFFECT`.

## Architecture delta

New invariant:

`CAPABILITY_REINTRODUCTION_MUST_CREATE_A_NEW_LINEAGE_IDENTITY_NOT_REACTIVATE_THE_OLD_COMPONENT_BY_NAME`

Capability truth must keep separate:

- component generation;
- dependency availability;
- enabled/configured state;
- source-level reachability;
- deployed runtime reachability;
- verified effect;
- self-description.

## Tests

1. Trace frontend control -> `/ws/voice` -> `process_chunk(mode='wake_word')` -> OpenWakeWord -> wake event -> conversation transition.
2. Measure false accept/reject and latency for intended phrase, proxy phrase, near-neighbors and ambient speech.
3. Assert legacy `aicore-voice` remains disabled while FrankVoice can provide the reintroduced function independently.
4. Remove OpenWakeWord dependency/model and verify fail-closed degradation while PTT/conversation voice remains healthy.

## Non-claims

- No claim that wake-word is enabled by default.
- No target-PC runtime effect was executed.
- No claim that the `hey_jarvis_v0.1` proxy is adequate for “Hey Frank”.
- No exact L0 completion credit or earned-work hours were assigned.

## Durable ref

`research_entity/archive_assimilation/receipts/666_20260809T1443p0700_chatgpt_secondary_pf_voice_wakeword_lineage.json`
