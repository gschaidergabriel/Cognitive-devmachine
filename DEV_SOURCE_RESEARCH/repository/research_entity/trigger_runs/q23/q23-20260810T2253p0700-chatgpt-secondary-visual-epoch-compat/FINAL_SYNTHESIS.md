# Q23 — Visual Epoch Compatibility + Spatial Geometry

**Run:** `q23-20260810T2253p0700-chatgpt-secondary-visual-epoch-compat`  
**Status:** MATERIAL DELTA / CANDIDATE NOT PROMOTED  
**Target:** `self.root` / human-surface Frank v0.1 on accepted Hostinger Ubuntu VPS

## Result

The prior exact `VisualFeatureEpoch` fail-closed gate remains correct but is too binary to be the only migration mechanism. This run adds a candidate `VisualFeatureCompatibilityCertificate` that allows cross-epoch prototype reuse only when the exact source/target epoch pair, direction, scope, transform, calibration fixture and independent held-out fixture are bound and the held-out metrics pass. Missing, failed, revoked or expired certificates force `REENCODE_REQUIRED`.

The bridge is temporary migration machinery. When provenance-bound source ROI/image evidence remains available, prototypes should be progressively re-encoded into the current epoch and the bridge retired.

## New negative result

The current reference pooling oracle (`global mean + token-order buckets`) is not sufficient as a production spatial descriptor. A synthetic 4x4 left/right layout swap produced cosine `1.0` under the old descriptor. A geometry-bound 2D spatial pyramid separated the same states at cosine approximately `0.02439`.

Therefore production Q23 pooling must bind actual libmtmd grid/position identity. Equal token count is not evidence of equal spatial semantics.

## Primary runtime counterevidence

Current upstream llama.cpp failure evidence reports a Qwen-VL fine-grained OCR regression in `llama-server` while `llama-cli` on the same build remains correct even with identical visual-token counts. This strengthens the requirement for server-vs-cli differential tests and explicit preprocessing/grid/mRoPE identity in `VisualGeometryIdentity`.

## Target repo deltas

Created on `gschaidergabriel/Dr.-Unterweger` main:

- `70ae4c50e15f4bdc597b2a1a8389113e5f6e0230` — cross-epoch compatibility + spatial collision oracle
- `9032085e6450d34421bc11014579d102abda576d` — ClayCode fail-closed compatibility certificate contract
- `a226cd243fda7d01ba34c6af51b8a345eb6c93ff` — accepted-target self-hosted workflow

Concurrent target-VPS Q23 capability work produced real receipt commit:

- `9ffead52492e1d7c25c363af36e14e59f998bb0d` — bounded read-only multimodal inventory on accepted target VPS

That receipt detected no `llama-server`, `llama-cli`, `llama-mtmd-cli`, Qwen/mmproj artifacts, NVIDIA runtime or ROCm runtime in the bounded standard locations. No model inference was executed. This is a scoped non-detection, not a universal absence claim.

## Synthetic oracle

A deliberately compatible cross-epoch mapping achieved held-out top-1 `1.0`, AUROC `1.0`, FPR95 `0.0` in the synthetic reference oracle. A deliberately incompatible mapping fell to top-1 `0.00390625`, AUROC about `0.5007`, FPR95 about `0.9362` and was rejected. These values validate the decision mechanism only; they are not real Qwen performance claims.

## Required next falsifier

`Q23-T6 REAL-CROSS-EPOCH-GEOMETRY`:

1. Pin exact Qwen3.5-4B GGUF/mmproj and llama.cpp commit/backend/config.
2. Freeze provenance-bound screenshot/ROI fixtures: exact recurrence, near-neighbor UIs, small OCR text, spatial swaps, modal changes and true open-set unknowns.
3. Capture real libmtmd projected embeddings plus real grid/position schema.
4. Compare exact-epoch reuse, raw cross-epoch reuse, certified mapping and full re-encode.
5. Measure top-1, AUROC, FPR95, calibration, task/action success, latency and memory.
6. Run server-vs-cli identical-image differential.
7. Perturb preprocessing/runtime/backend/mmproj one factor at a time and verify certificate rejection/revocation.
8. If a compatibility bridge passes, backfill current-epoch prototypes and prove safe bridge retirement.

No QNDRF promotion is justified until this real-Qwen held-out experiment exists.
