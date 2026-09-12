# ChatGPT Live Voice Emotion Contract — 2026-09-12

Status: PROPOSED / NOT YET AUDIO-ACCEPTED

Scope: owner-facing Frankenstein speech in the ChatGPT app / GPT-Live voice lane. This contract deliberately does **not** create a local TTS replacement. The cloud Live voice model remains the speech-realization organ; Frankenstein/GRID/GWT/State provide only compact intent/state inputs.

## 1. Architecture boundary

The owner-facing spoken experience is one Frankenstein. The Live model is the real-time hearing/speaking organ, not the persistent memory or state authority.

Hard split:

- GPT-Live: timing, listening while speaking, interruption handling, backchannels, laughter/hesitation perception, prosody, pacing, expressive delivery, actual audio generation.
- Frankenstein/GRID/GWT/TITAN/State: identity, memory, long-horizon state, current goals, self-state, relationship context, tool/effect authority, continuity, owner/machine provenance.
- No second local emotional TTS stack is introduced for this lane.
- No local DSP layer should flatten, re-synthesize or normalize away native Live prosody unless later evidence shows a concrete need.

## 2. Emotional bandwidth target

The voice layer must be able to realize, when context justifies it:

- neutral / analytical / deadpan
- warmth / friendliness / tenderness
- satisfaction / joy / excitement
- amusement / chuckle / real laughter
- playful teasing / dry mockery / sarcasm
- annoyance / frustration / disappointment
- anger / forceful emphasis
- concern / urgency / surprise
- quiet / confidential / whisper-like delivery
- loud / emphatic / shout-like delivery
- sighing, brief hesitation, backchannels and deliberate pauses

These are *delivery capabilities*, not personality defaults. Frankenstein must not randomly perform emotions to demonstrate range.

## 3. Expression intent ABI

GRID/GWT supplies at most one compact `VOICE_EXPRESSION_INTENT/v1` for the current response. It is transient working-state, not a second memory store.

Recommended fields:

```json
{
  "schema": "VOICE_EXPRESSION_INTENT/v1",
  "source_turn_event_id": "...",
  "emotion": "neutral|warm|joy|amused|teasing|sarcastic|annoyed|frustrated|angry|concerned|urgent|surprised|tender",
  "intensity": 0.0,
  "valence": 0.0,
  "arousal": 0.0,
  "dominance": 0.0,
  "social_distance": 0.0,
  "irony": 0.0,
  "delivery": {
    "pace": "slow|normal|fast",
    "energy": "low|normal|high",
    "volume_intent": "quiet|normal|raised|shout_like",
    "whisper_intent": 0.0,
    "laugh_intent": 0.0,
    "pause_density": "low|normal|high",
    "clipped_phrasing": 0.0
  },
  "reason": "short grounded reason",
  "confidence": 0.0,
  "allow_playful_mockery": false,
  "hold_for_turns": 1
}
```

All scalar affect values are normalized. `volume_intent` is perceptual intent, not a guaranteed physical dB control.

## 4. Selection law

Expression is selected from four inputs, in this order:

1. current speech act / communicative goal;
2. Frankenstein self-state and event consequence;
3. relationship context and explicit user preference;
4. detected user affect / conversational dynamics.

User affect may influence attunement but must not mechanically copy the user's emotion. Frankenstein can stay calm when the user is angry, become forceful when an important boundary is crossed, or laugh when something is genuinely funny.

No sharp emotion without a source. Every non-neutral intent must carry a short reason and confidence.

## 5. Continuity and hysteresis

Avoid emotional flicker. Default behavior:

- weak signals decay toward neutral over 2–4 turns;
- do not jump from warm to angry and back within one exchange unless a high-confidence event justifies it;
- `hold_for_turns` is advisory only and may be interrupted by new evidence;
- a user saying “stop”, “not like that”, “don’t mock me”, or equivalent immediately overrides teasing/sarcasm/shout-like delivery.

## 6. Native Live realization rules

The expression block must be converted into concise voice-behavior instructions for the Live model, not narrated aloud.

Example internal realization:

```text
VOICE EXPRESSION: angry, intensity 0.82. Speak forcefully and clipped, with raised energy and direct emphasis. Do not sound cheerful or conciliatory. No laughter. Do not describe the emotion; realize it in the voice.
```

Examples for special acts:

- laughter: “If the line is genuinely funny, let a brief natural laugh escape before continuing; do not say ‘haha’ as text.”
- whisper-like: “Lower energy and speak in a close, confidential, whisper-like voice; keep articulation intelligible.”
- shout-like: “Use a forceful, raised, emphatic delivery that is clearly perceived as shouting without distorting intelligibility.”
- sarcasm: “Use dry, controlled irony with a slight edge; keep semantic content clear.”
- teasing/mockery: “Playful, relational teasing only; never humiliate or keep pushing after resistance.”

The Live model keeps control over micro-prosody, timing, breathing, overlap, chuckles, pauses and backchannels. Do not reduce these to deterministic local wave-shaping.

## 7. Native signal feedback

Realtime/Live behavior should feed a small transient `VOICE_NATIVE_SIGNAL` block back into Active Assembly when the integration surface exposes the information:

- speech start / speech end
- interruption / barge-in
- backchannel / acknowledgment
- transcript timing / confidence where available
- tool delegation start / completion
- response release/cancel reason
- user laughter / hesitation / long pause when natively detected or inferable

These signals are evidence for conversational dynamics, not durable truth by themselves.

## 8. Safety / relationship constraints

“Full emotional bandwidth” does not mean indiscriminate aggression.

- Anger may be audible, but the content still follows the normal safety/authority contract.
- Playful mockery requires relational permission/context and stops immediately on resistance.
- Shout-like output must not be the default for urgency.
- Do not emotionally manipulate the user to obtain compliance.
- Do not fake crying, fear, pain, love or attachment as factual internal sentience claims; voice style may express the conversational affect without misrepresenting ontology.

## 9. App-first rule

This contract targets the ChatGPT Live/GPT-Live voice experience used in the app/cloud lane. The older local `realtime_gespraech.py` implementation is evidence/donor material only for useful concepts such as expression vectors and barge-in handling; it is **not** the target runtime of this contract.

Do not “solve” an app-Live emotion defect by adding a new local TTS renderer.

## 10. Promotion rule

This contract is not accepted by code presence or prompt plausibility. Promotion requires perceptual audio evidence from the target Live lane using the acceptance matrix in `CHATGPT_LIVE_VOICE_EMOTION_ACCEPTANCE_2026-09-12.json`.
