#!/usr/bin/env python3
"""Read-only Gate-0 verifier for FranKenstein Avatar parallax assets.

Scope: component metrology only. This script never mutates production files and never
claims visual/product acceptance. It answers one narrow question: do the experimental
parallax slices preserve the canonical roll-pose pixels closely enough to justify a
later isolated renderer experiment?

Expected families under --visual-root:
  kopf_rgba/roll/<pose>.png
  kopf_rgba_parallax/<pose>/slice_0_front_nase.png ... slice_3_hinten_haar.png

Exit codes:
  0 = all discovered poses satisfy the selected gate
  2 = scientific/component gate failed
  3 = evidence invalid / missing input / malformed asset
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageStat

POSE_PREFIX = "gier_"
EXPECTED_SIZE = (1536, 1024)
EXPECTED_LAYER_COUNT = 4


@dataclass
class PoseResult:
    pose: str
    source: str
    source_sha256: str
    layer_sha256: list[str]
    canvas_ok: bool
    rgba_ok: bool
    layer_count_ok: bool
    best_order: list[int]
    exact_reconstruction: bool
    max_channel_delta: int
    mean_rgba_delta: float
    changed_bbox: tuple[int, int, int, int] | None
    changed_pixel_fraction: float
    overlap_pixel_fraction: float
    uncovered_source_alpha_fraction: float
    alpha_support_extra_fraction: float
    gate_pass: bool
    invalid_reason: str | None = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def nonzero_count(img: Image.Image) -> int:
    # histogram avoids numpy dependency and counts nonzero pixels deterministically.
    h = img.histogram()
    return sum(h[1:])


def alpha_binary(img: Image.Image) -> Image.Image:
    return img.getchannel("A").point(lambda x: 255 if x else 0, mode="L")


def composite(order: Iterable[int], layers: list[Image.Image]) -> Image.Image:
    out = Image.new("RGBA", layers[0].size, (0, 0, 0, 0))
    # alpha_composite places the second image over the first. The order therefore
    # explicitly represents back -> front.
    for idx in order:
        out = Image.alpha_composite(out, layers[idx])
    return out


def diff_metrics(candidate: Image.Image, source: Image.Image) -> tuple[int, float, tuple[int, int, int, int] | None, float]:
    diff = ImageChops.difference(candidate, source)
    extrema = diff.getextrema()
    max_delta = max(ch_max for _ch_min, ch_max in extrema)
    mean_delta = sum(ImageStat.Stat(diff).mean) / 4.0
    bbox = diff.getbbox()
    # A pixel is changed if any RGBA channel differs.
    changed_mask = diff.convert("RGBA").split()[0].point(lambda _x: 0)
    bands = diff.split()
    any_changed = bands[0].point(lambda x: 255 if x else 0)
    for band in bands[1:]:
        any_changed = ImageChops.lighter(any_changed, band.point(lambda x: 255 if x else 0))
    changed_fraction = nonzero_count(any_changed) / float(source.width * source.height)
    return max_delta, mean_delta, bbox, changed_fraction


def support_metrics(layers: list[Image.Image], source: Image.Image) -> tuple[float, float, float]:
    width, height = source.size
    n = width * height
    source_support = alpha_binary(source)
    supports = [alpha_binary(layer) for layer in layers]

    union = Image.new("L", source.size, 0)
    for support in supports:
        union = ImageChops.lighter(union, support)

    missing = ImageChops.subtract(source_support, union)
    extra = ImageChops.subtract(union, source_support)

    # Count pixels where two or more slice supports overlap. Use Python over binary
    # byte buffers: deterministic and still small enough for 1536x1024 x 4 x 11.
    raw = [s.tobytes() for s in supports]
    overlap = 0
    for vals in zip(*raw):
        if sum(v != 0 for v in vals) > 1:
            overlap += 1

    return (
        overlap / float(n),
        nonzero_count(missing) / float(n),
        nonzero_count(extra) / float(n),
    )


def verify_pose(pose_dir: Path, source_dir: Path, mae_limit: float, changed_fraction_limit: float) -> PoseResult:
    pose = pose_dir.name
    source_path = source_dir / f"{pose}.png"
    layer_paths = sorted(pose_dir.glob("slice_*.png"))

    if not source_path.exists():
        return PoseResult(pose, str(source_path), "", [], False, False, False, [], False, 255, math.inf, None, 1.0, 1.0, 1.0, 1.0, False, "source_missing")
    if len(layer_paths) != EXPECTED_LAYER_COUNT:
        return PoseResult(pose, str(source_path), sha256(source_path), [sha256(p) for p in layer_paths], False, False, False, [], False, 255, math.inf, None, 1.0, 1.0, 1.0, 1.0, False, f"expected_{EXPECTED_LAYER_COUNT}_layers_got_{len(layer_paths)}")

    source = Image.open(source_path).convert("RGBA")
    layers_raw = [Image.open(p) for p in layer_paths]
    rgba_ok = all(im.mode == "RGBA" for im in layers_raw)
    layers = [im.convert("RGBA") for im in layers_raw]
    canvas_ok = source.size == EXPECTED_SIZE and all(im.size == source.size for im in layers)
    if not canvas_ok:
        return PoseResult(pose, str(source_path), sha256(source_path), [sha256(p) for p in layer_paths], False, rgba_ok, True, [], False, 255, math.inf, None, 1.0, 1.0, 1.0, 1.0, False, "canvas_mismatch")

    overlap, missing, extra = support_metrics(layers, source)

    # With only four layers, evaluate all 24 back->front orders. This prevents a
    # guessed naming convention from creating a false negative.
    best = None
    for order in itertools.permutations(range(EXPECTED_LAYER_COUNT)):
        candidate = composite(order, layers)
        metrics = diff_metrics(candidate, source)
        score = (metrics[1], metrics[0], metrics[3], order)
        if best is None or score < best[0]:
            best = (score, order, metrics)

    assert best is not None
    _score, order, (max_delta, mean_delta, bbox, changed_fraction) = best
    exact = bbox is None

    # Gate-0 is deliberately strict but supports a bounded approximate path for
    # anti-aliased layer boundaries. Provenance remains a separate requirement.
    gate_pass = (
        rgba_ok
        and mean_delta <= mae_limit
        and changed_fraction <= changed_fraction_limit
        and missing == 0.0
        and extra == 0.0
    )

    return PoseResult(
        pose=pose,
        source=str(source_path),
        source_sha256=sha256(source_path),
        layer_sha256=[sha256(p) for p in layer_paths],
        canvas_ok=canvas_ok,
        rgba_ok=rgba_ok,
        layer_count_ok=True,
        best_order=list(order),
        exact_reconstruction=exact,
        max_channel_delta=max_delta,
        mean_rgba_delta=mean_delta,
        changed_bbox=bbox,
        changed_pixel_fraction=changed_fraction,
        overlap_pixel_fraction=overlap,
        uncovered_source_alpha_fraction=missing,
        alpha_support_extra_fraction=extra,
        gate_pass=gate_pass,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, default=Path("/home/ai-core-node/.claude/star/visual"))
    ap.add_argument("--mae-limit", type=float, default=0.50, help="max mean absolute RGBA delta")
    ap.add_argument("--changed-fraction-limit", type=float, default=0.005, help="max fraction of pixels with any channel delta")
    ap.add_argument("--json-out", type=Path, default=None, help="optional output path; stdout is always emitted")
    args = ap.parse_args()

    parallax_root = args.visual_root / "kopf_rgba_parallax"
    source_root = args.visual_root / "kopf_rgba" / "roll"
    if not parallax_root.is_dir() or not source_root.is_dir():
        print(json.dumps({"schema": "AVATAR_PARALLAX_GATE0/v1", "status": "EVIDENCE_INVALID", "reason": "required_directory_missing", "parallax_root": str(parallax_root), "source_root": str(source_root)}, indent=2))
        return 3

    pose_dirs = sorted(p for p in parallax_root.iterdir() if p.is_dir() and p.name.startswith(POSE_PREFIX))
    if not pose_dirs:
        print(json.dumps({"schema": "AVATAR_PARALLAX_GATE0/v1", "status": "EVIDENCE_INVALID", "reason": "no_pose_directories"}, indent=2))
        return 3

    results = [verify_pose(p, source_root, args.mae_limit, args.changed_fraction_limit) for p in pose_dirs]
    invalid = [r for r in results if r.invalid_reason]
    passed = not invalid and all(r.gate_pass for r in results)
    report = {
        "schema": "AVATAR_PARALLAX_GATE0/v1",
        "scope": "READ_ONLY_COMPONENT_METROLOGY_NOT_PRODUCTION_ACCEPTANCE",
        "visual_root": str(args.visual_root),
        "pose_count": len(results),
        "mae_limit": args.mae_limit,
        "changed_fraction_limit": args.changed_fraction_limit,
        "status": "PASS" if passed else ("EVIDENCE_INVALID" if invalid else "FAIL"),
        "exact_pose_count": sum(r.exact_reconstruction for r in results),
        "gate_pass_pose_count": sum(r.gate_pass for r in results),
        "max_mean_rgba_delta": max((r.mean_rgba_delta for r in results), default=math.inf),
        "max_changed_pixel_fraction": max((r.changed_pixel_fraction for r in results), default=1.0),
        "max_overlap_pixel_fraction": max((r.overlap_pixel_fraction for r in results), default=1.0),
        "results": [asdict(r) for r in results],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out is not None:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    if invalid:
        return 3
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
