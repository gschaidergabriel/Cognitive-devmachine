#!/usr/bin/env python3
"""Run the exact v2 attribution matrix in a visible real-X11 Chrome app.

This wrapper changes only the execution surface plus the already-classified v2
special-trigger syntax bug:
  * headless Chrome -> /opt/google/chrome/chrome visible app on inherited DISPLAY
  * 1536x1024 browser -> production-like 746x449 app window
  * same semantic shadow, exact live/open-eye identities, same four conditions
No live source file is written.
"""
from __future__ import annotations

from pathlib import Path

source_path = Path(__file__).with_name("diagnose_shadow_scheduler_attribution_v2.py")
source = source_path.read_text(encoding="utf-8")
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
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION/v2",',
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION_VISIBLE/v4",',
        "SCHEMA",
    ),
    (
        '"scope": "EXACT_SHADOW_FRESH_CHROMIUM_IDLE_BLINK_SPECIAL_PREDECODE_NO_LIVE_WRITE",',
        '"scope": "EXACT_SHADOW_VISIBLE_X11_GPU_APP_IDLE_BLINK_SPECIAL_PREDECODE_NO_LIVE_WRITE",',
        "SCOPE",
    ),
    (
        'print("EYE_SCHEDULER_ATTRIBUTION=COMPLETE")',
        'print("EYE_SCHEDULER_ATTRIBUTION_VISIBLE=COMPLETE")',
        "COMPLETE_MARKER",
    ),
]
for old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"VISIBLE_PATCH_PRECONDITION_FAILED {label} count={count}")
    source = source.replace(old, new, 1)
compile(source, str(source_path) + ":visible-v4", "exec")
namespace = {
    "__name__": "__main__",
    "__file__": str(source_path),
    "__package__": None,
}
exec(compile(source, str(source_path) + ":visible-v4", "exec"), namespace, namespace)
