from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .unified_store import now


CHILDREN = {
    "assembly": [sys.executable, "-m", "omega.assembly"],
    "grid": [sys.executable, "-m", "omega.grid_runtime_v3"],
    "relay": [sys.executable, "-m", "omega.relay_entrypoint"],
    "receipt_reconciler": [sys.executable, "-m", "omega.spool_receipt_reconciler"],
    "telemetry": [sys.executable, "-m", "omega.telemetry_daemon"],
    "master_bridge": [sys.executable, "-m", "omega.master_bridge_carrier"],
}

STABLE_UPTIME_SECONDS = 60.0
MAX_RESTART_BACKOFF_SECONDS = 60.0
DEFAULT_HOST_RELAY_STALL_SECONDS = 360.0
STALL_TERM_GRACE_SECONDS = 10.0


class Supervisor:
    """Canonical OMEGA runtime supervisor.

    Startup first proves the static assembly core through the existing read-only
    assembly monitor.  The long-running central runtime then uses the credential-free
    OUTER_SPOOL boundary for host effects while preserving crash quarantine,
    no-automatic-replay semantics, watchdog/backoff behavior and exact late-receipt
    reconciliation.  Privileged host-side transport remains outside the sandbox.
    """

    def __init__(self, runtime_root: Path, repo_root: Path) -> None:
        self.runtime_root = runtime_root
        self.repo_root = repo_root
        self.logs = runtime_root / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.status_path = runtime_root / "SUPERVISOR_STATUS.json"
        self.assembly_preflight_path = runtime_root / "ASSEMBLY_PREFLIGHT.json"
        self.procs: dict[str, subprocess.Popen[Any]] = {}
        self.log_handles: dict[str, Any] = {}
        self.started_at: dict[str, float] = {}
        self.restart_count: dict[str, int] = {name: 0 for name in CHILDREN}
        self.restart_after: dict[str, float] = {}
        self.last_exit_code: dict[str, int | None] = {name: None for name in CHILDREN}
        self.host_relay_stall_seconds = max(
            60.0,
            float(os.getenv("OMEGA_RELAY_HOST_STALL_SECONDS", str(DEFAULT_HOST_RELAY_STALL_SECONDS))),
        )
        self.relay_stall_pid: int | None = None
        self.relay_stall_signal_at: float | None = None
        self.relay_stall_kill_count = 0
        self.last_relay_stall: dict[str, Any] | None = None
        self.stop = False

    @property
    def db_path(self) -> Path:
        return self.runtime_root.parent / "data" / "omega_unified.db"

    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": str(self.repo_root),
            "OMEGA_RUNTIME_ROOT": str(self.runtime_root),
            "OMEGA_REPO_ROOT": str(self.repo_root),
            "OMEGA_UNIFIED_DB": str(self.db_path),
            "OMEGA_ROUTER_CONFIG": str(self.repo_root / "config" / "organ_router.json"),
            "OMEGA_AUTONOMY_POLICY": str(self.repo_root / "config" / "autonomy_policy.json"),
            "OMEGA_CARRIER_REPO": str(self.runtime_root.parent / "carrier_repo"),
            "OMEGA_OUTER_SPOOL": str(self.runtime_root / "outer_bridge"),
            "OMEGA_RELAY_MODULE": "omega.spool_bridge_relay_parallel",
        })
        return env

    def assembly_preflight(self) -> dict[str, Any]:
        """Validate the canonical composition before any long-running child starts.

        ``omega.assembly --once`` is the existing read-only assembly monitor. Reusing
        it here avoids a second validator or authority. It may write assembly status and
        evidence to UnifiedDB, but it starts no donor daemon and performs no host/effect
        action. Probe-required donor organs may remain DECLARED_UNVERIFIED; the hard
        requirement for process startup is a valid manifest plus a bound static core.
        """
        cmd = [
            sys.executable,
            "-m",
            "omega.assembly",
            "--repo-root",
            str(self.repo_root),
            "--runtime-root",
            str(self.runtime_root),
            "--db",
            str(self.db_path),
            "--once",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_root,
                env=self.child_env(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            try:
                report = json.loads(proc.stdout) if proc.stdout.strip() else {}
            except json.JSONDecodeError:
                report = {}
            if not isinstance(report, dict):
                report = {}
            report = dict(report)
            report["supervisor_probe"] = {
                "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-4000:],
                "command": cmd,
            }
            report["preflight_ok"] = bool(
                proc.returncode == 0
                and report.get("schema") == "OMEGA_ASSEMBLY_STATUS/v1"
                and report.get("static_core_bound") is True
            )
            if not report["preflight_ok"]:
                report["preflight_error"] = "ASSEMBLY_PREFLIGHT_FAILED_CLOSED"
        except Exception as exc:
            report = {
                "schema": "OMEGA_ASSEMBLY_PREFLIGHT/v1",
                "preflight_ok": False,
                "preflight_error": f"{type(exc).__name__}:{exc}",
                "supervisor_probe": {"command": cmd},
            }

        self.assembly_preflight_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.assembly_preflight_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.assembly_preflight_path)
        return report

    def spawn(self, name: str) -> None:
        old = self.log_handles.pop(name, None)
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        log = open(self.logs / f"{name}.log", "a", encoding="utf-8", buffering=1)
        self.log_handles[name] = log
        proc = subprocess.Popen(
            CHILDREN[name], cwd=self.repo_root, env=self.child_env(),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
        self.procs[name] = proc
        self.started_at[name] = time.monotonic()
        self.restart_after.pop(name, None)
        if name == "relay":
            self.relay_stall_pid = None
            self.relay_stall_signal_at = None

    def note_exit(self, name: str, proc: subprocess.Popen[Any]) -> None:
        rc = proc.poll()
        if rc is None:
            return
        uptime = max(0.0, time.monotonic() - self.started_at.get(name, time.monotonic()))
        if uptime >= STABLE_UPTIME_SECONDS:
            self.restart_count[name] = 0
        self.restart_count[name] += 1
        exponent = min(self.restart_count[name] - 1, 6)
        delay = min(MAX_RESTART_BACKOFF_SECONDS, 2.0 * (2 ** exponent))
        self.restart_after[name] = time.monotonic() + delay
        self.last_exit_code[name] = rc
        self.procs.pop(name, None)
        handle = self.log_handles.pop(name, None)
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass

    def oldest_host_dispatch(self) -> dict[str, Any] | None:
        if not self.db_path.exists():
            return None
        try:
            con = sqlite3.connect(self.db_path, timeout=1)
            try:
                con.execute("PRAGMA busy_timeout=1000")
                table = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='relay_ledger' LIMIT 1"
                ).fetchone()
                if table is None:
                    return None
                row = con.execute(
                    """
                    SELECT effect_id,organ_id,updated_at
                      FROM relay_ledger
                     WHERE state='DISPATCHING' AND organ_id LIKE 'host:%'
                     ORDER BY updated_at ASC,effect_id ASC
                     LIMIT 1
                    """
                ).fetchone()
            finally:
                con.close()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        try:
            observed = dt.datetime.fromisoformat(str(row[2]))
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=dt.timezone.utc)
            age = max(
                0.0,
                (dt.datetime.now(dt.timezone.utc) - observed.astimezone(dt.timezone.utc)).total_seconds(),
            )
        except (TypeError, ValueError):
            return None
        return {
            "effect_id": str(row[0]),
            "organ_id": str(row[1]),
            "updated_at": str(row[2]),
            "age_seconds": age,
        }

    def watch_relay_stall(self) -> None:
        relay = self.procs.get("relay")
        if relay is None or relay.poll() is not None:
            return
        dispatch = self.oldest_host_dispatch()
        if dispatch is None or float(dispatch["age_seconds"]) <= self.host_relay_stall_seconds:
            return

        mono = time.monotonic()
        if self.relay_stall_pid != relay.pid:
            try:
                os.killpg(relay.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            self.relay_stall_pid = relay.pid
            self.relay_stall_signal_at = mono
            self.relay_stall_kill_count += 1
            self.last_relay_stall = {
                **dispatch,
                "detected_at": now(),
                "signal": "SIGTERM",
                "automatic_replay": False,
            }
            return

        if self.relay_stall_signal_at is not None and mono - self.relay_stall_signal_at >= STALL_TERM_GRACE_SECONDS:
            try:
                os.killpg(relay.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
            self.last_relay_stall = {
                **dispatch,
                "detected_at": self.last_relay_stall.get("detected_at") if self.last_relay_stall else now(),
                "escalated_at": now(),
                "signal": "SIGKILL",
                "automatic_replay": False,
            }

    def snapshot(self) -> None:
        mono = time.monotonic()
        children: dict[str, dict[str, Any]] = {}
        for name in CHILDREN:
            proc = self.procs.get(name)
            restart_at = self.restart_after.get(name)
            children[name] = {
                "pid": proc.pid if proc else None,
                "returncode": proc.poll() if proc else self.last_exit_code.get(name),
                "alive": bool(proc and proc.poll() is None),
                "restart_count": self.restart_count.get(name, 0),
                "restart_in_seconds": max(0.0, restart_at - mono) if restart_at is not None else None,
            }
        payload = {
            "schema": "OMEGA_SUPERVISOR_STATUS/v3",
            "transport_boundary": "OUTER_SPOOL",
            "relay_mode": "BOUNDED_NONBLOCKING_CRASH_GUARDED",
            "updated_at": now(),
            "pid": os.getpid(),
            "repo_root": str(self.repo_root),
            "assembly_preflight": str(self.assembly_preflight_path),
            "children": children,
            "relay_watchdog": {
                "host_stall_seconds": self.host_relay_stall_seconds,
                "current_oldest_host_dispatch": self.oldest_host_dispatch(),
                "kill_count": self.relay_stall_kill_count,
                "last_stall": self.last_relay_stall,
            },
        }
        tmp = self.status_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.status_path)

    def terminate(self) -> None:
        self.stop = True
        for proc in self.procs.values():
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and any(p.poll() is None for p in self.procs.values()):
            time.sleep(0.2)
        for proc in self.procs.values():
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        for h in self.log_handles.values():
            try:
                h.close()
            except Exception:
                pass

    def run(self) -> int:
        lock_path = self.runtime_root / "omega-supervisor.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = open(lock_path, "w", encoding="utf-8")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("OMEGA supervisor already active", file=sys.stderr)
            return 3
        lock.write(str(os.getpid()))
        lock.flush()

        preflight = self.assembly_preflight()
        if not preflight.get("preflight_ok"):
            print("OMEGA assembly preflight failed closed", file=sys.stderr)
            lock.close()
            return 4

        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop", True))
        signal.signal(signal.SIGINT, lambda *_: setattr(self, "stop", True))
        for name in CHILDREN:
            self.spawn(name)
        try:
            while not self.stop:
                for name, proc in list(self.procs.items()):
                    if proc.poll() is not None:
                        self.note_exit(name, proc)
                self.watch_relay_stall()
                mono = time.monotonic()
                for name, restart_at in list(self.restart_after.items()):
                    if mono >= restart_at and not self.stop:
                        self.spawn(name)
                self.snapshot()
                time.sleep(1.0)
        finally:
            self.terminate()
            self.snapshot()
            lock.close()
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/omega_runtime/current"))
    a = ap.parse_args()
    return Supervisor(Path(a.runtime_root), Path(a.repo_root)).run()


if __name__ == "__main__":
    raise SystemExit(main())
