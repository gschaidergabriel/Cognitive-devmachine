#!/usr/bin/env python3
"""Fail-closed visible-X11 scheduler discriminator for the exact canonical-eye shadow.

This successor exists because v4/v5 proved that Chrome 150 could start a DevTools browser
endpoint on the real X11 host while exposing only system extension targets and then exiting.
That is a harness/launch negative, not Avatar product evidence.

V6 keeps the production Avatar completely untouched and runs a fresh scratch Chrome per
condition with a fresh profile, explicit X11, extensions/default apps disabled, deterministic
process-group cleanup, and launch diagnostics if the expected page target never appears.
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
        "import json\n",
        "import json\nimport os\nimport signal\n",
        "PROCESS_GROUP_IMPORTS",
    ),
    (
        '"return {special:_sonderLaeuft,phase:blinzelPhase};}})()",',
        '"return {special:_sonderLaeuft,phase:blinzelPhase};})()",',
        "SPECIAL_TRIGGER_BRACE",
    ),
    (
        '"google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",',
        '"/opt/google/chrome/chrome", "--no-sandbox", "--disable-dev-shm-usage",\n'
        '            "--ozone-platform=x11", "--disable-extensions",\n'
        '            "--disable-component-extensions-with-background-pages", "--disable-default-apps",\n'
        '            "--no-first-run", "--no-default-browser-check", "--disable-session-crashed-bubble",',
        "VISIBLE_X11_STRICT_LAUNCH",
    ),
    (
        'f"--remote-debugging-port={cdp_port}", "--remote-allow-origins=*",',
        '"--remote-debugging-address=127.0.0.1", f"--remote-debugging-port={cdp_port}", "--remote-allow-origins=*",',
        "REMOTE_DEBUG_ADDRESS",
    ),
    (
        'f"--user-data-dir={tmp / \'profile\'}", "--window-size=1536,1024", url,',
        'f"--user-data-dir={tmp / \'profile\'}", "--window-size=746,449", "--window-position=0,0", f"--app={url}",',
        "PRODUCTION_LIKE_APP_WINDOW",
    ),
    (
        "        stdout=stdout_f,\n        stderr=stderr_f,\n    )",
        "        stdout=stdout_f,\n        stderr=stderr_f,\n        start_new_session=True,\n    )",
        "NEW_PROCESS_SESSION",
    ),
    (
        '        if not target:\n            row["error"] = "TARGET_PAGE_NOT_FOUND"\n            return row',
        '        if not target:\n'
        '            row["error"] = "TARGET_PAGE_NOT_FOUND"\n'
        '            row["chrome_returncode"] = proc.poll()\n'
        '            try:\n'
        '                tabs = requests.get(f"http://127.0.0.1:{cdp_port}/json/list", timeout=1.0).json()\n'
        '                row["cdp_targets"] = [{k: t.get(k) for k in ("type", "title", "url", "id")} for t in tabs]\n'
        '            except Exception as exc:\n'
        '                row["cdp_targets_error"] = f"{type(exc).__name__}:{exc}"\n'
        '            try:\n'
        '                stderr_f.flush()\n'
        '                row["chrome_stderr_tail"] = (tmp / "chrome.stderr").read_text(encoding="utf-8", errors="replace")[-6000:]\n'
        '            except Exception as exc:\n'
        '                row["chrome_stderr_error"] = f"{type(exc).__name__}:{exc}"\n'
        '            return row',
        "TARGET_FAILURE_DIAGNOSTICS",
    ),
    (
        "        proc.terminate()\n        try:\n            proc.wait(timeout=5)\n        except subprocess.TimeoutExpired:\n            proc.kill()",
        "        if proc.poll() is None:\n"
        "            try:\n"
        "                os.killpg(proc.pid, signal.SIGTERM)\n"
        "            except ProcessLookupError:\n"
        "                pass\n"
        "        try:\n"
        "            proc.wait(timeout=5)\n"
        "        except subprocess.TimeoutExpired:\n"
        "            try:\n"
        "                os.killpg(proc.pid, signal.SIGKILL)\n"
        "            except ProcessLookupError:\n"
        "                pass\n"
        "            proc.wait(timeout=5)",
        "PROCESS_GROUP_CLEANUP",
    ),
    (
        'modes = ("idle", "normal_blink", "special_raw", "special_predecoded")',
        f'modes = ({mode!r},)',
        "SINGLE_MODE",
    ),
    (
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION/v2",',
        '"schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION_VISIBLE_X11/v6",',
        "SCHEMA",
    ),
    (
        '"scope": "EXACT_SHADOW_FRESH_CHROMIUM_IDLE_BLINK_SPECIAL_PREDECODE_NO_LIVE_WRITE",',
        f'"scope": "EXACT_SHADOW_VISIBLE_X11_STRICT_SINGLE_{mode.upper()}_NO_LIVE_WRITE",',
        "SCOPE",
    ),
    (
        'print("EYE_SCHEDULER_ATTRIBUTION=COMPLETE")',
        'print("EYE_SCHEDULER_ATTRIBUTION_VISIBLE_X11_V6=COMPLETE")',
        "COMPLETE_MARKER",
    ),
]

for old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"VISIBLE_X11_V6_PATCH_PRECONDITION_FAILED {label} count={count}")
    source = source.replace(old, new, 1)

compile(source, str(source_path) + ":visible-x11-v6", "exec")
namespace = {"__name__": "__main__", "__file__": str(source_path), "__package__": None}
exec(compile(source, str(source_path) + ":visible-x11-v6", "exec"), namespace, namespace)
