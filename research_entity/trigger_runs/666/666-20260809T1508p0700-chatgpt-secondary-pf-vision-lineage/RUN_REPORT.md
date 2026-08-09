# 666 Level-0 Run — Project-Frankenstein Vision Lineage Reconciliation

## Result

Completed one non-overlapping Project-Frankenstein semantic/history shard and reconciled it against the already-assimilated Drive Digital Retina adaptive-learning lineage. No exact Level-0 percentage was added because the combined denominator remains unfrozen and the Project-Frankenstein recursive tree/history surface is still incomplete.

## Sources

- `90596662837a75801fd2024069ee9bd547137869` — adaptive visual pipeline introduction
- `tools/frank_adaptive_vision.py@90596662837a75801fd2024069ee9bd547137869`
- `0fd27f23e87cd1f0b53ce838347d1cdbcb7bd9bb` — FrankEye unification / old adaptive vision removal
- `279eb175a326cefdb1bbd8281ae1a639ce1e4986` — screenshot-specific FrankEye correction
- current `tools/frank_eye.py` at frozen Project-Frankenstein head surface
- current Project-Frankenstein `README.md`
- prior Drive Retina receipt `666_20260809T1203p0700_chatgpt_secondary_drive_retina_adaptive_learning_lineage.json`

## Main findings

Project-Frankenstein first implemented a real two-stage visual routing architecture: cheap detector/OCR evidence first, then a local VLM when confidence or question/scene triggers demanded escalation. The old source hard-coded a 0.55 threshold and claimed roughly 90% of images would avoid VLM; that claim is preserved as a source-code design claim, not promoted to benchmark evidence.

On 2026-03-19 the project deliberately collapsed this branch into `tools/frank_eye.py`, removing the former adaptive-vision and VLM bridge paths. FrankEye combined Digital Retina v8 CNN classification, DINOv2, GoL/GOLPU-derived features, OCR and face analysis into one CPU-only sensing pipeline. The current file explicitly marks the Retina CNN as `inference only`.

A later 2026-03-24 correction removed CIFAR-10 classification from screenshot handling because it produced useless output, replacing that part of the path with screenshot-specific app/browser/OCR handling. This is a concrete historical negative result: visual modality changes which readout is useful.

Cross-source reconciliation shows that Drive Digital Retina and Project-Frankenstein FrankEye are complementary but not equivalent ancestors. Drive preserves learned dictionary/prototype/replay/calibration mechanisms; Project-Frankenstein preserves low-cost selective routing and later unified CPU sensing. The adaptive learning mechanisms did not simply survive inside current FrankEye by virtue of the Retina/FrankEye name lineage.

## Current inheritance

- Frank/H3: keep a dissolved low-latency visual sensor plane, but add user-specific familiarity learning as a separate versioned, reversible, non-authoritative state layer.
- Harness: test photo/screenshot modality mismatch explicitly; compare FrankEye-only, embedding-prototype MVC and historical GoL-signature prototype MVC on the same replay set.
- ClayCode: encode sensor evidence, familiarity version, modality route, escalation decision, calibration and rollback as distinct typed state/effects.
- UnifiedDB/ClayGraph: preserve feature/classifier/prototype lineage and modality calibration separately from raw sensor evidence and semantic claims.
- GWT: broadcast visual evidence with its uncertainty and route provenance; generic classifier labels are not global truth.

## Negative-result value

- CIFAR screenshot labels were removed as useless.
- Hand-coded escalation confidence is not calibrated open-set recognition.
- Current FrankEye does not satisfy the current user-adaptive Micro Visual Classifier requirement by itself.
- Naming continuity must not be mistaken for mechanism continuity across refactors.

## Global gate

Level 0 remains `NOT_PASS`. Drive root structure is already closed, but the combined exact denominator is still `NOT_FROZEN`; Project-Frankenstein full tree/history enumeration remains the hard blocker on the current connector surface. This run therefore contributes semantic/history reconciliation only and assigns zero exact coverage credit and zero new earned-work hours.
