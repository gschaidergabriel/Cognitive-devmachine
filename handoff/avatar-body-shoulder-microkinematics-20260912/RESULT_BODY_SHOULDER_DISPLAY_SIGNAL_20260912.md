# Final-display shoulder residual calibration — accepted scratch signal

Date: 2026-09-12
Execution: real `ai-core-node`, AMD ANGLE/OpenGL 4.6
Live mutation: none
Scope: scratch calibration only

## Result

The pre-registered final-display sweep tested shoulder-only residual scales
`0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8` on four real photographed breathing plates and six temporal phases at the actual 620×414 compositor size.

Selection rule required all of:

- median pixels with channel delta >=3: at least 24;
- changed fraction with delta >=3: at most 3%;
- exact neck-lock ROI: max delta 0;
- deep holes: 0;
- alpha silhouette Jaccard >=0.9995;
- analytical peak vertical display displacement between 0.25 and 1.0 px.

**Selected scale: 4.0**

Observed at scale 4:

- analytical peak vertical displacement: `0.93796875 px` at 620×414;
- median changed pixels >=3: `49`;
- maximum changed pixels >=3: `203`;
- maximum changed fraction >=3: `0.000790868` (~0.0791% of display pixels);
- max RGBA MAE: `0.0043030`;
- minimum alpha Jaccard: `0.9999481744`;
- max neck ROI delta: `0`;
- max deep-hole pixels: `0`.

Scale 3 did not pass the signal rule (median changed pixels >=3 was 22), making scale 4 the smallest tested candidate that produced a measurable final-display shoulder signal while remaining inside all geometry/neck bounds.

## Interpretation

This is **not** a perceptual-superiority claim. It establishes a bounded, visible-on-the-final-raster amplitude for the next A/B candidate. The result replaces the earlier provisional `0.35 nominal` residual with an empirically calibrated shoulder scale of `4.0` for ordinary idle/breathing only.

Discrete photographed actions remain attenuated:

- `schulterzucken`: residual shoulder scale 0;
- `schulterdrehung`: residual shoulder scale 0;
- `aufrichten`, `lehnen`, `gewicht`: next-gate hypothesis <= `1.5` (not yet perceptually promoted);
- chest residual remains 0 everywhere.

No live production credit is minted by this scratch calibration.
