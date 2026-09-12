#!/usr/bin/env python3
"""Source-over identity v2: exact v1 experiment with only the proven Y-orientation bug repaired.

Authority: RESULT_SOURCEOVER_V1_HARNESS_INVALID_20260912.md.
The preregistered equations, input families, layer directions and thresholds are unchanged.
Only the vertex/upload orientation contradiction is repaired:
UNPACK_FLIP_Y_WEBGL remains enabled; the vertex shader uses uv=p; readback stays row-flipped.
"""
from __future__ import annotations

import pathlib

src = pathlib.Path(__file__).with_name("body_crossfade_sourceover_identity.py")
code = src.read_text()
old = "uv=vec2(p.x,1.-p.y);"
new = "uv=p;"
count = code.count(old)
if count != 1:
    raise SystemExit(f"HARNESS_SOURCE_DRIFT: expected exactly one orientation expression, found {count}")
code = code.replace(old, new, 1)
ns = {
    "__name__": "__main__",
    "__file__": str(src) + "#orientation-v2",
    "__package__": None,
}
exec(compile(code, str(src) + "#orientation-v2", "exec"), ns, ns)
