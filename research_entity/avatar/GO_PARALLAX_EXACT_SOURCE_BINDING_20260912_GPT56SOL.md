# GO — Avatar Parallax Exact Source Binding — 2026-09-12

Status: **EXACT SOURCE BINDING PASS; LIVE PARALLAX CREDIT REMAINS 0**

## Purpose

Close the remaining identity question between the four-layer Depth-Anything parallax assets and the head images actually consumed by the live avatar. This is an evidence-only promotion. No live avatar file, service, image asset or runtime configuration was changed.

## Execution boundary

Real host: `ai-core-node` via the machine-scoped local bridge.

Primary receipts:

- `go-avatar-gpt56sol-regscan-20260912-0801` — PASS
- `go-avatar-gpt56sol-parallax-map-20260912-0803` — PASS
- `go-avatar-gpt56sol-parallax-sourcebind-20260912-0806` — PASS
- `go-avatar-gpt56sol-parallax-compact-next-20260912-0812` — PASS

All receipts identify `machine_id=ai-core-node`, `owner=gabriel`, execution boundary `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`.

## Exact live subject observed

- `buehne.html`: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js`: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`

The live roll loader resolves `/kopf_rgba/roll/gier_+00_nick_+00_roll_±NN.png`.

## Binding result

For every live roll state `-25,-20,-15,-10,-05,+00,+05,+10,+15,+20,+25`, the matching directory under `kopf_rgba_parallax/` contains four 1536×1024 RGBA depth slices.

An independent reconstruction check performed the following for each roll state:

1. sum the four slice alpha planes;
2. reconstruct source RGB at visible pixels from the slice RGB values;
3. compare both against the exact corresponding live `/kopf_rgba/roll/...` image.

Result for all 11 states:

- `alpha_eq=True`
- `rgb_eq=True`
- classification `PASS`

Aggregate discriminator:

`ALL_ROLLS_SOURCE_BOUND True`

This is stronger than merely sharing dimensions, names, a generator, or a manifest. The parallax slice set is now empirically bound to the exact live roll-image family it is intended to replace/reconstruct.

## Negative controls

The same reconstruction was compared against the separate `kopf_rgba_tiefe/roll` and `kopf_rgba_tiefe_detail/roll` image families. Those RGB values do **not** match: representative visible-pixel mean absolute errors are roughly 10–17 levels with maxima reaching 221–255. Therefore the exact match to `kopf_rgba/roll` is discriminative, not a trivial consequence of shared alpha geometry.

## Registration evidence available for the next gate

`rig2/augen_anker_exakt.json` is present and identifies:

- head rotation anchor: `(768,600)`
- roll-0 eye anchor: `(610,207)`
- exact per-roll eye translation offsets for the full -25…+25 ladder.

The live runtime currently applies the roll image atomically and binds the eye/blink overlay to the same roll value and per-roll offset. This accepted invariant is the registration baseline parallax must preserve.

## Promotion decision

Promoted:

- parallax generator lineage: PASS
- static reconstruction integrity: PASS
- exact parallax→live-roll source identity: **PASS**

Still zero/open:

- perceptual depth/lifelikeness improvement: OPEN
- dynamic eye/face registration preservation: OPEN
- live parallax integration: 0
- whole-avatar acceptance: unchanged

## Next exact discriminator

The next legal step is matched dynamic A/B, not another provenance pass:

1. keep the exact current live roll subject as baseline;
2. render the same roll/eye/blink state with depth-dependent motion only;
3. preserve source alpha/silhouette and quantify seam/halo/edge inflation;
4. measure eye-region registration against the exact per-roll anchor model;
5. test the entire roll ladder, not only +00;
6. benchmark production-relevant compositor cost;
7. promote a reversible live candidate only if depth/lifelikeness increases without identity, registration, silhouette, temporal-stability or 60-FPS regression.

No evidence in this note authorizes a live mutation by itself.
