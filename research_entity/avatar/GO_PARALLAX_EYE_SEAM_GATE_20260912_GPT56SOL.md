# GO — Avatar Parallax Eye-Seam Gate — 2026-09-12

Status: **A=0.25 NATIVE CHROME `lighter` PASSES THE CURRENT NUMERIC PRE-LIVE GEOMETRY / EYE-SEAM GATES; PERCEPTUAL BENEFIT NOT YET PROVEN; LIVE PARALLAX CREDIT REMAINS 0.**

## Scope and evidence boundary

This packet records a real-host, read-only/scratch discriminator on `ai-core-node` for the current avatar subject under `/home/ai-core-node/.claude/star/visual/`.

It does **not** claim that parallax improves the avatar perceptually, and it does **not** claim a live integration. Production files were not mutated by this lane.

Current production subject observed throughout the gate:

- `buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py` SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js` SHA-256: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`

Execution boundary recorded by the receipts: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`.

## Upstream provenance already established

A preceding real-host source-binding discriminator proved that, for every tested live roll pose from `-25` through `+25`, the four files under:

`kopf_rgba_parallax/gier_+00_nick_+00_roll_<ROLL>/`

reconstruct the currently used `kopf_rgba/roll/gier_+00_nick_+00_roll_<ROLL>.png` subject exactly at zero displacement:

- alpha equal;
- RGB MAE `0.0`;
- RGB max error `0`.

Receipt: `go-avatar-gpt56sol-parallax-sourcebind-20260912-0806`.

This removes the previous ambiguity that the depth slices might belong to an alternate `_tiefe` / `_detail` head subject.

## Exact eye registration authority used

The gate used the measured roll-state anchor table from `rig2/augen_anker_exakt.json` and the current live overlay geometry:

- eye patch left: `31%`;
- top: `12%`;
- width: `27%`;
- transform origin: `70.38% 241.32%`;
- `#augen-blink` and `#pupillen-glow` both live inside `#kopf-dreh`;
- current roll transition applies the measured translation atomically with the roll photo step rather than interpolating a stale eye position across several frames.

The live code now applies the same measured roll translation to both blink and gaze layers, preserving one eye anchor authority.

## Candidate compositor

The retained candidate is the native browser primitive already characterized in scratch:

- Chrome Canvas2D;
- `globalCompositeOperation = "lighter"`;
- four depth slices;
- depth coefficients `[+1, +1/3, -1/3, -1] * A`;
- exact current roll subject;
- no inpainting/normalization layer.

The conservative first amplitude under this packet is `A = 0.25` source pixels.

## Real-Chrome whole-head quantitative gate

Receipt: `go-avatar-gpt56sol-parallax-quant-gate-20260912-0753`.

Across all 11 roll poses at `A=0.25`, worst observed values were:

- full-canvas alpha MAE: `0.061064 / 255`;
- minimum visible-mask Jaccard: `0.99725789`;
- lost visible pixels: `<= 43`;
- gained visible pixels: `<= 422`;
- deep-hole pixels: `0`;
- absolute eye-region best-shift: `<= 0.10` source px.

At `A=0.50`, the same gate still produced no deep holes, but the perturbation was larger:

- alpha MAE `<= 0.126813 / 255`;
- minimum Jaccard `>= 0.99627155`;
- lost visible pixels `<= 98`;
- gained visible pixels `<= 523`;
- absolute eye-region best-shift `<= 0.25` source px.

Therefore `A=0.25` remains the safer first perceptual candidate.

## Independent depth-field / eye-registration discriminator

Receipt: `go-avatar-gpt56sol-parallax-registration-field-v2-20260912-0752`.

Across all 11 roll poses:

- at `A=0.25`, eye-core p90 effective displacement was approximately `0.232–0.248` source px;
- at `A=0.50`, approximately `0.465–0.496` source px;
- at `A=0.50`, the mean eye-core versus eye-ring differential displacement remained at most about `0.0776` px.

Production `buehne.html` pre/post hash remained byte-identical.

## Fixed-alpha reconstruction falsifier

A proposed correction forced exact source alpha after separately shifting and normalizing RGB support.

Receipt: `go-avatar-gpt56sol-parallax-fixedalpha-gate-20260912-0816`.

That candidate was rejected as **PRODUCT_NEGATIVE at scratch visual-integrity scope** despite perfect alpha preservation.

At `A=0.25` it caused:

- mean opaque RGB MAE `2.0233` levels;
- worst p99 opaque error `20.716`;
- worst edge RGB MAE `4.7399`;
- Laplacian detail-energy ratio only `0.8866–0.8974`;
- worst eye-region phase displacement `0.6161` px.

