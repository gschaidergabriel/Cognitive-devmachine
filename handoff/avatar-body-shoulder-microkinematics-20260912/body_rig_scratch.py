#!/usr/bin/env python3
"""Scratch-only body/shoulder microkinematics discriminator.

This program does not modify buehne.html or any production asset.  It discovers
#koerper-schicht from the exact local HTML subject, derives a body alpha bbox,
then renders a tiny spatially-local deformation field for left shoulder, right
shoulder and upper chest.  The rendered frames are only diagnostic evidence for
selecting a future runtime implementation (e.g. a tiny WebGL mesh).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_body_src(html: str) -> str:
    m = re.search(r"<img[^>]+id=[\"']koerper-schicht[\"'][^>]*>", html, re.I)
    if not m:
        raise RuntimeError("#koerper-schicht img tag not found")
    sm = re.search(r"src=[\"']([^\"']+)", m.group(0), re.I)
    if not sm:
        raise RuntimeError("#koerper-schicht has no src")
    return sm.group(1)


def bbox_from_alpha(a: np.ndarray, threshold: int = 1) -> tuple[int, int, int, int]:
    ys, xs = np.where(a >= threshold)
    if not len(xs):
        raise RuntimeError("body alpha is empty")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def gaussian(x: np.ndarray, y: np.ndarray, cx: float, cy: float, sx: float, sy: float) -> np.ndarray:
    return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))


def kinematics(t: float) -> dict[str, float]:
    """Conservative deterministic first candidate; values are native-image px/deg."""
    breath = math.sin((2.0 * math.pi / 4.9) * t)
    micro = math.sin((2.0 * math.pi / 8.7) * t + 0.83)
    micro2 = math.sin((2.0 * math.pi / 11.3) * t + 2.14)
    # Do not mirror-lock the shoulders.  Common breathing dominates; asymmetry is tiny.
    return {
        "left_dy": -0.46 * breath + 0.12 * micro,
        "right_dy": -0.42 * breath + 0.09 * micro2,
        "left_rot_deg": 0.085 * micro + 0.025 * breath,
        "right_rot_deg": -0.070 * micro2 - 0.018 * breath,
        "chest_dy": -0.18 * breath,
    }


def displacement_field(shape: tuple[int, int], bbox: tuple[int, int, int, int], kin: dict[str, float]):
    h, w = shape
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    lcx, rcx = x0 + 0.27 * bw, x0 + 0.73 * bw
    scy = y0 + 0.19 * bh
    chest_cx, chest_cy = x0 + 0.50 * bw, y0 + 0.29 * bh

    wl = gaussian(xx, yy, lcx, scy, 0.19 * bw, 0.12 * bh)
    wr = gaussian(xx, yy, rcx, scy, 0.19 * bw, 0.12 * bh)
    wc = gaussian(xx, yy, chest_cx, chest_cy, 0.27 * bw, 0.16 * bh)

    # Suppress deformation below the upper torso so hips/lower body stay anchored.
    cutoff0 = y0 + 0.38 * bh
    cutoff1 = y0 + 0.62 * bh
    taper = np.ones_like(yy)
    mid = (yy > cutoff0) & (yy < cutoff1)
    taper[yy >= cutoff1] = 0.0
    taper[mid] = 0.5 + 0.5 * np.cos(math.pi * (yy[mid] - cutoff0) / (cutoff1 - cutoff0))
    wl *= taper
    wr *= taper
    wc *= taper

    lrad = math.radians(kin["left_rot_deg"])
    rrad = math.radians(kin["right_rot_deg"])
    # First-order local rotation around shoulder pivots, blended spatially.
    ldx = -lrad * (yy - scy)
    ldy = lrad * (xx - lcx)
    rdx = -rrad * (yy - scy)
    rdy = rrad * (xx - rcx)

    dx = wl * ldx + wr * rdx
    dy = (
        wl * (kin["left_dy"] + ldy)
        + wr * (kin["right_dy"] + rdy)
        + wc * kin["chest_dy"]
    )
    # Outside actual body support, field can be zeroed later by alpha support.
    return dx.astype(np.float32), dy.astype(np.float32), wl, wr, wc


def bilinear_rgba(src: np.ndarray, dx: np.ndarray, dy: np.ndarray) -> np.ndarray:
    """Inverse-map a tiny displacement field with bilinear interpolation."""
    h, w, _ = src.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sx = xx - dx
    sy = yy - dy
    x0 = np.floor(sx).astype(np.int32)
    y0 = np.floor(sy).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    fx = sx - x0
    fy = sy - y0

    valid = (x0 >= 0) & (y0 >= 0) & (x1 < w) & (y1 < h)
    x0c, x1c = np.clip(x0, 0, w - 1), np.clip(x1, 0, w - 1)
    y0c, y1c = np.clip(y0, 0, h - 1), np.clip(y1, 0, h - 1)

    a = src[y0c, x0c].astype(np.float32)
    b = src[y0c, x1c].astype(np.float32)
    c = src[y1c, x0c].astype(np.float32)
    d = src[y1c, x1c].astype(np.float32)
    wx0, wx1 = (1.0 - fx)[..., None], fx[..., None]
    wy0, wy1 = (1.0 - fy)[..., None], fy[..., None]
    out = (a * wx0 + b * wx1) * wy0 + (c * wx0 + d * wx1) * wy1
    out[~valid] = 0
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def edge_energy(gray: np.ndarray) -> float:
    gx = np.abs(np.diff(gray.astype(np.float32), axis=1)).mean()
    gy = np.abs(np.diff(gray.astype(np.float32), axis=0)).mean()
    return float(gx + gy)


def roi(arr: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    return arr[y0:y1, x0:x1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default=".")
    ap.add_argument("--out", default="/var/tmp/go_body_shoulder_scratch")
    ap.add_argument("--seconds", type=float, default=12.0)
    ap.add_argument("--fps", type=int, default=60)
    args = ap.parse_args()

    root = Path(args.visual_root).resolve()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    html_path = root / "buehne.html"
    html = html_path.read_text(errors="replace")
    body_src = discover_body_src(html)
    body_path = root / body_src.lstrip("/")
    if not body_path.exists():
        raise FileNotFoundError(body_path)

    im = Image.open(body_path).convert("RGBA")
    src = np.asarray(im, dtype=np.uint8)
    alpha = src[:, :, 3]
    bbox = bbox_from_alpha(alpha)
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    neck_box = (
        max(0, int(x0 + 0.34 * bw)),
        max(0, int(y0 + 0.00 * bh)),
        min(src.shape[1], int(x0 + 0.66 * bw)),
        min(src.shape[0], int(y0 + 0.22 * bh)),
    )

    # Temporal gate: validate every frame, render a sparse contact set.
    n = max(2, int(args.seconds * args.fps))
    traces = []
    max_step_px = 0.0
    max_step_deg = 0.0
    prev = None
    for i in range(n):
        t = i / args.fps
        k = kinematics(t)
        traces.append({"t": t, **k})
        if prev:
            max_step_px = max(max_step_px, abs(k["left_dy"] - prev["left_dy"]), abs(k["right_dy"] - prev["right_dy"]))
            max_step_deg = max(max_step_deg, abs(k["left_rot_deg"] - prev["left_rot_deg"]), abs(k["right_rot_deg"] - prev["right_rot_deg"]))
        prev = k

    sample_ts = [0.0, 1.225, 2.45, 3.675, 4.9, 7.35]
    frames = []
    metrics = []
    base_gray = np.asarray(im.convert("L"))
    base_neck_energy = edge_energy(roi(base_gray, neck_box))
    body_support = (alpha > 0).astype(np.float32)

    for j, t in enumerate(sample_ts):
        k = kinematics(t)
        dx, dy, wl, wr, wc = displacement_field(alpha.shape, bbox, k)
        # Avoid pulling transparent background into the body calculation far from support.
        support = np.maximum.reduce([body_support, np.roll(body_support, 1, 0), np.roll(body_support, -1, 0), np.roll(body_support, 1, 1), np.roll(body_support, -1, 1)])
        dx *= support
        dy *= support
        warped = bilinear_rgba(src, dx, dy)
        p = outdir / f"body_micro_{j:02d}_{t:.3f}s.png"
        Image.fromarray(warped, "RGBA").save(p)
        frames.append(p)
        g = np.asarray(Image.fromarray(warped, "RGBA").convert("L"))
        neck_e = edge_energy(roi(g, neck_box))
        diff = np.abs(warped.astype(np.int16) - src.astype(np.int16))
        metrics.append({
            "t": t,
            "kinematics": k,
            "max_abs_dx": float(np.max(np.abs(dx))),
            "max_abs_dy": float(np.max(np.abs(dy))),
            "rgba_mae": float(diff.mean()),
            "rgba_p99": float(np.percentile(diff, 99)),
            "neck_edge_energy": neck_e,
            "neck_edge_ratio_vs_base": neck_e / base_neck_energy if base_neck_energy else None,
            "path": str(p),
        })

    # Contact sheet on checkerboard, never production output.
    thumb_w = 420
    scale = thumb_w / im.width
    thumb_h = max(1, round(im.height * scale))
    checker = Image.new("RGB", (thumb_w * 3, thumb_h * 2), "#202020")
    dr = ImageDraw.Draw(checker)
    s = 20
    for yy in range(0, checker.height, s):
        for xx in range(0, checker.width, s):
            if ((xx // s) + (yy // s)) % 2:
                dr.rectangle((xx, yy, xx + s - 1, yy + s - 1), fill="#303030")
    for idx, p in enumerate(frames):
        tile = Image.open(p).convert("RGBA").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % 3) * thumb_w
        y = (idx // 3) * thumb_h
        checker.paste(tile, (x, y), tile)
    contact = outdir / "contact_sheet.jpg"
    checker.save(contact, quality=92)

    l = np.array([x["left_dy"] for x in traces])
    r = np.array([x["right_dy"] for x in traces])
    corr = float(np.corrcoef(l, r)[0, 1])
    report = {
        "schema": "FRANK_AVATAR_BODY_SHOULDER_SCRATCH/v1",
        "status": "SCRATCH_ONLY_NOT_LIVE",
        "html_sha256": sha256(html_path),
        "body_src": body_src,
        "body_sha256": sha256(body_path),
        "body_size": list(im.size),
        "alpha_bbox": list(bbox),
        "neck_box": list(neck_box),
        "temporal": {
            "seconds": args.seconds,
            "fps": args.fps,
            "samples": n,
            "max_frame_step_px": max_step_px,
            "max_frame_step_deg": max_step_deg,
            "left_right_vertical_corr": corr,
        },
        "frames": metrics,
        "contact_sheet": str(contact),
        "acceptance": {
            "temporal_step_px_le_0_35": max_step_px <= 0.35,
            "temporal_step_deg_le_0_12": max_step_deg <= 0.12,
            "not_mirror_locked": corr < 0.999,
        },
        "runtime_credit": 0,
        "live_mutation": False,
    }
    report_path = outdir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
