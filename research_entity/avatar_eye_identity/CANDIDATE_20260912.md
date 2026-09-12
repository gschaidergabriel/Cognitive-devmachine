# Avatar Eye Identity — canonical masked-eye candidate

Status: **REVIEW/CANDIDATE ONLY — NOT LIVE, NOT CANONICAL, NO RUNTIME CREDIT**

Date: 2026-09-12

## Exact subject

The candidate is bound to the observed live visual subject:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `augen_blink/blink_000.png` SHA-256: `f7c0abd552a91e117f90880bc67c29f22311f1ed5b90a043b169e93495fff44f`
- `augen_blink/blink_006.png` SHA-256: `f7cc3fc538478c9a0f5748f2139a8bba7234f74aa59b634dc3f266caa237d0fa`
- `augen_gaze/rotglow_tracking_master.png` SHA-256: `e9222dde99c5bf84adf838cde2c23284ed1d7b4a5d05c24fe48954871cf64ced`

Any subject change requires re-measurement before promotion.

## Root cause supported by current evidence

The special-expression path currently changes eye identity by design:

- 308 RGBA expression frames exist at 1536x1024 and carry their own eyes.
- while `_sonderLaeuft` is true, `gazeSchritt()` suppresses the canonical `#pupillen-glow`;
- `blinzeln()` returns early while `_sonderLaeuft`, so the canonical photographed blink/eye patch is also absent;
- therefore a special expression can replace the recognizable eye identity even though head/roll registration is already repaired.

This is a state/layer-coupling defect, not evidence of a missing eye asset.

## Falsified naive approach

Do **not** keep the complete 319x152 blink patch permanently opaque.

Measured `blink_000` alpha covers almost the whole rectangle:

- non-zero alpha: ~98.61%
- alpha >= 128: ~91.58%
- alpha >= 240: ~83.04%

Mapped by the live CSS (`left:31%; top:12%; width:27%`) this would overwrite a large upper-face rectangle and damage expression information.

## Empirically isolated eye region

Use open (`blink_000`) vs closed (`blink_006`) max-RGB difference, restricted to the measured glow anchor, then reject photographic noise.

At delta-RGB >= 70 after a small morphological close, exactly two dominant connected components remain:

- left eye: approximately `(55,68)-(111,99)` in the 319x152 patch;
- right eye: approximately `(202,68)-(257,101)`;
- component sizes: 1119 and 1130 pixels.

At delta-RGB >= 120 they remain two components:

- left: `(60,70)-(107,98)`;
- right: `(209,70)-(254,98)`.

This cleanly separates the actual eyelid/eye movement from brow/forehead/photo noise.

## Shadow mask v1

Deterministic recipe used by the successful shadow measurement:

1. max RGB difference `blink_000` vs `blink_006`;
2. threshold `>= 70`;
3. restrict to `rotglow_tracking_master` alpha bbox expanded by 35 px;
4. morphological close 5x5;
5. retain exactly the two largest connected components;
6. union the real glow-alpha pixels;
7. hard dilate by 6 px;
8. feather by Gaussian radius 4 px.

Observed shadow hashes:

- mask SHA-256: `321ef6fa09c6dfb72ab9eb486d623b49d5a4e9c512ace80bfd09ef4e7f3867b0`
- masked open-eye candidate SHA-256: `8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9`
- shadow manifest SHA-256: `2e16c2fb6f7ed3b204a093707492826dd81bd146677604f3c07430ff9db41d95`

Impact on the 1536x1024 expression canvas:

- any non-zero eye-mask alpha: ~0.9863% of full canvas;
- alpha >= 128: ~0.5231%;
- alpha >= 240: ~0.4913%;
- outside the mask: **zero mutation by construction**.

This is the intended compromise: enforce one eye identity while preserving >99% of every expression frame untouched.

## 308-frame identity stabilization discriminator

The eye-only candidate was composited over every one of the 308 special-expression frames without altering source files.

Measured RGB standard deviation across expressions:

- alpha >= 240 core: `15.6430 -> 0.0296`, ratio `0.001892`, **99.811% reduction**;
- alpha >= 128 region: `15.7021 -> 0.1997`, ratio `0.012718`, **98.728% reduction**;
- feather region: `18.3649 -> 15.0302`, **18.158% reduction**, intentionally preserving a soft seam transition.

