# 666 Level-0 Run Report — 2026-08-09 14:24 +07:00

## Run

- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent observed: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- mode: `L0_ARCHIVE_ASSIMILATION`
- release gate observed: `NOT_PASS`
- exact Level-0 coverage observed: `0.0%` because the combined denominator is not frozen

## Current source state refreshed

- Drive `clay` root was re-read through the connected Drive surface.
- The root still contains 14 direct entries, all folders, zero files. This is consistent with the current workspace statement that Drive structural-root enumeration is closed.
- Project-Frankenstein remains frozen at `abba90a5767d85abc8a1ac340bae92842dab35c1` for Level-0 analysis.
- The current hard blocker remains exhaustive Project-Frankenstein tree/history denominator construction because this ChatGPT GitHub surface has query/file reads but no recursive clone/tree-history enumeration primitive.

## Executed shard

### Project-Frankenstein visual self-model drift / Retina lineage

Files inspected at frozen HEAD:

- `tools/native_vision.py`
- `tools/frank_eye.py`
- `ext/feature_trainer.py`
- `personality/self_knowledge.py`

Operational wiring search additionally found NativeVision references in:

- `gateway/app.py`
- `agentic/loop.py`
- `ui/webui/app.py`
- `ext/sovereign/vcb_integration.py`
- `services/tools.py`
- `tools/screenshot_region_selector.py`

### Finding

The same frozen HEAD preserves two materially different visual architecture states:

1. `tools/native_vision.py` presents NativeVision as the Qwen3.5-4B multimodal bridge and explicitly says it replaces FrankEye entirely, without CNN, DINOv2, ONNX or Tesseract in that path.
2. `tools/frank_eye.py` preserves the older composite pipeline: Retina v8 CNN + DINOv2 + GOLPU-derived features + Tesseract OCR + OpenCV face detection.
3. `ext/feature_trainer.py` still encodes the older FrankEye/Retina stack as present-tense scoring `GROUND_TRUTH`, including the statement that FrankEye is CPU-only and uses no VLM.

This creates a concrete self-model/architecture-drift risk: if the feature trainer remains active, Frank can be trained to confidently describe a superseded visual backend as current while operational code has migrated to NativeVision.

## Interpretation

Do not resolve this by deleting the legacy side. The older Retina/FrankEye code is valuable Level-0 historical mechanism evidence and may contain reusable local visual learning/familiarity ideas needed by Frank v0.1's mandatory adaptive Micro Visual Classifier. The correct integration is versioned lineage:

`FrankEye/Retina legacy mechanism lineage -> NativeVision current perception path`

with a separate adaptive personal learner layer and truthful self-model metadata for whichever backend is actually active.

## Counterhypotheses

- NativeVision may not be selected on every runtime path. Multiple operational references weaken the hypothesis that it is unused, but runtime execution was not performed in this ChatGPT shard.
- `feature_trainer.py` may be historical or disabled. File presence does not establish active training; service enablement and recent training receipts are the next discriminating checks.

## Branch feedback

- **FRANK:** version sensor backend, learner backend and self-model claims independently.
- **Harness:** add regression that runtime visual backend receipts agree with self-reported architecture.
- **ClayCode:** encode backend version/provenance explicitly so sensor, learner and self-model semantics cannot collapse silently.
- **ClayGraph:** preserve FrankEye -> NativeVision as supersession/migration lineage and retain reusable Retina mechanisms as historical nodes.
- **UnifiedDB:** store backend/version/provenance separately from adaptive-classifier/prototype state.
- **GWT:** visual broadcast receipts should identify raw perception backend versus familiarity/learner contribution.
- **Emergenz:** backend substitution/stale priming is a confounder and must not be misread as emergent integration.
- **Hyperposition:** during migration, represent legacy/current visual alternatives explicitly rather than as hidden mixed state.

## Durable receipt

`research_entity/archive_assimilation/receipts/666_20260809T1424p0700_chatgpt_secondary_pf_visual_selfmodel_drift.json`

## Coverage / gate effect

