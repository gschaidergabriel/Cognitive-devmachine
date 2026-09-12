#!/usr/bin/env python3
"""Singleton-preserving entrypoint for the live FranKenstein Avatar daemon.

Owner law 2026-09-12:
- one production Avatar Chrome/window only;
- preserve/adopt the existing Chrome process across daemon re-entry when possible;
- screen 2 (HDMI-A-0) is the production presentation surface;
- refresh/reuse instead of spawning another production browser.

This wrapper deliberately imports the existing live buehne_daemon.py rather than forking a
second daemon implementation. It changes only lifecycle/geometry behavior at entry.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import threading
import time

LIVE = "/home/ai-core-node/.claude/star/visual/buehne_daemon.py"
HELPER = "/home/ai-core-node/.claude/star/visual/avatar_singleton_refresh.sh"

spec = importlib.util.spec_from_file_location("frankenstein_live_buehne", LIVE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {LIVE}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Physical screen 2 / HDMI-A-0 measured production geometry.
mod.FENSTER_X = 1847
mod.FENSTER_Y = 168
mod.FENSTER_B = 746
mod.FENSTER_H = 449


class _AdoptedProcess:
    """Minimal Popen-compatible view for an already-running Chrome leader PID."""

    def __init__(self, pid: int):
        self.pid = pid

    def poll(self):
        try:
            os.kill(self.pid, 0)
            return None
        except ProcessLookupError:
            return 0
        except PermissionError:
            # Same-user production process is expected; if visibility is restricted,
            # fail toward preserving rather than spawning a duplicate.
            return None


def _adopt_previous_chrome(self):
    """Adopt a live PID from chrome.pid; only delete the PID file when stale/invalid."""
    try:
        with open(mod.PID_DATEI, "r", encoding="utf-8") as fh:
            pid = int(fh.read().strip())
        adopted = _AdoptedProcess(pid)
        if adopted.poll() is None:
            self.proc = adopted
            print(f"[buehne-singleton] existing Chrome adopted (pid {pid}); no replacement spawned")
            return
    except Exception as exc:
        print(f"[buehne-singleton] no adoptable prior Chrome: {exc}")

    try:
        os.remove(mod.PID_DATEI)
    except FileNotFoundError:
        pass
    except Exception as exc:
        print(f"[buehne-singleton] stale PID cleanup failed: {exc}")


def _preserve_chrome_on_daemon_exit(self):
    """Daemon/service re-entry must not destroy the visible production browser.

    A deliberate stage-off through the existing state/API still uses the original
    `schliessen()` path. This override affects daemon shutdown/restart only: it leaves
    Chrome + chrome.pid in place so the next singleton entrypoint can adopt the same
    production process instead of creating a replacement.
    """
    if getattr(mod, "_blick_modul", None) is not None:
        try:
            mod._blick_modul.instanz().stoppen()
        except Exception as exc:
            print(f"[buehne-singleton] Blickfuehrung stop warning: {exc}")
    pid = getattr(getattr(self, "proc", None), "pid", None)
    print(f"[buehne-singleton] daemon exit preserves Chrome pid={pid}; next daemon adopts it")


mod.Fensterverwalter._alte_pid_aufraeumen = _adopt_previous_chrome
mod.Fensterverwalter.herunterfahren = _preserve_chrome_on_daemon_exit


def _delayed_singleton_reconcile():
    # Allow HTTP server and X11 window to settle. The helper itself never launches Chrome
    # directly; if absent, it asks the already-running buehne daemon through /api/schalten.
    time.sleep(2.0)
    try:
        subprocess.run(["bash", HELPER], check=False, timeout=15)
    except Exception as exc:
        print(f"[buehne-singleton] reconcile helper failed: {exc}")


threading.Thread(target=_delayed_singleton_reconcile, daemon=True).start()
mod.hauptschleife()
