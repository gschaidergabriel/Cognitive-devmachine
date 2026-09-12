from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .unified_store import now


CHILDREN = {
    "grid": [sys.executable, "-m", "omega.grid_runtime_v3"],
    "relay": [sys.executable, "-m", "omega.bridge_relay"],
    "telemetry": [sys.executable, "-m", "omega.telemetry_daemon"],
    "master_bridge": [sys.executable, "-m", "omega.master_bridge_carrier"],
}


class Supervisor:
    def __init__(self, runtime_root: Path, repo_root: Path) -> None:
        self.runtime_root = runtime_root
        self.repo_root = repo_root
        self.logs = runtime_root / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.status_path = runtime_root / "SUPERVISOR_STATUS.json"
        self.procs: dict[str, subprocess.Popen[Any]] = {}
        self.log_handles: dict[str, Any] = {}
        self.stop = False

    def child_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": str(self.repo_root),
            "OMEGA_RUNTIME_ROOT": str(self.runtime_root),
            "OMEGA_REPO_ROOT": str(self.repo_root),
            "OMEGA_UNIFIED_DB": str(self.runtime_root.parent / "data" / "omega_unified.db"),
            "OMEGA_ROUTER_CONFIG": str(self.repo_root / "config" / "organ_router.json"),
            "OMEGA_AUTONOMY_POLICY": str(self.repo_root / "config" / "autonomy_policy.json"),
            "OMEGA_CARRIER_REPO": str(self.runtime_root.parent / "carrier_repo"),
        })
        return env

    def spawn(self, name: str) -> None:
        log = open(self.logs / f"{name}.log", "a", encoding="utf-8", buffering=1)
        self.log_handles[name] = log
        proc = subprocess.Popen(
            CHILDREN[name], cwd=self.repo_root, env=self.child_env(),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
        self.procs[name] = proc

    def snapshot(self) -> None:
        payload = {
            "schema": "OMEGA_SUPERVISOR_STATUS/v1",
            "updated_at": now(),
            "pid": os.getpid(),
            "repo_root": str(self.repo_root),
            "children": {
                name: {"pid": p.pid, "returncode": p.poll(), "alive": p.poll() is None}
                for name, p in self.procs.items()
            },
        }
        tmp = self.status_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.status_path)

    def terminate(self) -> None:
        self.stop = True
        for proc in self.procs.values():
            if proc.poll() is None:
                try: os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError: pass
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and any(p.poll() is None for p in self.procs.values()):
            time.sleep(0.2)
        for proc in self.procs.values():
            if proc.poll() is None:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError: pass
        for h in self.log_handles.values():
            try: h.close()
            except Exception: pass

    def run(self) -> int:
        lock_path = self.runtime_root / "omega-supervisor.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = open(lock_path, "w", encoding="utf-8")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("OMEGA supervisor already active", file=sys.stderr)
            return 3
        lock.write(str(os.getpid())); lock.flush()
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop", True))
        signal.signal(signal.SIGINT, lambda *_: setattr(self, "stop", True))
        for name in CHILDREN: self.spawn(name)
        try:
            while not self.stop:
                for name, proc in list(self.procs.items()):
                    rc = proc.poll()
                    if rc is not None:
                        try: self.log_handles[name].close()
                        except Exception: pass
                        # Bounded restart delay prevents crash loops from consuming CPU.
                        time.sleep(2.0)
                        self.spawn(name)
                self.snapshot()
                time.sleep(5.0)
        finally:
            self.terminate(); self.snapshot(); lock.close()
        return 0


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--runtime-root",default=os.getenv("OMEGA_RUNTIME_ROOT","/workspace/omega_runtime/state")); ap.add_argument("--repo-root",default=os.getenv("OMEGA_REPO_ROOT","/workspace/omega_runtime/current")); a=ap.parse_args()
    return Supervisor(Path(a.runtime_root),Path(a.repo_root)).run()


if __name__ == "__main__":
    raise SystemExit(main())
