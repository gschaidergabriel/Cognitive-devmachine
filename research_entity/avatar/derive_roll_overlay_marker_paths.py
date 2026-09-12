#!/usr/bin/env python3
"""Derive exact roll-generator marker paths for arbitrary overlay anchors.

This is a read-only measurement tool. It reproduces the actual head-roll generator
geometry described by the live rig tooling:
  alpha bbox crop -> PIL rotate(angle=-roll, BICUBIC, expand=True)
  -> bottom-center repin to fixed neck anchor (768,600).

It reports both the legacy bbox-edge center convention used by
messen_augenanker_exakt.py and the integer-pixel-center convention so the historic
+0.5px zero-state artifact is explicit rather than hidden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

CANVAS = (1536, 1024)
NECK = (768, 600)
ROLLS = tuple(range(-25, 26, 5))
DEFAULT_ANCHORS = {"eye": (610, 207), "mouth": (622, 352)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_head_master(root: Path) -> Path:
    candidates = [
        root / "kopf/master/kopf_zero_mit_augen.png",
        root / "kopf_rgba/master/kopf_zero_mit_augen.png",
    ]
    hits = [p for p in candidates if p.is_file()]
    if len(hits) != 1:
        raise SystemExit(f"HEAD_MASTER_BINDING_COUNT={len(hits)} candidates={[str(x) for x in hits]}")
    return hits[0]


def transform_crop_about_anchor(canvas: Image.Image, head_bbox, angle: float, anchor=NECK) -> Image.Image:
    crop = canvas.crop(head_bbox)
    if angle:
        crop = crop.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    x = round(anchor[0] - crop.width / 2)
    y = round(anchor[1] - crop.height)
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(crop, (x, y))
    return out


def marker_canvas(anchor: tuple[int, int]) -> Image.Image:
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    ax, ay = anchor
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            out.putpixel((ax + dx, ay + dy), (255, 0, 0, 255))
    return out


def center_legacy(bbox) -> tuple[float, float]:
    # Historic script convention: right/bottom are exclusive, so this introduces
    # +0.5,+0.5 for an unrotated odd-sized marker. Kept for exact comparison.
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def center_pixel(bbox) -> tuple[float, float]:
    return ((bbox[0] + bbox[2] - 1) / 2.0, (bbox[1] + bbox[3] - 1) / 2.0)


def derive(head_bbox, name: str, anchor: tuple[int, int]) -> dict:
    marker = marker_canvas(anchor)
    vals = {}
    for roll in ROLLS:
        transformed = transform_crop_about_anchor(marker, head_bbox, angle=-roll, anchor=NECK)
        bbox = transformed.getchannel("A").getbbox()
        if bbox is None:
            raise SystemExit(f"MARKER_DISAPPEARED name={name} roll={roll}")
        lc = center_legacy(bbox)
        pc = center_pixel(bbox)
        vals[str(roll)] = {
            "legacy_center": [round(lc[0], 3), round(lc[1], 3)],
            "legacy_dxdy": [round(lc[0]-anchor[0], 3), round(lc[1]-anchor[1], 3)],
            "pixel_center": [round(pc[0], 3), round(pc[1], 3)],
            "pixel_dxdy": [round(pc[0]-anchor[0], 3), round(pc[1]-anchor[1], 3)],
            "alpha_bbox": list(bbox),
        }
    return {"name": name, "anchor": list(anchor), "values": vals}


def parse_anchor(raw: str) -> tuple[str, tuple[int, int]]:
    try:
        name, xs, ys = raw.split(":", 2)
        return name, (int(xs), int(ys))
    except Exception as exc:
        raise argparse.ArgumentTypeError("anchor must be NAME:X:Y") from exc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("visual_root", type=Path)
    ap.add_argument("--head-master", type=Path)
    ap.add_argument("--anchor", action="append", type=parse_anchor, default=[])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    root = args.visual_root.resolve()
    master = args.head_master.resolve() if args.head_master else discover_head_master(root)
    if not master.is_file():
        raise SystemExit(f"HEAD_MASTER_MISSING={master}")
    head = Image.open(master).convert("RGBA")
    if head.size != CANVAS:
        raise SystemExit(f"HEAD_MASTER_SIZE={head.size} expected={CANVAS}")
    bbox = head.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit("HEAD_ALPHA_EMPTY")

    anchors = dict(DEFAULT_ANCHORS)
    for name, point in args.anchor:
        anchors[name] = point
    payload = {
        "schema": "F2_AVATAR_ROLL_MARKER_GEOMETRY/v1",
        "visual_root": str(root),
        "head_master": str(master),
        "head_master_sha256": sha256(master),
        "head_bbox": list(bbox),
        "head_bbox_size": [bbox[2]-bbox[0], bbox[3]-bbox[1]],
        "neck_anchor": list(NECK),
        "rolls": list(ROLLS),
        "markers": [derive(bbox, name, anchor) for name, anchor in anchors.items()],
    }
    raw = json.dumps(payload, indent=2, sort_keys=True)
    print(raw)
    if args.json_out:
        args.json_out.write_text(raw + "\n", encoding="utf-8")
    print("SCOPE=READ_ONLY_GENERATOR_GEOMETRY_NO_LIVE_MUTATION")


if __name__ == "__main__":
    main()
