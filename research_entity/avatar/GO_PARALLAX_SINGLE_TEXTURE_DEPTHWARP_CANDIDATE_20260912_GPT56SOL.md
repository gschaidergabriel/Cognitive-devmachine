# GO — Avatar Single-Texture Depth-Warp Candidate — 2026-09-12

Status: **FIRST NON-FALSIFIED DISPLAY-SCALE PARALLAX REPRESENTATION; SCRATCH ONLY; LIVE CREDIT 0**

## Representation

Instead of shifting and recompositing the four RGBA depth slices, use them only as a control field.

The accepted live head image remains:

- the only colour/identity texture;
- the authoritative output alpha/silhouette;
- the exact eye-region source.

For each output pixel, infer a continuous signed depth coefficient from the four slice alpha fields and perform exactly one displaced lookup into the original head texture:

`rgb_out(x) = live_head_rgb(x - depth(x) * amplitude * guards(x))`

Identity guards fade displacement to zero:

- near source alpha/silhouette gradients;
- inside and around the exact per-roll eye anchor region.

Output alpha is copied byte-for-byte from the original live head.

Versioned falsifier:

`research_entity/avatar/tools/parallax_single_texture_depthwarp_gate.py`

Real-host receipt:

`go-avatar-gpt56sol-depthwarp-gate-20260912-0911` = PASS execution, no live mutation.

## 11-roll result

Two eye-protection radii were tested over all live roll states. The larger `eye220x125` variant is the preferred conservative candidate.

At A=1.00 source px:

- maximum display-space displacement: ~0.404 CSS px;
- p95 active displacement: ~0.403 CSS px;
- exact output alpha: PASS for all rolls;
- eye-region RGB MAE: 0;
- eye-region measured shift: 0;
- eye phase-correlation response: >=1.0 in this measurement;
- minimum local mapping derivative: ~0.500;
- opaque Laplacian detail-energy ratio: ~0.928–0.942;
- worst opaque RGB MAE: ~4.62 levels;
- worst opaque p99 RGB delta: 66 levels.

At A=1.25:

- maximum display displacement: ~0.505 CSS px;
- eye identity/shift remains exact/zero;
- minimum local mapping derivative: ~0.375;
- detail-energy ratio: ~0.925–0.936.

At A=1.50:

- ~0.605 CSS px max;
- minimum derivative ~0.250;
- detail-energy ratio ~0.918–0.929.

A=2.00 is not selected despite acceptable alpha/eye metrics because the minimum derivative collapses to about `0.00004`, i.e. near-singular local geometry.

A=2.50 is **rejected** because the derivative becomes negative (~`-0.25`), demonstrating an actual local fold.

## Comparison with previous representations

This is materially stronger than both rejected repairs:

- normalized fixed-alpha reconstruction at A=1.0: strong blur and ~0.9 source-px eye movement;
- interior additive residual: exact alpha but only ~0.80–0.84 detail-energy ratio already around A=0.75–1.0 and nonzero eye motion.

The single-texture warp preserves the eye region exactly by construction and retains substantially more high-frequency energy while producing a display-relevant displacement.

## Candidate corridor

Current non-falsified corridor:

`A = 1.00 ... 1.25 source px`

This corresponds to roughly `0.40 ... 0.50 CSS px` front-depth displacement at the measured live window geometry. The front/back relative excursion can be larger because inferred depth spans approximately `-0.955 ... +1.0`.

This is a candidate corridor, not a perceptual acceptance.

## Next gates before any live mutation

1. Re-evaluate at final rendered display dimensions (~620×414 head canvas at DPR1), because source-resolution Laplacian loss is not itself the perceptual output metric.
2. Implement the same formula in a scratch WebGL2 shader and measure real browser frame cost/jank.
3. Couple amplitude to a bounded head/body motion signal rather than running an independent oscillator.
4. Verify temporal return to exact A=0 identity and no eye/blink/mouth registration regression.
5. Only then construct a reversible dormant/live feature gate.

## Credits

Promoted:

- single-texture guarded depth warp: **CANDIDATE_NOT_FALSIFIED** at static scratch image-integrity scope;
- A>=2.0: unsafe/near-singular, with A=2.5 PRODUCT_NEGATIVE via actual fold.

Still zero:

- perceptual depth/lifelikeness credit;
- production GPU/runtime parallax credit;
- whole-avatar acceptance.
