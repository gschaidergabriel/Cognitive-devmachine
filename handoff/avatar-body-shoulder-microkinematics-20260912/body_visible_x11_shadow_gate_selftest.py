#!/usr/bin/env python3
"""Static fail-closed checks for body_visible_x11_shadow_gate.py.

No browser launch, no live write, no process mutation.
"""
from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE / "body_live_gpu_shadow_gate.py"
VISIBLE = HERE / "body_visible_x11_shadow_gate.py"
EXPECTED = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"


def main() -> int:
    base = BASE.read_text(encoding="utf-8")
    visible = VISIBLE.read_text(encoding="utf-8")

    parent_sha = re.search(r'^EXPECTED_SHA256\s*=\s*"([0-9a-f]{64})"', base, re.M)
    if not parent_sha or parent_sha.group(1) != EXPECTED:
        raise SystemExit("FAIL parent expected SHA drift")

    wrapper_sha = re.search(r'^EXPECTED_LIVE_SHA256\s*=\s*"([0-9a-f]{64})"', visible, re.M)
    if not wrapper_sha or wrapper_sha.group(1) != EXPECTED:
        raise SystemExit("FAIL wrapper expected SHA drift")

    ns = {"__name__": "not_main", "__file__": str(VISIBLE)}
    exec(compile(visible, str(VISIBLE), "exec"), ns)
    headless = ns["HEADLESS_CMD"]
    candidate = ns["VISIBLE_CMD"]

    if base.count(headless) != 1:
        raise SystemExit(f"FAIL patch anchor count={base.count(headless)}")
    if "--headless" not in headless:
        raise SystemExit("FAIL source anchor is not headless")
    if "--headless" in candidate:
        raise SystemExit("FAIL visible candidate still headless")
    if "--window-size=746,449" not in candidate:
        raise SystemExit("FAIL candidate viewport drift")
    if "--window-position=100,100" not in candidate:
        raise SystemExit("FAIL candidate not pinned to left monitor")
    if '"scratch_monitor": "HDMI-A-1"' not in visible:
        raise SystemExit("FAIL scratch monitor declaration drift")
    if '"production_monitor": "HDMI-A-0"' not in visible:
        raise SystemExit("FAIL production monitor declaration drift")
    if "production_pid_invariant" not in visible or "live_source_invariant" not in visible:
        raise SystemExit("FAIL postcondition gates missing")

    print("BODY_VISIBLE_X11_SHADOW_GATE_SELFTEST_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
