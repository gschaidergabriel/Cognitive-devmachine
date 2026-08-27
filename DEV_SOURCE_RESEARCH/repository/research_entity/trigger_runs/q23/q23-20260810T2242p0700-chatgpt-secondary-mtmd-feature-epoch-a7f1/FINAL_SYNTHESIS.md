# Q23 final synthesis — mtmd shared visual feature epoch

Run: `q23-20260810T2242p0700-chatgpt-secondary-mtmd-feature-epoch-a7f1`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Program: `FRANK_V0_1`
Work package: `F-V01-06-DIGITAL-RETINA-MVC`
Architecture promotion: **NONE**

## What materially changed

Q23's previous Qwen-native dissolved-Retina direction is now attached to a concrete current `llama.cpp/libmtmd` physical boundary. Current libmtmd exposes the projected media embedding buffer after visual encode, sized as `llama_model_n_embd_inp(model) * n_media_tokens * sizeof(float)`. Current `llama-server` retrieves this buffer and immediately sends the same pointer into `mtmd_helper_decode_image_chunk`. This creates a direct experimental hook for:

`one visual encode -> MVC/open-set classification -> zero or one 4B image decode`.

The hook is technically identifiable. Its scientific value is not yet established.

Current libmtmd also exposes relative decoder positions `(t,x,y)` for each media embedding token. Therefore token enumeration order must not be used as the production spatial authority. The latest reference oracle uses position-aware global + 2x2 coarse spatial pooling. A synthetic permutation test passes when embeddings and decoder coordinates are permuted together and deliberately shows token-order bucketing is not a valid spatial contract.

## Target-repo implementation delta

Added/revised in `gschaidergabriel/Dr.-Unterweger`:

- `runtime/q23_visual_embedding_gate_v1/target_vps_probe.py`
  - fail-closed FeatureEpoch guard;
  - UNKNOWN/AMBIGUOUS/CONFLICT/task-critical escalation;
  - position-aware synthetic descriptor oracle;
  - stale feature rejection;
  - latest local reference run: 14/14 logic tests PASS.
- `claycode/frank_visual_embedding_gate.clay`
  - semantic authority for feature identity, decoder positions, routing and provenance;
  - raw embedding pointers remain physical backing only;
  - visual route cannot mint effect authority.
- `.github/workflows/q23-visual-embedding-gate-v1.yml`
  - bounded self-hosted target-VPS oracle workflow and immutable/LATEST receipt path.
- `runtime/q23_visual_embedding_gate_v1/PROBE_REVISION.json`
  - binds research-run/source identity.

The current q23 target-VPS `LATEST.json` receipt was not observed after multiple checks. Therefore target-VPS execution receives zero evidence credit in this run.

## FeatureEpoch result

Persistent MVC prototypes should initially bind at least:

- exact model hash;
- exact mmproj hash;
- runtime implementation + commit;
- backend + version;
- runtime configuration hash;
- preprocessing hash;
- image-token policy hash;
- pooling/projection hash;
- temporal policy hash.

This is intentionally conservative. A field may be removed from compatibility identity only after controlled ablation shows descriptor topology, prototype transfer and open-set calibration remain inside declared tolerance.

## Original Retina baseline result

The historical Retina is not one flat CLIP call. Recovered source shows a conditional multi-stage vision organ:

- source materialization;
- OCR + face detection first;
- screenshot detection with a cheaper screenshot path;
- photo path with CLIP + YOLO + DINO in parallel;
- downstream faces/emotion, logos, scene/fine-object/region reasoning, captions/VQA, color/composition, AI/art handling and GoL/pattern functions;
- structured result surface and latency metadata.

Historical source/performance anchors conflict: comments describe approximately 100 ms fast / 300 ms deep in one file, about 900 ms warm p50 in the API core, while the historical working-paper lane records about 1.5-2.0 s/image on 4-vCPU CPU-only hardware. These values are not averaged. The baseline is classified `BASELINE_PARTIAL_ARCHAEOLOGY` until the exact bundle is re-executed on matched fixtures.

