# Q23 final-synthesis postscript — lifetime-safe feature reuse

This postscript adds a later primary-code/lifetime finding to `FINAL_SYNTHESIS.md` without rewriting the concurrently finalized run.

## Final fused result

The q23 merged-first conclusion survives, but the feature surface now has an explicit lifetime boundary:

1. Current Qwen/llama.cpp paths make **same-encode feature reuse physically implementable**.
2. Current `libmtmd` stores output in context- or batch-owned `std::vector<float>` buffers and returns borrowed pointers into those owners.
3. Therefore a raw `mtmd` pointer is **not** a durable Frank percept, replay object or cross-encode identity.
4. This does **not** kill zero-copy. The safe performance candidate is **scope-bound synchronous zero-copy readout** while the owner is live, followed by persistence of only a compact descriptor/prototype/evidence object.
5. A full raw-tensor copy remains a fault-isolation/asynchronous reference baseline, not the preferred production architecture by default.

## Current candidate path

```text
canonicalized visual observation
 -> one Qwen/libmtmd media encode
 -> owner-scoped EphemeralMediaEmbeddingView
 -> synchronous MVC-M0 or MVC-M1 readout
 -> compact durable descriptor + calibration/open-set evidence + VisualEncoderCompatibilityID
 -> if escalation: semantic decoder consumes same still-live encoded media buffer
 -> owner generation advances / view invalidates
 -> only compact typed evidence may enter UnifiedDB/GWT/re-entry
```

## Evidence status

Primary-code support:
- `ggml-org/llama.cpp:tools/mtmd/mtmd.cpp@82b73d5cd126720cb087fb8191a6226c5ffd4beb` shows `ctx->out_embd` and `mtmd_batch::output_embd` ownership plus pointer-return APIs.
- current server code consumes the batch embedding pointer in the multimodal decode path.

Executable reference result:
- `experiments/REFERENCE_PEH_SCOPE_TEST_RESULTS.json` passed all 5 synthetic generation-fence contract checks.
- example materialization at 256 media tokens x 2560 float32 dimensions: raw surface 2.5 MiB versus a one-vector pooled descriptor 10 KiB, a 256x byte reduction. This is an exact geometry calculation inside the reference test, not a target-runtime performance result.

Concurrent proxy evidence:
- direct-pool versus copy+pool synthetic rows favor avoiding full-tensor copies, but remain proxy evidence rather than target Qwen/VPS acceptance.

## Refutations / non-promotions

REFUTED:
- raw process pointer as durable perceptual identity;
- stock libmtmd buffer lifetime as implicit UnifiedDB/replay semantics.

NOT PROMOTED:
- raw Qwen/mmproj feature quality for user-specific open-set familiarity;
- target-VPS zero-copy speedup;
- any cross-epoch prototype reuse without compatibility evidence;
- any F-V01-06 completion credit.

## Next hard gate

`TO-Q23-SCOPED-ZC-07` on the exact target-compatible Qwen/llama.cpp runtime:
- full-copy+pool versus scope-bound zero-copy-pool+descriptor-copy versus dedicated light encoder;
- forced next-encode/free/reset/race/restart schedules;
- same-buffer semantic decoder handoff;
- descriptor equality, stale-view rejection, false familiarity, latency/resource/recovery metrics.

A read-only target-VPS multimodal runtime/model inventory lane has been armed. At postscript time no target receipt has been observed, so execution state remains `SYNC_PENDING_NO_TARGET_PASS_CLAIM`.

## Program effect

The research delta has been translated into test obligations for Digital Retina/MVC, UnifiedDB semantic boundaries, GWT/re-entry provenance and recovery. The work package remains OPEN until target-compatible measurements satisfy the relevant gates.
