# Avatar Idle Face V2 — state-driven microexpressions

Date: 2026-09-12
Target host: `ai-core-node`
Owner: `gabriel`
Live subject: existing singleton Avatar at `http://127.0.0.1:8788/` on display 2.

## Owner intent

Make the face visibly alive while silent, often but not constantly, with non-cyclic behavior derived from current state. Desired examples include nose wrinkle, asymmetric mouth motion, pout/smirk/jaw movement, tongue tip/out/side. Speech and existing special expressions must always win.

## Candidate

Source: `local_bridge/payloads/avatar_idle_face_v2.js`
Observed candidate SHA-256 in real-host preflight: `779d411b69c747584b1a1727dcf8a5e6eb415a45f42642d32840e71ff4c98f40`.

Design:
- recursive random opportunity scheduling, no new fixed `setInterval` expression cadence;
- exponentially distributed opportunity spacing with state-dependent hazard;
- weighted candidate competition from current expression/state, presence, surprise, speed, broadcast/self-category and crisis/load signals;
- per-expression cooldowns, recent-history suppression and energy/habituation budget;
- existing mouth transition engine (`mundZielSetzen`) and real expression assets;
- speech, `_sonderLaeuft`, active mouth frames and refractory periods suppress idle gestures;
- subtle independent nose overlay for scrunch/nostril motion;
- diagnostic state exposed as `window.__idleFaceV2.snapshot()` once installed.

Current real expression targets include:
`mund_20_grin_closed`, `mund_22_snarl_left`, `mund_23_snarl_right`, `mund_25_tongue_tip`, `mund_26_tongue_out`, `mund_27_tongue_left`, `mund_28_tongue_right`, `mund_29_whistle_small`, `mund_31_smirk_left`, `mund_32_smirk_right`, `mund_33_pout`, `mund_34_jaw_clench`, `mund_35_gasp`.

## Real-host preflight

Receipt: `local_bridge/results/receipts/avatar-idle-face-v2-preflight-20260912T0342Z.json`

PASS scope:
- candidate syntax accepted by `node --check`;
- `FIXED_INTERVAL_CALLS=0` for the new layer;
- live `buehne.html` still at pre-mutation SHA `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`;
- `frankenstein-buehne.service=active`;
- exactly one production Chrome app process;
- current mouth engine verified: six transition frames, ~22 ms/frame, then `mundAktivFrames=null`;
- host had ~14.4 GB MemAvailable at the preflight.

## Frequency calibration

Monte-Carlo calibration of V2's clamped exponential opportunity spacing, before exact cooldown/energy effects:

| State | Mean opportunity delay | Rough visible event interval |
|---|---:|---:|
| neutral | ~5.77 s | ~9.16 s |
| alert / soft | ~4.93 s | ~7.83 s |
| tense | ~4.71 s | ~7.47 s |
| exhausted | ~7.66 s | ~17.83 s |
| surprised | ~3.81 s | ~5.21 s |

This is intentionally non-periodic: the delay distribution is broad, with clamped tails, and a separate probability/cooldown gate decides whether an opportunity becomes an expression.

## Fail-closed live activation hold

**DO NOT PROMOTE V2 TO THE LIVE AVATAR WHILE CURRENT HOST TELEMETRY IS RED.**

The same real-host preflight recorded three consecutive `frankenstein-koerperpflege.service` entries at 10:21, 10:22 and 10:23 local:

`Stufe kritisch (temperatur:eng,dienste:frankenstein-gespraech-adhoc)`

Therefore live mutation/activation is intentionally held under the host-admission law. This is not an Avatar product negative.

A separate attempted V1 live apply also failed before mutation because the bridge checkout lacked the referenced apply script (`exit_code=2`). Preserve that failure; dispatch did not equal installation.

## Next admitted activation

Only after fresh host telemetry is non-red:
1. re-read exact live SHA and singleton process/window;
2. re-bind the newest candidate source SHA;
3. CAS-inject the layer inline into the existing `buehne.html` (do not invent `/idle_face.js`; daemon serves only its explicit JS route such as `/filmlook.js`);
4. syntax-check the combined inline JS before atomic replace;
5. reload the existing production Chrome window only — do not spawn another browser;
6. verify same display-2 subject, one Chrome app process, HTTP/service health and runtime diagnostics;
7. observe event timestamps/types long enough to prove non-periodicity, speech suppression and cooldown behavior;
8. only then promote this scope.
