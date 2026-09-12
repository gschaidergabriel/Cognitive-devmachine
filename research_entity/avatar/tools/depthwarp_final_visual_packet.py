#!/usr/bin/env python3
"""Build a provenance-bound final-size visual packet for the guarded depth warp.

Scope is deliberately narrow:
- read-only scratch rendering from the exact live-head/roll assets;
- baseline, A=1.00 and A=1.25 use the identical INTER_AREA final-size path;
- output alpha remains authoritative baseline alpha;
- eye-region displacement and image-detail metrics are measured;
- optional externally bound identity ROIs can add hair/nose/mouth/neck readbacks;
- diagnostic PNGs and every source/output SHA256 are emitted.

This tool DOES NOT claim perceptual improvement, execute production filmlook.js, mutate
the live avatar, or mint runtime/whole-avatar credit.  If no canonical identity ROI
file is supplied, the result is explicitly incomplete for non-eye identity regions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw

import depthwarp_display_space_gate as gate

SCHEMA = "DEPTHWARP_FINAL_VISUAL_PACKET/v1"
ROLLS = gate.ROLLS
DEFAULT_AMPS = (1.0, 1.25)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rgba_resize(arr: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.resize(arr, (width, height), interpolation=cv2.INTER_AREA)


def gray(arr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY).astype(np.float32)


def phase(a: np.ndarray, b: np.ndarray, rect: tuple[int, int, int, int]) -> dict[str, float]:
    x0, y0, x1, y1 = rect
    aa = a[y0:y1, x0:x1]
    bb = b[y0:y1, x0:x1]
    if min(aa.shape, default=0) < 10:
        return {"dx": 0.0, "dy": 0.0, "magnitude": 0.0, "response": 0.0}
    (dx, dy), response = cv2.phaseCorrelate(aa, bb)
    return {
        "dx": float(dx),
        "dy": float(dy),
        "magnitude": float(math.hypot(dx, dy)),
        "response": float(response),
    }


def rect_clip(rect: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    if len(rect) != 4:
        raise ValueError("ROI rect must have four numbers")
    x0, y0, x1, y1 = [int(round(float(v))) for v in rect]
    x0, x1 = sorted((max(0, min(width, x0)), max(0, min(width, x1))))
    y0, y1 = sorted((max(0, min(height, y0)), max(0, min(height, y1))))
    if x1 - x0 < 10 or y1 - y0 < 10:
        raise ValueError(f"ROI too small after clipping: {rect}")
    return x0, y0, x1, y1


def roi_metrics(base: np.ndarray, candidate: np.ndarray, rect: tuple[int, int, int, int]) -> dict[str, Any]:
    x0, y0, x1, y1 = rect
    a = base[y0:y1, x0:x1]
    b = candidate[y0:y1, x0:x1]
    diff = np.abs(a[:, :, :3].astype(np.float32) - b[:, :, :3].astype(np.float32))
    mx = diff.max(2)
    ga = gray(a)
    gb = gray(b)
    lap_a = np.abs(cv2.Laplacian(ga, cv2.CV_32F)).mean()
    lap_b = np.abs(cv2.Laplacian(gb, cv2.CV_32F)).mean()
    return {
        "rect": [x0, y0, x1, y1],
        "rgb_mae": float(diff.mean()),
        "rgb_p95": float(np.quantile(diff, 0.95)),
        "rgb_p99": float(np.quantile(diff, 0.99)),
        "changed_gt1_fraction": float((mx > 1).mean()),
        "gradient_energy_ratio": float((lap_b + 1e-9) / (lap_a + 1e-9)),
        "phase": phase(ga, gb, (0, 0, ga.shape[1], ga.shape[0])),
    }


def load_optional_rois(path: Path | None, width: int, height: int) -> tuple[dict[str, tuple[int, int, int, int]], dict[str, Any] | None]:
    if path is None:
        return {}, None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != "AVATAR_IDENTITY_ROIS/v1":
        raise ValueError("identity ROI file must use AVATAR_IDENTITY_ROIS/v1")
    if int(raw.get("display_width", -1)) != width or int(raw.get("display_height", -1)) != height:
        raise ValueError("identity ROI geometry does not match requested display size")
    regions = raw.get("regions")
    if not isinstance(regions, dict):
        raise ValueError("identity ROI regions must be an object")
    out: dict[str, tuple[int, int, int, int]] = {}
    for name, spec in regions.items():
        if not isinstance(spec, dict) or not isinstance(spec.get("rect"), list):
            raise ValueError(f"invalid ROI spec for {name!r}")
        out[str(name)] = rect_clip(spec["rect"], width, height)
    return out, raw


def diagnostic_grid(base: np.ndarray, variants: list[tuple[str, np.ndarray]], out: Path, rois: dict[str, tuple[int, int, int, int]]) -> None:
    images: list[tuple[str, np.ndarray]] = [("BASE", base)] + variants
    tiles: list[Image.Image] = []
    for label, arr in images:
        im = Image.fromarray(arr, "RGBA").convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, min(210, im.width - 1), 26), fill=(0, 0, 0))
        d.text((6, 6), label, fill=(255, 255, 255))
        for name, (x0, y0, x1, y1) in rois.items():
            d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 255, 255), width=1)
            d.text((x0 + 2, y0 + 2), name, fill=(255, 255, 255))
        tiles.append(im)
    canvas = Image.new("RGB", (base.shape[1] * len(tiles), base.shape[0]))
    for i, tile in enumerate(tiles):
        canvas.paste(tile, (i * base.shape[1], 0))
    canvas.save(out, optimize=True)


def heatmap(base: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    d = np.abs(candidate[:, :, :3].astype(np.int16) - base[:, :, :3].astype(np.int16)).max(2).astype(np.uint8)
    scaled = np.clip(d.astype(np.uint16) * 4, 0, 255).astype(np.uint8)
    return np.dstack([scaled, scaled, scaled, np.full_like(scaled, 255)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=620)
    ap.add_argument("--height", type=int, default=414)
    ap.add_argument("--roll", default="+00", choices=ROLLS)
    ap.add_argument("--identity-rois", default=None, help="Optional bound AVATAR_IDENTITY_ROIS/v1 JSON")
    args = ap.parse_args()

    root = Path(args.visual_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    anchors_path = root / "rig2/augen_anker_exakt.json"
    anchors = json.loads(anchors_path.read_text(encoding="utf-8"))
    a0 = np.array([anchors["augen_anker_roll0"]["x"], anchors["augen_anker_roll0"]["y"]], float)
    off = anchors["werte"][str(int(args.roll))]
    eye_src = a0 + np.array([off["dx_px"], off["dy_px"]], float)
    sx = args.width / 1536.0
    sy = args.height / 1024.0
    eye_display = (float(eye_src[0] * sx), float(eye_src[1] * sy))
    # Match depthwarp_display_space_gate.phase() exactly: 48x32 DISPLAY pixels.
    eye_rect = rect_clip([
        eye_display[0] - 48.0,
        eye_display[1] - 32.0,
        eye_display[0] + 48.0,
        eye_display[1] + 32.0,
    ], args.width, args.height)

    rois, roi_raw = load_optional_rois(Path(args.identity_rois).resolve() if args.identity_rois else None, args.width, args.height)
    all_rois = {"eyes_exact_anchor": eye_rect, **rois}

    base_src_path = root / f"kopf_rgba/roll/gier_+00_nick_+00_roll_{args.roll}.png"
    base_src, _, _, _ = gate.build(root, args.roll, tuple(eye_src), DEFAULT_AMPS[0])
    baseline = rgba_resize(base_src, args.width, args.height)
    base_path = out / "baseline.png"
    Image.fromarray(baseline, "RGBA").save(base_path, optimize=True)

    variants: list[tuple[str, np.ndarray]] = []
    amp_records: dict[str, Any] = {}
    output_files: list[Path] = [base_path]
    g0 = gray(baseline)
    opaque = baseline[:, :, 3] >= 245

    for amp in DEFAULT_AMPS:
        _, warped_src, active_src, dx_src = gate.build(root, args.roll, tuple(eye_src), amp)
        warped = rgba_resize(warped_src, args.width, args.height)
        active = cv2.resize(active_src.astype(np.float32), (args.width, args.height), interpolation=cv2.INTER_AREA) > 0.05
        dx = cv2.resize(dx_src.astype(np.float32), (args.width, args.height), interpolation=cv2.INTER_AREA)
        p = out / f"warp_A{amp:.2f}.png"
        Image.fromarray(warped, "RGBA").save(p, optimize=True)
        hp = out / f"diff_A{amp:.2f}.png"
        Image.fromarray(heatmap(baseline, warped), "RGBA").save(hp, optimize=True)
        output_files.extend([p, hp])
        variants.append((f"A={amp:.2f}", warped))

        diff = np.abs(warped[:, :, :3].astype(np.float32) - baseline[:, :, :3].astype(np.float32))
        mx = diff.max(2)
        g1 = gray(warped)
        lap0 = float(np.abs(cv2.Laplacian(g0, cv2.CV_32F))[opaque].mean()) if opaque.any() else 0.0
        lap1 = float(np.abs(cv2.Laplacian(g1, cv2.CV_32F))[opaque].mean()) if opaque.any() else 0.0
        amp_records[f"{amp:.2f}"] = {
            "alpha_exact": bool(np.array_equal(baseline[:, :, 3], warped[:, :, 3])),
            "active_fraction": float(active.mean()),
            "changed_gt1_active": float((mx[active] > 1).mean()) if active.any() else 0.0,
            "changed_gt3_active": float((mx[active] > 3).mean()) if active.any() else 0.0,
            "rgb_mae_active": float(diff[active].mean()) if active.any() else 0.0,
            "rgb_p99_active": float(np.quantile(diff[active], 0.99)) if active.any() else 0.0,
            "opaque_gradient_energy_ratio": float((lap1 + 1e-9) / (lap0 + 1e-9)),
            "max_abs_shift_display_px": float(np.max(np.abs(dx)) * sx),
            "p95_abs_shift_display_px": float(np.quantile(np.abs(dx[active]), 0.95) * sx) if active.any() else 0.0,
            "regions": {name: roi_metrics(baseline, warped, rect) for name, rect in all_rois.items()},
        }

    grid = out / "matched_visual_grid.png"
    diagnostic_grid(baseline, variants, grid, all_rois)
    output_files.append(grid)

    source_paths = [base_src_path, anchors_path]
    slice_dir = root / f"kopf_rgba_parallax/gier_+00_nick_+00_roll_{args.roll}"
    for i in range(4):
        matches = sorted(slice_dir.glob(f"slice_{i}_*.png"))
        if len(matches) != 1:
            raise SystemExit(f"expected exactly one slice_{i}_*.png, got {len(matches)}")
        source_paths.append(matches[0])
    if args.identity_rois:
        source_paths.append(Path(args.identity_rois).resolve())

    mandatory_identity_regions = {"hair", "nose", "mouth", "neck"}
    bound_names = {str(x).lower() for x in rois}
    missing_identity = sorted(mandatory_identity_regions - bound_names)
    identity_complete = not missing_identity

    receipt = {
        "schema": SCHEMA,
        "scope": "FINAL_SIZE_STATIC_VISUAL_PACKET_ONLY",
        "visual_root": str(root),
        "roll": args.roll,
        "display_size": [args.width, args.height],
        "amplitudes": list(DEFAULT_AMPS),
        "source_hashes": {str(p): sha256_file(p) for p in source_paths},
        "output_hashes": {p.name: sha256_file(p) for p in output_files},
        "eye_anchor_source_px": [float(eye_src[0]), float(eye_src[1])],
        "eye_anchor_display_px": list(eye_display),
        "eye_phase_crop_half_extent_display_px": [48, 32],
        "amp_metrics": amp_records,
        "identity_roi_file_bound": bool(roi_raw is not None),
        "identity_roi_missing_required_regions": missing_identity,
        "identity_roi_complete": identity_complete,
        "production_filmlook_applied": False,
        "production_filmlook_credit": 0,
        "perceptual_lifelikeness_credit": 0,
        "live_avatar_mutation": 0,
        "production_runtime_credit": 0,
        "whole_avatar_credit": 0,
        "status": "READY_FOR_BOUND_VISUAL_REVIEW" if identity_complete else "INCOMPLETE_IDENTITY_ROIS",
        "next_exact_gate": "Bind canonical hair/nose/mouth/neck ROIs or masks from the real live visual subject, then obtain matched final-presentation baseline/A1.00/A1.25 readback; production filmlook must be exercised through the actual browser path rather than emulated here.",
    }
    receipt_path = out / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
