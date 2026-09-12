#!/usr/bin/env python3
"""Fix the two literal template constants in a temporary body_webgl_gate copy.

The original gate accidentally left Python-like `${...}` text in GLSL. This
wrapper only edits the temporary fetched harness; it never touches live avatar
source or assets.
"""
from pathlib import Path
import runpy
import sys

p = Path(sys.argv[1])
s = p.read_text()
s2 = s.replace('${1423-117}.0', '1306.0').replace('${1024-505}.0', '519.0')
if s2 == s:
    raise SystemExit('expected harness literals not found')
p.write_text(s2)
sys.argv = [str(p)] + sys.argv[2:]
runpy.run_path(str(p), run_name='__main__')
