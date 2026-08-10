# Qwen-native Dissolved Retina Fusion Candidate — 2026-08-10

**Status:** CANDIDATE / NOT PROMOTED / REQUIRES H1-H3 DIFFERENTIAL EVIDENCE  
**Actor:** chatgpt-secondary / OpenAI GPT-5.6 Sol  
**Goal:** Frank v0.1 fully operational on Andreas Ubuntu developer system  
**Scope:** Digital Retina, dissolved perception, Qwen3.5-4B multimodal runtime, adaptive Micro Visual Classifier, GWT, UnifiedDB/ClayGraph, H1/H2/H3.

## 1. Research question

Given that the current FRANK 4B family is already natively multimodal, what causal function remains for Digital Retina, and can the current target be simplified so that Qwen's own vision tower becomes the shared deep visual feature core rather than operating beside a second heavy visual backbone?

This candidate preserves the project-owner fixed requirement that FRANK v0.1 has visual perception and adaptive user-specific visual learning. It does **not** preserve Retina as a separate semantic service. It refines the physical implementation candidate for the already-fixed dissolved-perception direction.

## 2. Internal evidence refreshed

Current owner-fixed contracts already say:

- Digital Retina is historical lineage, not a required independent cognitive process boundary.
- The H3 target is one FRANK module/runtime with sensor ingress, change/event extraction, perceptual transformation, Clay state projection, GWT/memory/world/action and re-entry integrated as far down the runtime stack as feasible.
- The Micro Visual Classifier must not be a second heavy vision model; it should reuse frozen features and learn only prototypes/linear/tiny readouts.
- A roughly 19-second anchor cadence is only a tunable candidate, not a frozen law.
- Full-frame, event/change-only, hybrid anchor/change and adaptive-familiarity paths must be compared.

Primary internal refs:

- `research_entity/global/FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md`
- `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`
- `research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md`
- `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md`

Historical local 4B evidence further shows the existing Qwen3.5-4B-abliterated Q4_K_M can satisfy the SE-XENO semantic bridge test when syntax framing is delegated to deterministic tooling, but long-session and multimodal Frank behavior remain unproven. The current runtime lineage already includes an `mmproj` for Qwen3.5 multimodal use.

## 3. Fresh external evidence

### E1 — Qwen3.5-4B is natively multimodal

Official Qwen/Hugging Face material exposes `Qwen3_5ForConditionalGeneration` with image and video tokens. Current config has a 24-layer vision tower with hidden size 1024, patch size 16 and spatial merge size 2, projecting to the text hidden size 2560.

Source:
- https://huggingface.co/Qwen/Qwen3.5-4B
- https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/config.json
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py

### E2 — The Qwen implementation exposes image features before language decoding

Transformers `get_image_features()` runs the visual tower and returns the vision `pooler_output`; those image embeddings are then inserted into the language-model input embeddings. This establishes a real physical interception point between visual encoding and 4B semantic decoding.

Source:
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py

### E3 — llama.cpp/libmtmd already has the same physical split

Current llama.cpp multimodal support uses `libmtmd`; an `mmproj` may contain the vision encoder as well as projection components. The public C API exposes `mtmd_encode_chunk`, `mtmd_get_output_embd`, `mtmd_batch_encode`, and `mtmd_batch_get_output_embd`. Current `llama-server` obtains the media embedding buffer from `mtmd_batch_get_output_embd` and then feeds that exact buffer into the LLM decode path.

This is the strongest implementation finding of this run: **Qwen vision features can in principle be consumed by a tiny familiarity/readout path and, on escalation, reused for the same semantic decode without re-running a second vision encoder.**

Sources:
- https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md
- https://github.com/ggml-org/llama.cpp/blob/master/tools/mtmd/mtmd.cpp
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-context.cpp

### E4 — image-token cost is material and controllable

Qwen3.5-4B uses patch size 16 and spatial merge size 2. Nominally, after spatial merge, one LLM-visible visual token covers approximately a 32x32 spatial cell. Therefore an uncapped 1920x1080-like frame is on the order of ~2k visual tokens and a 3840x2160-like frame on the order of ~8k visual tokens after normal divisibility rounding. These are derived estimates, not measured FRANK receipts.

