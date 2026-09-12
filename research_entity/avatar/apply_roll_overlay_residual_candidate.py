#!/usr/bin/env python3
"""Build a scratch candidate correcting roll-overlay translation semantics.

Fail-closed exact-subject patcher. It is NOT a production installer. The current
live table stores full generated eye-anchor displacement, while the live CSS also
rotates the overlay about the neck anchor. This candidate replaces only that table
with the translation residual required after the browser rotation.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
from pathlib import Path

EXPECTED_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EYE = (610.0, 207.0)
NECK = (768.0, 600.0)
FULL = {
    -25: (-32.5, 22.0), -20: (-30.0, 12.0), -15: (-24.0, 5.0),
    -10: (-16.5, 0.0), -5: (-9.5, -1.0), 0: (0.0, 0.0),
      5: (10.5, -29.0), 10: (22.0, -55.5), 15: (35.0, -77.5),
     20: (47.5, -97.0), 25: (62.5, -112.0),
}
TABLE_RE = re.compile(r"const KOPF_ROLL_AUGEN_OFFSET = \{.*?\n\};", re.S)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def css_rotation_displacement(deg: int) -> tuple[float, float]:
    """Movement of the neutral eye marker under CSS rotate(deg) about NECK.

    CSS works in a y-down coordinate space. Positive angles use the browser's
    clockwise visual convention represented by x'=c*x-s*y, y'=s*x+c*y.
    """
    x, y = EYE
    ox, oy = NECK
    dx, dy = x - ox, y - oy
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    xr = ox + c * dx - s * dy
    yr = oy + s * dx + c * dy
    return xr - x, yr - y


def residual_table() -> dict[int, tuple[float, float]]:
    out = {}
    for deg, (tx, ty) in FULL.items():
        rx, ry = css_rotation_displacement(deg)
        out[deg] = (tx - rx, ty - ry)
    return out


def js_num(x: float) -> str:
    if abs(x) < 0.0005:
        x = 0.0
    return f"{x:.3f}"


def replacement_block() -> str:
    r = residual_table()
    order = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]
    lines = [
        "const KOPF_ROLL_AUGEN_OFFSET = { // CSS-Translations-RESIDUAL nach rotate(roll), native 1536x1024 px",
    ]
    for i, deg in enumerate(order):
        dx, dy = r[deg]
        key = str(deg)
        suffix = "," if i < len(order) - 1 else ""
        lines.append(f'  "{key}": {{dx:{js_num(dx)}, dy:{js_num(dy)}}}{suffix}')
    lines += [
        "};",
    ]
    return "\n".join(lines)


def patch_text(text: str) -> str:
    matches = list(TABLE_RE.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"ROLL_TABLE_COUNT={len(matches)} expected=1")
    old = matches[0].group(0)
    # Fail closed unless the measured full-displacement sentinels are present.
    for sentinel in ['"-25": {dx:-32.5, dy: 22.0}', '"5":   {dx: 10.5, dy:-29.0}']:
        if sentinel not in old:
            raise SystemExit(f"EXPECTED_SENTINEL_MISSING={sentinel}")
    out = text[: matches[0].start()] + replacement_block() + text[matches[0].end() :]
    if out.count("const KOPF_ROLL_AUGEN_OFFSET = {") != 1:
        raise SystemExit("POST_TABLE_COUNT_INVALID")
    # The temporal atomicity fix must remain present and unmodified.
    for invariant in [
        "kopfRollAusgleichDeg = kopfRollWert;",
        "augenOffsetDx = zielOffset.dx;",
        "augenOffsetDy = zielOffset.dy;",
    ]:
        if invariant not in out:
            raise SystemExit(f"ATOMICITY_INVARIANT_MISSING={invariant}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--allow-subject-sha", default=EXPECTED_SHA256)
    args = ap.parse_args()

    raw = args.source.read_bytes()
    actual = sha256_bytes(raw)
    if actual != args.allow_subject_sha:
        raise SystemExit(
            f"SUBJECT_MISMATCH expected={args.allow_subject_sha} actual={actual}; refusing patch"
        )
    out = patch_text(raw.decode("utf-8")).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"SOURCE_SHA256={actual}")
    print(f"OUTPUT_SHA256={sha256_bytes(out)}")
    print("PATCH_SCOPE=ROLL_OVERLAY_TRANSLATION_SEMANTICS_ONLY")
    for deg, (dx, dy) in residual_table().items():
        print(f"RESIDUAL {deg:+d} {dx:+.6f} {dy:+.6f}")


if __name__ == "__main__":
    main()
