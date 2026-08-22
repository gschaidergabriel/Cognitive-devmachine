#!/usr/bin/env python3
"""Deprecated compatibility entry point.

V1 corpus/template admission was superseded by the diversity/compositional OOD and
fail-closed BYOM-template gates in launch_together_v2.py. Keep this filename only so
old operator instructions cannot accidentally bypass the current training authority.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "launch_together_v2.py"

if __name__ == "__main__":
    print("CLAYCOG_V1_DEPRECATED: routing through launch_together_v2.py", file=sys.stderr)
    os.execv(sys.executable, [sys.executable, str(TARGET), *sys.argv[1:]])
