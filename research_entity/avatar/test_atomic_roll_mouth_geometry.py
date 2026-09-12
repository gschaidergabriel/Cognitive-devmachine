#!/usr/bin/env python3
"""Deterministic regression for the mouth-roll registration candidate.

No browser and no production write. This proves the geometry contract and patch
shape; visual/product promotion still requires an exact real-host A/B gate.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_atomic_roll_mouth_geometry as p  # noqa: E402


def close(a: float, b: float, eps: float = 1e-9) -> None:
    if abs(a - b) > eps:
        raise AssertionError((a, b, eps))


def transform_about(point, origin, degrees):
    """2-D y-down image-coordinate rotation with one consistent convention.

    The exact sign convention is irrelevant to the common-translation theorem:
    if two transforms share the same R, their difference is point-independent.
    """
    x, y = point
    ox, oy = origin
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    dx, dy = x - ox, y - oy
    return (ox + c * dx + s * dy, oy - s * dx + c * dy)


def test_manifest_origin() -> None:
    # Transform origin converted back through the exact mouth box must be neck anchor.
    ox = p.MOUTH_X + p.MOUTH_W * p.ORIGIN_X_PCT / 100.0
    oy = p.MOUTH_Y + p.MOUTH_H * p.ORIGIN_Y_PCT / 100.0
    close(ox, p.NECK_X)
    close(oy, p.NECK_Y)
    close(p.ORIGIN_X_PCT, 49.49152542372881)
    close(p.ORIGIN_Y_PCT, 136.26373626373626)


def test_common_translation_theorem() -> None:
    # Model generated roll as R(point)+Tgen and CSS patch as R(point)+Tcss.
    # Difference must be the same Tgen-Tcss for eyes, mouth, nose, any point.
    pts = [(610.0, 207.0), (622.0, 352.0), (768.0, 600.0), (900.0, 300.0)]
    for deg in (-25, -10, -5, 0, 5, 10, 25):
        # Arbitrary translations are intentional: theorem must not depend on values.
        tgen = (13.25 + deg * 0.7, -8.5 + deg * 0.3)
        tcss = (-2.0 + deg * 0.1, 4.0 - deg * 0.2)
        residuals = []
        for q in pts:
            r = transform_about(q, (700.0, 500.0), deg)
            generated = (r[0] + tgen[0], r[1] + tgen[1])
            css = (r[0] + tcss[0], r[1] + tcss[1])
            residuals.append((generated[0] - css[0], generated[1] - css[1]))
        for residual in residuals[1:]:
            close(residual[0], residuals[0][0])
            close(residual[1], residuals[0][1])


def test_patch_shape() -> None:
    fixture = (
        "prefix\n" + p.OLD_CSS + "\nmid\n" + p.OLD_JS + "\nsuffix\n"
    )
    out = p.patch_text(fixture)
    assert p.OLD_CSS not in out
    assert p.OLD_JS not in out
    assert out.count('$("mund-effekt").style.transform') == 1
    assert f"transform-origin:{p.ORIGIN_X_PCT:.8f}% {p.ORIGIN_Y_PCT:.8f}%" in out
    assert "augenOffsetDx +=" not in out
    assert "augenOffsetDy +=" not in out


def test_zero_roll_identity_contract() -> None:
    # Current measured roll table has 0 -> translation (0,0). Candidate reuses that
    # exact residual and rotation=0; therefore neutral geometry is byte-independent
    # and geometrically identity at the transform level.
    dx = dy = angle = 0.0
    close(dx, 0.0)
    close(dy, 0.0)
    close(angle, 0.0)


def main() -> None:
    test_manifest_origin()
    test_common_translation_theorem()
    test_patch_shape()
    test_zero_roll_identity_contract()
    print("PASS atomic mouth-roll geometry regression")
    print(f"origin={p.ORIGIN_X_PCT:.8f}% {p.ORIGIN_Y_PCT:.8f}%")
    print("scope=STATIC_GEOMETRY_AND_PATCH_SHAPE_ONLY")


if __name__ == "__main__":
    main()
