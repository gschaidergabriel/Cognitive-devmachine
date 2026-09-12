# BODY WEBGL CONVERGENCE RECONCILIATION — 2026-09-12

Scope: reviewer/falsifier evidence for the existing photographed body player and residual shoulder mesh. This does **not** mutate the live avatar and does not mint whole-avatar/product credit.

## Exact subject

Live subject observed throughout the read-only body runs:

- `/home/ai-core-node/.claude/star/visual/buehne.html`
- SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- GPU renderer in performance attribution: `ANGLE (AMD, AMD Radeon Graphics (radeonsi phoenix LLVM 20.1.2), OpenGL 4.6)`

All accepted runs below preserved live source byte identity before/after.

## Reconciled findings

1. `body_dom_webgl_crossfade_screenshot_gate.py` v1 produced a severe DOM/WebGL mismatch (~21.85 max RGB MAE, ~61.7% changed area). That result is retained as negative evidence, but it is **not** valid evidence that the product compositor is wrong: the harness contained a double-Y convention (`UNPACK_FLIP_Y_WEBGL=1` plus shader `1.-p.y`) and later tests exposed additional stacked-canvas/render-synchronization confounders.

2. Correcting only the Y convention reduced the mismatch by about half (~10.56 max MAE). Therefore the Y error was real but not sufficient.

3. Clean paint-order evidence showed DOM source-over is normal B-over-A and closely matches Canvas2D at production geometry (max MAE ~0.174, p99 3). Reversing order was substantially worse (~2.78 max MAE, p99 45). Paint order is not the remaining blocker.

4. Robust per-case production geometry isolated the remaining residual to **texture downsampling**:
   - Canvas2D vs raw 1536x1024 WebGL upload with `LINEAR`: max MAE `0.8619409381`, p99 `15`, max changed>=3 `0.1734104722`.
   - Canvas2D vs source pre-resized to 620x414 before WebGL upload: max MAE `0.1045698925`, p99 `1`, max changed>=3 `0.0000038959`.
   - pre-resized/raw MAE ratio: `0.1213190926`.
   - classification: `RESAMPLING_KERNEL_ROOT_CAUSE_STRONGLY_SUPPORTED`.

5. Fail-closed direct DOM -> pre-resized WebGL closure (`BODY_DOM_WEBGL_PRERESIZE_ATTESTED/v5`) passed on the real host:
   - JS ready/status pixel: `[0,255,0]`
   - minimum DOM activity: `0.2772479352`
   - minimum GPU activity: `0.2773920835`
   - max DOM/GPU MAE: `0.2229117968`
   - max p99: `3`
   - max changed>=3 fraction: `0.0272167680`
   - classification: `PRERESIZE_DOM_WEBGL_ATTESTED_FIDELITY_PASS`.

6. The separate fail-closed 72-case attested harness that returned red status and `gpu_activity_fraction=0.0` is **EVIDENCE_INVALID / NONTERMINAL FOR PRODUCT SEMANTICS**, not a product-negative result. Its own readiness fence failed, so it correctly minted zero pixel-equivalence credit.

7. Real-host four-condition performance attribution isolates the cadence blocker on raw 1536x1024 texture uploads:
   - static_base: ~`60.003 fps`, p95 max `16.7 ms`, zero >20ms frames.
   - static_warp: ~`60.002 fps`, p95 max `16.7 ms`, zero >20ms frames.
   - player_base: ~`56.827 fps`, p95 max `33.3 ms`, 20 >20ms frames over two runs.
   - player_warp: ~`56.678 fps`, p95 max `33.3 ms`, 20 >20ms frames over two runs.
   - residual warp overhead: `0.00028 ms` static and `0.04637 ms` with player.
   - player/upload overhead: ~`0.93-0.98 ms` mean plus periodic 33.3ms stalls.

8. The same four-condition harness with body frames resized once and cached at 620x414 **before** the measured animation/upload loop closes the cadence gate while retaining the same 40 selected-image uploads:
   - static_base: `60.001676 fps`, p95 max `16.8 ms`, zero >20ms frames.
   - static_warp: `60.001676 fps`, p95 max `16.7 ms`, zero >20ms frames.
   - player_base: `60.002682 fps`, p95 max `16.8 ms`, zero >20ms frames, 40 measured uploads.
   - player_warp: `60.001676 fps`, p95 max `16.7 ms`, zero >20ms frames, 40 measured uploads.
   - measured player/warp overhead collapses to timer noise (`<=0.00028 ms`).
   - classification: `PRERESIZED_BODY_PLAYER_WARP_50FPS_HEADROOM_PASS`.

The shoulder residual mesh is therefore **not** the performance blocker. Large-frame texture uploads are the measured blocker. Pre-resizing from 1536x1024 to 620x414 reduces upload pixel count to ~16.32% of the original while simultaneously fixing fidelity and restoring stable 60 Hz cadence at this real-host component scope.

## Current engineering decision

Promote only this candidate architecture for the next body-player integration discriminator:

`photographed body state -> one-time/cached high-quality resize to 620x414 -> WebGL texture upload on selected-image change -> existing source-over blend -> existing residual shoulder mesh`

Do not promote the old raw 1536x1024 direct-upload path as the production default.

Prefer caching resized sources (or equivalently precomputed 620x414 assets) so the resize is outside the animation hot path. Preserve source-space mesh coordinates/semantics unless a separate discriminator proves a reason to change them.

## Closed gates at exact scope

- real-host production-shape pre-resized DOM/WebGL fidelity: PASS;
- real-host cached-pre-resize dynamic player cadence with residual shoulder warp: PASS;
- residual shoulder-mesh compute overhead as primary blocker: falsified;
- raw full-resolution texture-upload path as acceptable cadence baseline: falsified.

## Open gates

- exact live-runtime insertion point and current mutation ownership;
- shadow/integration A/B against the byte-exact live subject before any live replacement;
- integrated visual + cadence gate with the actual live scheduler/state transitions rather than the isolated player harness;
- rollback/hash/HTTP-readback fences for any eventual live promotion;
- whole-avatar interaction with canonical eye identity route and head/body coupling;
- no HCU/GWT/J-Space/training credit from these presentation-layer results.

## Zero-credit boundaries

Still zero/not established by this packet:

- live body WebGL promotion;
- whole-avatar acceptance;
- whole EntityOS product acceptance;
- physical GRID10 credit;
- semantic GWT/J-Space credit;
- effect authority credit;
- training credit.
