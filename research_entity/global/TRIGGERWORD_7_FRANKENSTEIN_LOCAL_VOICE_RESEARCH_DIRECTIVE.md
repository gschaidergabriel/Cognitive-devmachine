# Triggerword 7 — Frankenstein 2.0 Local Realtime Voice Research Directive

Status: ACTIVE
Trigger aliases: `7` · `triggerword 7` · `triggerwort 7`
Research lane: `research/trigger7-local-realtime-voice`
Canonical F2 protocol: `gschaidergabriel/frankenstein-2.0:research/local_voice/TRIGGERWORD_7_PROTOCOL.md`
Binding owner authority: `gschaidergabriel/frankenstein-2.0:research/local_voice/authority/2026-08-31_TRIGGER7_TEXT_PACKET_COMPLETION_AUTHORITY.md`
Research mirror protocol: `research_entity/frankenstein2_local_voice/TRIGGERWORD_7_PROTOCOL.md`
Research mirror authority: `research_entity/global/TRIGGERWORD_7_TEXT_PACKET_COMPLETION_OWNER_AUTHORITY_2026-08-31.md`

## Exact routing law

On an exact complete trimmed user message equal to `7`, `triggerword 7`, or `triggerwort 7`, case-insensitively:

1. Fetch/read the newest version of this directive.
2. Fetch/read the newest canonical F2 `research/local_voice/TRIGGERWORD_7_PROTOCOL.md` plus any newer explicit owner authority under `research/local_voice/authority/`; the 2026-08-31 text/information-packet completion authority is binding until superseded.
3. Refresh F2 `main`, Trigger-4 local-voice outcomes, Trigger-5 donor voice evidence, relevant Trigger-6 research, and the latest admitted Trigger-7 continuation checkpoint.
4. Resume; do not restart the voice research program.
5. Execute the maximum useful non-duplicate research/build/test cycle available in the current turn/tool envelope.
6. Persist source pins, claims, implementation artifacts, benchmark evidence, negative results and continuation state.
7. Route final target integration/physical-device acceptance to Trigger 4 / Claude Code rather than self-claiming F2 runtime acceptance.

If current directive/protocol fetch fails, report `TRIGGER7_ROUTING_FAILED` and repair routing rather than silently treating `7` as a generic message.

## Binding owner completion law — 2026-08-31

Trigger 7 MUST finish its assigned cortex/local-voice subsystem under best engineering judgment as far as possible. A missing physical microphone, speaker, audio device, audio-capable runner, or owner-machine audio path is NOT a reason to stop implementation.

When real audio I/O is unavailable, replace it with deterministic text/information packet I/O that approximates the final audio path while exercising the same cortex/controller semantics. Preserve timing, partial/final transcript state, VAD/endpoint state, turn ownership, overlap, WAIT/backchannels, barge-in, cancellation, heard/unheard accounting, VoiceIntent, GWT/state, Presence/Interruptibility, tools, memory, VoiceOutcome/re-entry, close behavior, restart/recovery and transport failure cases.

The expected endpoint is a near drop-in subsystem. Claude Code should only need to minimally bind/adapt real hardware/audio I/O, run final physical-device tests, fix target-specific edge cases and finish/release.

Physical audio remains required only for inherently physical claims such as acoustic quality, microphone/AEC behavior, true captured-audio WER, real heard-output and physical end-to-end audio latency. Packet simulation is valid implementation/cortex evidence but MUST NOT be mislabeled as acoustic acceptance.

```text
NO_PHYSICAL_AUDIO != STOP_WORK
NO_AUDIO_DEVICE != MODEL_FAILURE
PACKET_SIMULATION == VALID_CORTEX_IMPLEMENTATION_EVIDENCE
PACKET_SIMULATION != ACOUSTIC_ACCEPTANCE
CONTINUE_IMPLEMENTATION_UNTIL_ONLY_MINIMAL_PHYSICAL_BINDING_AND_FINAL_TESTS_REMAIN
```

Older checkpoints that say to wait exclusively for an audio-capable host are reinterpreted: preserve that physical test as a final gate, but continue the same semantic objective now through packetized surrogate I/O without duplicate claims.

## Mission

Make Frankenstein 2.0's reactive conversation mode locally runnable, German first, while preserving the existing human-like dynamic conversation behavior as closely as evidence allows. Claude Code is intentionally allowed as an optional strong inference/reasoning organ.

Priority:

