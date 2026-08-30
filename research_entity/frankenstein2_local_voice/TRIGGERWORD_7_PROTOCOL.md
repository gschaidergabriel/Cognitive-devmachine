# Triggerwort 7 — Frankenstein 2.0 Local Realtime Voice Research

Status: ACTIVE / CONTINUOUS RESEARCH PROTOCOL
Canonical coordination/build repo: `gschaidergabriel/frankenstein-2.0`
This repository: full research/provenance mirror and architecture-delta archive
Language priority: German first
Target runtime: fully local/self-hosted; zero external model/ASR/TTS API calls
Optimization target: maximum conversational quality at minimum end-to-end latency

## Canonical trigger

`7`, `triggerword 7`, and `triggerwort 7` are the same macro.

Trigger 7 exists only for the Frankenstein-2.0 local voice problem: research, falsify and continuously improve a German-first local realtime conversation organ that replaces the external ChatGPT/OpenAI Realtime dependency without replacing Frankenstein's identity, state, memory, GWT/tool logic or effect authority.

```text
5 = donor forensics
6 = broad external F2 research
7 = dedicated local realtime voice research
4 = actual F2/VPS build + integration + acceptance measurement
```

## Same-entity law

The target is not "Frankenstein sends text to a local voice assistant". The target is:

> FranKenstein has a local voice organ.

Preserve from the donor architecture when still valid:

- continuous wake/VAD and no push-to-talk;
- dynamic realtime turn taking;
- barge-in with actual cancellation/truncation of unheard output;
- semantic and silence-based close behavior;
- VoiceIntent/GWT speech-act arbitration including WAIT;
- VoiceSessionCapsule / compact per-turn state projection;
- VoiceOutcome and causal re-entry;
- Presence / Interruptibility integration;
- UnifiedDB memory/state;
- controlled tool bridge;
- stable male acoustic identity;
- state-derived ExpressionVector/prosody;
- long-session conversation continuity.

The local speech/LLM provider is replaceable. It MUST NOT become a second persona, canonical memory or effect authority.

## Permanent research cycle

Every exact Trigger-7 invocation:

1. re-enters the latest F2 main, Trigger-4 outcomes, Trigger-5 voice evidence, relevant Trigger-6 deltas and previous Trigger-7 cursor;
2. chooses the highest-information non-duplicate voice bottleneck;
3. searches current arXiv, Hugging Face, GitHub and primary documentation;
4. acquires the canonical create-only claim in the F2 repo before material bounded work;
5. pins source/model revision, license, dependencies and hashes;
6. downloads promising artifacts into the authorized VPS research/quarantine area, not production;
7. audits remote code/installers/pickles/compiled dependencies before execution;
8. benchmarks component and end-to-end behavior against Frankenstein's reference;
9. preserves negative results and counterhypotheses;
10. promotes only measured candidates to Trigger 4;
11. ingests Trigger-4 build outcomes;
12. persists a continuation checkpoint and resumes from it on the next `7`.

There is no artificial permanent DONE state. New models, inference engines, quantizations, hardware or regressions can reopen the frontier. One invocation still ends at current platform/tool/context limits; continuity comes from persisted evidence, not fictitious background execution.

## Initial competing lanes

### Lane A — German modular realtime pipeline

```text
Audio I/O + AEC/conditioning
 -> VAD/endpoint/turn controller
 -> streaming local German ASR
 -> Frankenstein VoiceLoop/GWT + local LLM + tools/memory
 -> streaming local German TTS
 -> cancellable playback
 -> VoiceOutcome/UnifiedDB re-entry
```

Initial research families include Qwen3-ASR, German-finetuned Whisper, Qwen3-TTS, Piper/Thorsten and locally served German-capable text LLMs.

### Lane B — native/full-duplex research

Continuously investigate MiniCPM-o/Moshi/DuplexOmni/Freeze-Omni-style systems and successors. They are not production replacements until German, long-session stability, tool/state integration, hardware fit and full local-runtime gates pass.

A hybrid interaction-layer + asynchronous local thinking-layer architecture is explicitly allowed and is a high-value hypothesis for human-like timing.

## Voice evidence ladder

