# GO — Avatar Parallax Dynamic Scratch Sweep — 2026-09-12

Status: **DYNAMIC SCRATCH GEOMETRY CHARACTERIZED; CONSERVATIVE AMPLITUDE REGION IDENTIFIED; LIVE PARALLAX CREDIT 0**

This evidence packet continues from `GO_PARALLAX_CANVAS_ADDITIVE_ZERO_OFFSET_20260912.md`. No live avatar file was modified by the parallax experiments.

## Exact scratch experiment

Receipt:

`go-avatar-gpt56sol-parallax-dynamic-sweep-20260912-0749`

Execution boundary: real `ai-core-node`, separate scratch/headless Chrome profile.

Input pose: exact +00 roll head plus its four matching Depth-Anything slices.

Compositor: Canvas 2D `lighter`, already established to preserve zero-offset alpha exactly and visible RGB within 8-bit Canvas quantization.

Depth translation coefficients across the four layers:

`[+1, +1/3, -1/3, -1] * A`

where `A` is the maximum horizontal displacement in pixels.

This is a geometry/falsification sweep, not a visual-quality acceptance claim.

## Sweep results

At `A = 0`, alpha reconstruction remained exact: zero mean/max alpha error and zero hole/overdraw/silhouette deltas.

As displacement increased:

| max amplitude A | mean alpha abs error on visible px | high-alpha holes >8 | high-alpha holes >16 | new silhouette >8 (full canvas) |
|---:|---:|---:|---:|---:|
| 0.25 px | 0.511 /255 | 0.495% | 0.429% | 0.0291% |
| 0.50 px | 1.077 /255 | 0.669% | 0.502% | 0.0341% |
| 1.00 px | 2.601 /255 | 1.656% | 0.743% | 0.0382% |
| 1.50 px | 3.375 /255 | 3.448% | 1.319% | 0.0725% |
| 2.00 px | 4.866 /255 | 9.836% | 1.954% | 0.0764% |
| 3.00 px | 7.178 /255 | 16.426% | 5.182% | 0.1139% |

The slope is strongly nonlinear once displacement reaches roughly 1–2 px. Large displacement rapidly creates real opacity holes inside originally strong-alpha head pixels.

## Engineering interpretation

For the current 1536×1024 assets, **0.25–0.50 px maximum per-layer displacement is the conservative first dynamic A/B region**. It perturbs depth while keeping deterministic alpha damage low. `A >= 2 px` is rejected as a sensible first candidate because nearly 10% or more of strong-alpha pixels show >8 alpha loss.

This does not prove that 0.25–0.50 px is perceptually strong enough to improve lifelikeness. It only constrains a low-damage search region. Visual benefit remains an empirical A/B gate.

## Scratch render-cost observation

The same headless Chrome process issued 180 four-layer additive composites with sinusoidally changing amplitude and reported about `0.137 ms/frame` in its unthrottled microbenchmark.

This result is **not promoted to production FPS credit** because headless scheduling, command submission and GPU synchronization do not reproduce the live compositor/vsync boundary. It only indicates that four Canvas draw calls are not an obvious gross cost blocker.

## Independent post-experiment live readback

Receipt:

`go-avatar-gpt56sol-postgo-live-readback-20260912-0751`

After the scratch work, the real production avatar was re-bound to exact hashes and independently sampled again.

Observed:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`;
- HTTP root SHA-256: the same `18770d8e...`;
- `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`;
- `filmlook.js`: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`;
- `GPU_PROCESS_COUNT=1`;
- `RENDERER_COUNT=2`;
- `BAD_FLAG_COUNT=0`;
- production service active;
- 15/15 live telemetry samples at exactly `60.0 FPS` (`MIN=MEDIAN=MEAN=MAX=60.0`).

Therefore the scratch experiments did not mutate or degrade the accepted live subject.

## Next exact gate

The remaining parallax blocker is now **perceptual/registration causality**, not provenance, alpha mathematics, compositor selection or gross render cost.

Next candidate work should:

1. use Canvas additive compositing only;
2. start at `A = 0.25` and `0.50 px` rather than multi-pixel displacement;
3. render matched baseline/variant frames across roll states with the same eyes/blink/pose;
4. test eye-to-face registration and silhouette/seam/halo energy;
5. reject the variant if the depth cue is imperceptible or if it harms identity;
6. only then create a hash-gated reversible live candidate;
7. retain automatic rollback and independently re-read the live 60 FPS boundary after any promotion.

## Credits

- Parallax generator provenance: **PASS**.
- Alpha partition/static RGB consistency: **PASS**.
- Naive source-over: **REJECTED**.
- Canvas additive zero-offset primitive: **PASS**.
- Scratch dynamic geometry: **CHARACTERIZED**.
- Recommended first search region: **A = 0.25–0.50 px**.
- Perceptual lifelikeness benefit: **OPEN / 0 credit**.
- Live parallax integration: **0**.
- Live baseline: **UNCHANGED, exact subject re-read at 60 FPS**.
- GRID10 / GWT / J-Space / effects / training / whole-product credit: **unchanged**.
