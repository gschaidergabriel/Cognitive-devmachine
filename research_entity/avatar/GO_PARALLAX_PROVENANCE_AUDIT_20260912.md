# GO — Avatar Parallax Provenance / Compositing Audit — 2026-09-12

Status: **ASSET LINEAGE + ALPHA-PARTITION INTEGRITY PASS; NAIVE CSS SOURCE-OVER COMPOSITING FALSIFIED; LIVE PARALLAX CREDIT 0**

## Scope

Read-only audit of the real `ai-core-node` avatar subject under `/home/ai-core-node/.claude/star/visual`. This note does not claim that `kopf_rgba_parallax/` is live-wired, visually superior, or accepted for product use.

Live baseline observed during the audit:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py` SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js` SHA-256: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`

Bridge evidence used here:

- `go-avatar-gpt56sol-parallax-provenance-20260912-0722`: PASS.
- `go-avatar-gpt56sol-parallax-compact-audit-20260912-0724`: **EVIDENCE_INVALID** because the audit script itself raised a Python `TypeError`; no product conclusion.
- `go-avatar-gpt56sol-parallax-compact-audit-v2-20260912-0725`: PASS, exit 0.
- `go-avatar-gpt56sol-parallax-integrity-20260912-0734`: **EVIDENCE_INVALID** because its generated command JSON was malformed; no product conclusion.
- `go-avatar-gpt56sol-parallax-integrity-v2-20260912-0736`: PASS, exit 0.
- `go-avatar-gpt56sol-parallax-sourceover-audit-v2-20260912-0743`: PASS, exit 0; this is the compositor-semantics falsifier.

## Exact asset inventory

The real host contains **48 PNG assets in 12 directories**, not the older handoff shorthand of “12 files”. There is one neutral/head-zero set plus roll states `-25,-20,-15,-10,-05,+00,+05,+10,+15,+20,+25` degrees. Every state contains four 1536×1024 RGBA depth slices:

1. `slice_0_front_nase.png`
2. `slice_1_mitte_gesicht.png`
3. `slice_2_seite_ohren.png`
4. `slice_3_hinten_haar.png`

`kopf_zero_mit_augen` is byte-identical to `gier_+00_nick_+00_roll_+00` for all four slices (`ZERO_EQUALS_ROLL0=True`).

## Generator / provenance PASS

The real host contains `tiefe_bauen.py`, SHA-256:

`41c4a7c6195b421eb026d122040fca8e58595f277cdb396777f30c7a500ae33d`

The source explicitly binds:

- `depth-anything/Depth-Anything-V2-Small-hf`, offline/local-cache loading;
- `BANDS = 4`;
- `FEDER = 0.020` soft depth-boundary weighting;
- `modus_parallax()` for `kopf_zero_mit_augen` plus all roll poses;
- depth-derived quantile boundaries;
- integer alpha splitting with residual pixels assigned to the maximum-weight band;
- an assertion that the arithmetic sum of the four slice alphas is byte-identical to the original alpha;
- `manifest.json` output.

The manifest `kopf_rgba_tiefe/parallax/manifest.json` has SHA-256:

`00b773e05b990547992484e27e72a10add7be5720dee10c40ac05b0e3df640d2`

It records 4 slices and `alpha_summe_identisch: true` for the neutral image and every roll state from -25 through +25 degrees.

Classification: **generated depth-slice candidate with identified generator/model lineage and explicit arithmetic alpha-partition invariant**.

## Static slice-content integrity PASS

The independent real-host integrity runner inspected all 12 four-layer states. Across every state:

- `FILES = 4`;
- `ALPHA_SUM_MAX = 255`;
- visible union is stable at approximately 10.34–10.41% of the 1536×1024 canvas;
- roughly 154k–162k pixels have more than one nonzero-alpha layer;
- **`RGB_OVERLAP_MAXDIFF = 0`** across all overlapping layer-pair pixels.

Therefore multiple soft-alpha slices carry the same source RGB wherever they overlap. The PNGs themselves are not statically color-disagreeing copies of the face.

Important correction: this is **asset/partition integrity**, not yet browser reconstruction integrity.

## Falsifier: arithmetic alpha sum != browser source-over reconstruction

A second real-host audit evaluated the exact four slice alphas under ordinary source-over semantics:

`A_composite = 1 - product(1 - A_slice_i)`

while the generator's invariant is:

`A_original = sum(A_slice_i)`

For overlapping soft masks these are not equivalent.

Measured across all 12 states:

- mean alpha loss over visible pixels: approximately **0.212–0.228**;
- median loss: approximately **0.250–0.278**;
- 90th-percentile loss: approximately **0.293–0.302**;
- maximum loss: approximately **0.295–0.304**;
- roughly **72–76%** of visible pixels lose more than 0.20 alpha;
- in pixels that were originally effectively opaque, ordinary source-over produces only about **0.766–0.783 mean composite alpha**;
- worst originally-opaque pixels drop to about **0.696–0.705 alpha**.

Example, roll +00:

- `LOSS_MEAN = 0.219460`
- `LOSS_P50 = 0.269057`
- `LOSS_P90 = 0.300046`
- `LOSS_MAX = 0.302037`
- `OPAQUE_COMP_MEAN = 0.774643`
- `OPAQUE_COMP_MIN = 0.697963`

This is a large deterministic opacity defect. A naive stack of four ordinary alpha-composited images would make the head substantially more translucent/washed out even at **zero parallax displacement**.

Classification:

**PRODUCT_NEGATIVE / DESIGN FALSIFIER for a naive multi-layer source-over compositor.**

It does not invalidate the Depth-Anything maps or the slice assets. It invalidates the assumption that the arithmetic alpha partition can be rendered unchanged through ordinary browser source-over layering.

## Current accepted baseline that must be protected

The live roll-registration fix is independently accepted on the real host at exact HTML SHA `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`.

That promotion removed delayed local roll/eye interpolation and made photo-to-eye-overlay registration atomic while leaving the shared outer wrapper free to spring. Its live receipt observed active service/HTTP and 5/5 sampled 60 FPS.

The parallax experiment must not silently replace this baseline or reintroduce opacity, identity, eye, blink, or roll-registration regressions.

## Promotion decision

**Do not live-wire the four depth PNGs with normal source-over semantics.** That candidate path is now falsified before live mutation.

The next missing mechanism is not more depth generation. It is a compositor whose zero-displacement output preserves the accepted source image before any depth motion is allowed.

Candidate implementation families may include:

- a GPU/canvas/WebGL path with explicitly controlled premultiplied/additive accumulation;
- a regenerated mask representation whose browser compositing law reconstructs the original by construction;
- another deterministic compositor that demonstrates zero-offset pixel equivalence.

No candidate gets promoted by theory alone.

## Next exact discriminator

Before any dynamic parallax A/B:

1. implement the smallest scratch-only compositor candidate;
2. at zero displacement, compare its output against the exact original head image;
3. require pixel/alpha equivalence within an explicitly bounded quantization tolerance;
4. only then introduce tiny depth-dependent translations;
5. compare baseline vs parallax across the full roll ladder with identical eyes/blink/pose;
6. measure eye-to-face registration, silhouette/seam/halo/ghost energy and temporal stability;
7. read back GPU/FPS on the exact candidate;
8. rollback/reject on identity, opacity, registration or runtime regression.

Until that passes:

- parallax source/provenance credit: **PASS at exact generator-lineage scope**;
- parallax asset/alpha-partition integrity: **PASS**;
- naive source-over compositor: **REJECTED**;
- browser zero-offset reconstruction: **OPEN**;
- parallax dynamic visual-quality credit: **0**;
- parallax live-integration credit: **0**;
- avatar whole-product credit: **unchanged**;
- GRID10/GWT/J-Space/effect/training credit: **unchanged**.
