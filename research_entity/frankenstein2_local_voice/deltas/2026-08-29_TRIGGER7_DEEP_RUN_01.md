# Trigger 7 provenance delta — Deep Run 01

Date: 2026-08-29
Canonical F2 merge: `a066ab258a9885e50370169239dffe6723e59d34`
F2 PR: #571
Status: SOURCE/ARCHITECTURE FRONTIER ADVANCED; TARGET/VPS RUNTIME NOT OBSERVED

## Owner authority absorbed

Frankenstein 2.0 intentionally supports two inference modes:

- `CLAUDE-AUGMENTED`: Claude Code may act as an optional strong inference/reasoning organ when installed/authorized.
- `LOCAL-SOLO`: the installed Frankenstein retains a usable local inference path and local realtime voice organ without Claude.

Provider outputs remain candidate state. Frankenstein identity, durable state/memory, GRID10/HCU/GWT/J-Space coordination and EffectGate/effect authority remain provider-independent.

## Deep-run frontier delta

The current strongest near-term voice architecture is a speculative cancellation-safe modular path:

`streaming German ASR -> semantic/dual-channel endpointing -> speculative provider-neutral inference -> streaming local TTS -> cancellable playback -> heard-only VoiceOutcome commit`.

High-value new candidates/findings admitted to source-level research:

- NVIDIA Nemotron 3.5 ASR Streaming 0.6B as a German streaming challenger beside Qwen3-ASR and Whisper;
- endpoint anticipation for speculative LLM/TTS execution before reactive endpoint completion;
- DualTurn-like two-channel EOT/VAD/FVAD signals for overlap/barge-in;
- Qwen3-TTS, Fun-CosyVoice3 and Chatterbox as primary local German TTS quality challengers;
- persistent Claude Code/Claude Agent SDK provider research rather than the donor's historical one-short-lived-process-per-turn bridge;
- Qwen3.5-4B local inference ladder including official, abliterated and Claude-reasoning-distilled abliterated variants.

## First pinned local 4B execution candidate

Repository: `kaineone/Qwen3.5-4B-abliterated-GGUF`
Immutable repository revision: `551991a575c1d4221ca0f0cfca74037d26268411`
File: `KAINE-Qwen3.5-4B-abliterated.Q4_K_M.gguf`
Runtime target: local `llama.cpp` / `llama-server`

Quality-preservation challenger:
`wangzhang/Qwen3.5-4B-abliterated` at source revision `3bcc7a546b609f8d4f7344b52a5dda1b8298cf7d`; upstream self-reports 3/200 refusals and KL divergence 0.0065. These are upstream results only.

High-interest Claude-distilled challenger:
`huihui-ai/Huihui-Qwen3.5-4B-Claude-4.6-Opus-abliterated`; no German/F2 runtime credit yet.

## Runtime boundary

This trigger invocation had no connected target/VPS SSH or remote-shell surface. Therefore:

- target hardware receipt: NOT OBSERVED;
- model weights on target/VPS: NOT DOWNLOADED;
- llama.cpp target execution: NOT OBSERVED;
- German runtime benchmark: NOT OBSERVED;
- V2/V3/V4 runtime credit: ZERO.

The canonical F2 side contains the create-only E3 benchmark claim and a Trigger-4 execution handoff. The next decisive step is actual target/VPS execution, not additional README ranking.

## Continuation

Resume from F2 `research/local_voice/checkpoints/CURRENT.json` after merge `a066ab258a9885e50370169239dffe6723e59d34`. Execute the pinned Qwen3.5-4B local benchmark when an authorized shell surface exists, then compare identical German VoiceSessionCapsule workloads across persistent Claude Code, official Qwen3.5-4B Q4, abliterated Q4 and Claude-distilled abliterated Q4.
