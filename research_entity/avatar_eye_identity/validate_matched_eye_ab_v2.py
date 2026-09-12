#!/usr/bin/env python3
"""Transport/readiness repair for validate_matched_eye_ab.py.

Keeps the original exact-subject checks, frozen A/B metrics and acceptance
thresholds unchanged. The only change is that Chrome virtual time is not
advanced/expired before the page has reached SHADOW_RUNTIME_NOT_READY's
readiness predicate. The original validator already pauses virtual time after
entering the real special expression; that freeze remains unchanged.
"""
from __future__ import annotations

import pathlib

src = pathlib.Path(__file__).with_name("validate_matched_eye_ab.py")
code = src.read_text(encoding="utf-8")
old = '        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "advance", "budget": 1000.0})\n'
if code.count(old) != 1:
    raise SystemExit(f"HARNESS_SOURCE_DRIFT: pre-ready virtual-time call count={code.count(old)}")
code = code.replace(old, "", 1)
ns = {"__name__": "__main__", "__file__": str(src) + "#readiness-v2", "__package__": None}
exec(compile(code, str(src) + "#readiness-v2", "exec"), ns, ns)
