#!/usr/bin/env python3
"""Static regression for apply_roll_overlay_residual_candidate.py."""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_roll_overlay_residual_candidate as p  # noqa: E402


def norm(v):
    return math.hypot(v[0], v[1])


def main() -> None:
    residual = p.residual_table()
    max_corrected = 0.0
    max_current = 0.0
    for deg, target in p.FULL.items():
        rot = p.css_rotation_displacement(deg)
        current = (rot[0] + target[0], rot[1] + target[1])
        corrected = (rot[0] + residual[deg][0], rot[1] + residual[deg][1])
        current_error = norm((current[0] - target[0], current[1] - target[1]))
        corrected_error = norm((corrected[0] - target[0], corrected[1] - target[1]))
        max_current = max(max_current, current_error)
        max_corrected = max(max_corrected, corrected_error)
        if corrected_error > 1e-9:
            raise AssertionError((deg, corrected_error))
    if max_current < 180.0:
        raise AssertionError(f"expected strong current defect, got {max_current}")
    if residual[0] != (0.0, 0.0):
        raise AssertionError(residual[0])
    block = p.replacement_block()
    if '"-25": {dx:118.786' not in block or '"25": {dx:-118.392' not in block:
        raise AssertionError(block)
    print(f"PASS max_current_error={max_current:.6f}px max_corrected_error={max_corrected:.12f}px")
    print("scope=STATIC_GEOMETRY_ONLY_NO_LIVE_MUTATION")


if __name__ == "__main__":
    main()
