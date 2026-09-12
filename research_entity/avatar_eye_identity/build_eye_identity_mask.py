#!/usr/bin/env python3
"""Build the review-only canonical eye mask from exact live avatar assets.

This script does not patch buehne.html and does not write into the live visual tree.
It fails closed unless the exact admitted source assets match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

EXPECTED = {
    "blink_000.png": "f7c0abd552a91e117f90880bc67c29f22311f1ed5b90a043b169e93495fff44f",
    "blink_006.png": "f7cc3fc538478c9a0f5748f2139a8bba7234f74aa59b634dc3f266caa237d0fa",
    "rotglow_tracking_master.png": "e9222dde99c5bf84adf838cde2c23284ed1d7b4a5d05c24fe48954871cf64ced",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            pts: list[tuple[int, int]] = []
            while stack:
                yy, xx = stack.pop()
                pts.append((yy, xx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if not (dx or dy):
                            continue
                        ny, nx = yy + dy, xx + dx
                        if (
                            0 <= ny < h
                            and 0 <= nx < w
                            and mask[ny, nx]
                            and not seen[ny, nx]
                        ):
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            out.append(pts)
    return sorted(out, key=len, reverse=True)


def build(root: Path, out: Path) -> dict:
    blink_dir = root / "augen_blink"
    gaze_dir = root / "augen_gaze"
    p0 = blink_dir / "blink_000.png"
    p6 = blink_dir / "blink_006.png"
    pg = gaze_dir / "rotglow_tracking_master.png"

    for p in (p0, p6, pg):
        expected = EXPECTED[p.name]
        actual = sha256(p)
        if actual != expected:
            raise SystemExit(f"subject mismatch: {p}: {actual} != {expected}")

    open_img = rgba(p0)
    closed_img = rgba(p6)
    glow_alpha = rgba(pg)[:, :, 3] > 0

    diff = np.max(
        np.abs(open_img[:, :, :3].astype(np.int16) - closed_img[:, :, :3].astype(np.int16)),
        axis=2,
    )

    gy, gx = np.where(glow_alpha)
    focus = np.zeros_like(glow_alpha, dtype=bool)
    x0 = max(0, int(gx.min()) - 35)
    y0 = max(0, int(gy.min()) - 35)
    x1 = min(diff.shape[1], int(gx.max()) + 1 + 35)
    y1 = min(diff.shape[0], int(gy.max()) + 1 + 35)
    focus[y0:y1, x0:x1] = True

    threshold = (diff >= 70) & focus
    closed = np.asarray(
        Image.fromarray((threshold * 255).astype("uint8"))
        .filter(ImageFilter.MaxFilter(5))
        .filter(ImageFilter.MinFilter(5))
    ) > 0

    comps = components(closed)
    if len(comps) < 2:
        raise SystemExit("eye component extraction failed: fewer than two components")

    base = np.zeros_like(closed, dtype=bool)
    for pts in comps[:2]:
        for y, x in pts:
            base[y, x] = True
    base |= glow_alpha

    hard = np.asarray(
        Image.fromarray((base * 255).astype("uint8")).filter(ImageFilter.MaxFilter(13))
    )
    feather = np.asarray(Image.fromarray(hard).filter(ImageFilter.GaussianBlur(4.0)))
    mask = np.maximum(hard, feather).astype(np.uint8)

    out.mkdir(parents=True, exist_ok=True)
    blink_out = out / "blink"
    blink_out.mkdir(parents=True, exist_ok=True)

    mask_path = out / "eye_identity_mask.png"
    Image.fromarray(mask, "L").save(mask_path)

    generated = []
    for src in sorted(blink_dir.glob("blink_*.png")):
        im = rgba(src).copy()
        if im.shape[:2] != mask.shape:
            raise SystemExit(f"geometry mismatch: {src} -> {im.shape[:2]} vs {mask.shape}")
        im[:, :, 3] = (
            im[:, :, 3].astype(np.uint16) * mask.astype(np.uint16) // 255
        ).astype(np.uint8)
        dst = blink_out / src.name
        Image.fromarray(im, "RGBA").save(dst)
        generated.append({"name": dst.name, "sha256": sha256(dst)})

    open_out = out / "eye_identity_open.png"
    open_out.write_bytes((blink_out / "blink_000.png").read_bytes())

    ys, xs = np.where(mask > 0)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    manifest = {
        "schema": "GO_AVATAR_EYE_IDENTITY_SHADOW/v1",
        "source": {k: v for k, v in EXPECTED.items()},
        "algorithm": {
            "rgb_delta_threshold": 70,
            "glow_focus_expansion_px": 35,
            "morphological_close_px": 5,
            "retained_components": 2,
            "hard_dilation_radius_px": 6,
            "gaussian_feather_radius_px": 4.0,
        },
        "component_sizes": [len(c) for c in comps[:2]],
        "mask_bbox": bbox,
        "mask_nonzero_pixels": int((mask > 0).sum()),
        "mask_a128_pixels": int((mask >= 128).sum()),
        "mask_a240_pixels": int((mask >= 240).sum()),
        "mask_sha256": sha256(mask_path),
        "open_sha256": sha256(open_out),
        "blink_assets": generated,
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_sha256"] = sha256(manifest_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="Exact live visual root (read-only input)")
    parser.add_argument("--out", type=Path, required=True, help="Shadow output directory")
    args = parser.parse_args()
    manifest = build(args.root.resolve(), args.out.resolve())
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
