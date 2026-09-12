#!/usr/bin/env python3
"""Single-condition visible-X11/GPU scheduler attribution.

The four-condition visible v4 established that the rendering class is much closer
to production, but subsequent Chrome targets did not materialize after the first
fresh process.  This successor runs exactly one condition per Python invocation,
so each measurement has one fresh visible Chrome process and one CDP target.
No live avatar source is written.
"""
from __future__ import annotations

import os
from pathlib import Path

source_path = Path(__file__).with_name("diagnose_shadow_scheduler_attribution_v2.py")
source = source_path.read_text(encoding="utf-8")
mode = os.environ.get("GO_EYE_MODE", "special_raw")
allowed = {"idle", "normal_blink", "special_raw", "special_predecoded"}
if mode not in allowed:
    raise SystemExit(f"INVALID_GO_EYE_MODE {mode}")
replacements = [
    (
        '"return {special:_sonderLaeuft,phase:blinzelPhase};}})()",',
        '"return {special:_sonderLaeuft,phase:blinzelPhase};})()",',
        "SPECIAL_TRIGGER_BRACE",
    ),
    (
        '"google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",',
        '"/opt/google/chrome/chrome", "--no-sandbox", "--disable-dev-shm-usage",',
        "VISIBLE_CHROME_BINARY",
    ),
    (
        'f"--user-data-dir={tmp / \'profile\'}", "--window-size=1536,1024", url,',
        'f"--user-data-dir={tmp / \'profile\'}", "--window-size=746,449", "--window-position=0,0", f"--app={url}",',
        "PRODUCTION_LIKE_APP_WINDOW",
    ),
    (
        'modes = ("idle", "normal_blink", "special_raw", "special_predecoded")',
        f'modes = ({mode!r},)',
        "SINGLE_MODE",
    ),
    (
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION/v2",',
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION_VISIBLE_SINGLE/v5",',
        "SCHEMA",
    ),
    (
        '"scope": "EXACT_SHADOW_FRESH_CHROMIUM_IDLE_BLINK_SPECIAL_PREDECODE_NO_LIVE_WRITE",',
        f'"scope": "EXACT_SHADOW_VISIBLE_X11_GPU_SINGLE_{mode.upper()}_NO_LIVE_WRITE",',
        "SCOPE",
    ),
    (
        'print("EYE_SCHEDULER_ATTRIBUTION=COMPLETE")',
        'print("EYE_SCHEDULER_ATTRIBUTION_VISIBLE_SINGLE=COMPLETE")',
        "COMPLETE_MARKER",
    ),
]
for old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"VISIBLE_SINGLE_PATCH_PRECONDITION_FAILED {label} count={count}")
    source = source.replace(old, new, 1)
compile(source, str(source_path) + ":visible-single-v5", "exec")
namespace = {"__name__": "__main__", "__file__": str(source_path), "__package__": None}
exec(compile(source, str(source_path) + ":visible-single-v5", "exec"), namespace, namespace)