- exact Level-0 coverage credit added: **0.0%**
- release-gate transition: **none**
- scientific/research delta: **yes** — a new repository-head contradiction/lineage finding was persisted
- canonical promotion: **not attempted**; this shard is evidence input, not authority to rewrite canonical state

## Next highest-information work

1. Trace exact runtime backend selection in `gateway/app.py` and `agentic/loop.py`.
2. Determine whether `feature_trainer.py` is enabled/current and whether `frankeye_vision` training was recently executed.
3. Continue Project-Frankenstein history search for Retina learning/familiarity/prototype/dictionary mechanisms relevant to the mandatory v0.1 adaptive learner.
4. Preserve the current hard blocker: exact Project-Frankenstein tree/history coverage still requires a recursive read-capable surface or equivalent exhaustive external manifest.

---

## Additional shard — SOMA safety/failure lineage delta

This shard cross-read and deduplicated against:
`research_entity/archive_assimilation/receipts/666_20260809T0421p0700_chatgpt_secondary_pf_lcme_soma_autonomy_shard.json`

The prior receipt already preserves the broad SOMA train/evaluate/deploy/rollback lifecycle, so this addition awards no duplicate earned-work hours.

### Sources

- `services/soma/interaction_buffer.py@abba90a5767d85abc8a1ac340bae92842dab35c1`
- `services/soma/safety_check.py@abba90a5767d85abc8a1ac340bae92842dab35c1`
- `services/soma/micro_trainer.py@abba90a5767d85abc8a1ac340bae92842dab35c1`
- initial SOMA commit `78f31e7f1e4fa7109a90f6e32514923ca7428a87`
- SOMA audit/fix commit `c16e5991466e50e059e176c07910ca75293b415c`

### Material findings

1. **Safety-gate implementation gap.** The frozen-head `safety_check.py` documents held-out perplexity/performance as its third gate, but the implementation does not execute a held-out behavioral test. It checks adapter drift, per-layer similarity, optional baseline drift and tensor sanity. This is retained as a negative/audit result.

2. **Failure lineage.** The SOMA audit commit records defects in score-schema mapping, timestamp recovery, EMA key-set evolution, near-zero drift handling, threshold boundaries, large-object cleanup, background-thread shutdown and substring-based probe measurement. Adaptive learning therefore needs schema/version/concurrency/recovery tests in addition to model-quality tests.

3. **Feedback semantics boundary.** SOMA uses explicit user feedback plus heuristic quality signals as weighted training input. For visual learning, user labels/feedback must remain provenance-bearing supervision signals, not sensor truth.

4. **Transfer hypothesis for Retina/Micro Visual Classifier.** Strong candidate lifecycle:
`trusted labeled example + provenance/tier -> versioned candidate learner update -> held-out semantic tests -> state/weight sanity -> staged promotion -> last-known-good snapshot -> rollback/rebuild on regression`.

### Branch feedback delta

- **FRANK:** expose visual learner version identity and last-known-good rollback; supervision != sensor truth.
- **Harness:** inject mislabels, OOD classes, restart-mid-update, schema-version changes and concurrent shutdown; require exact rollback restoration.
- **ClayCode:** express candidate/promotion/rollback as typed provenance/authority/recovery transitions; parameter drift alone never proves promotion success.
- **UnifiedDB:** persist learner version, feature-backbone compatibility, example provenance/tier, calibration/open-set metrics, candidate state and rollback lineage separately from sensor facts.
- **ClayGraph:** learned familiarity remains a provenance-bearing weighted association, never automatic truth authority.
- **Emergenz:** NO_CHANGE — this adaptation lineage is not evidence for causal emergence or consciousness.

### Durable delta receipt

`research_entity/archive_assimilation/receipts/666_20260809T1424p0700_chatgpt_secondary_pf_soma_safety_failure_lineage_delta.json`

### Surface/blocker update

This run verified that the GitHub connector now exposes a large bounded commit-history search surface plus direct commit diffs. It still exposes no recursive read-tree or exhaustive paginated tree/history denominator. The old blocker is therefore narrowed, not removed; exact Level-0 coverage remains unclaimable until the exhaustive denominator is externally obtainable and reconciled.
