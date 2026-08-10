# Q23 Final Synthesis — 2026-08-10

Run: `q23-20260810T224100p0700-chatgpt-secondary`  
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`  
Program: `FRANK_V0_1`  
Affected work: `F-V01-06-DIGITAL-RETINA-MVC`  
Status: `MATERIAL DELTA / NOT PROMOTED`

## Executive result

This run did **not** rediscover that Qwen3.5-4B is multimodal or that libmtmd exposes media embeddings; both were already captured by QNDRF-1 and are explicitly excluded from new progress credit.

The material advance is a narrower, more executable decision frontier:

1. Qwen3.5's visual representation path differs materially from Qwen3-VL: the current Transformers reference removes Qwen3-VL's DeepStack helper paths and exposes both pre-merger `last_hidden_state` and merged `pooler_output` visual representations.
2. Current llama.cpp helper code can decode an image from an already-calculated embedding buffer. Therefore Frank can test a literal one-image-encode path in which MVC reads the same encoded buffer that semantic decode consumes on escalation; no private decoder hook is required merely for that reuse.
3. This does **not** establish that the public LLM-facing projected embedding is the best familiarity/open-set representation. Qwen's own dedicated multimodal embedding models use explicit retrieval-oriented training, so raw generative visual outputs remain uncalibrated until Frank-specific evidence says otherwise.
4. The separate-encoder counterhypothesis is now made non-strawman: MobileCLIP2-S0 is a tiny current image encoder candidate, while DINOv3-S/16 is a dense frozen-feature adversarial baseline.
5. A new QNDRF-1.1 architecture candidate separates persistent semantic visual state from ephemeral raw embeddings and optional runtime caches so optimization state cannot silently become Frank truth.

## Architecture candidate: QNDRF-1.1

Hot path:

`capture/provenance`
` -> deterministic frame/tile delta`
` -> ROI + visual-token budget`
` -> one Qwen3.5/libmtmd visual encode`
` -> projected visual-token grid + public decoder positions`
` -> MVC descriptor/readout`
` -> known/high-confidence/no-conflict fast path OR semantic escalation`
` -> on escalation reuse same encoded media buffer`
` -> Qwen semantic decode`
` -> typed Clay PerceptualField`
` -> GWT when globally useful`
` -> effect proposal through deterministic authority boundary`
` -> outcome verification + provenance-bound re-entry`

The representation ladder remains experimental:

- F0: public Qwen projected token-grid descriptor;
- F1: Qwen3.5 pre-merger feature reference tap;
- F2: MobileCLIP2-S0 independent tiny encoder;
- F3: DINOv3-S/16 dense-feature baseline.

No level is promoted by aesthetic preference.

## Visual-state lifetime law candidate

L0 — `SENSOR_IDENTITY`

Persistent compact source/frame/ROI/hash/delta/provenance identity.

L1 — `MVC_STATE`

Persistent versioned compact descriptor, prototypes, calibration and evidence-tier state. This is learned routing evidence, never raw sensor truth.

L2 — `RAW_MTMD_EMBEDDINGS`

Ephemeral same-cycle backing buffer by default. It may be read by MVC and then reused by semantic decode. It is not canonical durable semantic state.

L3 — `LLAMA_RUNTIME_MEDIA_STATE`

Optional rebuildable version-bound media/prefix/slot/checkpoint state. This is an implementation acceleration surface. It never becomes UnifiedDB semantic authority and must be safe to discard/rebuild.

The cache identity must bind at least frame/ROI content, preprocessing/dynamic-resolution/token budget, model revision/quantization, mmproj revision/hash, runtime ABI, descriptor version, MVC calibration/prototype version, and — when continuation state is reused — the Qwen3.5 LLM recurrent-state epoch.

## Why Qwen3.5 hybrid state matters

Qwen3.5 text inference is not a pure transformer KV-cache problem: current reference code mixes gated-delta recurrent layers with full-attention layers. Therefore equality of visual embedding buffers is not sufficient evidence that two continuation states are equivalent after save/restore. A restart test must compare uninterrupted versus restored continuation under matched media and deliberately mismatched state identities.

## Strongest surviving counterhypothesis

The strongest counter is no longer “use another huge visual model.” It is:

> A tiny specialized image encoder may produce substantially better instance/layout/open-set geometry at so little extra cost that duplicate visual encoding is rational, especially if it prevents false familiarity and avoids many 4B semantic decodes.

MobileCLIP2-S0 makes this experimentally credible. DINOv3-S/16 separately tests whether dense self-supervised patch geometry provides a better familiarity space.

Conversely, Qwen reuse wins only if complete pathway cost is better: familiarity/open-set quality, calibration, safe decoder-bypass rate, task/action outcome, latency, RAM/VRAM, state movement, power and recovery — not because “one model is cleaner.”

## Mandatory next tests

### T-Q23-FEATURE-LADDER-01

Compare projected-global, projected mean+variance, projected 2x2/3x3 spatial descriptors, pre-merger Qwen reference features, MobileCLIP2-S0 and DINOv3-S/16 under the same user-specific replay corpus and identical MVC head-capacity controls.

Hard metrics: false familiarity, unknown AUROC/AUPR, FPR95, calibration/ECE/Brier, known recall/F1, safe decoder-bypass rate, downstream action/task success, p50/p95/p99 latency and full resources.

### T-Q23-ZERO-REENCODE-01

Instrument target libmtmd and prove encode-call count exactly once when MVC consumes the encoded buffer before semantic escalation. Compare against normal path and record buffer identity plus semantic-output tolerance.

### T-Q23-CACHE-LIFETIME-01

Compare no cache, one durable raw-embedding cache, L0/L1/L2 split, and L0/L1/L2 plus optional L3 runtime cache across exact-repeat, changed ROI, preprocess/token-budget change, mmproj/model swap, restart and stale-state cases.

### T-Q23-HYBRID-RESTART-01

Compare uninterrupted and checkpoint/restored Qwen3.5 continuation state across same and mismatched media/model conditions. Record next-token/logit equivalence where accessible, task-output equivalence, restore latency and failure classification.

### T-Q23-TRANSFORM-INVARIANCE-01

Ensure spatial pooling does not merely memorize window coordinates. Test translation, resize, DPI scale, theme, crop, compression and text-render perturbations.

## Spatial descriptor candidate

libmtmd exposes decoder-position metadata for image tokens. Therefore the first spatial descriptor does not require a private Qwen feature hook: use normalized token x/y positions to compute global statistics plus coarse spatial bins over the public projected token grid.

This is deliberately a candidate, because absolute/coarse spatial structure may overfit harmless window movement. Transformation controls decide.

## What was narrowed or rejected

- `Qwen3.5 is multimodal` — established input, not research progress.
- `mtmd_get_output_embd exists` — already known in QNDRF-1, not research progress.
- `Qwen reuse is automatically better because it avoids a second model` — rejected as an argument; only measured Pareto evidence can establish it.
- `Use a second 2B Qwen embedding model as the primary MVC baseline` — deprioritized; too heavy for the first counterbaseline when much smaller encoders exist.
- `Persist raw vision embeddings as canonical Frank memory` — not selected as default. Persistent semantic state should remain compact, typed and versioned; raw buffers are physical backing/cache unless tests prove a stronger need.

## Capability boundary reached

Current worker could inspect and persist current primary runtime/repository evidence and create the full discriminating test plan, but it did not possess a directly invokable target Qwen3.5-4B/mmproj runtime lane in this turn. General web search also returned HTTP 503, so external refresh remained `DEGRADED_LIVE_REFRESH`; direct primary GitHub sources remained available.

The next material recurrence needs actual target-runtime capability rather than more same-lineage reading. Highest-value GO question: identify/invoke the current target lane with Qwen3.5-4B + matching mmproj and instrument encode count, embedding identity and restart state.

## Promotion state

`QNDRF-1.1 = CANDIDATE_TESTING_REQUIRED`

`F-V01-06-DIGITAL-RETINA-MVC = OPEN`

No global-stage, Harness-release, Frank-acceptance or final-model credit is claimed from this q23 run.
