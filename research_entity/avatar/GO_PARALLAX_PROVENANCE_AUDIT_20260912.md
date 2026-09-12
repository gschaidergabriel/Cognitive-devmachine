# GO — Avatar Parallax Provenance Audit — 2026-09-12

Status: **SOURCE/PROVENANCE ESTABLISHED; LIVE INTEGRATION NOT YET PROMOTED**

## Scope

Read-only audit of the real `ai-core-node` avatar subject under `/home/ai-core-node/.claude/star/visual`. This note does not claim that `kopf_rgba_parallax/` is live-wired, visually superior, or accepted for product use.

Live subject observed during the audit:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py` SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js` SHA-256: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`

Bridge evidence:

- `go-avatar-gpt56sol-parallax-provenance-20260912-0722`: PASS
- `go-avatar-gpt56sol-parallax-compact-audit-20260912-0724`: **EVIDENCE_INVALID** because the audit script itself raised a Python `TypeError`; no product conclusion was drawn.
- `go-avatar-gpt56sol-parallax-compact-audit-v2-20260912-0725`: PASS, exit 0.

## Exact asset inventory

The live host contains **48 PNG assets in 12 directories**, not the older handoff shorthand of “12 files”. The directories are one neutral/head-zero set plus roll states `-25,-20,-15,-10,-05,+00,+05,+10,+15,+20,+25` degrees. Every state contains four 1536×1024 RGBA depth slices:

1. `slice_0_front_nase.png`
2. `slice_1_mitte_gesicht.png`
3. `slice_2_seite_ohren.png`
4. `slice_3_hinten_haar.png`

`kopf_zero_mit_augen` is byte-identical to `gier_+00_nick_+00_roll_+00` for all four slices (`ZERO_EQUALS_ROLL0=True`).

## Provenance finding

The prior uncertainty “where did these parallax assets come from?” is resolved at source level. The real host contains `tiefe_bauen.py`; its text explicitly identifies:

- `depth-anything/Depth-Anything-V2-Small-hf`
- a `parallax` mode for head depth slices
- `modus_parallax()`
- writing a `parallax/manifest.json`

Therefore the correct classification is **generated depth-slice candidate with identified generator/model lineage**, not unexplained image material.

This does **not** yet prove that the copied `kopf_rgba_parallax/` tree is byte-for-byte reconstructible from a particular original head source + exact model/cache/runtime. That stronger claim remains a separate gate.

## Geometry / alpha evidence at roll +00

For the four +00 layers, the read-only audit measured:

| layer | nonzero-alpha fraction | opaque fraction | alpha bbox |
|---|---:|---:|---|
| front_nase | 0.103722 | 0.003168 | `(574,40)-(962,599)` |
| mitte_gesicht | 0.099026 | 0.000000 | `(581,40)-(962,599)` |
| seite_ohren | 0.090314 | 0.000000 | `(603,40)-(957,575)` |
| hinten_haar | 0.088564 | 0.000000 | `(580,40)-(962,599)` |

Union coverage is `0.104076` of the full 1536×1024 canvas. Pixels with >1 nonzero-alpha layer occupy `0.099212` of the full canvas. This is consistent with strongly overlapping soft depth weights rather than four disjoint hard cut-outs. That is a structural observation only; it is not yet visual-quality acceptance.

## Promotion decision

**Do not wire the 48 slices blindly into the live compositor yet.** The lineage question is now substantially answered, but the next promotion must establish that the four-layer reconstruction is coherent and that layer motion adds depth without degrading face identity, eye registration, roll registration, edge quality, or the established 60 FPS runtime boundary.

The current live roll registration fix is independently accepted on the real host with exact HTML hash `18770d8e...` and 5/5 sampled 60 FPS after promotion. That accepted subject should be treated as the baseline, not silently replaced by an unmeasured parallax experiment.

## Next exact discriminator

Run a non-destructive integrity/AB gate bound to the exact current subject:

1. hash `tiefe_bauen.py`, relevant manifests, original source head(s), and all 48 slice files;
2. verify the generator's reconstruction/alpha-sum invariant for all 12 states;
3. prove overlapping layers preserve source RGB/alpha semantics rather than creating ghost/double-face energy;
4. render baseline vs parallax using the same pose/eye/blink state across the roll ladder;
5. measure face/eye registration, seam/halo/ghost metrics and runtime FPS;
6. promote only if the parallax variant wins the visual discriminator while preserving the existing runtime and identity gates.

Until that passes:

- parallax source/provenance credit: **bounded PASS at generator-lineage scope**;
- parallax live-integration credit: **0**;
- avatar whole-product credit: **unchanged**;
- GRID10/GWT/J-Space/effect/training credit: **unchanged**.
