# 666 Level-0 Run — PF Native Vision Successor / Documentation Drift

## Result

Completed a second non-overlapping Project-Frankenstein history/current-code shard in the same `666` invocation. This extends the visual lineage beyond FrankEye into the frozen-head `native_vision` backend and records a material documentation/runtime contradiction.

## Sources

- `6158be8ddde637fbf6b78e820239bf4ee8e8b5ee` — 2026-03-31 native_vision introduction/routing switch
- `tools/native_vision.py@abba90a5767d85abc8a1ac340bae92842dab35c1`
- `README.md@abba90a5767d85abc8a1ac340bae92842dab35c1`
- preceding PF vision-lineage reconciliation receipt

## Main findings

At the frozen Project-Frankenstein head, `tools/native_vision.py` explicitly says Qwen3.5-4B native multimodal inference replaces FrankEye entirely. The implementation submits the image directly to the local llama-server and explicitly removes the CNN/DINOv2/ONNX/Tesseract stack from that runtime path.

The 2026-03-31 commit rerouted error screenshots, VCB integration and WebUI image analysis from `get_eye()` to `get_vision()`, so this is a real runtime successor.

The same frozen-head README still documents FrankEye as the active 937-line CPU-only vision pipeline. This is a direct current-source contradiction: executable routing says native Qwen vision; documentation says FrankEye. H1 baseline reconstruction therefore must privilege executable code and live receipts over README architecture prose.

NativeVision is still not the current v0.1 adaptive visual learner. It is a stateless semantic inference bridge; it does not supply user-scoped prototype/version state, trust-tiered examples, calibrated open-set familiarity, candidate promotion or rollback.

## Current inheritance

- H1/H3 should benchmark `native_vision`, FrankEye and a hybrid native-vision + MVC path on identical frozen visual corpora.
- Preserve backend identity/version and evidence class in ClayCode/UnifiedDB/ClayGraph.
- Treat native multimodal text as interpreted evidence, not raw sensor truth or trusted self-labels.
- Add a regression that checks architecture documentation against executable visual routing.

## Global gate

No exact Level-0 coverage or earned-work hours were added. The combined denominator remains unfrozen and the Project-Frankenstein recursive tree/history surface is still the hard Level-0 blocker.
