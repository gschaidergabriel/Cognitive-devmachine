# Body player composition v3 — real-host result

Date: 2026-09-12
Execution boundary: real `ai-core-node`, AMD ANGLE/OpenGL 4.6, headless real-wall-clock Chrome
Live mutation: none
Result: **REJECT naive upload-on-selection compositor path**

## Exact result

The v3 gate used all six existing photographed action families for static composition checks and a production-shaped dynamic player path. The candidate was shoulder-only; mesh chest residual was zero.

Static composition evidence was strong:

| family | min alpha Jaccard | max deep-hole px | max RGBA MAE |
|---|---:|---:|---:|
| atmen | 1.0 | 0 | 0.0003555010 |
| aufrichten | 0.9999863192 | 0 | 0.0001051893 |
| gewicht | 1.0 | 0 | 0.0001256428 |
| lehnen | 1.0 | 0 | 0.0001090852 |
| schulterdrehung | 1.0 | 0 | 0 |
| schulterzucken | 1.0 | 0 | 0 |

The two body actions for which residual shoulder amplitude is required to be zero (`schulterzucken`, `schulterdrehung`) were exactly pixel-identical to the baseline path in the composition test.

However, the real-wall-clock dynamic path failed its preregistered performance gate:

- BASE: 53.8346 FPS mean; p95 33.3 ms; p99 50 ms; 35 intervals >33 ms.
- WARP: 52.2679 FPS mean; p95 33.4 ms; p99 50 ms; 34 intervals >33 ms.
- WebGL error: 0.

The BASE and WARP failure signatures are nearly the same while the previously isolated constant-texture mesh A/B held ~60 Hz with no >20 ms intervals. The new variable in v3 is the body-player texture-selection path (`texImage2D` on selected-image changes).

## Failure classification

`PRODUCT_NEGATIVE` for the **naive WebGL texture-update architecture**.

It is **not** evidence that the residual shoulder deformation itself is too expensive. It is also not permission to weaken the frame gate: baseline already violates it.

## Architectural consequence

Do not upload 1536×1024 body images synchronously on the animation frame in which the photographed pose changes.

Next discriminator:

1. build a display-resolution GPU texture cache outside the measured animation path;
2. reuse one texture object per unique body frame;
3. measured animation path may only bind already-resident textures + update tiny uniforms;
4. stress all six families at their real frame intervals, back-to-back (strictly harder than production idle scheduling);
5. retain the same static composition / zero-residual invariants;
6. separately gate zero-residual cached rendering against the final-size live `<img>` baseline before any production mutation.

The texture cache is a rendering cache only. Existing `ATMEN_BILDER`, `KOERPER_AKTIONEN`, `koerperCrossfade()` and the one body scheduler remain semantic authority.
