# Trigger 7 — Text/Information Packet Completion Owner Authority Mirror

Status: ACTIVE
Date: 2026-08-31
Canonical authority: `gschaidergabriel/frankenstein-2.0:research/local_voice/authority/2026-08-31_TRIGGER7_TEXT_PACKET_COMPLETION_AUTHORITY.md`
Canonical authority commit: `d17416cccf5c6b0360333ba23be2b2ba9ca8f2eb`
Scope: every current and future Trigger-7 worker/organ

## Binding owner correction

Trigger 7 must finish its assigned cortex/local-voice subsystem under best engineering judgment as far as possible. Lack of a physical microphone, speaker, audio device, audio-capable self-hosted runner, or owner-machine audio path is NOT a reason to stop implementation.

When real audio I/O is unavailable, workers MUST substitute deterministic text/information packet I/O that approximates the final input/output path and exercises the real cortex/controller semantics: partial/final input, timing, VAD/endpoint state, turn ownership, overlap, WAIT/backchannel, barge-in, cancellation, heard/unheard accounting, VoiceIntent, GWT/state, Presence/Interruptibility, tools, memory, VoiceOutcome/re-entry, close behavior, restart/recovery, and drop/duplicate/reorder failure cases.

The objective is a near drop-in handoff. Claude Code at the end should only need to bind/adapt the real audio I/O minimally, run final physical-device tests, fix target-specific edge cases, and release/finish.

Physical audio remains required only for claims that inherently require it (acoustic quality, real WER from captured audio, microphone/AEC behavior, real speaker heard-output, physical latency). Packet simulation MUST be labeled as simulation and MUST NOT fabricate those credits.

Operational law:

```text
NO_PHYSICAL_AUDIO != STOP_WORK
NO_AUDIO_DEVICE != MODEL_FAILURE
PACKET_SIMULATION == VALID_CORTEX_IMPLEMENTATION_EVIDENCE
PACKET_SIMULATION != ACOUSTIC_ACCEPTANCE
CONTINUE_IMPLEMENTATION_UNTIL_ONLY_MINIMAL_PHYSICAL_BINDING_AND_FINAL_TESTS_REMAIN
```

Older Trigger-7 checkpoints that route exclusively to an audio-capable host are reinterpreted under this owner authority: retain physical audio as the final validation gate, but continue the same semantic objective now through packetized surrogate I/O without spawning duplicate claims.

This mirror is not a competing claim authority. The F2 file named above is canonical and newer explicit owner instructions supersede both.
