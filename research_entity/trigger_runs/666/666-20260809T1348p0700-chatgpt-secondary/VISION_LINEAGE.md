# Level-0 Shard — Project-Frankenstein Adaptive Vision / FrankEye / Native Vision

## Scope

This shard reconstructs the Project-Frankenstein runtime perception lineage and reconciles it with the already-assimilated Drive Digital Retina learning lineage and the current owner-fixed FRANK 0.1 adaptive visual learning directive.

It intentionally separates two meanings that historical naming can blur:

- **adaptive visual inference** = cheap first-stage perception plus conditional escalation;
- **adaptive visual learning** = persistent user-specific familiarity state that updates over time under provenance, calibration, replay and rollback controls.

The historical Project-Frankenstein `Adaptive Visual Pipeline` provides evidence for the first. The Drive Digital Retina lineage provides stronger evidence for prototype/dictionary learning ancestors of the second.

## Chronology

### 2026-02-25 — adaptive compute escalation

Commit `90596662837a75801fd2024069ee9bd547137869` introduced a two-stage path:

1. YOLO + OCR + scene heuristics (~100 ms),
2. VLM only when escalation triggers (~800 ms stated in code comments).

The VCB bridge attempted this adaptive path first and retained the old Ollama path as fallback. This is an important low-latency routing ancestor, but no evidence in the inspected mechanism establishes personal online classifier learning.

### 2026-03-19 — FrankEye consolidation

Commit `0fd27f23e87cd1f0b53ce838347d1cdbcb7bd9bb` deleted `frank_visual_pipeline.py` and `frank_adaptive_vision.py` and replaced them with `tools/frank_eye.py`.

FrankEye merged:

- Digital Retina v8 CNN classification;
- DINOv2 INT8 ONNX scene features;
- HOG/color and additional fixed visual features;
- OCR;
- face detection;
- optional GoL analysis.

The CNN path is explicitly marked `inference only`. The module had a fast/deep split, but not the previous explicit conditional VLM escalation and not a personal cyclic learner.

### 2026-03-24 — screenshot-domain correction

Commit `279eb175a326cefdb1bbd8281ae1a639ce1e4986` added screenshot-specific app/browser-tab/UI analysis, dark-theme OCR preprocessing and recognition of Frank's own WebUI, while removing CIFAR-10 classification from screenshots as useless/noisy.

This is a valuable negative result: generic classifier output can actively degrade a different visual domain even when the classifier itself is valid on its training distribution. Current familiarity routing therefore needs domain-aware calibration and an unknown/escalate path.

### 2026-03-31 — native multimodal simplification

Commit `6158be8ddde637fbf6b78e820239bf4ee8e8b5ee` replaced FrankEye with `tools/native_vision.py`, which sends images directly to Qwen3.5-4B native vision through llama-server.

The file explicitly says the path replaces FrankEye entirely and uses no CNN, DINOv2, ONNX or Tesseract. It therefore simplifies semantic vision integration, but does not preserve personal familiarity state or the old explicit cheap detector-first escalation inside this module.

## Cross-source reconciliation

The current FRANK 0.1 visual directive is not a simple resurrection of one old implementation. It is a synthesis of historical strengths that previously existed in different places/times:

- Project-Frankenstein: cheap/conditional escalation and later task-specific screenshot handling;
- Drive Digital Retina: learned dictionary/centroid/prototype mechanisms, cached replay and threshold calibration;
- current directive: user-scoped provenance tiers, open-set semantics, candidate-vs-current shadow evaluation, versioning, rollback and bounded cyclic updates.

A testable candidate shape is therefore:

`change/region gate -> reusable frozen feature -> user-adaptive MVC -> calibrated known/unknown/conflict gate -> familiar fast path OR deeper native multimodal/Retina escalation`

Native Qwen vision is a candidate deep path, not a substitute for the fixed Micro Visual Classifier requirement.

## Negative results preserved

- Historical `adaptive vision` does not equal user-specific online learning.
- CIFAR-10 classification was removed from screenshot perception as useless/noisy.
- Native multimodal vision by itself does not provide personal prototype/readout state, cyclic update governance or rollback.
- Classifier confidence/familiarity cannot be promoted to sensor truth.

## History-denominator refinement

A new connector route was discovered during this shard: `compare_commits`.

Comparing `3085d354aaf7a523b9389d6e9deaab1ca990758f` to frozen HEAD `abba90a5767d85abc8a1ac340bae92842dab35c1` reports `ahead_by = 406`, giving a verified interval of 407 commits including the base commit. However, the base is not proven to be the repository root: it modifies already-existing files and refers to earlier removals, while the connector still lacks an exhaustive parent-paginated commit-list/tree enumeration surface.

Therefore the Project-Frankenstein history denominator remains unfrozen. The previous generic blocker can now be sharpened to: **at least a 407-commit verified interval exists, and earlier history plus the recursive tree still need exhaustive enumeration.**

## Coverage / promotion

- Exact Level-0 coverage credit from this shard: `0.0`.
- New historical earned-work hours: `0.0` pending row-level deduplication.
- No canonical scientific claim promotion.
- Durable receipt: `research_entity/archive_assimilation/receipts/666_20260809T1354p0700_chatgpt_secondary_pf_vision_adaptive_lineage.json`.
