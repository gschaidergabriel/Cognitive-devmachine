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
- an existing independent damped `koerper-dreh` wrapper following the current head motion;
- an existing synchronized head/body breathing scale reaching about +1.2%, retained specifically to prevent the neck seam from slipping;
- global camera drift/micro-motion outside the body player.

Therefore a second body scheduler, a second breathing oscillator that directly moves the visible plate, or a parallel action player is rejected as architecture duplication. The residual candidate adds **no chest/breathing displacement**: photographed breathing + synchronized scale already own that degree of freedom.

## Authority split

There shall be exactly three ordered layers of body motion:

1. **Semantic photographed pose authority** — the existing body frame player chooses the actual photographed source image and crossfade state. Existing `ATMEN_BILDER`, `KOERPER_AKTIONEN`, `koerperCrossfade()` and their scheduler remain authoritative.
2. **Residual shoulder compositor** — one low-dimensional mesh deformation may add only the missing sub-pixel/asymmetric shoulder residual to the already-selected body image. It does not choose poses, actions, breathing phase or image files.
3. **Global body/head follow** — the existing `koerper-dreh` spring remains the outer transform and is not duplicated inside the mesh.

Order:

`existing image selection/crossfade + existing synchronized breathing scale -> residual shoulder mesh -> existing koerper-dreh -> camera/film presentation`

## Required coupling law

The residual compositor must consume existing state rather than creating a competing scheduler.

- When photographed breathing is active and no discrete body action is active, residual shoulder asymmetry uses the empirically calibrated final-display candidate scale `4.0`; mesh chest displacement is exactly zero.
- While a discrete photographed body action is active, residual shoulder amplitude is attenuated toward zero. `schulterzucken` and `schulterdrehung` receive exactly zero residual shoulder articulation.
- `aufrichten`, `lehnen`, `gewicht` use at most scale `1.5` in the next gate; this attenuated action value is still a hypothesis, not live credit.
- The residual timebase is the page's existing `requestAnimationFrame` timestamp. No additional 60-Hz timer is permitted.
- Crossfade source/opacity remains owned by the existing two-layer player. A future WebGL compositor must represent both currently selected layers during transition rather than forcing a new image scheduler.
- Zero residual amplitude must reproduce the existing rendered body baseline within the admitted image-fidelity gate.
- The exact neck lock remains mandatory so the mesh cannot fight head/body registration.
- Existing synchronized breathing transform/filter values are upstream inputs and must not be recreated in WebGL.

## Rendering cache law

A real-host discriminator falsified synchronous `texImage2D` upload on body pose-selection frames: both BASE and WARP dropped to roughly 52–54 FPS with p95 around 33 ms. Therefore texture upload in the measured animation path is forbidden.

The accepted scratch rendering architecture is:

- prewarm one display-resolution GPU texture per unique photographed body frame;
- retain existing paths/arrays as semantic authority; GPU textures are only a rebuildable rendering cache;
- measured rAF path performs only resident texture binding, tiny uniform updates and mesh draw;
- no synchronous image upload on a pose-transition frame.

On the real AMD renderer, 45 cached 620×414 RGBA textures consumed an estimated `46,202,400` bytes and took about `557.2 ms` to prewarm; a 777-frame all-family stress schedule then held `60.002 FPS`, p95 `16.7 ms`, with zero intervals above 20 ms in both BASE and WARP lanes.

## Calibrated residual envelope

Final-display scratch calibration across four real photographed breathing frames × six temporal phases selected the smallest tested measurable candidate:

- ordinary breathing/idle: shoulder residual scale `4.0`, chest residual `0`;
- scale 4 analytical peak vertical displacement at 620×414: ~`0.938 px`;
- scale 4 median pixels with channel delta >=3: `49`; max `203` (~0.0791% of display pixels);
- scale 4 neck ROI max delta: `0`; deep-hole pixels: `0`; minimum alpha Jaccard: `0.999948`;
- scale 3 failed the pre-registered signal floor (median changed pixels >=3 was 22 vs required 24);
- `aufrichten`, `lehnen`, `gewicht`: next-gate shoulder scale <= `1.5`; chest residual `0`;
- `schulterzucken`, `schulterdrehung`: shoulder residual `0`; chest residual `0`;
- action entry ramp >=120 ms; action exit ramp >=180 ms; no step activation.

Scale 4 is a bounded measurable candidate, not a perceptual-superiority claim.

## Promotion gates

No production mutation until all remaining gates pass on the exact current body assets:

1. both existing body crossfade directions are semantically reproduced without flash, ghost silhouette or meaningful alpha/color error;
2. all action families run through the cached compositor without missing assets;
3. neck ROI remains unchanged at zero and bounded under residual deformation;
4. action-transition + residual envelope has no one-frame transform step above the preregistered limit;
5. whole-scene BASE/WARP/WARP/BASE real-wall-clock A/B retains the frame-budget gate on the admitted AMD renderer;
6. a matched perceptual A/B shows benefit or at minimum no degradation at the calibrated scale;
7. live source hashes are unchanged during scratch gates;
8. only after those pass may a reversible dormant production feature gate be constructed and tested.

## Current evidence scope

Established on the real `ai-core-node` AMD renderer:

- 399-vertex / 720-triangle residual body mesh executes with `gl_error=0`;
- isolated constant-texture BASE/WARP held ~60 Hz;
- naive upload-on-selection compositor is rejected as a performance negative;
- cached display-resolution compositor held ~60 Hz under a stricter 777-frame all-family schedule with zero >20 ms intervals;
- final-display scale `4.0` is the first tested shoulder-only amplitude meeting the preregistered measurable-signal + neck/silhouette bounds;
- live HTML, daemon and body assets remained unchanged throughout these scratch gates;
- real `buehne_daemon.py` is running and the live scheduler has one self-chaining 22–50 s body-action lane plus photographed breathing fallback.

Not established yet:

- exact/accepted crossfade color/alpha equivalence at semitransparent silhouette edges;
- action-entry/exit residual envelope behavior;
- whole-scene cost with the compositor integrated into the full live render stack;
- perceptual superiority;
- live production body-mesh credit.

The next exact blocker is crossfade edge-fidelity characterization, followed by action-envelope and whole-scene shadow integration gates. No live body-mesh promotion before those close.
