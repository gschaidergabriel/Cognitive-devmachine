#!/usr/bin/env python3
"""BODY_DOM_WEBGL_CROSSFADE_SCREENSHOT/v2 orientation-correct wrapper.

The v1 direct screenshot gate combined UNPACK_FLIP_Y_WEBGL=1 with a second
shader-space Y inversion (uv=vec2(p.x,1.-p.y)). That double-flip makes the
WebGL column vertically inverted relative to the DOM <img> reference and can
produce a large false mismatch even when source-over blending is correct.

v2 changes only that coordinate convention in scratch: with upload-time flip
enabled, sample with uv=p. The underlying v1 gate remains untouched for exact
reproduction of the original negative result.
"""
from __future__ import annotations
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
V1 = HERE / "body_dom_webgl_crossfade_screenshot_gate.py"
src = V1.read_text()
old = "uv=vec2(p.x,1.-p.y);"
assert src.count(old) == 1, src.count(old)
patched = src.replace(old, "uv=p;")
ns = {"__name__": "__main__", "__file__": str(V1), "__package__": None}
exec(compile(patched, str(V1) + "#v2_orientation", "exec"), ns, ns)
