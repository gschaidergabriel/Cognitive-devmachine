#!/usr/bin/env python3
"""Fail-closed, read-only discriminator for FranKenstein roll/eye geometry.

This gate addresses a geometry question that is distinct from the already-fixed
photo/overlay timebase mismatch. The live eye overlays use CSS

    translate(measured_dx, measured_dy) rotate(roll)

with a transform origin mapped to the same neck pivot as the head.  The measured
KOPF_ROLL_AUGEN_OFFSET values are the *final marker displacement* produced by the
roll-image generator, not a pre-rotation CSS translation.  Therefore the CSS
rotation already contributes part of that displacement.  Feeding the complete
measured displacement into translate() double-counts the rigid rotation term.

The correct local translation is:

    residual = measured_generator_displacement - rigid_rotation_displacement

This tool verifies that statement against Chromium's own transform semantics. It
never writes the live Avatar and emits zero production credit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

SCHEMA = "FRANK_AVATAR_ROLL_EYE_RESIDUAL_GEOMETRY_GATE/v1"
# Same native 1536x1024 coordinate system documented by rig2 and live source.
EYE_MARKER = (610.0, 207.0)
NECK_ANCHOR = (768.0, 600.0)
EXPECTED_ROLLS = tuple(range(-25, 26, 5))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_offsets(text: str) -> dict[int, tuple[float, float]]:
    m = re.search(r"const\s+KOPF_ROLL_AUGEN_OFFSET\s*=\s*\{(?P<body>.*?)\n\s*\};", text, re.S)
    if not m:
        raise ValueError("KOPF_ROLL_AUGEN_OFFSET table not found")
    body = m.group("body")
    rows: dict[int, tuple[float, float]] = {}
    for angle, dx, dy in re.findall(
        r'["\'](-?\d+)["\']\s*:\s*\{\s*dx\s*:\s*(-?\d+(?:\.\d+)?)\s*,\s*dy\s*:\s*(-?\d+(?:\.\d+)?)\s*\}',
        body,
    ):
        rows[int(angle)] = (float(dx), float(dy))
    if tuple(sorted(rows)) != EXPECTED_ROLLS:
        raise ValueError(f"unexpected roll table keys: {sorted(rows)}")
    return rows


def analytic_rotation_displacement(deg: int) -> tuple[float, float]:
    x, y = EYE_MARKER
    nx, ny = NECK_ANCHOR
    a = math.radians(deg)
    vx, vy = x - nx, y - ny
    xr = math.cos(a) * vx - math.sin(a) * vy
    yr = math.sin(a) * vx + math.cos(a) * vy
    return (nx + xr - x, ny + yr - y)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", type=Path, required=True)
    ap.add_argument("--expected-sha256", default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    if not args.live.is_file():
        print(json.dumps({"schema": SCHEMA, "status": "EVIDENCE_INVALID", "reason": "live_source_missing"}))
        return 3

    source_sha = sha256(args.live)
    if args.expected_sha256 and source_sha != args.expected_sha256:
        print(json.dumps({"schema": SCHEMA, "status": "EVIDENCE_INVALID", "reason": "source_hash_mismatch", "actual_sha256": source_sha, "expected_sha256": args.expected_sha256}, indent=2))
        return 3

    text = args.live.read_text(encoding="utf-8")
    required_literals = (
        '$("augen-blink").style.transform =',
        'rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)',
        'kopfRollAusgleichDeg = kopfRollWert;',
        'transform-origin:70.38% 241.32%',
    )
    missing = [s for s in required_literals if s not in text]
    if missing:
        print(json.dumps({"schema": SCHEMA, "status": "EVIDENCE_INVALID", "reason": "live_semantics_not_bound", "missing": missing, "source_sha256": source_sha}, indent=2))
        return 3

    offsets = extract_offsets(text)
    x, y = EYE_MARKER
    nx, ny = NECK_ANCHOR
    ox, oy = nx - x, ny - y
    html = f"""<!doctype html><style>
html,body{{margin:0}}
#c{{position:relative;width:1536px;height:1024px}}
#m{{position:absolute;left:{x}px;top:{y}px;width:0;height:0;transform-origin:{ox}px {oy}px}}
</style><div id='c'><div id='m'></div></div>"""

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1100})
        page.set_content(html)

        def position(transform: str) -> tuple[float, float]:
            a = page.eval_on_selector(
                "#m",
                "(e,t)=>{e.style.transform=t;const r=e.getBoundingClientRect();return [r.left,r.top]}",
                transform,
            )
            return float(a[0]), float(a[1])

        base = position("none")
        for roll in EXPECTED_ROLLS:
            target_dx, target_dy = offsets[roll]
            rigid = position(f"rotate({roll}deg)")
            rigid_dx, rigid_dy = rigid[0] - base[0], rigid[1] - base[1]
            analytic_dx, analytic_dy = analytic_rotation_displacement(roll)
            browser_vs_analytic = math.hypot(rigid_dx - analytic_dx, rigid_dy - analytic_dy)

            current = position(f"translate({target_dx}px,{target_dy}px) rotate({roll}deg)")
            current_dx, current_dy = current[0] - base[0], current[1] - base[1]
            current_error = math.hypot(current_dx - target_dx, current_dy - target_dy)

            residual_dx = target_dx - rigid_dx
            residual_dy = target_dy - rigid_dy
            corrected = position(f"translate({residual_dx}px,{residual_dy}px) rotate({roll}deg)")
            corrected_dx, corrected_dy = corrected[0] - base[0], corrected[1] - base[1]
            corrected_error = math.hypot(corrected_dx - target_dx, corrected_dy - target_dy)

            rows.append({
                "roll_deg": roll,
                "generator_target_native_px": {"dx": target_dx, "dy": target_dy},
                "rigid_rotation_native_px": {"dx": rigid_dx, "dy": rigid_dy},
                "analytic_rotation_native_px": {"dx": analytic_dx, "dy": analytic_dy},
                "browser_vs_analytic_error_px": browser_vs_analytic,
                "current_effective_native_px": {"dx": current_dx, "dy": current_dy},
                "current_error_px": current_error,
                "residual_translation_native_px": {"dx": residual_dx, "dy": residual_dy},
                "corrected_effective_native_px": {"dx": corrected_dx, "dy": corrected_dy},
                "corrected_error_px": corrected_error,
            })
        browser.close()

    max_current = max(r["current_error_px"] for r in rows)
    max_corrected = max(r["corrected_error_px"] for r in rows)
    max_browser_math = max(r["browser_vs_analytic_error_px"] for r in rows)
    status = "PASS" if max_current > 1.0 and max_corrected < 0.001 and max_browser_math < 0.001 else "FAIL"
    report = {
        "schema": SCHEMA,
        "status": status,
        "scope": "READ_ONLY_SCRATCH_GEOMETRY_NO_PRODUCTION_CREDIT",
        "source": str(args.live),
        "source_sha256": source_sha,
        "eye_marker_native_px": EYE_MARKER,
        "neck_anchor_native_px": NECK_ANCHOR,
        "roll_count": len(rows),
        "max_current_error_px": max_current,
        "max_corrected_error_px": max_corrected,
        "max_browser_vs_analytic_error_px": max_browser_math,
        "candidate_rule": "translate = measured_generator_displacement - rigid_rotation_displacement",
        "rows": rows,
        "production_credit": 0,
    }
    out = json.dumps(report, indent=2, sort_keys=True)
    print(out)
    if args.json_out:
        args.json_out.write_text(out + "\n", encoding="utf-8")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
