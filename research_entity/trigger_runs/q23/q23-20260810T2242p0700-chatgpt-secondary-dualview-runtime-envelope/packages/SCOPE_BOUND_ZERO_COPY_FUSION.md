# Q23 fusion — scope-bound zero-copy, durable compact descriptor

Status: `HIGH_VALUE_FUSION_CANDIDATE / NOT_PROMOTED`

This package reconciles two concurrently produced q23 findings that are compatible only when their lifetimes are made explicit:

1. current `libmtmd` permits immediate readout of the just-encoded merged media embedding buffer before language decode, enabling a synchronous zero-copy MVC calculation;
2. that pointer aliases mutable context- or batch-owned storage, so it cannot be treated as a durable/asynchronous perceptual identity across the next encode, batch destruction, reset or restart.

The correct fusion is therefore **scope-bound zero-copy**, not "copy everything" and not "let raw pointers escape".

## Candidate runtime split

```text
visual input
 -> canonicalize/change/ROI gate
 -> ONE libmtmd/Qwen media encode
 -> EphemeralMediaEmbeddingView (owner-scoped, non-persistable)
      -> synchronous MVC-M0/M1 pooling/calibration
      -> DurablePerceptualDescriptor + classifier evidence + compatibility/provenance identity
      -> if escalation required: semantic decoder consumes the same live media buffer before owner scope closes
 -> invalidate EphemeralMediaEmbeddingView on next encode/free/reset/owner-generation change
 -> only compact descriptor/prototype/evidence may enter UnifiedDB/GWT/re-entry
```

## EphemeralMediaEmbeddingView law

An ephemeral view MUST carry or be protected by:

- exact `mtmd_context` or `mtmd_batch` owner identity;
- an owner generation/lease epoch maintained by the Frank runtime wrapper;
- token count and embedding width;
- exact frame/ROI identity;
- VisualEncoderCompatibilityID;
- no serialization;
- no queue/await/restart crossing;
- no use after another encode into the same context, batch free/reset, slot reset, model/mmproj reload or generation mismatch.

The wrapper invalidation generation is Frank-owned state. It does not pretend the upstream experimental C API itself guarantees a persistent handle.

## DurablePerceptualDescriptor law

The durable object is the compact result of the MVC readout, not the raw token tensor. At minimum bind:

- descriptor/prototype version and content hash;
- frame/ROI/canonical-pixel identity;
- source and state epoch;
- exact model/mmproj/runtime/preprocessor/token-budget compatibility identity;
- pooling/projection/calibration version;
- open-set score/state and uncertainty;
- source provenance and causal episode identity when admitted.

For a simple per-dimension pooled descriptor, durable storage scales with `n_embd`, while the raw token surface scales with `n_tokens * n_embd`. Thus descriptor materialization is orders of magnitude smaller for multi-token images; the exact chosen descriptor geometry remains a benchmark variable.

## Full-copy role

Full raw embedding copy remains a **reference/fault-isolation baseline** for:

- asynchronous algorithms that genuinely require token-level features;
- differential debugging;
- race/lifetime falsification;
- exact reproduction experiments.

It is not the preferred production path merely because it is the easiest ownership model.

## Relation to zero-copy proxy benchmark

The concurrent q23 proxy benchmark reported direct-pool p50 below copy+pool p50 across tested synthetic tensor sizes, with copy+pool/direct ratios roughly 2.14x–2.67x. This is useful mechanism evidence for avoiding unnecessary full-tensor copies, but it is not target-VPS Qwen runtime evidence and does not prove end-to-end advantage.

Therefore the production candidate is:

`zero-copy synchronous readout -> copy/persist compact descriptor only`.

## New discriminating test

`TO-Q23-SCOPED-ZC-07` must compare on the target-compatible runtime:

A. `FULL_COPY_THEN_POOL`
B. `SCOPED_ZERO_COPY_POOL_THEN_DESCRIPTOR_COPY`
C. `DEDICATED_LIGHT_ENCODER`

Under identical frames and MVC logic measure:

- descriptor equality/tolerance A vs B;
- stale-view rejection after next encode/free/reset;
- race failures under forced reader/writer interleavings;
- direct-pool + descriptor-copy latency p50/p95/p99;
- full-copy + pool latency p50/p95/p99;
- bytes copied per frame;
- RAM high-water mark;
- decoder handoff correctness using the same encoded buffer;
- end-to-end correct-decision latency and false familiarity.

Hard gate: any cross-frame contamination, stale-view acceptance, torn read, wrong descriptor attribution or semantic decoder corruption rejects the zero-copy implementation regardless of speed.

## Disposition

- synchronous zero-copy readout: `SUPPORTED_AS_IMPLEMENTABLE_CANDIDATE`;
- raw pointer escaping its owner scope: `REFUTED`;
- persist full token tensor by default: `NOT_SELECTED_PENDING_NEED`;
- persist compact descriptor/prototype/evidence: `PREFERRED_CANDIDATE`;
- zero-copy end-to-end benefit: `UNMEASURED_ON_TARGET`;
- canonical architecture promotion: `NONE`.