The Qwen processor supports dynamic image sizing, and llama.cpp exposes `--image-min-tokens` / `--image-max-tokens` for dynamic-resolution models. Therefore crop-first and token-budget routing is physically supported and should be benchmarked rather than repeatedly sending full-resolution desktop frames.

Sources:
- https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/preprocessor_config.json
- https://github.com/ggml-org/llama.cpp/blob/master/tools/cli/README.md

### E5 — GUI screenshots contain exploitable spatial and temporal redundancy

Recent primary research on GUI agents reports useful gains from adaptive spatial token reduction, temporal redundancy handling, recency-weighted history compression, and action-grounded crop memory rather than naively retaining full screenshots.

Sources:
- AQuaUI, arXiv:2605.19260
- GUI-KV, arXiv:2510.00536
- Rethinking Token Pruning for Historical Screenshots, arXiv:2603.26041
- Action-Grounded Visual Memory failure-mode study, arXiv:2606.14106

These results support testing change/crop/history control around a VLM. They do not prove a particular FRANK routing threshold.

### E6 — counterevidence: raw generative-VLM features are not automatically optimal familiarity embeddings

VLM2Vec and Qwen3-VL-Embedding research show that generative VLMs can become strong multimodal embedding models, but the embedding objective is explicitly trained/contrastively adapted. Therefore raw Qwen3.5 mmproj outputs must **not** be assumed to provide calibrated cosine-distance identity/open-set behavior.

Sources:
- VLM2Vec, arXiv:2410.05160
- Qwen3-VL-Embedding and Reranker, arXiv:2601.04720

This counterevidence keeps a lightweight independent feature baseline alive until measured.

### E7 — current Huihui abliteration does not alter the image part

The model author's card for `huihui-ai/Huihui-Qwen3.5-4B-abliterated` says only the text part was processed, not the image part. Therefore the present abliterated branch does not by itself require a separate visual backbone; however, semantic visual decisions still pass through the altered text decoder and require end-to-end benchmarking.

Source:
- https://huggingface.co/huihui-ai/Huihui-Qwen3.5-4B-abliterated/blob/main/README.md

## 4. Candidate architecture: QNDRF-1

Name: **Qwen-Native Dissolved Retina Fusion v1 (QNDRF-1)**.

The word Retina remains lineage/audit terminology. In the hot runtime, the architecture is one perceptual control fabric:

`screen/camera/image`
` -> S0 capture + timestamp + source/epoch binding`
` -> S1 deterministic cheap frame/tile/hash delta + ROI proposal`
` -> if unchanged: preserve state + no deep vision`
` -> if changed: Qwen mmproj/vision encode only selected ROI(s) under token budget`
` -> Qwen vision embedding buffer`
` -> MVC familiarity/open-set readout + temporal/action-grounded memory`
` -> KNOWN_HIGH_CONFIDENCE and no contradiction: local PerceptualField delta, optionally no 4B decode`
` -> UNKNOWN/AMBIGUOUS/CONFLICT/goal-critical/action-critical: reuse same vision embedding buffer in Qwen3.5-4B semantic decode`
` -> typed Clay PerceptualField delta`
` -> GWT only when globally useful`
` -> action/effect proposal through existing authority boundary`
` -> post-action capture/delta/verification/re-entry`

Key rule:

`one expensive visual encode -> zero or one semantic 4B escalation`

Never:

`cheap gate -> separate heavy CLIP/DINO -> Qwen vision tower -> Qwen decoder`

unless matched experiments prove the separate encoder materially wins under the total resource budget.

## 5. What Retina still means after fusion

Retina is **not** the visual intelligence model. Its surviving causal functions are:

1. sensor ingress and provenance;
2. temporal continuity and frame identity;
3. cheap change detection;
4. region/token-budget selection;
5. cached visual evidence and action-grounded visual memory;
6. familiarity/open-set routing;
7. active sensing (when to capture again, which crop/resolution);
8. expected-vs-observed action verification;
9. uncertainty/conflict preservation;
10. PerceptualField -> GWT causal observability;
11. recovery/replay/version lineage.

Qwen supplies the deep visual representation and semantic interpretation when required.

Thus the clean statement is:

**Retina becomes perception control + temporal evidence fabric; Qwen becomes its deep multimodal perceptual core.**

