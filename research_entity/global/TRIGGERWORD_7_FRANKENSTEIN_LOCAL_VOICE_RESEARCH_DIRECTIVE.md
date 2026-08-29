# Triggerword 7 — Frankenstein 2.0 Local Realtime Voice Research Directive

Status: ACTIVE
Trigger aliases: `7` · `triggerword 7` · `triggerwort 7`
Research lane: `research/trigger7-local-realtime-voice`
Canonical F2 protocol: `gschaidergabriel/frankenstein-2.0:research/local_voice/TRIGGERWORD_7_PROTOCOL.md`
Research mirror protocol: `research_entity/frankenstein2_local_voice/TRIGGERWORD_7_PROTOCOL.md`

## Exact routing law

On an exact complete trimmed user message equal to `7`, `triggerword 7`, or `triggerwort 7`, case-insensitively:

1. Fetch/read the newest version of this directive.
2. Fetch/read the newest canonical F2 `research/local_voice/TRIGGERWORD_7_PROTOCOL.md`.
3. Refresh F2 `main`, Trigger-4 local-voice outcomes, Trigger-5 donor voice evidence, relevant Trigger-6 research, and the latest admitted Trigger-7 continuation checkpoint.
4. Resume; do not restart the voice research program.
5. Execute the maximum useful non-duplicate research/test cycle available in the current turn/tool envelope.
6. Persist source pins, claims, benchmark evidence, negative results and continuation state.
7. Route build/integration candidates to Trigger 4 rather than self-claiming F2 runtime acceptance.

If current directive/protocol fetch fails, report `TRIGGER7_ROUTING_FAILED` and repair routing rather than silently treating `7` as a generic message.

## Mission

Make Frankenstein 2.0's reactive conversation mode fully local/self-hosted, German first, while preserving the existing human-like dynamic conversation behavior as closely as evidence allows.

Priority:

```text
MAXIMIZE conversational quality
SUBJECT TO fully local runtime
THEN minimize end-to-end latency and resource cost
```

Target-runtime acceptance requires zero external LLM/ASR/TTS/model inference API calls. Research is allowed to use arXiv, Hugging Face, GitHub and other primary sources and to download models/code to an authorized VPS research/quarantine area.

## Architecture invariant

The old external Realtime provider is an organ substrate, not Frankenstein's identity. Replace the provider, not the entity.

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

Streaming local ASR -> Frankenstein/local LLM brain + tools/memory -> streaming local TTS, with explicit turn controller and cancellable audio.

### Lane B — native full duplex

Continuously test speech-native/full-duplex systems and interaction-layer/thinking-layer architectures. No German support means research/reference credit only, not production voice credit.

## Current first candidate families

- Qwen3-ASR 0.6B / 1.7B;
- German Whisper Large-v3-Turbo family;
- Qwen3-TTS 12Hz 0.6B;
- Piper/Thorsten as German latency floor;
- local German-capable text LLMs under measured runtimes;
- MiniCPM-o, Moshi, DuplexOmni/Freeze-Omni lineages for full-duplex research.

## Evidence law

```text
UPSTREAM_RESULT != F2_RESULT
SOURCE_PIN != LOCAL_RUN
LOCAL_COMPONENT_RUN != GERMAN_E2E_PASS
GOOD_ASR + GOOD_TTS != HUMANLIKE_CONVERSATION
FAST_TTFT != FAST_TURN
TRIGGER7 != TRIGGER4_ACCEPTANCE
```

The full measurement and continuation protocol is canonical in the F2 Trigger-7 protocol file above.
