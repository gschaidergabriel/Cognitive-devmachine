#!/usr/bin/env python3
"""Corrected BODY_CROSSFADE_SOURCEOVER_IDENTITY/v2 harness.

This deliberately derives from the preserved v1 harness and applies exactly two
text substitutions: remove the duplicate Y inversion in the vertex shader and
bump the evidence schema. Acceptance thresholds are external/preregistered and
are not modified here.
"""
from __future__ import annotations
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
V1 = HERE / "body_crossfade_sourceover_identity.py"
src = V1.read_text()
old_uv = "uv=vec2(p.x,1.-p.y);"
new_uv = "uv=p;"
old_schema = "BODY_CROSSFADE_SOURCEOVER_IDENTITY/v1"
new_schema = "BODY_CROSSFADE_SOURCEOVER_IDENTITY/v2"
assert src.count(old_uv) == 1, f"expected one v1 UV inversion, got {src.count(old_uv)}"
assert src.count(old_schema) == 1, f"expected one v1 schema, got {src.count(old_schema)}"
patched = src.replace(old_uv, new_uv).replace(old_schema, new_schema)
ns = {"__name__": "__main__", "__file__": str(V1), "__package__": None}
exec(compile(patched, str(V1) + "#v2_yfix", "exec"), ns, ns)
