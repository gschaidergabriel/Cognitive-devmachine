#!/usr/bin/env python3
"""Matched ABBA v2 wrapper around body_visible_scratch_ab.py.

Transforms only the scratch harness timing: excluded warm-up, then equal A/B/A/B
windows. Production invariants and thresholds remain those of the preregistered
v1 gate.
"""
from pathlib import Path

p = Path(__file__).with_name("body_visible_scratch_ab.py")
s = p.read_text()
old_phase = "window.__bodyVisiblePhase='base';"
old_switch = "setTimeout(()=>window.__bodyVisibleEnable(),7000);"
old_timing = '''        time.sleep(4.5)\n        result["base_screenshot"] = screenshot(wid, out / "base.png")\n        time.sleep(5.0)\n        result["candidate_screenshot"] = screenshot(wid, out / "candidate.png")\n        time.sleep(2.0)'''
new_switch = '''window.__bodyVisiblePhase='warmup';\n setTimeout(()=>{window.__bodyVisibleDisable();window.__bodyVisiblePhase='base'},4000);\n setTimeout(()=>{window.__bodyVisibleEnable();window.__bodyVisiblePhase='candidate'},10000);\n setTimeout(()=>{window.__bodyVisibleDisable();window.__bodyVisiblePhase='base'},16000);\n setTimeout(()=>{window.__bodyVisibleEnable();window.__bodyVisiblePhase='candidate'},22000);'''
new_timing = '''        time.sleep(5.0)\n        result["base_screenshot"] = screenshot(wid, out / "base.png")\n        time.sleep(6.0)\n        result["candidate_screenshot"] = screenshot(wid, out / "candidate.png")\n        time.sleep(17.0)'''
for needle in (old_phase, old_switch, old_timing):
    if s.count(needle) != 1:
        raise SystemExit(f"SOURCE_BINDING_FAIL: expected exactly one occurrence: {needle[:60]!r}")
s = s.replace(old_phase, "window.__bodyVisiblePhase='warmup';", 1)
s = s.replace(old_switch, new_switch, 1)
s = s.replace(old_timing, new_timing, 1)
s = s.replace('"schema": "BODY_VISIBLE_SCRATCH_AB/v1"', '"schema": "BODY_VISIBLE_SCRATCH_ABBA/v2"', 1)
exec(compile(s, str(p) + "#abba_v2", "exec"), {"__name__": "__main__", "__file__": str(p)})