## 6. MVC redesign candidate

The current MVC document names CLIP/DINO or equivalent as the initial frozen feature backbone. QNDRF-1 adds a new first-choice experiment, not an automatic replacement:

### MVC-Q0 — raw Qwen/mmproj prototypes

- obtain patch-level mmproj output for the ROI;
- construct deterministic pooled descriptors (global mean plus optional coarse spatial pyramid);
- normalize;
- maintain multiple prototypes per familiar class/state;
- measure calibrated similarity, margin, support and unknown rejection.

### MVC-Q1 — tiny learned projection/readout over frozen Qwen features

- freeze Qwen vision tower/mmproj;
- learn only a small projection and/or linear classifier;
- preserve MVC-0 prototype baseline;
- candidate-vs-current shadow evaluation and rollback remain mandatory.

### Counterbaseline MVC-D0/D1

- a dedicated lightweight embedding backbone such as the current CLIP/DINO-class candidate;
- same prototype/linear readout and same evidence sets;
- total resource accounting must include its model memory and inference.

Promotion is based on complete pathway cost and task outcome, not only classifier accuracy.

## 7. Spatial/temporal strategy

### S0 exact/near-exact unchanged gate

Use deterministic image/tile hashes and/or bounded pixel-delta statistics. If no material change, do not invoke Qwen vision.

### S1 changed-region proposal

Maintain changed tiles plus halo/context. Do not discard static context blindly: recent GUI pruning research indicates background and spatial structure can still carry state-transition information. Therefore ROI-only must be compared with ROI+context and periodic anchors.

### S2 adaptive image-token budget

Use low token budgets for familiarity probing and larger budgets for small text, dense tables, uncertain regions or explicit high-fidelity tasks. `image_max_tokens` is a tunable control parameter and must enter receipts.

### S3 action-grounded visual memory

Prefer storing/retrieving the local visual region tied to a successful action/recovery plus source frame/hash/action/outcome identity, rather than injecting long histories of full screenshots into model context.

### S4 recency hierarchy

Recent visual evidence receives more detail. Older frames collapse toward compact typed deltas/prototypes unless a task explicitly reopens them.

## 8. High-value special case: before/after action verification

For tool/effect verification, the system should not rely only on a generated caption such as "the button changed".

Candidate sequence:

`pre_action frame/ROI hash + optional Qwen features`
` -> effect`
` -> immediate post_action capture`
` -> deterministic delta`
` -> if expected state can be verified cheaply, close outcome`
` -> else Qwen deep comparison on the affected ROI(s)`
` -> verified outcome + provenance-bound re-entry`

This directly supports the existing Frank action/outcome/causal-credit architecture.

## 9. Main hypotheses

### H-QNDRF-01 — Qwen feature reuse

Using the existing Qwen mmproj output for MVC/readout yields equal-or-better familiar-state routing accuracy than a separate feature backbone at lower total latency/RAM/VRAM/state movement.

**Counterhypothesis:** raw mmproj features are poorly calibrated for instance/layout similarity and a dedicated lightweight embedding backbone dominates.

### H-QNDRF-02 — decoder bypass

On recurring GUI states, Qwen vision-encode-only + MVC can safely bypass full 4B semantic decoding often enough to materially reduce visual-cycle cost without increasing false familiarity or task failures.

**Counterhypothesis:** the vision tower itself dominates cost or semantic decoder feedback is required too often for a useful bypass rate.

### H-QNDRF-03 — ROI/token-budget benefit

Delta-guided ROI plus adaptive visual-token budgets materially reduce prompt processing and visual-token load while preserving action/task performance.

**Counterhypothesis:** cropping loses spatial/background context and increases grounding or hidden-operation errors.

### H-QNDRF-04 — action-grounded memory

Action/outcome-linked crops plus compact typed state outperform repeated full-screenshot history under equal context/compute budgets.

**Counterhypothesis:** local crops omit global state needed for future reasoning.

### H-QNDRF-05 — periodic anchors remain necessary

Hybrid event/change processing with periodic/on-demand anchors dominates pure change-only sensing on static/slowly varying and hidden-context tasks.

**Counterhypothesis:** anchor processing adds cost without measurable recovery benefit on Frank workloads.

