# ChatGPT Live App Runtime Boundary — 2026-09-12

Status: CURRENT BOUNDARY / INTEGRATION PARTIAL

## Verified target

The owner-facing target is **ChatGPT Voice → Live**, not the local `realtime_gespraech.py` voice implementation and not the existing text/browser ChatGPT terminal harness.

Current OpenAI product behavior verified on 2026-09-12:

- ChatGPT Voice Live is powered by GPT-Live-1 or GPT-Live-1 mini depending on plan/runtime.
- Live operates inside the current ChatGPT chat and supports natural full-duplex interaction, interruptions, web search and memory.
- Live currently does **not** support connected apps/plugins.
- GPT-Live-1's developer/API surface can steer tone, pace and conversational style by instructions/system prompt, but acoustic realization is model behavior rather than deterministic DSP control.

Therefore do not conflate these three surfaces:

1. `~/.claude/star/f2wp1207_chatgpt_organ.py` = canonical GRID10-backed ChatGPT **text organ**.
2. `~/.claude/star/f2wp1207_chatgpt_exact_backend.py` = targeted **browser transport** for that text organ.
3. ChatGPT app Voice Live = GPT-Live owner-facing **continuous audio organ**.

The existing text organ/browser backend is useful for identity, state and task continuity but is not evidence that a GPT-Live audio session is wired to GRID on every acoustic turn.

## What is implementable now without inventing a parallel runtime

The current branch provides a pure transient adapter:

`research_entity/coordination/chatgpt_live_voice_expression.py`

It accepts `VOICE_EXPRESSION_INTENT/v1`, validates/gates it and compiles a small native-Live instruction block. It owns no DB, memory, network session, audio renderer or turn loop.

This adapter is intentionally ready for either of two future canonical call sites:

- a first-party ChatGPT Live instruction/context injection surface, if/when the app exposes one to this project; or
- a separately admitted GPT-Live API frontend that delegates cognition to the existing Frankenstein organ while keeping audio realization in GPT-Live.

The second option is **not** silently created here because the owner explicitly selected the ChatGPT app/cloud lane and current ChatGPT Live does not expose connected-app/plugin calls into the local harness.

## App-mode behavior available now

Because Live operates in the same ChatGPT chat, the active conversation can carry the persistent persona and high-level delivery rules. The Live model should natively choose and realize emotion from conversational context rather than requiring a local TTS pass.

The desired app-level rules are:

- full range is permitted when context warrants it: warmth, joy, amusement/laughter, dry sarcasm, playful mockery, annoyance, frustration, anger, concern, urgency, surprise, tenderness, whisper-like and shout-like delivery;
- do not narrate an emotion that can be expressed through voice;
- do not mechanically mirror the user's emotion;
- explicit user resistance immediately cancels teasing/sarcasm/whisper/shout performance;
- preserve intelligibility at high intensity;
- use native pauses, timing, chuckles, backchannels and interruption behavior rather than locally synthesized substitutes.

## Missing canonical bridge

What remains unproven is **dynamic per-turn bidirectional GRID/GWT/TITAN ↔ ChatGPT app Live injection**.

Current ChatGPT app Live has chat context + memory but no connected-app/plugin surface. Consequently, a local `VOICE_EXPRESSION_INTENT/v1` produced after every GRID turn cannot honestly be claimed to reach the app Live model in real time through an existing supported connector.

This is an integration gap, not a reason to build a duplicate memory/voice system.

Required closure evidence before promotion:

1. identify an admitted canonical mechanism that injects the current Active Assembly / expression intent into the same owner-facing Live session without creating a second cognitive authority;
2. bind response/session/turn IDs end-to-end;
3. prove user barge-in cancels stale audio and reaches the canonical turn state;
4. prove Live-native signals can be correlated back to GRID when the integration surface exposes them;
5. run the E01–E18 perceptual acceptance matrix against actual app Live audio.

Until then:

`APP_NATIVE_EMOTIONAL_STYLE = AVAILABLE/CONTEXT-DRIVEN`

`DYNAMIC_GRID_TO_APP_LIVE_EXPRESSION_INJECTION = UNPROVEN`

`APP_LIVE_AUDIO_ACCEPTANCE = NOT_YET_RUN`
