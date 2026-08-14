# Original Retina executable artifact boundary delta

Run: `go-20260811T2029p0700-chatgpt-secondary-q23-temporal-feature-epoch`
Work package: `F-V01-06-DIGITAL-RETINA-MVC`
This is ordinary recursive baseline analysis; the sole GO OOB experiment remains `TEMPORAL_POLICY_EPOCH_ALIAS`.

## Finding

The end-of-lineage standalone `digital-retina@819dcac12253b7de45795239b44482627ade624f` retains a legacy `_GOLPU_LIBRARY = .../library_L3.npz` path declaration, but the recovered `frank_eye.py` execution path uses the imported `gol_library` module for the active archetype readout:

`_gol_lib_mod.analyze_with_library(img, size=32, ticks=15)`

and renders the returned library phrases.

The recovered `retina/vision/gol_library.py` constructs the archetype library from deterministic NumPy/OpenCV generators with explicit fixed RNG seeds. It does not require the historical `library_L3.npz` for this end-of-lineage semantic readout.

Therefore `library_L3.npz` is reclassified for the May-27 standalone end state as:

`LEGACY_ANCESTRY_ARTIFACT_NOT_ENDSTATE_EXECUTION_BLOCKER`

This does **not** erase its ancestry. Earlier Frank/Agentforge states may have used it and should retain lineage if reconstructing those exact historical states.

## Remaining executable-artifact blockers

1. `retina_v8.pt`: still an exact-weight blocker for the in-house CNN path. Source-level retraining is recoverable, but newly trained weights are reconstructed surrogates because the recovered training loop does not globally seed Torch stochasticity.
2. DINOv2 ONNX artifact: still required by `_load_dino()` for end-state DINO scene/attention features. Missing file disables that path explicitly rather than fabricating results.
3. Other public/pretrained model caches used by CLIP/YOLO/BLIP/Marian/etc. must be bound to exact model/revision/runtime identity when replayed; source package names alone are insufficient for a release-grade original baseline.

## Consequence

The original-baseline recovery plan should no longer waste effort treating `library_L3.npz` as a mandatory end-state binary. Search/recovery effort should prioritize the exact Retina-v8 weight and DINO artifact/model provenance, while preserving `library_L3.npz` only for earlier-state ancestry reconstruction.

No replacement claim is promoted. Whole Frank v0.1 acceptance remains unclaimed.
