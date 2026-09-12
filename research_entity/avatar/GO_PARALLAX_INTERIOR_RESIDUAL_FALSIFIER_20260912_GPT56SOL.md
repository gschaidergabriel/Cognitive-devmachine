# GO — Avatar Interior-Residual Parallax Falsifier — 2026-09-12

Status: **REJECTED AT SCRATCH IMAGE-INTEGRITY SCOPE; LIVE MUTATION 0**

## Hypothesis

The naive four-slice compositor develops alpha holes once depth shifts become display-visible. A proposed repair kept the exact live head image as authoritative base/silhouette and added only an interior residual:

`base_rgb + interior_gate * (shifted_premult_depth - zero_premult_depth)`

Output alpha was forced byte-identical to the live base. Residual motion was suppressed near alpha edges. Three conservative mask/gain variants were tested over all 11 live roll states at 0.75–2.0 source-pixel amplitudes.

Versioned tool:

`research_entity/avatar/tools/parallax_interior_residual_gate.py`

Real-host receipt:

`go-avatar-gpt56sol-parallax-residual-gate-20260912-0901` = PASS execution, scratch/read-only.

## Result

The architecture does remove the silhouette-hole failure by construction:

- exact source alpha: PASS for every tested roll/variant/amplitude;
- live source hashes: unchanged;
- live service: active.

But it fails the more important identity/detail objective.

Representative `soft85_g075` results:

- A=0.75 (~0.303 CSS-px max front-layer excursion): worst eye shift ~0.292 CSS px; opaque/detail Laplacian ratio about `0.820–0.840`; core RGB p99 ~45 levels.
- A=1.00 (~0.404 CSS px): worst eye shift ~0.324 CSS px; Laplacian ratio about `0.803–0.825`; core RGB p99 ~60 levels.
- A=1.25 (~0.505 CSS px): worst eye shift ~0.343 CSS px; Laplacian ratio about `0.738–0.767`; core RGB p99 ~67 levels.
- larger amplitudes degrade further.

The full-gain variants behave similarly or worse. Narrowing the alpha gate from `soft75` to `soft85` does not materially recover detail because most high-alpha facial core pixels are common to both masks.

## Decision

**Reject interior additive residual as the production parallax representation.**

It fixes the alpha metric but still degrades the high-frequency identity signal once amplitude reaches a display-relevant range. This is the same class of Goodhart failure as the fixed-alpha normalizer, reached through a different compositor.

Do not spend further cycles tuning mask thresholds/gain on this representation unless new evidence shows a qualitatively different sampling path.

## Next representation

Use the accepted depth slices only to infer a continuous control field, but sample the original live head texture exactly once per output pixel:

`rgb_out(x) = live_head_rgb(x - depth(x) * amplitude * identity_guards)`

with:

- exact original alpha output;
- one texture sample rather than multiple shifted layer samples/re-normalization;
- displacement faded to zero near silhouette gradients;
- displacement faded to zero around exact per-roll eye anchors;
- local mapping derivative checked to prevent folds;
- all 11 roll states tested in real display-pixel units.

A versioned single-texture depth-warp falsifier is the next gate.

## Credits

Promoted:

- interior-residual candidate = PRODUCT_NEGATIVE at scratch image-integrity scope.

Still zero:

- live parallax integration;
- perceptual/lifelikeness gain;
- whole-avatar acceptance.
