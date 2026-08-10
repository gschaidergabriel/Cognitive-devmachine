# Q23 final synthesis — 2026-08-10 22:42 +07

Status: MATERIAL RESEARCH DELTA / NO PROMOTION

## Decision

Keep Qwen3.5-4B as the current small multimodal baseline and refine QNDRF-1 into **QNDRF-1.1-ZC**: a synchronous zero-copy MVC/open-set gate that reads the existing libmtmd projected media buffer after encode and before llama decode. Do not add a second heavy vision stack and do not persist the complete projected token tensor by default.

The immediate target-VPS experiment is not another broad model search. It is the matched discriminator `T-Q23-ZC-001` plus `T-Q23-RECOVERY-002`.

## Why this changed the frontier

1. Current Transformers Qwen3.5 exposes visual pooler output before language decoding.
2. Current llama.cpp/libmtmd exposes the encoded media buffer and feeds that same buffer to llama decode. This makes a zero-copy familiarity readout physically implementable without re-encoding.
3. Local synthetic memory-walk benchmarks show that copy-then-pool costs materially more than direct pooling across tested 2560-wide token buffers. At 2040 tokens the full FP32 projected buffer is ~19.9 MiB; at 8160 tokens ~79.7 MiB. These are proxy memory-layout facts, not target inference performance.
4. A direct 5-pool spatial descriptor (global + 2x2 quadrants) is 50 KiB at width 2560 and measured ~1.27 ms p50 for 2040 tokens and ~5.86 ms p50 for 8160 tokens on the local proxy host. This is a useful baseline, not proof of visual discrimination quality.
5. Current multimodal embedding papers strengthen the counterhypothesis: generative VLM features often require explicit contrastive/embedding training to become strong retrieval embeddings. Raw Qwen features therefore remain uncalibrated until Frank-specific held-out/OOD tests prove otherwise.
6. GUI-agent research supports adaptive spatial/temporal compression, but also provides counterevidence against changed-pixels-only or naive full-history policies. Retina should preserve ROI context and periodic/on-demand anchors and prefer action-grounded memory.
7. Current llama.cpp issue evidence adds mandatory runtime fault tests: Qwen3.5-4B conversion/load failure reports, multimodal backend crashes, M-RoPE/cache sensitivity, and unresolved image-containing slot save/restore behavior.
8. Qwen3.6 does not currently provide an official <=4B open model, so it does not supersede Qwen3.5-4B for the present small-model path. Gemma 4 E4B is a valid current multimodal challenger but not an automatic strict <=4B replacement under its official total parameter accounting.

## Architecture candidate

```text
sensor bytes
-> auth/provenance/frame epoch
-> deterministic change/ROI gate
-> Qwen/libmtmd vision encode
-> EXISTING projected embedding buffer
-> synchronous ZERO-COPY MVC descriptor/readout
   -> KNOWN_HIGH_CONFIDENCE + non-critical + no contradiction:
      compact PerceptualMemorySeed / VisualPercept delta
      optional bounded EAP ActiveAssembly
      skip full 4B semantic decode
   -> UNKNOWN / AMBIGUOUS / CONFLICT / OCR-critical / action-critical:
      same unchanged embedding buffer -> llama decode
-> ClayCode PerceptualField
-> GWT / memory / action / verified outcome / re-entry
```

Hard constraints:
- raw embedding != semantic truth;
- familiarity != effect authority;
- retrieved memory != observation;
- full projected token tensor is transient by default;
- compact descriptor/prototype state is versioned by frame/model/mmproj/projection/semantic epoch;
- stale version mismatch fails closed to deeper perception, not silent reuse.

## Next falsifiers

1. Execute `T-Q23-ZC-001` on exact target VPS with frozen recurring/unknown/OCR/layout/modal/action fixtures.
2. Execute `T-Q23-RECOVERY-002` before any runtime promotion, including image-containing restart/cache/replay and stale model/mmproj/MVC versions.
3. Compare `RAW_QWEN_GLOBAL_POOL`, `ZERO_COPY_QWEN_SPATIAL_POOL`, `ZERO_COPY_QWEN_TINY_PROJECTION`, and `DEDICATED_EMBEDDER_MVC` under identical total resource accounting.
4. Only after open-set calibration passes, test `PAR_COMPACT_SEED` against QWEN_ONLY and DIRECT_MEMORY with wrong-seed, stale-layout and shuffled controls.
5. If experience benefit is claimed, run the existing N={0,1,2,4,8,16,32,64} experience-dose protocol rather than a binary familiar/unfamiliar claim.

## Result disposition

- QNDRF-1.1-ZC: CANDIDATE / TESTING REQUIRED.
- PAR-1.1 compact seed: REFINED / NOT PROMOTED.
- Qwen3.6 <=4B replacement: CURRENTLY ELIMINATED BY AVAILABLE OFFICIAL SIZE SET.
- Gemma 4 E4B: CHALLENGER ONLY, RESOURCE/BUDGET INTERPRETATION REQUIRED.
- F-V01-06: remains not complete; this run supplies architecture/test evidence, not acceptance.

No paid/final training was started. No Frank/self.root Harness mutation was authorized by the target. This run was performed by a temporary Clay research worker and persisted only reproducible decision traces/results.