Therefore `NO_ORIGINAL_BASELINE -> NO_REPLACEMENT_CLAIM` still blocks any declaration that Qwen has replaced the Retina.

## Dedicated-feature counterbaseline correction

A second 2B multimodal embedding model is not a fair permanent 'micro' baseline. The counterbaseline ladder is now:

1. Qwen projected feature reuse, global descriptor;
2. Qwen projected feature reuse, position-aware global+2x2 descriptor;
3. tiny learned projection over frozen Qwen features only if needed;
4. historical DINOv2-Small INT8 reproduction;
5. MobileCLIP2-S0 image encoder (11.4M image parameters) when operationally available;
6. DINOv3 ViT-S/16 (21M) when it adds discriminating value;
7. Qwen3-VL-Embedding-2B only as a non-micro scientific upper bound.

Promotion uses whole sensor-to-verified-outcome cost, not classifier accuracy alone.

## Local resource shadow

A separate C++ `-O3 -march=native` synthetic microbenchmark on a non-target AMD EPYC 9V74 measured position-aware 2560-d projected-buffer pooling at roughly:

- 64 visual tokens / 0.625 MiB input: p50 26 us;
- 256 tokens / 2.5 MiB: p50 95 us;
- 1024 tokens / 10 MiB: p50 349 us;
- 2048 tokens / 20 MiB: p50 1246 us.

The global+2x2 descriptor is 12,800 float32 values = 50 KiB. Brute-force similarity over 100 such prototypes measured roughly 1.05 ms p50 locally; 1000 roughly 11 ms. These are resource shadows only, not target evidence.

The architectural implication is to read the MTMD buffer synchronously/zero-copy where possible, immediately reduce it, and persist only a bounded descriptor plus provenance. Raw MTMD output should not become persistent semantic state.

## GUI / temporal perception fusion

Fresh GUI-agent work supports testing temporal redundancy reduction and action-grounded local visual memory, while also warning that background/spatial context can remain useful. Q23 therefore does not promote ROI-only perception.

First discriminating arms:

- ROI only;
- global deterministic tile/hash structure + ROI deep vision;
- low-detail global + ROI deep vision;
- full-frame deep vision.

Deterministic frame/tile change remains the cheapest baseline before any learned pruning module. Learned pruning is admitted only if it reduces total verified-outcome cost without increasing missed consequential changes or recovery complexity.

## Provenance / replay fusion

libmtmd supports media IDs useful for cache identity, but chunk serialization retains metadata and not the source media bytes. Frank therefore needs content-addressed frame/ROI evidence outside MTMD runtime state. The intended join is:

`immutable frame/ROI evidence -> source hash -> VisualPercept -> MTMD derived receipt -> MVC descriptor/prototype -> GWT/use/outcome -> replay`.

A saved MTMD chunk or a descriptor alone is not sufficient replay evidence.

## Runtime risks

Current public `llama.cpp` Qwen3.5 issue evidence shows that larger-family variants have exhibited multimodal sensitivity to batch/ubatch, Flash Attention/backend, CPU fallback, prompt ordering and M-RoPE paths. These are transfer-risk hypotheses only. Exact Qwen3.5-4B target reproduction or negative results are mandatory.

Because Frank v0.1 has exactly one active global execution lease, `llama-server parallel=1` is the simplest first baseline. It is not owner-fixed as a final knob: parallel>1 may return if a serialized-workload benchmark shows material benefit without state/recovery regressions.

## Next executable frontier

P0 order:

1. reproduce original Retina cold/warm/function baseline;
2. instrument exact Qwen3.5-4B target MTMD buffer + decoder positions;
3. run FeatureEpoch invariance matrix;
4. run MVC ladder including open-set/OOD;
5. enable decoder bypass behind a feature flag only after the read-only tap is characterized;
6. run exact 4B M-RoPE/runtime matrix and restart/recovery;
7. then decide RETAIN/FUSE/EMERGENT_DISTRIBUTE/CLAY_REDESIGN_CANDIDATE per historical function.

No training authorization was consumed and no paid/final training started.