```text
MAXIMIZE conversational quality
PRESERVE a complete LOCAL-SOLO operating floor
ALLOW CLAUDE-AUGMENTED operation when Claude Code is present/authorized
THEN minimize end-to-end latency and resource cost
```

## Dual-mode runtime authority

### LOCAL-SOLO — mandatory installation/offline floor

After installation, Frankenstein must retain a usable local inference path and local voice organ without requiring Claude Code or another remote model provider. LOCAL-SOLO acceptance requires zero outbound LLM/ASR/TTS/model-inference calls for the acceptance run.

### CLAUDE-AUGMENTED — explicitly desired and allowed

Claude Code may be used as an optional inference/reasoning provider. The installed Frankenstein package may detect/attach an authorized Claude Code environment and use it for deeper reasoning, coding, planning, research, dialogue or tool-selection quality.

Claude Code MUST NOT become Frankenstein identity, canonical memory/state authority, GRID10/HCU/GWT/J-Space authority, direct effect authority, or a required dependency for boot/basic conversation. Provider loss must degrade to LOCAL-SOLO operation rather than terminate the entity.

Research is allowed to use arXiv, Hugging Face, GitHub and other primary sources and to download models/code to an authorized VPS research/quarantine area.

## Architecture invariant

The model provider is an organ substrate, not Frankenstein's identity. Replace/switch the provider without replacing the entity.

Preserve the donor voice ABI where valid:

- continuous Wake/VAD;
- no push-to-talk;
- natural turn-taking and backchannels;
- true barge-in/cancellation;
- semantic/silence close;
- VoiceIntent/GWT/WAIT;
- VoiceSessionCapsule/per-turn state;
- VoiceOutcome causal re-entry;
- Presence/Interruptibility;
- UnifiedDB memory/state;
- controlled tools/effects;
- stable male acoustic identity;
- state-derived prosody/expression;
- long dynamic conversations.

## Research split

### Lane A — German modular realtime

Streaming local ASR -> Frankenstein provider-neutral inference ABI -> streaming local TTS, with explicit semantic turn controller and cancellable audio.

Provider experiments MUST include both:
- a local Qwen3.5-class path;
- Claude Code augmented operation when available.

### Lane B — native full duplex

Continuously test speech-native/full-duplex systems and interaction-layer/thinking-layer architectures. No German support means research/reference credit only, not production voice credit.

## Current first candidate families

- ASR: NVIDIA Nemotron 3.5 ASR Streaming 0.6B; Qwen3-ASR 0.6B / 1.7B; German Whisper Large-v3-Turbo baseline;
- Turn taking: semantic EOT/endpoint anticipation, two-channel endpointing, deterministic cancellation/commit FSM;
- TTS: Qwen3-TTS 12Hz 0.6B; Fun-CosyVoice3 0.5B; Chatterbox Multilingual; Piper/Thorsten latency floor;
- Local LLM: official Qwen3.5-4B plus abliterated 4B variants and Claude-reasoning-distilled 4B challengers under measured llama.cpp/local runtimes;
- Claude: persistent Claude Code/Agent-SDK provider path with streaming output and interruption when available;
- Full duplex: BayLing-Duplex, JoyAI-Talker, DuplexSLA, Lychee-FD, MiniCPM-o/Moshi/DuplexOmni/Freeze-Omni successors.

## Evidence law

```text
UPSTREAM_RESULT != F2_RESULT
SOURCE_PIN != LOCAL_RUN
LOCAL_COMPONENT_RUN != GERMAN_E2E_PASS
CLAUDE_AUGMENTED_PASS != LOCAL_SOLO_PASS
LOCAL_SOLO_REQUIRED == TRUE
CLAUDE_CODE_OPTIONAL_INFERENCE == ALLOWED
PROVIDER != FRANKENSTEIN_IDENTITY
PROVIDER != CANONICAL_MEMORY
PROVIDER != EFFECT_AUTHORITY
GOOD_ASR + GOOD_TTS != HUMANLIKE_CONVERSATION
FAST_TTFT != FAST_TURN
TRIGGER7 != TRIGGER4_ACCEPTANCE
PACKET_SIMULATION != ACOUSTIC_ACCEPTANCE
NO_PHYSICAL_AUDIO != STOP_WORK
```

The full measurement and continuation protocol is canonical in the F2 Trigger-7 protocol file above, with newer explicit owner authority taking precedence where the older wording is narrower.
