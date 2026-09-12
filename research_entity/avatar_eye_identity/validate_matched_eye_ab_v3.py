#!/usr/bin/env python3
"""Matched-eye A/B harness repair v3.

Acceptance thresholds, exact subject hashes and report schema are unchanged.
Relative to the original validator this wrapper:
1. lets the shadow reach readiness before any virtual-time budget is consumed;
2. after the real special expression is active, freezes virtual time AND all
   document/Web Animations/media so compositor-thread animation cannot corrupt
   the off/on/off matched control.
No production bytes are changed.
"""
from __future__ import annotations

import pathlib

src = pathlib.Path(__file__).with_name("validate_matched_eye_ab.py")
code = src.read_text(encoding="utf-8")
pre = '        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "advance", "budget": 1000.0})\n'
if code.count(pre) != 1:
    raise SystemExit(f"HARNESS_SOURCE_DRIFT: pre-ready VT count={code.count(pre)}")
code = code.replace(pre, "", 1)
needle = '        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "pause"})\n'
if code.count(needle) != 1:
    raise SystemExit(f"HARNESS_SOURCE_DRIFT: pause VT count={code.count(needle)}")
freeze = needle + '''        cdp.call("Animation.enable")\n        cdp.call("Animation.setPlaybackRate", {"playbackRate": 0})\n        cdp.eval(\n            "(()=>{document.getAnimations({subtree:true}).forEach(a=>{try{a.pause()}catch(_){}});"\n            "document.querySelectorAll('video,audio').forEach(m=>{try{m.pause()}catch(_){}});"\n            "return {animations:document.getAnimations({subtree:true}).length,"\n            "media:document.querySelectorAll('video,audio').length}})()"\n        )\n'''
code = code.replace(needle, freeze, 1)
ns = {"__name__": "__main__", "__file__": str(src) + "#matched-v3", "__package__": None}
exec(compile(code, str(src) + "#matched-v3", "exec"), ns, ns)
