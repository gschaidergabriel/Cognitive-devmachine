#!/usr/bin/env python3
"""BODY_CROSSFADE_SOURCEOVER_IDENTITY/v5 — identical raster + highp fragment math.

v4 removed the resampling confound and passed silhouette topology but retained
~0.29/255 mean alpha mismatch against Canvas2D. v5 changes only fragment float
precision from mediump to highp while preserving the identical-raster input and
all original strict acceptance thresholds externally.
"""
from __future__ import annotations
import pathlib
HERE=pathlib.Path(__file__).resolve().parent
V4=HERE/'body_crossfade_sourceover_identity_v4.py'
src=V4.read_text()
old_schema=".replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v4')"
new_schema=".replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v5')"
assert src.count(old_schema)==1
# The v4 wrapper compiles v1 source at runtime. Extend that transformation by
# replacing the single fragment precision declaration in the derived source.
old_compile="patched=(src.replace(old_uv,'uv=p;')\n            .replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v4')\n            .replace(old_cache,new_cache)\n            .replace(old_css,new_css))"
new_compile="patched=(src.replace(old_uv,'uv=p;')\n            .replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v5')\n            .replace(old_cache,new_cache)\n            .replace(old_css,new_css)\n            .replace('precision mediump float;varying vec2 uv;uniform sampler2D layer1,layer2;', 'precision highp float;varying vec2 uv;uniform sampler2D layer1,layer2;'))"
assert src.count(old_compile)==1
patched_wrapper=src.replace(old_compile,new_compile)
ns={'__name__':'__main__','__file__':str(V4),'__package__':None}
exec(compile(patched_wrapper,str(V4)+'#v5_highp_wrapper','exec'),ns,ns)
