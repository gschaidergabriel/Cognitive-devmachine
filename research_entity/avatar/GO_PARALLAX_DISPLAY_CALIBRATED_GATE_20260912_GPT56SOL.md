# GO — Avatar Parallax Display-Calibrated Gate — 2026-09-12

Status: **NAIVE LARGE-AMPLITUDE LAYER TRANSLATION FALSIFIED; PARALLAX LIVE CREDIT REMAINS 0**

## Why this gate was needed

Earlier real-Chrome scratch tests established a narrow integrity-safe region around 0.25–0.50 source pixels for the four-slice additive compositor. That was not yet a perceptual statement because the 1536×1024 head source is downscaled in the actual avatar window.

A real-host display/DOM readback therefore measured the current rendering scale before expanding amplitude.

## Exact live subject

- `buehne.html`: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js`: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`
- service remained `active` throughout.

## Real display scale

Receipt `go-avatar-gpt56sol-parallax-display-scale-20260912-0832` observed:

- primary HDMI output: 1024×600;
- visible Chrome window: 958×523;
- the live head canvas uses the source geometry 1536×1024 and computes `_kopfCanvasScale` from the face-frame object-fit cover geometry.

A separate isolated CDP geometry probe emitted the actual DOM numbers before suffering only a temporary-profile cleanup race:

- `#gesicht-rahmen`: about 620.75×332.05 CSS px;
- `#kopf-canvas`: about 620.35×413.86 CSS px;
- `_kopfCanvasScale = 0.4036458333333333`;
- DPR = 1.

Thus one source pixel is only about `0.40365` visible CSS pixels at this geometry.

The CDP command's terminal `FAIL` is classified **HARNESS_CLEANUP_FAILURE**, not product negative: the measurement was already fully printed, the only stderr was inability to remove a still-changing temporary Chrome profile directory, and the live hashes/service remained unchanged.

## Consequence for the old safe region

- A=0.25 source px → ~0.101 CSS px maximum front-layer shift.
- A=0.50 source px → ~0.202 CSS px.

These are valid subpixel motions, but they are too small to treat as an established visible depth cue merely from static integrity metrics. Perceptual credit remains zero.

## Display-calibrated extended real-Chrome gate

Versioned tool: `research_entity/avatar/tools/parallax_extended_css_gate.py`

Real-host receipt: `go-avatar-gpt56sol-parallax-extended-tool-run-20260912-0847` = PASS.

The exact Chrome Canvas2D `lighter` compositor was tested over all 11 current live roll states at amplitudes 0.75, 1.0, 1.25, 1.5 and 2.0 source pixels.

Worst-case results:

| source amp | max CSS shift | min mask Jaccard | deep-hole px | worst eye shift CSS | lost px | gained px |
|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | 0.303 | 0.995229 | 167 | 0.141 | 211 | 587 |
| 1.00 | 0.404 | 0.992655 | 462 | 0.202 | 590 | 614 |
| 1.25 | 0.505 | 0.990146 | 495 | 0.222 | 617 | 1014 |
| 1.50 | 0.605 | 0.989069 | 560 | 0.222 | 666 | 1137 |
| 2.00 | 0.807 | 0.985577 | 1028 | 0.545 | 1157 | 1223 |

This is a clear crossover: amplitudes large enough to become an obvious static pixel-scale depth displacement also create real alpha holes and rapidly worsening silhouette mismatch under the naive shifted-slice reconstruction.

By contrast, the earlier A=0.25/A=0.50 gate had zero deep-hole pixels across the same 11-roll ladder and worst source-space eye shifts <=0.10/0.25 px respectively.

## Decision

**Do not promote naive larger-amplitude translated depth slices.**

The current evidence supports two separate statements only:

1. low-amplitude additive slice motion is geometrically clean enough for temporal/perceptual testing;
2. simply increasing amplitude to make the effect statically obvious is not acceptable because silhouette/alpha defects appear before a large display-space excursion is reached.

This falsifies `AMPLITUDE_UP = SOLUTION`.

## Architectural next discriminator

The next candidate should preserve the exact live head as the authoritative silhouette/base image and inject depth motion only as an interior residual:

`live_base + gate(alpha, edge_gradient) * (shifted_depth_premul - zero_depth_premul)`

Properties to require before any live candidate:

- exact base alpha/silhouette by construction;
- no normalized-resampling blur of the fixed-alpha candidate;
- high-frequency detail energy near baseline;
- bounded eye-region displacement in real CSS pixels;
- amplitude tested in the 0.30–0.80 CSS-pixel range;
- no live source mutation until the scratch discriminator passes.

A versioned scratch falsifier for this residual architecture is the next legal step.

## Credits

Promoted:

- exact source-to-display scale at the measured window geometry;
- naive large-amplitude parallax = PRODUCT_NEGATIVE at scratch geometry-integrity scope.

Still zero:

- perceptual/lifelikeness improvement;
- live parallax runtime integration;
- whole-avatar acceptance;
- EntityOS/HCU/GWT/J-Space/training credit from this lane.
