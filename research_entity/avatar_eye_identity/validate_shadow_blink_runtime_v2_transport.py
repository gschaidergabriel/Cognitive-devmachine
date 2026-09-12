#!/usr/bin/env python3
"""Transport-only repair for validate_shadow_blink_runtime_v2.py.

No product predicate, threshold, exact-subject hash, blink requirement or report
schema is changed. The repair only increases synchronous CDP response tolerance
from 8s to 20s and reduces state polling pressure from ~83Hz to 50Hz.
"""
from __future__ import annotations

import pathlib

src = pathlib.Path(__file__).with_name("validate_shadow_blink_runtime_v2.py")
code = src.read_text(encoding="utf-8")
repls = {
    "def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 8.0)":
        "def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 20.0)",
    "def eval(self, expression: str, timeout: float = 8.0)":
        "def eval(self, expression: str, timeout: float = 20.0)",
    "            time.sleep(0.012)": "            time.sleep(0.020)",
}
for old, new in repls.items():
    if code.count(old) != 1:
        raise SystemExit(f"HARNESS_SOURCE_DRIFT: {old!r} count={code.count(old)}")
    code = code.replace(old, new, 1)
ns = {"__name__": "__main__", "__file__": str(src) + "#transport-v2b", "__package__": None}
exec(compile(code, str(src) + "#transport-v2b", "exec"), ns, ns)
