#!/usr/bin/env python3
"""Build canonical-eye special expressions against an explicit runtime subject.

Unlike the original candidate, this builder never assumes base directory names.
The caller must bind the exact productive expression tree, neutral head, gaze
asset, and their expected digests. Any drift fails before output is created.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops, ImageDraw

CANVAS = (1536, 1024)
PATCH = (319, 152)
PATCH_LEFT_FRAC = 0.31
PATCH_TOP_FRAC = 0.12
PATCH_WIDTH_FRAC = 0.27
MEASURED_EYE_BBOX_PATCH = (42, 50, 274, 118)
HARD_EXPAND_PATCH_PX = 14
SOFT_EXPAND_PATCH_PX = 24
FEATHER_CANVAS_PX = 12
EXPECTED_EXPRESSION_DIRS = 44
EXPECTED_FRAMES_PER_EXPRESSION = 7


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_digest(source_root: Path) -> tuple[str, list[tuple[Path, str]]]:
    rows: list[tuple[Path, str]] = []
    h = hashlib.sha256()
    for path in sorted(source_root.glob("*/*/frontal/stufe_*.png")):
        rel = path.relative_to(source_root)
        digest = sha256(path)
        rows.append((rel, digest))
        h.update(rel.as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest(), rows


def expand(box: tuple[int, int, int, int], px: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return x0 - px, y0 - px, x1 + px, y1 + px


def patch_box_to_canvas(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    scale = (CANVAS[0] * PATCH_WIDTH_FRAC) / PATCH[0]
    xoff = CANVAS[0] * PATCH_LEFT_FRAC
    yoff = CANVAS[1] * PATCH_TOP_FRAC
    x0, y0, x1, y1 = box
    out = (
        round(xoff + x0 * scale),
        round(yoff + y0 * scale),
        round(xoff + x1 * scale),
        round(yoff + y1 * scale),
    )
    return max(0, out[0]), max(0, out[1]), min(CANVAS[0], out[2]), min(CANVAS[1], out[3])


def make_mask() -> tuple[Image.Image, dict]:
    hard_box = patch_box_to_canvas(expand(MEASURED_EYE_BBOX_PATCH, HARD_EXPAND_PATCH_PX))
    soft_box = patch_box_to_canvas(expand(MEASURED_EYE_BBOX_PATCH, SOFT_EXPAND_PATCH_PX))
    hard = Image.new("L", CANVAS, 0)
    soft = Image.new("L", CANVAS, 0)
    ImageDraw.Draw(hard).rectangle(hard_box, fill=255)
    ImageDraw.Draw(soft).rectangle(soft_box, fill=255)
    soft = soft.filter(ImageFilter.GaussianBlur(FEATHER_CANVAS_PX))
    mask = ImageChops.lighter(hard, soft)
    return mask, {
        "measured_eye_bbox_patch": list(MEASURED_EYE_BBOX_PATCH),
        "hard_expand_patch_px": HARD_EXPAND_PATCH_PX,
        "soft_expand_patch_px": SOFT_EXPAND_PATCH_PX,
        "feather_canvas_px": FEATHER_CANVAS_PX,
        "hard_box_canvas": list(hard_box),
        "soft_box_canvas": list(soft_box),
        "patch_geometry": {
            "source_size": list(PATCH),
            "left_fraction": PATCH_LEFT_FRAC,
            "top_fraction": PATCH_TOP_FRAC,
            "width_fraction": PATCH_WIDTH_FRAC,
        },
    }


def validate_frame_set(source_root: Path) -> list[Path]:
    dirs: list[Path] = []
    expected = [f"stufe_{i:02d}.png" for i in range(EXPECTED_FRAMES_PER_EXPRESSION)]
    for frontal in sorted(source_root.glob("*/*/frontal")):
        names = [p.name for p in sorted(frontal.glob("stufe_*.png"))]
        if names != expected:
            raise SystemExit(f"FAIL frame set {frontal}: {names!r}")
        dirs.append(frontal)
    if len(dirs) != EXPECTED_EXPRESSION_DIRS:
        raise SystemExit(f"FAIL expression dir count: {len(dirs)} != {EXPECTED_EXPRESSION_DIRS}")
    return dirs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expression-root", type=Path, required=True)
    ap.add_argument("--neutral-path", type=Path, required=True)
    ap.add_argument("--gaze-path", type=Path, required=True)
    ap.add_argument("--expected-expression-tree-digest", required=True)
    ap.add_argument("--expected-neutral-sha256", required=True)
    ap.add_argument("--expected-gaze-sha256", required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    args = ap.parse_args()

    source_root = args.expression_root.resolve()
    neutral_path = args.neutral_path.resolve()
    gaze_path = args.gaze_path.resolve()
    outroot = args.output_root.resolve()
    for p in (source_root, neutral_path, gaze_path):
        if not p.exists():
            raise SystemExit(f"FAIL missing {p}")
    if outroot.exists():
        raise SystemExit(f"FAIL output already exists: {outroot}")

    digest, source_rows = tree_digest(source_root)
    if digest != args.expected_expression_tree_digest:
        raise SystemExit(f"FAIL expression tree drift {digest}")
    neutral_sha = sha256(neutral_path)
    gaze_sha = sha256(gaze_path)
    if neutral_sha != args.expected_neutral_sha256:
        raise SystemExit(f"FAIL neutral hash drift {neutral_sha}")
    if gaze_sha != args.expected_gaze_sha256:
        raise SystemExit(f"FAIL gaze hash drift {gaze_sha}")

    expression_dirs = validate_frame_set(source_root)
    if len(source_rows) != EXPECTED_EXPRESSION_DIRS * EXPECTED_FRAMES_PER_EXPRESSION:
        raise SystemExit(f"FAIL frame count {len(source_rows)}")
    neutral = Image.open(neutral_path).convert("RGBA")
    gaze = Image.open(gaze_path).convert("RGBA")
    if neutral.size != CANVAS:
        raise SystemExit(f"FAIL neutral size {neutral.size}")
    if gaze.size != PATCH:
        raise SystemExit(f"FAIL gaze size {gaze.size}")

    mask, mask_meta = make_mask()
    outtree = outroot / "ausdruck_erweitert"
    outtree.mkdir(parents=True)
    outside_mask = mask.point(lambda v: 255 if v == 0 else 0)
    hard_core_mask = mask.point(lambda v: 255 if v == 255 else 0)
    rows = []

    for frontal in expression_dirs:
        rel_dir = frontal.relative_to(source_root)
        dst_dir = outtree / rel_dir
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(frontal.glob("stufe_*.png")):
            expr = Image.open(src).convert("RGBA")
            if expr.size != CANVAS:
                raise SystemExit(f"FAIL size {src}: {expr.size}")
            out = Image.composite(neutral, expr, mask)
            outside_probe = Image.composite(out, expr, outside_mask)
            if ImageChops.difference(outside_probe, expr).getbbox() is not None:
                raise SystemExit(f"FAIL outside-mask mutation {src}")
            core_probe = Image.composite(out, neutral, hard_core_mask)
            if ImageChops.difference(core_probe, neutral).getbbox() is not None:
                raise SystemExit(f"FAIL hard-core mismatch {src}")
            dst = dst_dir / src.name
            out.save(dst, "PNG", optimize=True)
            rows.append({
                "relative_path": str(src.relative_to(source_root)),
                "source_sha256": sha256(src),
                "output_sha256": sha256(dst),
            })

    manifest = {
        "schema": "FRANK_AVATAR_CANONICAL_EYE_EXPRESSIONS_RUNTIME_BOUND/v2",
        "status": "CANDIDATE_NOT_LIVE",
        "authority": {
            "expression_root": str(source_root),
            "expression_tree_digest_sha256": digest,
            "neutral_path": str(neutral_path),
            "neutral_sha256": neutral_sha,
            "gaze_path": str(gaze_path),
            "gaze_sha256": gaze_sha,
        },
        "mask": mask_meta,
        "expression_dirs": len(expression_dirs),
        "frames": len(rows),
        "pixel_invariants": {
            "outside_mask_changed_frames": 0,
            "hard_core_non_neutral_frames": 0,
        },
        "files": rows,
    }
    outroot.mkdir(parents=True, exist_ok=True)
    (outroot / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    mask.save(outroot / "canonical_eye_mask.png", "PNG")
    print(json.dumps({
        "ok": True,
        "frames": len(rows),
        "expression_dirs": len(expression_dirs),
        "expression_tree_digest_sha256": digest,
        "neutral_sha256": neutral_sha,
        "gaze_sha256": gaze_sha,
        "manifest": str(outroot / "manifest.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
