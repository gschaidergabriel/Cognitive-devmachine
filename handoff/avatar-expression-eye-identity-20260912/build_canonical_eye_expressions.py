#!/usr/bin/env python3
"""Build special-expression frames whose eye identity is canonical.

Non-destructive: reads the live/source tree and writes a sibling candidate tree.
The output keeps every source-expression pixel outside the measured eye mask,
but replaces the eye core with the canonical neutral-head pixels, feathered at
the boundary. The canonical red gaze/blink overlays remain separate runtime
layers; this builder never paints a new red-eye signal.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops

CANVAS = (1536, 1024)
PATCH = (319, 152)
PATCH_LEFT_FRAC = 0.31
PATCH_TOP_FRAC = 0.12
PATCH_WIDTH_FRAC = 0.27

# Measured on the already validated blink-eye-local candidate
# (FRANK_AVATAR_LOCAL_INTEGRATION_CANDIDATE/v1, e8d09af9...).
MEASURED_EYE_BBOX_PATCH = (42, 50, 274, 118)
HARD_EXPAND_PATCH_PX = 14
SOFT_EXPAND_PATCH_PX = 24
FEATHER_CANVAS_PX = 12

EXPECTED_NEUTRAL_SHA256 = "489e928fd436253c087183a25b01d685d4ba138bc75bc1b3c4c70a415762f261"
EXPECTED_GLOW_SHA256 = "e9222dde99c5bf84adf838cde2c23284ed1d7b4a5d05c24fe48954871cf64ced"
EXPECTED_EXPRESSION_DIRS = 44
EXPECTED_FRAMES_PER_EXPRESSION = 7

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def expand(box, px):
    x0,y0,x1,y1 = box
    return (x0-px, y0-px, x1+px, y1+px)

def patch_box_to_canvas(box):
    scale = (CANVAS[0] * PATCH_WIDTH_FRAC) / PATCH[0]
    xoff = CANVAS[0] * PATCH_LEFT_FRAC
    yoff = CANVAS[1] * PATCH_TOP_FRAC
    x0,y0,x1,y1 = box
    out = (
        round(xoff + x0 * scale),
        round(yoff + y0 * scale),
        round(xoff + x1 * scale),
        round(yoff + y1 * scale),
    )
    return (
        max(0, out[0]), max(0, out[1]),
        min(CANVAS[0], out[2]), min(CANVAS[1], out[3])
    )

def make_mask() -> tuple[Image.Image, dict]:
    hard_box = patch_box_to_canvas(expand(MEASURED_EYE_BBOX_PATCH, HARD_EXPAND_PATCH_PX))
    soft_box = patch_box_to_canvas(expand(MEASURED_EYE_BBOX_PATCH, SOFT_EXPAND_PATCH_PX))
    hard = Image.new("L", CANVAS, 0)
    soft = Image.new("L", CANVAS, 0)
    from PIL import ImageDraw
    ImageDraw.Draw(hard).rectangle(hard_box, fill=255)
    ImageDraw.Draw(soft).rectangle(soft_box, fill=255)
    soft = soft.filter(ImageFilter.GaussianBlur(FEATHER_CANVAS_PX))
    mask = ImageChops.lighter(hard, soft)
    meta = {
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
    return mask, meta

def validate_frame_set(source_root: Path) -> list[Path]:
    dirs = []
    for frontal in sorted(source_root.glob("*/*/frontal")):
        files = sorted(frontal.glob("stufe_*.png"))
        names = [p.name for p in files]
        expected = [f"stufe_{i:02d}.png" for i in range(EXPECTED_FRAMES_PER_EXPRESSION)]
        if names != expected:
            raise SystemExit(f"FAIL frame set {frontal}: {names!r}")
        dirs.append(frontal)
    if len(dirs) != EXPECTED_EXPRESSION_DIRS:
        raise SystemExit(f"FAIL expression dir count: {len(dirs)} != {EXPECTED_EXPRESSION_DIRS}")
    return dirs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--allow-hash-drift", action="store_true",
                    help="diagnostic only; never use for promotion")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    outroot = args.output_root.resolve()
    source_root = visual / "ausdruck_erweitert"
    neutral_path = visual / "kopf_rgba" / "kopf_zero_ohne_rotes_augenglow.png"
    glow_path = visual / "augen_gaze" / "rotglow_tracking_master.png"

    for p in (source_root, neutral_path, glow_path):
        if not p.exists():
            raise SystemExit(f"FAIL missing {p}")

    neutral_sha = sha256(neutral_path)
    glow_sha = sha256(glow_path)
    if not args.allow_hash_drift:
        if neutral_sha != EXPECTED_NEUTRAL_SHA256:
            raise SystemExit(f"FAIL neutral hash drift {neutral_sha}")
        if glow_sha != EXPECTED_GLOW_SHA256:
            raise SystemExit(f"FAIL glow hash drift {glow_sha}")

    neutral = Image.open(neutral_path).convert("RGBA")
    glow = Image.open(glow_path).convert("RGBA")
    if neutral.size != CANVAS:
        raise SystemExit(f"FAIL neutral size {neutral.size}")
    if glow.size != PATCH:
        raise SystemExit(f"FAIL glow size {glow.size}")

    expression_dirs = validate_frame_set(source_root)
    mask, mask_meta = make_mask()
    outtree = outroot / "ausdruck_erweitert"
    if outtree.exists():
        raise SystemExit(f"FAIL output already exists: {outtree}")
    outtree.mkdir(parents=True)

    rows = []
    changed_outside = 0
    full_core_mismatches = 0
    outside_mask = mask.point(lambda v: 255 if v == 0 else 0)
    hard_core_mask = mask.point(lambda v: 255 if v == 255 else 0)

    for frontal in expression_dirs:
        rel_dir = frontal.relative_to(source_root)
        dst_dir = outtree / rel_dir
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(frontal.glob("stufe_*.png")):
            expr = Image.open(src).convert("RGBA")
            if expr.size != CANVAS:
                raise SystemExit(f"FAIL size {src}: {expr.size}")
            out = Image.composite(neutral, expr, mask)

            # Pixel invariants, checked without per-pixel Python loops.
            outside_probe = Image.composite(out, expr, outside_mask)
            if ImageChops.difference(outside_probe, expr).getbbox() is not None:
                changed_outside += 1
            core_probe = Image.composite(out, neutral, hard_core_mask)
            if ImageChops.difference(core_probe, neutral).getbbox() is not None:
                full_core_mismatches += 1
            if changed_outside or full_core_mismatches:
                raise SystemExit(
                    f"FAIL pixel invariant at {src}: outside={changed_outside} core={full_core_mismatches}"
                )

            dst = dst_dir / src.name
            out.save(dst, "PNG", optimize=True)
            rows.append({
                "relative_path": str(src.relative_to(source_root)),
                "source_sha256": sha256(src),
                "output_sha256": sha256(dst),
            })

    manifest = {
        "schema": "FRANK_AVATAR_CANONICAL_EYE_EXPRESSIONS/v1",
        "status": "CANDIDATE_NOT_LIVE",
        "source_root": str(source_root),
        "output_root": str(outtree),
        "neutral": {"path": str(neutral_path), "sha256": neutral_sha},
        "canonical_glow": {"path": str(glow_path), "sha256": glow_sha},
        "source_evidence": {
            "blink_candidate_commit": "e8d09af9b3fb3df9020ee3956111f3ba99a1ce5d",
            "measured_eye_bbox_patch": list(MEASURED_EYE_BBOX_PATCH),
        },
        "mask": mask_meta,
        "expression_dirs": len(expression_dirs),
        "frames": len(rows),
        "pixel_invariants": {
            "outside_mask_changed_frames": changed_outside,
            "hard_core_non_neutral_frames": full_core_mismatches,
        },
        "files": rows,
    }
    (outroot / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    mask.save(outroot / "canonical_eye_mask.png", "PNG")
    print(json.dumps({
        "ok": True,
        "frames": len(rows),
        "expression_dirs": len(expression_dirs),
        "manifest": str(outroot / "manifest.json"),
        "mask": str(outroot / "canonical_eye_mask.png"),
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
