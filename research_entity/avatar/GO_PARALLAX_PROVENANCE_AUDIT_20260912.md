# GO — Avatar Parallax Provenance / Integrity Audit — 2026-09-12

Status: **SOURCE/PROVENANCE + STATIC RECONSTRUCTION INTEGRITY ESTABLISHED; LIVE PARALLAX INTEGRATION NOT YET PROMOTED**

## Scope

Read-only audit of the real `ai-core-node` avatar subject under `/home/ai-core-node/.claude/star/visual`. This note does not claim that `kopf_rgba_parallax/` is live-wired, visually superior, or accepted for product use.

Live subject observed during the audit:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py` SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js` SHA-256: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`

Bridge evidence:

- `go-avatar-gpt56sol-parallax-provenance-20260912-0722`: PASS.
- `go-avatar-gpt56sol-parallax-compact-audit-20260912-0724`: **EVIDENCE_INVALID** because the audit script itself raised a Python `TypeError`; no product conclusion was drawn.
- `go-avatar-gpt56sol-parallax-compact-audit-v2-20260912-0725`: PASS, exit 0.
- `go-avatar-gpt56sol-parallax-integrity-20260912-0734`: **EVIDENCE_INVALID** because the generated command JSON contained unescaped physical newlines; it was not treated as product evidence.
- `go-avatar-gpt56sol-parallax-integrity-v2-20260912-0736`: PASS, exit 0 on the real `ai-core-node` host.

## Exact asset inventory

The live host contains **48 PNG assets in 12 directories**, not the older handoff shorthand of “12 files”. The directories are one neutral/head-zero set plus roll states `-25,-20,-15,-10,-05,+00,+05,+10,+15,+20,+25` degrees. Every state contains four 1536×1024 RGBA depth slices:

1. `slice_0_front_nase.png`
2. `slice_1_mitte_gesicht.png`
3. `slice_2_seite_ohren.png`
4. `slice_3_hinten_haar.png`

`kopf_zero_mit_augen` is byte-identical to `gier_+00_nick_+00_roll_+00` for all four slices (`ZERO_EQUALS_ROLL0=True`).

## Generator / provenance

The real host contains `tiefe_bauen.py`, SHA-256:

`41c4a7c6195b421eb026d122040fca8e58595f277cdb396777f30c7a500ae33d`

The source explicitly binds:

- `depth-anything/Depth-Anything-V2-Small-hf`, offline/local-cache loading;
- `BANDS = 4`;
- `FEDER = 0.020` soft depth-boundary weighting;
- `modus_parallax()` for `kopf_zero_mit_augen` plus all roll poses;
- depth-derived quantile boundaries;
- integer alpha splitting with residual pixels assigned to the maximum-weight band;
- an assertion that the sum of the four slice alphas is byte-identical to the original alpha;
- `manifest.json` output.

The current manifest is:

`kopf_rgba_tiefe/parallax/manifest.json`

SHA-256:

`00b773e05b990547992484e27e72a10add7be5720dee10c40ac05b0e3df640d2`

It records 4 slices and `alpha_summe_identisch: true` for the neutral image and every roll state from -25 through +25 degrees.

Classification: **generated depth-slice candidate with identified generator/model lineage and explicit reconstruction invariant**. This is no longer an unexplained asset set.

## Geometry / alpha evidence

For roll +00 the four layers measured:

| layer | nonzero-alpha fraction | opaque fraction | alpha bbox |
|---|---:|---:|---|
| front_nase | 0.103722 | 0.003168 | `(574,40)-(962,599)` |
| mitte_gesicht | 0.099026 | 0.000000 | `(581,40)-(962,599)` |
| seite_ohren | 0.090314 | 0.000000 | `(603,40)-(957,575)` |
| hinten_haar | 0.088564 | 0.000000 | `(580,40)-(962,599)` |

The four layers therefore deliberately overlap as soft depth weights rather than acting as disjoint hard cut-outs.

## Independent static reconstruction check

The real-host integrity runner independently inspected all 12 four-layer states.

For every state:

- `FILES = 4`;
- `ALPHA_SUM_MAX = 255`;
- visible union is stable at approximately 10.34–10.41% of the 1536×1024 canvas;
- there are roughly 154k–162k pixels with more than one nonzero-alpha layer;
- **`RGB_OVERLAP_MAXDIFF = 0`** across all overlapping layer-pair pixels.

This means overlapping slices preserve the same RGB source value wherever multiple soft-alpha layers coexist. There is no static RGB disagreement between depth layers that could itself create a double/ghost face before transforms are applied.

Together with the generator assertion and manifest, static reconstruction integrity is now a bounded PASS.

## Current accepted baseline that must be protected

The live roll-registration fix is independently accepted on the real host at exact HTML SHA `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`.

That promotion replaced delayed local roll/eye interpolation with atomic photo-to-eye-overlay registration while leaving the shared outer wrapper free to spring. The live receipt also observed active service/HTTP and 5/5 sampled 60 FPS.

Therefore the parallax experiment must not silently replace this baseline or reintroduce eye/head misregistration.

## Promotion decision

**Do not promote parallax to live yet.** Provenance and static reconstruction are no longer blockers. The remaining blocker is dynamic visual causality:

> Does small depth-dependent motion create a stronger 3D/lifelike head while preserving face identity, eyes/blink/roll registration, seam quality and the established 60 FPS runtime boundary?

## Next exact discriminator

Run a reversible, exact-subject A/B gate:

1. baseline = current accepted atomic-roll subject;
2. variant = same subject plus the four depth slices for the same pose, with conservative depth-dependent transforms only;
3. same pose / eyes / blink state / viewport / render path for A and B;
4. test the full roll ladder, especially transitions around ±5/10/15/20/25°;
5. measure or inspect eye-to-face registration, silhouette/edge seams, haloing, ghost/double-face energy and temporal stability;
6. read back service/HTTP/GPU and FPS after the variant;
7. immediate rollback on any identity or registration regression;
8. promote only if B wins visual depth/lifelikeness without violating the accepted runtime/identity gates.

Until that A/B passes:

- parallax source/provenance credit: **PASS at exact generator-lineage scope**;
- parallax static reconstruction integrity: **PASS**;
- parallax live-integration credit: **0**;
- avatar whole-product credit: **unchanged**;
- GRID10/GWT/J-Space/effect/training credit: **unchanged**.
