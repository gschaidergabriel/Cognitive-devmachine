# Single body-motion authority contract

Date: 2026-09-12
Status: integration contract; no live mutation

## Evidence that changed the design

The exact live subject `buehne.html` SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e` already contains a coherent body player:

- two body image layers (`koerper-schicht`, `koerper-schicht2`);
- one `koerperCrossfade()` image-switch authority;
- a 12-frame photographed breathing cycle at 330 ms/frame;
- one `KOERPER_AKTIONEN` scheduler for shoulder shrug, straighten, lean, weight shift and shoulder rotation;
- lazy image loading for rare actions;
- an existing independent damped `koerper-dreh` wrapper following the current head motion.

Therefore a second body scheduler, a second breathing oscillator that directly moves the visible plate, or a parallel action player is rejected as architecture duplication.

## Authority split

There shall be exactly three ordered layers of body motion:

1. **Semantic photographed pose authority** — the existing body frame player chooses the actual photographed source image and crossfade state. Existing `ATMEN_BILDER`, `KOERPER_AKTIONEN`, `koerperCrossfade()` and their scheduler remain authoritative.
2. **Residual microkinematic compositor** — one low-dimensional mesh deformation may add sub-pixel/asymmetric residual motion to the already-selected body image. It does not choose poses, actions or image files.
3. **Global body/head follow** — the existing `koerper-dreh` spring remains the outer transform and is not duplicated inside the mesh.

Order:

`existing image selection/crossfade -> residual mesh deformation -> existing koerper-dreh -> camera/film presentation`

## Required coupling law

The residual compositor must consume existing state rather than creating a competing scheduler.

- When ordinary photographed breathing is active and no discrete body action is active, the residual compositor may use only a small asymmetric shoulder/chest residual. It must not recreate the full breathing excursion already present in the 12 source frames.
- While a discrete photographed body action is active, the residual shoulder amplitude is attenuated toward zero. In particular `schulterzucken` and `schulterdrehung` must not receive a second large shoulder articulation.
- The residual timebase is the page's existing `requestAnimationFrame` timestamp. No additional 60-Hz timer is permitted.
- Crossfade source/opacity remains owned by the existing two-layer player. A future WebGL compositor must represent both currently selected layers during transition rather than forcing a new image scheduler.
- Zero residual amplitude must reproduce the existing rendered body baseline within the preregistered image gate.
- The exact neck lock remains mandatory so the mesh cannot fight head/body registration.

## Initial residual envelope

Conservative first production-shaped gate, not yet live:

- idle/no discrete action: residual scale `0.35` of the already-tested nominal scratch field;
- photographed breathing: chest component <= `0.15` nominal and shoulder asymmetry <= `0.35` nominal;
- `aufrichten`, `lehnen`, `gewicht`: residual ramps down to <= `0.15` nominal over 120 ms;
- `schulterzucken`, `schulterdrehung`: shoulder residual = `0`; chest residual <= `0.10` nominal;
- on action end: smooth ramp back over >= 180 ms; no step activation.

These are bounded discriminator values, not permanent artistic constants.

## Promotion gates

No production mutation until a composition gate proves on the exact current body assets:

1. baseline and zero-residual paths are equivalent at final display size;
2. both existing body crossfade layers can be represented without flash or ghost silhouette;
3. all action families run through the compositor without missing assets;
4. neck ROI remains unchanged at zero and bounded under residual deformation;
5. action-transition + residual envelope has no one-frame transform step above the preregistered limit;
6. BASE/WARP/WARP/BASE real-wall-clock A/B on the admitted AMD renderer retains the 60-Hz frame gate;
7. live source hashes are unchanged during the scratch gate;
8. only after those pass may a reversible dormant production feature gate be constructed.

## Current evidence scope

Already established independently on the real `ai-core-node` AMD renderer:

- the 399-vertex / 720-triangle body mesh executes with `gl_error=0`;
- BASE/WARP/WARP/BASE held ~60 Hz with no measured interval above 20 ms in the isolated component A/B;
- live HTML and `koerper_zero.png` hashes remained unchanged.

Not established yet:

- photographed-action x residual-mesh composition correctness;
- whole-scene cost;
- perceptual superiority;
- live production body-mesh credit.

The next discriminator is therefore composition correctness, not another isolated mesh benchmark.
