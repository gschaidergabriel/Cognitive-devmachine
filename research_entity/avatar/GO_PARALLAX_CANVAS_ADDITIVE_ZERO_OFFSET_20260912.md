# GO — Avatar Parallax Canvas Additive Zero-Offset Gate — 2026-09-12

Status: **SCRATCH ZERO-OFFSET RECONSTRUCTION PASS; DYNAMIC PARALLAX OPEN; LIVE INTEGRATION CREDIT 0**

This note is the successor evidence delta to `GO_PARALLAX_PROVENANCE_AUDIT_20260912.md` for browser-compositor selection. It does not change the live avatar.

## Why this gate exists

The four Depth-Anything parallax slices have an arithmetic alpha-partition invariant: their alpha values sum byte-exactly to the original head alpha. A prior real-host falsifier showed that ordinary browser `source-over` does not preserve that invariant when soft alpha masks overlap. At roll +00, normal source-over lost mean alpha `0.219460`; originally opaque pixels reconstructed at only `0.774643` mean alpha, with a minimum near `0.697963`. Therefore naive four-IMG/CSS stacking is rejected.

## Candidate tested

On the real `ai-core-node`, in a completely separate headless Chrome profile and scratch HTML under `/var/tmp`, the exact +00 source head and exact four depth slices were rendered into Canvas 2D using:

`globalCompositeOperation = "lighter"`

No live profile, service, HTML, image asset, daemon or persistent avatar file was modified.

The same scratch run also rendered the same four slices with ordinary `source-over` as a control.

Receipt:

`go-avatar-gpt56sol-parallax-canvas-blend-ab-20260912-0745`

Execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`.

## Real-Chrome A/B result

Canvas size: 1536×1024.

### Additive / `lighter`

Compared against the exact original +00 head:

- mean absolute error over all RGBA channels: `0.0194416 / 255`;
- alpha mean absolute error: **0**;
- alpha maximum error: **0**;
- fraction of all channels with error >1: `0.000104904`;
- fraction with error >4: `0.0000230471`.

The all-pixel RGB maximum of 128 was traced to near/fully transparent regions where unpremultiplied RGB is not visually authoritative. A second real-Chrome audit therefore conditioned error on reference alpha and measured premultiplied error.

Receipt:

`go-avatar-gpt56sol-parallax-canvas-visible-audit-20260912-0747`

For pixels with reference `alpha >= 254`:

- pixels: `158726`;
- RGB mean absolute error: `0.237667 / 255`;
- RGB maximum error: `2 / 255`;
- RGB fraction with error >1: `0.00000840022` (about 0.00084% of RGB channels);
- RGB fraction with error >2: `0`;
- premultiplied RGB mean absolute error: `0.237665 / 255`;
- premultiplied RGB maximum error: `1.992157 / 255`.

For `alpha >= 128`, RGB maximum error was 3 and no channel exceeded 4. For `alpha >= 32`, RGB maximum error was 8; large raw RGB outliers are confined to increasingly transparent pixels, while alpha remains exact.

Classification: **PASS within ordinary 8-bit Canvas quantization at zero displacement.**

### Ordinary source-over control

In the same Chrome run:

- mean absolute RGBA error: `1.542765 / 255`;
- alpha mean absolute error: `5.901361 / 255` across the whole canvas;
- alpha maximum error: `78 / 255`;
- alpha fraction with error >4: `0.0931803`.

This independently reproduces the earlier analytical/source-over falsifier in the browser itself.

## Promotion decision

The smallest viable browser reconstruction primitive is now empirically identified:

**Canvas 2D additive (`lighter`) is admitted for scratch dynamic-parallax experiments because it preserves alpha exactly at zero displacement and reproduces visible RGB to <=2 levels in effectively opaque pixels.**

This is not yet a live-product promotion. It establishes only the compositor primitive.

## Next exact gate

The next experiment may introduce tiny, depth-dependent transforms in scratch Canvas only. It must:

1. start from the accepted zero-offset additive compositor;
2. use the exact current head pose and four matching depth slices;
3. bound translation amplitude conservatively and sweep multiple amplitudes;
4. measure alpha holes/overdraw, edge/seam/halo energy and face/eye registration;
5. compare the exact same pose/eye/blink state against the current accepted live baseline;
6. benchmark render cost on the real host;
7. only after a winning scratch configuration exists, construct a reversible live candidate with exact hash gates and automatic rollback;
8. preserve the current atomic photo/eye roll-registration invariant and the established 60 FPS boundary.

## Credits after this gate

- Depth-slice generator lineage: **PASS**.
- Arithmetic alpha partition: **PASS**.
- Static slice RGB consistency: **PASS**.
- Naive CSS/source-over compositor: **REJECTED**.
- Scratch Canvas additive zero-offset reconstruction: **PASS**.
- Dynamic parallax visual-quality credit: **0 / OPEN**.
- Live parallax integration credit: **0**.
- Avatar whole-product credit: **unchanged**.
- GRID10 / semantic GWT / J-Space / effect / training credit: **unchanged**.
