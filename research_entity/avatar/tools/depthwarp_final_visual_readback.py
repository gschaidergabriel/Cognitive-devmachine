#!/usr/bin/env python3
"""Matched final-display visual readback for the guarded single-texture depth warp.

Purpose
-------
Close the next *measurement* boundary after the isolated real-AMD 60 Hz gate:
render the exact live head baseline and A=1.00/A=1.25 candidates through the same
final-size resampling path, preserve source identity/provenance, emit inspectable
contact sheets, and quantify mechanical identity drift.

This tool intentionally does NOT auto-promote perceptual/lifelikeness quality.
It can prove bounded invariants (source hashes, alpha identity, eye-registration,
edge/detail preservation) and produce matched images for a separate perceptual
readback. Live-avatar mutation remains zero.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from depthwarp_display_space_gate import build, gray, lap, phase

ROLLS = ["-25", "-20", "-15", "-10", "-05", "+00", "+05", "+10", "+15", "+20", "+25"]
AMPS = [1.0, 1.25]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_manifest(root: Path) -> dict:
    paths = [
        root / "rig2/augen_anker_exakt.json",
        root / "kopf_rgba/roll/gier_+00_nick_+00_roll_+00.png",
    ]
    for r in ROLLS:
        paths.append(root / f"kopf_rgba/roll/gier_+00_nick_+00_roll_{r}.png")
        d = root / f"kopf_rgba_parallax/gier_+00_nick_+00_roll_{r}"
        paths.extend(sorted(d.glob("slice_*.png")))
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing source files: " + ", ".join(missing[:8]))
    return {str(p.relative_to(root)): sha256(p) for p in paths}


def composite_rgba(rgba: np.ndarray, background: int = 20) -> np.ndarray:
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    bg = np.full(rgba[:, :, :3].shape, background, np.float32)
    return np.clip(rgba[:, :, :3].astype(np.float32) * a + bg * (1.0 - a), 0, 255).astype(np.uint8)


def resize_rgba(rgba: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.resize(rgba, (width, height), interpolation=cv2.INTER_AREA)


def annotate(rgb: np.ndarray, label: str) -> Image.Image:
    im = Image.fromarray(rgb)
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, 126, 26), fill=(0, 0, 0))
    dr.text((7, 7), label, fill=(255, 255, 255))
    return im


def quantile(v: np.ndarray, q: float) -> float:
    return float(np.quantile(v, q)) if v.size else 0.0


def evaluate_pair(base_d: np.ndarray, cand_d: np.ndarray, eye_xy: tuple[float, float], active: np.ndarray) -> dict:
    diff = np.abs(cand_d[:, :, :3].astype(np.float32) - base_d[:, :, :3].astype(np.float32))
    mx = diff.max(2)
    opaque = base_d[:, :, 3] >= 245
    g0, g1 = gray(base_d), gray(cand_d)
    px, py, response = phase(g0, g1, eye_xy[0], eye_xy[1], rx=34, ry=23)
    eye_shift = math.hypot(px, py)
    alpha_exact = bool(np.array_equal(base_d[:, :, 3], cand_d[:, :, 3]))
    lap_ratio = (lap(g1, opaque) + 1e-9) / (lap(g0, opaque) + 1e-9)
    # A strict mechanical guard only. It does not decide whether the added depth looks better.
    mechanical_pass = bool(alpha_exact and eye_shift <= 0.20 and 0.97 <= lap_ratio <= 1.03)
    return {
        "alpha_exact": alpha_exact,
        "eye_shift_px": float(eye_shift),
        "eye_phase_response": float(response),
        "laplacian_detail_ratio": float(lap_ratio),
        "rgb_mae_active": float(diff[active].mean()) if active.any() else 0.0,
        "rgb_p95_active": quantile(diff[active], 0.95),
        "rgb_p99_active": quantile(diff[active], 0.99),
        "changed_gt1_active_frac": float((mx[active] > 1).mean()) if active.any() else 0.0,
        "changed_gt3_active_frac": float((mx[active] > 3).mean()) if active.any() else 0.0,
        "mechanical_identity_guard_pass": mechanical_pass,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--out-dir", default="/tmp/depthwarp-final-readback")
    ap.add_argument("--width", type=int, default=620)
    ap.add_argument("--height", type=int, default=414)
    ap.add_argument("--preview-roll", default="+00", choices=ROLLS)
    ap.add_argument("--emit-base64-preview", action="store_true")
    args = ap.parse_args()

    root = Path(args.visual_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    before = source_manifest(root)
    anchors = json.loads((root / "rig2/augen_anker_exakt.json").read_text())
    anchor0 = np.array([anchors["augen_anker_roll0"]["x"], anchors["augen_anker_roll0"]["y"]], float)
    sx, sy = args.width / 1536.0, args.height / 1024.0

    results: dict[str, dict] = {}
    all_rows: list[Image.Image] = []
    preview: Image.Image | None = None

    for r in ROLLS:
        off = anchors["werte"][str(int(r))]
        eye_src = tuple(anchor0 + np.array([off["dx_px"], off["dy_px"]]))
        eye_display = (eye_src[0] * sx, eye_src[1] * sy)
        base = np.array(Image.open(root / f"kopf_rgba/roll/gier_+00_nick_+00_roll_{r}.png").convert("RGBA"), np.uint8)
        base_d = resize_rgba(base, args.width, args.height)
        panels = [annotate(composite_rgba(base_d), f"ROLL {r} BASE")]
        rr: dict[str, dict] = {}

        for amp in AMPS:
            _, warped, gate, dx = build(root, r, eye_src, amp)
            cand_d = resize_rgba(warped, args.width, args.height)
            gate_d = cv2.resize(gate.astype(np.float32), (args.width, args.height), interpolation=cv2.INTER_AREA)
            active = gate_d > 0.05
            m = evaluate_pair(base_d, cand_d, eye_display, active)
            dx_d = cv2.resize(dx.astype(np.float32), (args.width, args.height), interpolation=cv2.INTER_AREA)
            m["max_abs_displacement_display_px"] = float(np.max(np.abs(dx_d)) * sx)
            m["p95_abs_displacement_display_px"] = float(np.quantile(np.abs(dx_d[active]), 0.95) * sx) if active.any() else 0.0
            rr[f"A{amp:.2f}"] = m
            panels.append(annotate(composite_rgba(cand_d), f"ROLL {r} A{amp:.2f}"))

        row = Image.new("RGB", (args.width * len(panels), args.height))
        for i, panel in enumerate(panels):
            row.paste(panel, (i * args.width, 0))
        row_path = out / f"roll_{r}_base_A100_A125.png"
        row.save(row_path, optimize=True)
        if r == args.preview_roll:
            preview = row.copy()
        all_rows.append(row)
        results[r] = rr

    sheet = Image.new("RGB", (args.width * 3, args.height * len(all_rows)))
    for i, row in enumerate(all_rows):
        sheet.paste(row, (0, i * args.height))
    sheet_path = out / "all_rolls_base_A100_A125.png"
    sheet.save(sheet_path, optimize=True)

    after = source_manifest(root)
    source_unchanged = before == after
    if not source_unchanged:
        raise RuntimeError("source manifest changed during readback")

    summary = {
        "schema": "DEPTHWARP_FINAL_VISUAL_READBACK/v1",
        "scope": "SCRATCH_FINAL_DISPLAY_READBACK_NO_LIVE_MUTATION",
        "visual_root": str(root),
        "display_size": [args.width, args.height],
        "amplitudes": AMPS,
        "rolls": ROLLS,
        "source_manifest_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        "source_unchanged": source_unchanged,
        "all_mechanical_identity_guards_pass": all(
            x["mechanical_identity_guard_pass"] for rr in results.values() for x in rr.values()
        ),
        "perceptual_lifelikeness_verdict": "UNRESOLVED_REQUIRES_MATCHED_IMAGE_READBACK",
        "whole_avatar_live_credit": 0,
        "results": results,
        "artifacts": {
            "all_rolls_contact_sheet": str(sheet_path),
            "all_rolls_contact_sheet_sha256": sha256(sheet_path),
        },
    }
    report_path = out / "report.json"
    report_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))

    if args.emit_base64_preview:
        if preview is None:
            raise RuntimeError("preview roll not rendered")
        # Compact transport artifact for bridge receipts / remote visual inspection.
        compact = preview.resize((930, 207), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        compact.save(buf, "JPEG", quality=88, optimize=True)
        raw = buf.getvalue()
        print("PREVIEW_JPEG_SHA256", hashlib.sha256(raw).hexdigest())
        print("PREVIEW_JPEG_BYTES", len(raw))
        print("PREVIEW_JPEG_B64", base64.b64encode(raw).decode())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