At `A=0.50` it was materially worse. The correction optimized silhouette alpha while degrading the actual photoreal/detail/registration objective, so it is a Goodhart failure and must not be promoted.

Canonical rejection packet: `GO_PARALLAX_FIXED_ALPHA_FALSIFIER_20260912_GPT56SOL.md`.

## Eye-patch seam gate

The exact remaining pre-live concern was whether a fixed/registered eye-overlay patch would expose a new hard rectangular seam when the face texture beneath it received depth-dependent motion.

### Attempt 1 — invalid harness evidence

Receipt: `go-avatar-gpt56sol-parallax-eye-seam-gate-20260912-0804`.

Chrome produced a valid first pose but later screenshot files were not readable. This is classified **EVIDENCE_INVALID**, not `PRODUCT_NEGATIVE`.

No conclusion was promoted from the partial run.

### Attempt 2 — repaired isolated-capture harness

Receipt: `go-avatar-gpt56sol-parallax-eye-seam-gate-v2-20260912-0807`.

Repair:

- isolated Chrome profile per capture;
- output existence/size validation;
- image decode verification;
- bounded retry;
- identical head/eye geometry otherwise.

Result:

- `22/22` captures valid on first attempt: baseline + `A=0.25` for all 11 roll poses;
- `buehne.html` pre/post SHA remained exactly `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`;
- `LIVE_MUTATION=0`.

Worst observed seam metrics at `A=0.25`:

- eye-patch core RGB MAE: `0.0892126 / 255`;
- patch-ring RGB MAE: `1.0794283 / 255`;
- patch-ring p99 RGB difference: `12.3333 / 255`;
- outer-ring RGB MAE: `1.2277273 / 255`;
- mean patch-ring gradient-energy ratio: `0.9728786–0.9824031` relative to baseline;
- patch-ring p99 gradient-energy ratio: `0.9420276–0.9691472`.

The decisive result is that the patch boundary does **not** gain a harder edge under this matched gate. Gradient energy is slightly lower rather than higher for every tested roll state.

This falsifies the immediate hypothesis that `A=0.25` necessarily creates a new visible eye-patch seam through local edge inflation.

## Decision

### Promoted at exact scope

`A=0.25` with native Chrome Canvas2D `lighter` is admitted as a **PRE-LIVE PERCEPTUAL CANDIDATE** because the current exact-source numeric gates show:

- correct source provenance across all 11 roll states;
- bounded silhouette perturbation;
- zero deep holes in the measured head gate;
- very small eye-region displacement;
- no measured hard eye-patch seam inflation;
- no production mutation during the tests.

### Explicitly not promoted

The following remain zero/unproven:

- perceptual depth benefit;
- photorealism improvement;
- live parallax integration;
- sustained runtime performance in the production loop;
- whole-avatar acceptance;
- whole-product completion;
- GRID10/GWT/J-Space/effect/training credit.

**Live parallax integration credit remains `0`.**

A technically safe micro-displacement is not automatically useful. At the current source-to-CSS scale, `A=0.25` may be too subtle to produce a meaningful visible depth benefit.

## Next exact gate

Run one matched **benefit-vs-artifact perceptual A/B** using the same:

- roll pose;
- eye/blink state;
- background;
- canvas/CSS scale;
- film/filter state;
- viewport;
- source identities.

Compare at minimum:

1. baseline `A=0`;
2. `A=0.25` native `lighter`;
3. one larger still-eligible candidate only if needed to establish a visible benefit.

The discriminator must separately score:

- perceived 3D/depth benefit;
- eye/face registration;
- silhouette/halo/seam artifacts;
- sharpness/detail preservation;
- temporal plausibility when the offset is animated.

If `A=0.25` is imperceptible, do **not** promote it merely because it is safe. Select the smallest amplitude that demonstrates repeatable benefit while remaining inside the artifact gates.

Only after a positive matched perceptual discriminator should a reversible live feature-flag candidate be installed, with:

- exact pre-mutation hashes;
- one mutation owner;
- rollback artifact;
- live service readback;
- screenshot/video evidence;
- runtime/performance measurement;
- post-test hash + rollback verification if rejected.

## Failure classifications preserved

- fixed-alpha normalized reconstruction: **PRODUCT_NEGATIVE** at scratch visual-integrity scope;
- eye-seam attempt 1: **EVIDENCE_INVALID** harness failure;
- eye-seam attempt 2: **PASS** at read-only matched 11-pose seam scope;
- live parallax: **NOT YET EXECUTED / CREDIT 0**.
