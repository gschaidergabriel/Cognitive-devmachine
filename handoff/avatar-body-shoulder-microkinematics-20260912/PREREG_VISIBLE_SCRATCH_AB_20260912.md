# Visible scratch shoulder-residual A/B — preregistration — 2026-09-12

Status: **PREREGISTERED / SCRATCH ONLY / NO LIVE MUTATION**

## Exact parent evidence

This gate starts from branch head `14e1a18551dcee44fb79f372d2f48766eafa94b6` and the already accepted-at-scope shoulder residual evidence:

- live `buehne.html` subject SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`;
- calibrated idle/breathing shoulder residual scale: `4.0`;
- discrete-action envelope already bounded separately;
- whole-scene hidden-shadow AMD characterization already passed at scope;
- production Avatar remains the existing `FranKenstein -- live` Chrome on display 2 and MUST NOT be replaced or restarted by this gate.

## Purpose

Close one missing boundary between headless/scratch compositor evidence and a physically visible X11/browser candidate. The candidate must be visibly rendered by a separate, isolated **SCRATCH** Chrome window on the non-production monitor while the real display-2 production window remains untouched.

This is deliberately **not** a production promotion gate. It asks only whether the residual compositor can become the visible body path in a real non-headless AMD Chrome window while preserving runtime health and exact live-source invariance.

## Hard invariants

1. Live `/home/ai-core-node/.claude/star/visual/buehne.html` hash is read before and after and must stay exactly `18770d8e...`.
2. Existing production Chrome PID set and `FranKenstein -- live` X11 window ID must be unchanged before/after.
3. Scratch Chrome uses its own temporary `--user-data-dir`, its own temporary HTTP port and title `FRANK_SHOULDER_AB_SCRATCH`.
4. Scratch window must be placed on the left/non-production monitor (`x < 1680`), never on HDMI-A-0 display 2.
5. No service restart, no source write, no production DOM injection.
6. Candidate affects only the body representation. Head/eyes/blink authority remains the page's original DOM path.

## Candidate

Use the previously measured 399-vertex/720-triangle residual WebGL body compositor with shoulder scale `4.0`. Unlike the earlier hidden-shadow cost gate, this gate inserts the canvas into `#koerper-dreh` and, only after WebGL readiness, temporarily hides the two original body image layers **inside the scratch page only** so the WebGL result becomes the visible body.

The shader must account for current computed opacity of the two body crossfade layers rather than simply compositing both at opacity 1.

## Measurement

- BASE phase: original DOM body visible in scratch Chrome.
- CANDIDATE phase: WebGL body canvas visible, original scratch body layers hidden.
- FPS telemetry sampled in both phases from the page's existing `window.__buehneFps`.
- Candidate metadata must attest WebGL renderer, texture count, draw count and `gl_error`.
- Capture one X11 screenshot in each phase from the exact scratch window; record SHA-256 and dimensions.
- Record scratch window geometry plus production PID/window IDs before and after.

Because the live scene is dynamic, BASE and CANDIDATE screenshots are **physical/readback evidence**, not a matched-pixel equivalence test. Pixel-level shoulder/neck geometry remains grounded in the prior deterministic same-frame calibration. Do not infer perceptual superiority from this pair alone.

## Pass criteria

All must hold:

- exact live HTML hash unchanged pre/post;
- production Chrome PID set unchanged pre/post;
- production X11 window ID unchanged pre/post;
- scratch window found and located entirely on the non-production monitor;
- BASE screenshot exists, non-empty, expected window class dimensions;
- CANDIDATE screenshot exists, non-empty, same dimensions;
- renderer string contains AMD/Radeon;
- `gl_error == 0`;
- candidate draw count > 100;
- texture cache >= 12;
- BASE valid FPS mean >= 58 and minimum >= 55;
- CANDIDATE valid FPS mean >= 58 and minimum >= 55;
- no candidate initialization error.

## Promotion fence

PASS promotes only: **visible non-headless scratch AMD body-residual execution with bounded runtime health and unchanged production subject**.

It does not promote production activation, perceptual superiority, whole-avatar acceptance, eye/blink acceptance, HCU/GWT/J-Space or training credit.