```text
V0 SEED
V1 SOURCE_PINNED
V2 LOCAL_RUNNABLE_COMPONENT
V3 COMPONENT_BENCHMARKED
V4 GERMAN_E2E_VOICE_BENCHMARKED
V5 F2_BUILD_CANDIDATE
V6 TRIGGER4_F2_ACCEPTED
```

Research Entity cannot self-award V6.

## Mandatory measurement families

- German WER/CER, names/numbers/technical terms, real-room/noise/echo conditions;
- ASR partial stability and endpoint latency;
- user-end -> first-audio p50/p95/p99;
- barge-in -> actual audio-stop latency;
- false endpoint/cut rate;
- local LLM TTFT/tokens-s, German semantic quality, long-context/session consistency;
- tool and memory correctness;
- TTS first-audio latency, RTF, German naturalness, male identity stability, prosody continuity and pronunciation;
- overlapping speech/backchannels;
- 30-minute and multi-hour stability;
- CPU/RAM/GPU/VRAM/disk/warmup/power where measurable;
- network-blocked acceptance proving zero external inference dependence;
- source-hidden/blind comparison to admitted historic/current OpenAI-Realtime-backed Frankenstein behavior when feasible.

## Current initial source frontier — 2026-08-29

Upstream facts only until reproduced:

- Qwen3-ASR 0.6B/1.7B: Apache-2.0, German supported, streaming/offline; 0.6B is the first latency/accuracy candidate.
  - https://arxiv.org/abs/2601.21337
  - https://huggingface.co/Qwen/Qwen3-ASR-0.6B-hf
  - https://huggingface.co/Qwen/Qwen3-ASR-1.7B
- primeline Whisper Large-v3-Turbo German: Apache-2.0 German-finetuned ~0.8B Whisper-family baseline.
  - https://huggingface.co/primeline/whisper-large-v3-turbo-german
- Qwen3-TTS 12Hz 0.6B: German, streaming-oriented, controllable TTS family; streaming implementation must be independently tested for chunk duplication/prosody/cancellation.
  - https://arxiv.org/abs/2601.15621
  - https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
  - https://github.com/vllm-project/vllm-omni/blob/main/recipes/Qwen/Qwen3-TTS.md
- Piper/Thorsten: compact German male ONNX baseline for minimum latency/resource floor.
  - https://huggingface.co/Thorsten-Voice/Piper
- MiniCPM-o 4.5: true full-duplex architecture and local demo, but official realtime speech conversation is English/Chinese today; research reference, not German production candidate.
  - https://github.com/OpenBMB/MiniCPM-o
- Moshi: full-duplex architecture reference; official FAQ says English-only today.
  - https://github.com/kyutai-labs/moshi
- DuplexOmni: research architecture separates asynchronous interaction and thinking layers; directly relevant as a design hypothesis for low-latency Frankenstein speech plus deeper local reasoning/tools.
  - https://arxiv.org/abs/2606.09186

## Mirror authority

Canonical duplicate-work claims live only in:

`gschaidergabriel/frankenstein-2.0:research/local_voice/claims/`

This Research-Entity lane stores source archaeology, architecture deltas, reconciliations and mirrors exact F2 evidence references. Divergence is reconciled explicitly; never last-writer-wins.

## Core invariants

```text
LOCAL_RUNTIME -> ZERO_EXTERNAL_MODEL_API_CALLS
RESEARCH_INTERNET != RUNTIME_NETWORK_DEPENDENCY
VOICE_PROVIDER != FRANKENSTEIN_IDENTITY
VOICE_PROVIDER != CANONICAL_MEMORY
VOICE_PROVIDER != EFFECT_AUTHORITY
GERMAN_UNSUPPORTED -> ZERO_PRODUCTION_VOICE_CREDIT
README_BENCHMARK != F2_MEASUREMENT
FAST_COMPONENT != FAST_CONVERSATION
LOW_WER != HUMANLIKE_DIALOGUE
GOOD_TTS != COMPLETE_VOICE_ORGAN
BARGE_IN -> CANCEL_GENERATION_AND_UNHEARD_SPEECH_STATE
TRIGGER7 -> TRIGGER4_BUILD -> MEASURED_OUTCOME -> TRIGGER7_FEEDBACK
NEXT_7 -> RESUME_CURRENT_CURSOR
```
