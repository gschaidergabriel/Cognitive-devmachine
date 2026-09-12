# Shoulder residual action-envelope + whole-scene cost evidence — 2026-09-12

Status: **ACCEPTED_AT_SCOPE / SCRATCH RUNTIME / NO LIVE MUTATION / NO PRODUCTION PERFORMANCE CREDIT**

## Exact subject

- live `buehne.html` SHA-256 before run: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- body evidence source head: `d3c8f7a1f9901c0478fd6331844f87d61eb8eb10`
- real host: `ai-core-node`
- renderer: `ANGLE (AMD, AMD Radeon Graphics (radeonsi phoenix LLVM 20.1.2), OpenGL 4.6)`
- command receipt: `go-avatar-shoulder-residual-envelope-fullscene-gpt56sol-20260912`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

The live HTML SHA-256 was read again after both whole-scene repetitions and remained byte-identical.

## Deterministic residual action-envelope gate

The preregistered single-authority envelope uses:

- idle/breathing shoulder scale: `4.0`
- `schulterzucken`: target `0.0`
- `schulterdrehung`: target `0.0`
- `aufrichten`: target `1.5`
- `lehnen`: target `1.5`
- `gewicht`: target `1.5`
- entry ramp: `120 ms` smoothstep
- exit ramp: `180 ms` smoothstep
- chest residual: `0`

Result: `RESIDUAL_ENVELOPE_PASS`.

Maximum one-frame final-display displacement:

| action | target scale | max one-frame display step |
|---|---:|---:|
| aufrichten | 1.5 | 0.121252 px |
| lehnen | 1.5 | 0.121252 px |
| gewicht | 1.5 | 0.121252 px |
| schulterzucken | 0.0 | 0.194003 px |
| schulterdrehung | 0.0 | 0.194003 px |

All remain below the preregistered first-candidate temporal discontinuity bound of `0.35 px` per frame. Analytical entry and exit jumps remain zero because each smoothstep ramp begins exactly at the currently authoritative value.

## Real-AMD whole-scene additive-cost characterization

The existing exact-live page was served from scratch and measured twice in BASE vs SHADOW lanes. SHADOW retained the original DOM body and additionally executed the cached 399-vertex / 720-triangle residual WebGL body compositor from the page's existing rAF loop. This is deliberately conservative additive-cost measurement rather than replacement rendering.

Each SHADOW repetition used 45 resident display-resolution textures and reported WebGL error `0`.

### Repetition 1

- BASE mean FPS: `60.416667`
- BASE minimum sampled FPS: `60.0`
- SHADOW mean FPS: `60.2`
- SHADOW minimum sampled FPS: `59.0`
- SHADOW draws: `719`
- texture cache size: `45`
- prewarm: `1493.3 ms`

### Repetition 2

- BASE mean FPS: `60.583333`
- BASE minimum sampled FPS: `60.0`
- SHADOW mean FPS: `60.4`
- SHADOW minimum sampled FPS: `60.0`
- SHADOW draws: `703`
- texture cache size: `45`
- prewarm: `1787.1 ms`

Aggregate:

- BASE mean: `60.500000 FPS`
- SHADOW mean: `60.300000 FPS`
- additive delta: `-0.200000 FPS`

This characterizes the shoulder residual path as small relative to the current whole-scene budget on the admitted AMD renderer.

## Evidence fence

The preregistration explicitly forbids minting production performance credit from a headless-only microbenchmark. Therefore this result promotes only:

- deterministic action-envelope continuity;
- exact-subject real-host AMD execution of the residual compositor;
- bounded whole-scene additive-cost characterization;
- unchanged live source during the scratch run.

It does **not** promote:

- production/live shoulder residual;
- visible-window production 60-fps acceptance;
- perceptual superiority;
- installed/reversible live feature-gate acceptance;
- whole-avatar completion;
- HCU/GWT/J-Space/training credit.

## Next exact gates

1. Use the newly mapped visible production-display/runtime route for a visible exact-subject candidate, without modifying eye/head authority.
2. Obtain matched baseline/candidate screenshots plus runtime FPS/readback on the visible AMD path.
3. Require no neck-seam/ghost regression and at minimum no perceptual degradation at the calibrated scale `4.0`.
4. Only then construct a reversible dormant production feature gate; do not silently make the residual always-on.
