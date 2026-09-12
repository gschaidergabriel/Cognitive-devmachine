# Source-over identity v1 — invalid harness result

Date: 2026-09-12
Classification: **EVIDENCE_INVALID / HARNESS_ORIENTATION_BUG**
Product credit: none
Product negative: none

The first real-host source-over identity run produced catastrophic whole-frame disagreement in both layer directions (RGBA MAE about 60, alpha MAE about 150, Jaccard near zero). That signature is incompatible with the intended narrow question of source-over versus WebGL alpha ordering and immediately exposed a harness orientation error.

Root cause in v1 vertex/upload path:

- texture upload set `UNPACK_FLIP_Y_WEBGL = 1`;
- vertex shader also used `uv = vec2(p.x, 1.0 - p.y)`;
- readback was then row-flipped to top-left order for comparison.

The upload + UV path therefore inverted the source twice relative to the 2D reference. The result cannot be used to reject source-over composition.

Repair rule:

- retain `UNPACK_FLIP_Y_WEBGL = 1`;
- use `uv = p` on the full-screen quad;
- retain the readPixels bottom-up -> top-down row conversion;
- do not change the preregistered acceptance thresholds or source-over equations.

Only the corrected rerun can produce crossfade identity evidence.
