# GO — Avatar Parallax Fixed-Alpha Falsifier — 2026-09-12

Status: **CANDIDATE REJECTED; NATIVE CHROME CANVAS `lighter` REMAINS PREFERRED SCRATCH PATH**

## Hypothesis

The first dynamic Canvas2D parallax sweep showed small alpha/silhouette perturbations when the four depth slices are translated independently. A plausible correction was to decouple output silhouette alpha from shifted depth weights:

1. shift the four premultiplied RGB/alpha slice fields;
2. normalize RGB by shifted alpha support;
3. fall back to exact source RGB when support is weak;
4. force output alpha to the exact unshifted live-source alpha.

This would guarantee a byte-exact silhouette while retaining depth-dependent internal texture motion.

## Real-host discriminator

Receipt: `go-avatar-gpt56sol-parallax-fixedalpha-gate-20260912-0816`

Boundary: real `ai-core-node`, staging/scratch only. Production hashes remained unchanged and `frankenstein-buehne.service` remained active.

Tested all 11 live roll states at amplitudes `0.25, 0.50, 0.75, 1.00, 1.50` source pixels using the exact four parallax slices bound to each `/kopf_rgba/roll` source.

## Result

The correction succeeds at only one property:

- output alpha exact for every roll/amplitude: **PASS**.

But it loses too much image sharpness and registration quality.

At `A=0.25`:

- mean opaque-pixel RGB MAE across rolls: `2.0233` levels;
- worst p99 opaque RGB error: `20.716`;
- worst edge RGB MAE: `4.7399`;
- Laplacian detail-energy ratio range: `0.8866–0.8974`;
- worst measured eye-region phase shift: `0.6161 px`.

At `A=0.50`:

- mean opaque-pixel RGB MAE: `3.9234`;
- worst p99 opaque RGB error: `40.746`;
- worst edge RGB MAE: `7.8187`;
- Laplacian detail-energy ratio range: `0.8215–0.8398`;
- worst measured eye-region phase shift: `0.7197 px`.

At `A=1.00`:

- mean opaque RGB MAE: `8.0091`;
- worst p99 opaque RGB error: `82.929`;
- worst edge RGB MAE: `14.2591`;
- worst measured eye-region phase shift: `0.8975 px`.

The loss of high-frequency energy is systematic across the roll ladder, not a single-pose anomaly. The normalization/interpolation step therefore trades a tiny silhouette perturbation for visibly more destructive smoothing and larger eye-region displacement.

## Control comparison

An independent real-Chrome Canvas2D `lighter` gate (`go-avatar-gpt56sol-parallax-quant-gate-20260912-0753`) measured the simpler compositor across all 11 roll states.

At `A=0.25` its worst observed values were:

- alpha MAE `0.061064 / 255` over the full canvas;
- mask Jaccard `>= 0.99725789`;
- lost visible pixels `<= 43`;
- gained visible pixels `<= 422`;
- deep-hole pixels `0`;
- absolute eye-region best-shift `<= 0.10 px`.

At `A=0.50`:

- alpha MAE `<= 0.126813 / 255`;
- mask Jaccard `>= 0.99627155`;
- lost visible pixels `<= 98`;
- gained visible pixels `<= 523`;
- deep-hole pixels `0`;
- absolute eye-region best-shift `<= 0.25 px`.

The native browser path therefore preserves eye registration materially better while its silhouette error remains small and contains no deep holes in this gate.

## Decision

**Reject fixed-alpha normalized reconstruction for the current avatar.**

Do not add normalization/inpainting merely to optimize alpha metrics. It is a Goodhart failure: the targeted metric becomes perfect while the actual photoreal/detail/registration objective gets worse.

Preferred candidate frontier remains:

- Chrome/Canvas2D additive `lighter`;
- amplitude region `0.25–0.50 px` for the first perceptual A/B;
- exact current roll-source identity;
- unchanged eye/blink registration chain;
- no live promotion until a matched visual/perceptual gate shows a real depth benefit.

Credits:

- fixed-alpha candidate: **PRODUCT_NEGATIVE at scratch visual-integrity scope**;
- live avatar: unchanged;
- live parallax integration: `0`.
