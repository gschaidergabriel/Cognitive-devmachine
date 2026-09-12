#!/usr/bin/env python3
"""Visible-X11 derivative of body_live_gpu_shadow_gate.py.

Scope:
- NEVER mutates the production buehne.html.
- Requires the exact live SHA admitted by the parent gate.
- Reuses the parent gate's single-scheduler WebGL shadow implementation.
- Removes only Chrome headless mode and pins the scratch window to HDMI-A-1
  (left monitor), away from the existing production Avatar on HDMI-A-0.
- Verifies the production Chrome subject PID set is unchanged before/after.

This is an evidence gate, not production activation.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
BASE = pathlib.Path(__file__).with_name("body_live_gpu_shadow_gate.py")
LIVE = pathlib.Path("/home/ai-core-node/.claude/star/visual/buehne.html")

HEADLESS_CMD = "cmd=[a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/\"profile\"}',f'--window-size=900,700',f'http://127.0.0.1:{srv.server_address[1]}/buehne.html']"
VISIBLE_CMD = "cmd=[a.chrome,'--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/\"profile\"}','--window-size=746,449','--window-position=100,100',f'http://127.0.0.1:{srv.server_address[1]}/buehne.html']"


def sha256(path: pathlib.Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def production_chrome_pids() -> list[int]:
    """Recognize only the existing production app/profile subject."""
    found: list[int] = []
    proc = pathlib.Path("/proc")
    for p in proc.iterdir():
        if not p.name.isdigit():
            continue
        try:
            argv = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if "--app=http://127.0.0.1:8788/" in argv and "/home/ai-core-node/.claude/star/visual/chrome-profile" in argv:
            found.append(int(p.name))
    return sorted(found)


def main() -> int:
    live_sha = sha256(LIVE)
    before = production_chrome_pids()
    print(json.dumps({
        "schema": "BODY_VISIBLE_X11_SHADOW_GATE/v1",
        "phase": "PRE",
        "live_sha256": live_sha,
        "expected_live_sha256": EXPECTED_LIVE_SHA256,
        "production_pids": before,
        "display": ":0",
        "scratch_geometry": "746x449+100+100",
        "scratch_monitor": "HDMI-A-1",
        "production_monitor": "HDMI-A-0",
    }, sort_keys=True))

    if live_sha != EXPECTED_LIVE_SHA256:
        print("SOURCE_MISMATCH", file=sys.stderr)
        return 5
    if not before:
        print("PRODUCTION_SUBJECT_NOT_BOUND", file=sys.stderr)
        return 6
    if not BASE.is_file():
        print("BASE_GATE_MISSING", file=sys.stderr)
        return 7

    src = BASE.read_text(encoding="utf-8")
    count = src.count(HEADLESS_CMD)
    if count != 1:
        print(f"PATCH_ANCHOR_MISMATCH={count}", file=sys.stderr)
        return 8
    src = src.replace(HEADLESS_CMD, VISIBLE_CMD, 1)

    old_display = os.environ.get("DISPLAY")
    os.environ["DISPLAY"] = ":0"
    ns = {
        "__name__": "__main__",
        "__file__": str(BASE.with_name("body_live_gpu_shadow_gate.VISIBLE_DERIVED.py")),
    }
    rc = 0
    try:
        exec(compile(src, ns["__file__"], "exec"), ns)
    except SystemExit as exc:
        rc = int(exc.code or 0)
    finally:
        if old_display is None:
            os.environ.pop("DISPLAY", None)
        else:
            os.environ["DISPLAY"] = old_display

    after = production_chrome_pids()
    post_sha = sha256(LIVE)
    invariant = before == after
    source_invariant = live_sha == post_sha == EXPECTED_LIVE_SHA256
    print(json.dumps({
        "schema": "BODY_VISIBLE_X11_SHADOW_GATE/v1",
        "phase": "POST",
        "base_gate_exit": rc,
        "production_pids_before": before,
        "production_pids_after": after,
        "production_pid_invariant": invariant,
        "live_sha256_after": post_sha,
        "live_source_invariant": source_invariant,
    }, sort_keys=True))

    if rc != 0:
        return rc
    if not invariant:
        return 11
    if not source_invariant:
        return 12
    print("BODY_VISIBLE_X11_SHADOW_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
