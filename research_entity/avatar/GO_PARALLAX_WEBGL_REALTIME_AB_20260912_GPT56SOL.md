# GO — Avatar Guarded Depth-Warp WebGL Real-Time A/B — 2026-09-12

Status: **PASS AT ISOLATED REAL-AMD 60-FPS COMPONENT SCOPE; LIVE AVATAR MUTATION 0**

## Candidate under test

The candidate is the guarded single-texture depth warp already admitted at static scratch image-integrity scope:

- exact live head PNG remains the sole colour/identity texture;
- a precomputed signed control map contains continuous depth × silhouette guard × eye guard;
- the fragment shader performs one control lookup and one displaced live-head lookup;
- output alpha comes from the unwarped original head sample;
- candidate amplitude is driven around the non-falsified A≈1.0–1.25 source-pixel corridor.

## Why this benchmark exists

Two prior performance probes were intentionally not credited:

1. the first WebGL benchmark parser matched the JavaScript source literal rather than the rendered report — `EVIDENCE_INVALID / HARNESS_PARSER`;
2. the corrected renderer probe used Chrome virtual-time budgeting, which made `performance.now()` unsuitable for real elapsed-time performance — shader/hardware compatibility only, **zero performance credit**.

The present A/B removes virtual time entirely.

## Real-host execution

Receipt:

`go-avatar-gpt56sol-webgl-realtime-ab-20260912-0958` = PASS.

Host/runtime:

- machine: `ai-core-node`;
- real renderer: `ANGLE (AMD, AMD Radeon Graphics (radeonsi phoenix LLVM 20.1.2), OpenGL 4.6)`;
- WebGL 1 / OpenGL ES 2.0 Chromium interface;
- canvas: 620×414 at DPR 1;
- `gl_error = 0`;
- temporary localhost scratch server + temporary Chrome profile;
- no virtual-time flags;
- live avatar source hashes unchanged and live service remained active.

A/B ordering:

`BASE -> WARP -> WARP -> BASE`

Each stage used 45 warm-up rAFs followed by 300 requested animation frames (299 intervals measured). The same browser/renderer/canvas/textures were reused.

## rAF cadence result

Baseline pass 1:

- mean: 16.6659 ms;
- p50: 16.70 ms;
- p95: 16.70 ms;
- p99: 16.80 ms;
- max: 16.80 ms;
- >20 / >25 / >33 ms: 0 / 0 / 0.

Warp pass 1:

- mean: 16.6659 ms;
- p50: 16.70 ms;
- p95: 16.70 ms;
- p99: 16.80 ms;
- max: 16.80 ms;
- >20 / >25 / >33 ms: 0 / 0 / 0.

Warp pass 2:

- mean: 16.6662 ms;
- p50: 16.70 ms;
- p95: 16.80 ms;
- p99: 16.80 ms;
- max: 16.80 ms;
- >20 / >25 / >33 ms: 0 / 0 / 0.

Baseline pass 2:

- mean: 16.6662 ms;
- p50: 16.70 ms;
- p95: 16.80 ms;
- p99: 16.80 ms;
- max: 16.80 ms;
- >20 / >25 / >33 ms: 0 / 0 / 0.

Within this isolated component test, the guarded warp therefore introduces **no measured rAF cadence degradation relative to baseline**.

## Forced-finish microtiming caveat

The benchmark also executed short `draw -> gl.finish()` loops. Browser timer resolution quantized those values to roughly 0.1 ms steps, with many individual values reported as zero. They are not precise enough to claim a microsecond/absolute GPU cost or the absurd FPS figures derived from them.

Therefore:

- rAF cadence comparison: admitted bounded evidence;
- exact GPU milliseconds per draw: **UNRESOLVED**;
- whole live-avatar CPU/GPU overhead: **UNRESOLVED**.

## Promotion

Promoted:

- shader/control-map path executes on the real AMD ANGLE renderer;
- isolated 620×414 component A/B holds 60-Hz rAF cadence with no >20 ms intervals across both warp stages;
- no OpenGL error;
- no production mutation.

Still zero/open:

- production/live avatar parallax runtime credit;
- perceptual depth/lifelikeness improvement;
- long-run thermal/load impact inside the complete avatar scene;
- live eye/mouth/body interaction under the shader;
- whole-avatar acceptance.

## Next exact gate

The next blocker is **not performance** at isolated component scope. It is perceptual/identity value under final presentation conditions.

Required before a live feature gate:

1. matched final-size baseline vs A=1.0/A=1.25 visual readback;
2. verify the depth cue survives minification and film/camera treatment;
3. verify no visible identity drift around hair, nose, mouth, neck or eyes;
4. only then construct a reversible dormant production gate and repeat whole-scene FPS/load readback.
