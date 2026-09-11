# GO Avatar coordination delta — GPT-5.6 Sol — 2026-09-12

Status: **COORDINATION / EVIDENCE-RECONCILIATION ONLY**. This packet does not mint product/runtime credit and does not claim mutation ownership over the active avatar candidate.

## Owner target

Continue the current `go` avatar convergence toward one photoreal, lifelike, dynamically coherent identity: stable eyes/face, coherent head/body motion, eventual independent shoulder/body articulation where the asset representation supports it, shared film/camera treatment, and low average load with bounded short CPU peaks.

## Exact observed subjects

- Accepted Round-1 handoff parent ZIP SHA256: `03ad0dd38ba2cb3b09f01b3b38496e5acda9b700d4979e7ee28cf334f0b7d6d1`.
- Earlier inspected `buehne.html` SHA256: `9527ff5e4af48919f83d58c7e873c74bdeeebf3bf8bd084e810985c4918a1a93`.
- Local eye-mask candidate package SHA256: `a5b172642a9a40ef36c633c26d57743e6351fcbd1652502e4a9d453fd9cda479`.
- Blink-integration candidate reports `buehne.html` SHA256: `14b949ffd6cfe2de46bb321b952de2cc7a13c852a8f2ab76e797f98bf0cd7652`.
- Same integration receipt reports an internal `candidate_zip_sha256` of `1dc252d503afa827eb0b0237537703ea6627c4b78faa8eedf1352def402b28dd`, then prints `FINAL_ZIP_SHA256 168d4fe04b532554351e89ab9e5f78317ee2656e276df6e2092490451a94c5d8` after the manifest/write step. Therefore the only candidate for external artifact identity is the final byte hash `168d4f...`; the `1dc252...` value must not be presented as the same final ZIP identity. Rename/type it as a pre-finalization payload hash if that is what it is.

## Reconciled blink finding

A prior pixel falsifier measured very large peripheral deltas in full-head blink-related frames. That measurement is real, but it is **not by itself proof of a current live-render defect**.

Current source inspection shows the live blink path uses a dedicated `#augen-blink` image overlay, located inside `#kopf-dreh`, with `/augen_blink/blink_000..011.png`, while gaze/blink overlays follow the same head transform. Therefore:

- full-head historical/alternative blink-frame contamination = valid asset-level negative evidence;
- current live compositor identity failure = **UNRESOLVED until the actual composite path is measured**;
- do not mutate the head/base identity merely because unused or historical full-head frames differ.

## Mandatory next discriminator — blink/eye identity

Run against the exact final candidate bytes, not a neighboring source tree:

1. Bind candidate ZIP SHA256 `168d4fe04b532554351e89ab9e5f78317ee2656e276df6e2092490451a94c5d8` and extracted `buehne.html` SHA256 before execution.
2. Render or deterministically composite the **actual live base head + actual `#augen-blink` frame** for open, half-close, closed, half-open states.
3. Define the allowed-change mask from the blink overlay's nonzero alpha plus a tiny antialias margin; do not use a broad arbitrary eye band.
4. Outside that allowed-change mask, required pixel delta is exactly zero for the blink-only operation before film/camera post-processing. If the compositor intentionally modifies a larger region, name and justify that region explicitly.
5. Verify that the blink layer is a descendant of `#kopf-dreh` and follows the identical head transform for at least neutral and nonzero roll/yaw surrogate states.
6. Verify one blink layer and one gaze layer only; no stationary duplicate/ghost layer.
7. Verify that blink does not change the base head image source, expression layer identity, body frame, or camera state.
8. Separately evaluate whether the blink patch changes eye/skin identity inside its rectangle beyond the eyelid motion itself. A small rectangle is not sufficient if it contains skin/eye texture from another generated face. Prefer alpha restricted to the actual moving eyelid/occlusion pixels.
9. Record output frame hashes or deterministic pixel-stat receipts so the result is independently reproducible.

Promotion rule: only after this discriminator passes may the blink integration be called accepted at **blink compositor identity scope**. It still does not prove whole-avatar lifelikeness.

## Artifact identity gate

The integration packaging step must emit unambiguous identities:

- `parent_round_zip_sha256`
- `blink_mask_package_sha256`
- `buehne_sha256`
- optional `pre_finalize_payload_sha256` if useful
- `final_candidate_zip_sha256` computed after every ZIP mutation

No manifest field may ambiguously claim the final ZIP hash if the ZIP is subsequently changed. External promotion/readback must bind `final_candidate_zip_sha256` only.

## Failure classification corrections

- Worker/export prose that claimed a complete avatar export while also recording that `/home/ai-core-node/frankenstein-repo` was inaccessible: **EVIDENCE_INVALID**.
- Timebase probe that failed due malformed Python/indentation: **EVIDENCE_INVALID**, not product negative.
- Perf-metrology probe whose harness raised `AttributeError: 'NoneType' object has no attribute 'decode'`: **EVIDENCE_INVALID / HARNESS_FAILURE**, not avatar performance evidence.
- Large periphery delta in full-head blink assets: **ASSET_LEVEL_PRODUCT_NEGATIVE for those full-head assets**, but **not yet a live-compositor PRODUCT_NEGATIVE** because current runtime uses a local blink overlay.

## Motion/pose frontier after blink closure

The current RAF path advances breathing, body action, head-photo roll, mouth, head/body springs, camera, gaze, and rain as separate subsystems. The next architectural convergence target should be a frame-authoritative pose/compositor state that computes once then renders once, while preserving the existing optimization that avoids per-frame rasterization of invisible 1536x1024 layers.

Do not fake independent shoulders with a global torso warp. Current inspection found no shoulder-specific DOF; true shoulder independence requires a split shoulder/arm representation, articulated mesh, or newly generated compatible assets. New assets are owner-authorized, but they must preserve the same face/body identity and be empirically gated.

## Work ownership / anti-duplication

- Do not start a second blink implementation while the `go-avatar-integrate-blink-mask-qa-candidate-gpt56sol-20260912-0653` subject is under QA.
- Independent workers should run falsifiers/readbacks against that exact final candidate or work on disjoint boundaries (performance harness repair, pose-state metrology, shoulder asset representation).
- A failed infrastructure/harness probe must not trigger semantic avatar mutation.

## Evidence depth after this packet

- Source/asset understanding: advanced.
- Blink integration candidate: built, not promoted.
- Exact final candidate identity: known externally as `168d4f...`, internal manifest naming needs reconciliation.
- Blink live-compositor identity QA: open.
- Performance baseline: open; latest attempted metrology harness invalid.
- Unified pose state / independent shoulders: open.
- Physical visual acceptance / whole avatar lifelikeness: open.
- HCU/J-Space/training: no new evidence from this avatar delta; training credit remains zero.
