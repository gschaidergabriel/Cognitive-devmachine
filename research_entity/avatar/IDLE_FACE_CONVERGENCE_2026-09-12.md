# Avatar idle face convergence — 2026-09-12

## Goal

A quiet FranKenstein face must remain alive without looking periodic, scripted, manic, or detached from internal state. Idle facial acts are one-shot consequences of current state, not a loop. Speech always owns the mouth. Existing production Chrome remains the single display-2 subject.

## Renderable production candidate already coordinated in parallel

The current `avatar_idle_face_v1.js` candidate uses real existing surfaces only:

- mouth keyframes + sub-pixel asymmetry for lip press, corner pull, skew, purse and small-O;
- a masked local head-image overlay for nose scrunch / nostril flare;
- the existing `anime_90s/anime_zunge_raus` full-expression asset for a rare tongue peek;
- existing `aktuellerAusdruck`, `tempo`, near/presence, surprise, body/crisis state and self-emote category as causes;
- randomized next opportunity, per-action cooldown, recent-history exclusion and a refillable activity budget;
- hard avoidance of `_sonderLaeuft`, mouth speech frames and the locally estimated speaking interval.

This is materially better than a fixed timer cycle and must not be replaced by another writer while its live promotion is in flight.

## Research v2 intent layer on `chatgpt-work/avatar-state-idle-expressions-20260912`

The isolated research layer adds a more general state-to-behaviour model with 16 intents:

`lip_press`, `mouth_corner_left`, `mouth_corner_right`, `lip_purse`, `micro_smile`, `jaw_shift_left`, `jaw_shift_right`, `nose_scrunch`, `nostril_flare`, `brow_pinched_micro`, `brow_raise_asym_left`, `brow_raise_asym_right`, `cheek_twitch_left`, `cheek_twitch_right`, `tongue_peek`, `tongue_out`.

The intent layer deliberately does not assume that all 16 have a production renderer yet. Missing local deformation/asset support stays unpromoted instead of being faked.

### Causal state channels

The adapter consumes already-existing daemon/page state rather than inventing a second mood authority:

- valence / current expression;
- arousal / broadcast-derived tempo;
- tension and fatigue / body-resource state;
- curiosity / surprise;
- presence + attention / gaze/presence readback;
- playfulness / recent self-emote category;
- uncertainty;
- speaking/listening/engaged gates.

A temporal filter gives different inertia to different channels. Presence and attention may rise quickly; tension, fatigue and playfulness decay more slowly. This prevents the face from snapping every status poll.

### Event law

For each idle act:

1. speech/special-expression/renderer ownership gate;
2. state-conditioned hazard;
3. novelty penalty against the last action and family;
4. action cooldown + family refractory + global refractory;
5. rolling duty-cycle budget;
6. randomized attack/hold/release envelope;
7. return to neutral;
8. event telemetry for rate and repetition auditing.

No modulo-time selection. No `setInterval` repeating a gesture. No deterministic round-robin.

## Frequency target

The current v1 opportunity law is intentionally active, but a static simulation of its scheduling constants indicates roughly ten successful quiet microgesture opportunities per minute in a neutral/free renderer state. That is likely too dense for a human-like idle face even though the gestures are randomized.

Target envelope for the next admitted tuning pass:

- quiet neutral: ~2–4 successful facial microgestures/minute;
- attentive/engaged: ~3–6/minute;
- high surprise/state kick: short temporary burst may exceed that, then refractory recovery;
- exhausted/heavy: ~1–3/minute;
- tongue peek: typically minutes apart, never a frequent idle tic;
- full tongue-out: rarer than tongue peek and only under strong playful state.

These are perceptual targets, not acceptance by themselves. Final tuning must use display-2 observation and telemetry.

## Production integration order

1. Finish/audit the in-flight v1 live promotion and preserve its receipt, including red/failed pre-promotion readbacks.
2. Prove exactly one production Avatar window on display 2 and healthy service/HTTP.
3. Observe `window.__idleFaceV1.snapshot()` over a bounded quiet interval and record event rate/history.
4. Verify speech suppression and special-expression exclusion in the same real page.
5. Tune only the installed module, with CAS against exact module SHA; do not rewrite `buehne.html` unless the include itself changes.
6. Add renderers incrementally for brow/cheek/jaw intents only when there is an exact asset or validated local-warp mechanism.
7. Keep tongue as an expressive punctuation event, not background noise.

## Acceptance boundary

A source payload or simulation is not live acceptance. Production idle-face acceptance requires:

- exact installed bytes/readback;
- singleton visible window;
- no second Chrome/kiosk;
- no speech collision;
- no sustained special-expression collision;
- non-periodic event intervals;
- bounded repetition and duty cycle;
- measured quiet event rate in target envelope;
- visual check that nose/mouth overlays do not expose seams during breathing/head roll;
- service/HTTP healthy after the existing page reload.

Until those observations exist, call the implementation `LIVE_CANDIDATE` or `COMPONENT_PASS`, not whole-avatar acceptance.