### H-QNDRF-06 — abliteration separation

Because current Huihui processing leaves the image part unchanged, MVC-Q0/Q1 behavior can remain stable across text-decoder ablation/fine-tune revisions if mmproj identity is held fixed.

**Counterhypothesis:** end-to-end visual semantics or exported mmproj/version coupling changes sufficiently that compatibility assumptions fail; exact hashes and differential tests are required.

## 10. Required matched experiment matrix

Freeze identical screenshot/task/action fixtures and compare:

A. `FULL_QWEN`: full-frame Qwen multimodal decode every visual cycle.

B. `CURRENT_DISSOLVED_BASELINE`: current planned change gate + dedicated frozen feature backbone + MVC + Qwen escalation.

C. `QNDRF_FEATURE_REUSE`: change gate + Qwen mmproj features + MVC-Q0/Q1 + decoder escalation using same embeddings.

D. `QNDRF_ROI_TOKEN`: C + ROI/context + adaptive image-token budget.

E. `QNDRF_MEMORY`: D + action-grounded crop memory + recency hierarchy.

Mandatory lesions/controls:

- no change gate;
- no MVC;
- shuffled prototype labels;
- stale prototype/feature-version mismatch;
- ROI-only vs ROI+context;
- no periodic anchors;
- misleading visual prior;
- unknown near-neighbor UI;
- OCR-small-text stress;
- full-screen modal/notification outside selected ROI;
- before/after action mismatch;
- mmproj version swap;
- crash/restart/replay.

## 11. Metrics

Outcome/accuracy:
- full task success;
- visual state correctness;
- action grounding correctness;
- expected-outcome verification correctness;
- false familiar / missed familiar / unknown rejection;
- OCR/text-critical accuracy;
- calibration and abstention.

Efficiency:
- sensor->state p50/p95/p99;
- sensor->action p50/p95/p99;
- mmproj encode time;
- 4B prompt processing time;
- generated decode time;
- visual tokens/frame and visual tokens/successful action;
- percent cycles with zero mmproj;
- percent changed cycles with mmproj but no 4B decoder;
- CPU/GPU utilization;
- RAM/VRAM peak;
- bytes copied/serialized;
- cached embedding/prototype state growth;
- power/energy when available.

Reliability/recovery:
- stale frame acceptance;
- mismatched mmproj/prototype rejection;
- restart recovery;
- last-known-good MVC rollback;
- state replay equivalence;
- false GWT ignition from visual noise.

## 12. Promotion rules

Promote QNDRF-1 only if matched H1/H2/H3 evidence shows:

1. no task/visual safety regression outside frozen tolerance;
2. unknown/open-set and action-verification behavior is not degraded;
3. total resource cost is lower or Pareto-superior, including mmproj and MVC;
4. reuse truly avoids duplicate visual encoding on escalated paths;
5. feature/prototype versioning and replay are correct;
6. one-module Clay semantics remain intact;
7. no simpler baseline dominates.

If raw Qwen features fail MVC-E2/E5, retain a dedicated lightweight feature encoder while preserving all other QNDRF control-plane findings.

## 13. Architecture interpretation

This run does **not** refute the Digital Retina requirement. It sharpens it.

The current owner-fixed architecture already says Retina should dissolve. The research result is that, because Qwen3.5-4B is natively multimodal and both Transformers and llama.cpp expose a physical visual-feature stage before language decoding, the likely simplest H3 architecture is:

**one FRANK visual control fabric + one Qwen vision tower + one Qwen text/semantic decoder + tiny adaptive readout, rather than Retina vision model plus Qwen vision model.**

This is a high-value architecture simplification candidate, not yet a promoted replacement claim.

## 14. Next falsifier

Implement an H1 benchmark tap around `libmtmd` that records the exact Qwen image embedding buffer, pools it into MVC-Q0 descriptors, and measures the same screenshots under:

- exact/full-frame baseline;
- changed ROI;
- raw Qwen prototype familiarity;
- dedicated lightweight embedding baseline;
- escalation into 4B decode using the already-computed Qwen media embeddings.

The decisive first question is not "does Qwen understand screenshots?". It is:

**Can Qwen's already-required vision encoding double as Frank's familiarity/routing representation well enough that a second frozen visual backbone can be deleted?**