Range collapse:

- core median per-pixel RGB range: `171 -> 0`;
- core pixels with total range <= 1 RGB level: `34.65% -> 95.89%`;
- alpha >= 128 pixels with range <= 1: `34.76% -> 93.98%`.

Outside the candidate eye mask, measured maximum RGB delta is exactly `0`.

Interpretation: this candidate is not merely visually plausible; it deterministically collapses expression-dependent eye appearance to one photographed identity in the high-confidence eye core while leaving expression information outside the mask unchanged.

## Current staged runtime evidence

A concurrent integrator independently materialized `augen_blink_relief2/` assets on the real `ai-core-node`. Its open frame is byte-identical to this review candidate (`8ab1a11c...`). A reversible real-window A/B exercised those relief2 assets with direct HTTP readback and recorded 15/15 FPS samples at `60.0`.

Important scope fence: the persistent `buehne.html` observed after that A/B still had SHA-256 `18770d8e...`, did not persistently reference `augen_blink_relief2`, and retained the old `_sonderLaeuft` glow/blink coupling. Therefore asset runtime/performance evidence exists, but semantic eye-identity integration is **not yet live**.

## Minimal runtime design

Prefer reuse over a new rendering authority.

### Layer semantics

`#augen-blink` becomes the canonical photographed eye/eyelid identity layer, but is constrained by the eye-only mask.

Idle/open state:

- `#augen-blink.src = BLINK_BILDER[0]`;
- `#augen-blink.opacity = 1`;
- mask limits it to the two measured eye islands;
- this remains present during ordinary and special-expression faces.

Blink state:

- existing photographed `blink_000..011` sequence continues;
- the same eye mask applies to every blink frame;
- at blink completion, restore `BLINK_BILDER[0]` and keep opacity `1`, rather than hiding the layer.

Glow state:

- `#pupillen-glow` remains gaze/recognition driven;
- do **not** suppress it merely because `_sonderLaeuft` is true;
- suppress glow while `blinzelPhase` is non-null, so glow never paints through a closed lid;
- keep the glow above the canonical open-eye layer when the eye is open.

Special-expression state:

- remove the early return in `blinzeln()` for `_sonderLaeuft`;
- expression frames may change brow, cheeks, mouth, skin and head expression;
- their embedded eye pixels are deterministically covered only inside the measured canonical eye mask.

### Required z-order

Conceptually:

1. head / expression RGBA layer;
2. masked canonical eye/blink layer;
3. recognition-linked pupil glow while eye is open;
4. other effects only if they do not violate the eye mask.

Exact numeric `z-index` values may reuse current local values; preserve existing head/roll canvas and do not create a second transform authority.

## Roll / movement invariant

Do not reopen the already-repaired roll boundary.

The current live subject already uses atomic roll/eye geometry rather than the previous local 0.4 lerps. Any candidate must reuse the same `#kopf-dreh` parent and existing eye offset/roll transform path.

## Promotion gates

No live promotion unless all of these pass on the **same exact subject**:

1. deterministic mask generation hashes match;
2. candidate changes no pixels outside the intended eye mask in the offline 308-frame sweep;
3. canonical eye-region variance across all 308 expression frames drops materially;
4. special-expression blink works without duplicate eyes;
5. glow is visible only when its existing gaze/recognition law admits it and is hidden during actual lid closure;
6. roll poses keep eye registration with the head;
7. isolated browser A/B shows no seam/rectangle/ghost-head regression;
8. direct FPS readback remains 60.0 under the existing measurement method;
9. live write uses an exact SHA fence and has byte-exact rollback assets;
10. independent readback/falsifier confirms the post-write subject before any acceptance claim.

## Explicit non-credit

This candidate does **not** establish:

- live visual acceptance;
- semantic eye-identity runtime promotion;
- whole-avatar photorealism;
- GRID10/GWT/J-Space credit;
- training credit;
- whole-product completion.

It is an evidence-bound candidate intended for the current avatar integrator or an independent falsifier.