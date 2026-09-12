#!/usr/bin/env python3
"""Regression for the OpenCV split-remap coordinate ABI.

The real-host blind gate failed on OpenCV 4.13 because mapx could be promoted to
float64 while mapy stayed float32.  cv2.remap requires both split maps to be
CV_32FC1 (or one packed CV_32FC2 map).  This regression deliberately supplies a
float64 displacement so future scalar/dtype changes cannot silently reopen it.
"""
from __future__ import annotations

import numpy as np

from depthwarp_display_space_gate import remap_xy


def main() -> int:
    yy, xx = np.mgrid[0:7, 0:11].astype(np.float32)
    dx = np.linspace(-1.5, 1.5, 77, dtype=np.float64).reshape(7, 11)
    mapx, mapy = remap_xy(xx, yy, dx)
    assert mapx.dtype == np.float32
    assert mapy.dtype == np.float32
    assert mapx.flags.c_contiguous
    assert mapy.flags.c_contiguous
    np.testing.assert_allclose(mapx, (xx.astype(np.float64) - dx).astype(np.float32), rtol=0, atol=1e-6)
    np.testing.assert_array_equal(mapy, yy)
    print("DEPTHWARP_REMAP_DTYPE_REGRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
