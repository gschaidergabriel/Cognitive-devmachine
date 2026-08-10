# Q23 package — PEH lifetime + calibrated feature adapter

Run: `q23-20260810T2242p0700-chatgpt-secondary-dualview-runtime-envelope`
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`
Status: `MATERIAL_RESEARCH_DELTA / CANDIDATE_NOT_PROMOTED`

## New discriminator

Current `llama.cpp` primary code resolves an ambiguity left by the earlier feature-reuse work.

`mtmd_get_output_embd(ctx)` returns `ctx->out_embd.data()`. The same `ctx->out_embd` vector is passed into subsequent `mtmd_encode_chunk_impl` / `mtmd_encode_impl` calls, where it is resized to the new token-count x embedding-dimension surface before encode. Therefore the raw pointer is a view into mutable context-owned storage, not a persistent perception identity.

The batch path is similar but batch-scoped: `mtmd_batch` owns `std::vector<float> output_embd`; `mtmd_batch_get_output_embd` returns an offset into that vector; `mtmd_batch_free` deletes the owning batch. The public API is explicitly experimental.

Primary evidence:
- `ggml-org/llama.cpp:tools/mtmd/mtmd.h`, current public API.
- `ggml-org/llama.cpp:tools/mtmd/mtmd.cpp@82b73d5cd126720cb087fb8191a6226c5ffd4beb`.
- current server path consumes `mtmd_batch_get_output_embd` when decoding multimodal chunks.

## Result

**Physical same-encode reuse remains supported, but stock libmtmd does not provide the persistent embedding-handle lifetime contract Frank needs.**

This refines, rather than refutes, QNDRF/merged-feature reuse.

### PEH-1 candidate contract

Introduce a runtime-owned `PerceptualEmbeddingHandle` only at the Frank/Retina boundary:

```text
PerceptualEmbeddingHandle = {
  handle_id,
  frame_id,
  source_epoch,
  roi_hash,
  canonical_pixel_hash,
  runtime_repo_sha,
  mtmd_api_version,
  model_hash,
  mmproj_hash,
  preprocessing_version,
  image_token_budget,
  grid_or_token_geometry,
  embedding_surface_id,
  element_dtype,
  n_tokens,
  n_embd,
  pooling_projection_hash?,
  ownership_mode,
  created_at,
  valid_until,
  invalidation_epoch,
  content_hash,
  provenance
}
```

`ownership_mode` candidate values:
- `COPY_ON_CAPTURE` — Frank owns immutable copied media embeddings. This is the safe reference baseline.
- `PINNED_RUNTIME_BUFFER` — zero-copy only if an exact runtime version provides a proved ownership/lifetime fence and mutation cannot occur while readers exist.
- `INVALID` — stale model/mmproj/runtime/preprocessing/token-grid/epoch mismatch or owner freed/re-encoded.

A naked `float *` is never a durable perceptual identity and may not be persisted into UnifiedDB/ClayGraph as if its address or current contents were stable evidence.

## Feature geometry consequence

Current primary retrieval systems strengthen the counterhypothesis that raw generative-VLM features are automatically calibrated familiarity embeddings:

- official Qwen3-VL-Embedding uses retrieval-specific adaptation and a final multimodal hidden-state embedding;
- VLM2Vec trains VLM backbones contrastively and current MMEB-V3 includes GUI-control and agent-memory retrieval tasks.

Therefore q23 should test this ordered ladder before adding a second heavy encoder:

1. `Q0_MERGED_RAW`: deterministic pooling + normalization of the already-computed Qwen/mmproj media surface.
2. `Q1_TINY_ADAPTER`: the same frozen Qwen media surface plus a tiny trainable projector/open-set calibration head; no second deep visual encode.
3. `D0_LIGHT_ENCODER`: independent lightweight visual embedding baseline.
4. `D1_LIGHT_ENCODER_ADAPTED`: same admission/calibration protocol as Q1.
5. `Q2_DUALVIEW`: pre-merger + merged same-encode surface only if Q0/Q1 fail enough to justify bounded runtime instrumentation.

The ordered test prevents a false binary choice between raw features and a second full vision model.

## Mandatory falsifiers

### PEH-LIFE-01 — next-encode mutation
1. encode frame A;
2. obtain raw mtmd pointer and copy A;
3. encode B with different token geometry;
4. verify raw-A pointer cannot be treated as stable A evidence;
5. verify copied PEH-A remains byte/content-hash stable.

### PEH-BATCH-02 — owner destruction
1. batch encode A/B;
2. obtain per-chunk views;
3. destroy/reset batch;
4. assert all zero-copy handles become INVALID before any MVC/GWT/re-entry use.

### PEH-CONC-03 — reader/writer race
Concurrent MVC read and next visual encode must either use immutable copy-on-capture or an explicit ownership fence. Any torn/stale/misattributed feature read is a hard fail.

### PEH-RESTART-04 — persistence/replay
Only serialized copied/projection-derived feature evidence with complete version envelope may survive restart. Process pointers and batch addresses must never survive replay.

### MVC-GEOM-05 — matched geometry ladder
Frozen Frank-specific visual fixtures: known, same-entity state variants, near-neighbor unknown, OOD, alias/conflict, changed preprocessing/runtime. Compare Q0/Q1/D0/D1 and Q2 only if justified.

Measure AUROC/AUPRC where meaningful, false familiarity, known rejection, selective risk/coverage, calibration, prototype drift, latency p50/p95/p99, CPU/RAM/VRAM, bytes copied, decoder calls, and end-to-end sensor-to-correct-decision cost.

## Experience boundary

No Frank-experience benefit is claimed here. Any user-specific learning/retrieval claim still requires the existing independent dose ladder `N={0,1,2,4,8,16,32,64}`, QWEN_ONLY/direct-memory/PAR/sham controls, wrong-seed/stale-memory lanes and separation of pretrained Qwen knowledge from Frank episodic experience.

## Architecture disposition

- `QNDRF / merged-feature reuse`: KEEP AS TEST CANDIDATE.
- `raw mtmd pointer as persistent percept`: REFUTED.
- `PEH COPY_ON_CAPTURE`: REFERENCE IMPLEMENTATION CANDIDATE.
- `PEH zero-copy`: OPTIMIZATION CANDIDATE, blocked on exact lifetime proof and benchmark benefit.
- `tiny adapter over frozen Qwen features`: HIGH-VALUE NEXT DISCRIMINATOR, not promoted.
- `second heavy encoder`: NOT DEFAULT; retain only as counterbaseline unless measured geometry/resource results justify it.
- `multi-level/pre-merger tap`: DO NOT enable by assumption; instrument only after Q0/Q1 evidence justifies maintenance/runtime cost.

## Cross-branch effect

Affected Frank v0.1 work:
- Digital Retina/MVC: feature identity and invalidation contract.
- UnifiedDB/ClayGraph: may persist versioned feature evidence/prototypes, never process pointers.
- GWT/re-entry: must carry PEH identity/provenance if visual evidence is causally reused.
- Recovery: restart invalidates runtime-backed handles and reloads only durable compatible feature evidence.
- target-VPS acceptance: add PEH lifetime/concurrency/restart plus Q0/Q1/D0/D1 matched measurements.

No target Frank mutation and no architecture promotion were performed by this research package.