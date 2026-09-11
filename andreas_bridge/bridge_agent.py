#!/usr/bin/env python3
"""Frankenstein/ChatGPT <-> Andreas machine bridge executor.

Runs on the already registered Andreas self-hosted GitHub runner.
Requests are immutable JSON files in andreas_bridge/requests/.
Results are written to andreas_bridge/results/ and committed by the workflow.

Execution authority remains the self-hosted runner account. This program does not
read or export secrets and never serializes the process environment.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REQUESTS = ROOT / "requests"
RESULTS = ROOT / "results"
SCHEMA = "f2.andreas.bridge.request.v1"
RESULT_SCHEMA = "f2.andreas.bridge.result.v1"
MAX_OUTPUT = 200_000
MAX_TIMEOUT = 900


def _clip(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_OUTPUT:
        return value, False
    return value[:MAX_OUTPUT] + "\n...[truncated by bridge]...\n", True


def _result_path(request_id: str) -> Path:
    return RESULTS / f"{request_id}.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def _cwd(raw: Any) -> str:
    if raw in (None, "", "~"):
        return str(Path.home())
    return str(Path(str(raw)).expanduser().resolve())


def execute(path: Path) -> dict[str, Any]:
    started = time.time()
    req = _load(path)
    request_id = str(req.get("id") or path.stem)
    if request_id != path.stem:
        raise ValueError("request id must equal request filename stem")
    if req.get("schema") != SCHEMA:
        raise ValueError(f"unsupported schema: {req.get('schema')!r}")

    op = req.get("operation")
    cwd = _cwd(req.get("cwd"))
    timeout = min(max(int(req.get("timeout_seconds", 120)), 1), MAX_TIMEOUT)

    base: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "id": request_id,
        "request_file": str(path.relative_to(ROOT.parent)),
        "operation": op,
        "host": socket.gethostname(),
        "runner_user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "cwd": cwd,
        "started_unix": started,
    }

    if op == "exec":
        argv = req.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("exec requires non-empty string array 'argv'")
        completed = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        stdout, out_trunc = _clip(completed.stdout)
        stderr, err_trunc = _clip(completed.stderr)
        base.update({
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": out_trunc,
            "stderr_truncated": err_trunc,
            "ok": completed.returncode == 0,
        })
    elif op == "read_file":
        target = Path(str(req["path"])).expanduser().resolve()
        text = target.read_text(encoding="utf-8", errors="replace")
        text, trunc = _clip(text)
        base.update({"path": str(target), "content": text, "content_truncated": trunc, "ok": True})
    elif op == "list_dir":
        target = Path(str(req.get("path") or cwd)).expanduser().resolve()
        entries = []
        for item in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "dir" if item.is_dir() else "file" if item.is_file() else "other",
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                })
            except OSError as exc:
                entries.append({"name": item.name, "path": str(item), "error": type(exc).__name__})
        base.update({"path": str(target), "entries": entries[:5000], "entries_truncated": len(entries) > 5000, "ok": True})
    else:
        raise ValueError(f"unsupported operation: {op!r}")

    base["finished_unix"] = time.time()
    base["duration_seconds"] = round(base["finished_unix"] - started, 6)
    return base


def main() -> int:
    REQUESTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    pending = sorted(REQUESTS.glob("*.json"))
    if not pending:
        print("BRIDGE_NO_REQUESTS")
        return 0

    wrote = 0
    for request_path in pending:
        result_path = _result_path(request_path.stem)
        if result_path.exists():
            continue
        try:
            result = execute(request_path)
        except subprocess.TimeoutExpired as exc:
            result = {
                "schema": RESULT_SCHEMA,
                "id": request_path.stem,
                "ok": False,
                "error": "TimeoutExpired",
                "detail": str(exc),
                "host": socket.gethostname(),
                "finished_unix": time.time(),
            }
        except Exception as exc:
            result = {
                "schema": RESULT_SCHEMA,
                "id": request_path.stem,
                "ok": False,
                "error": type(exc).__name__,
                "detail": str(exc),
                "host": socket.gethostname(),
                "finished_unix": time.time(),
            }
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"BRIDGE_RESULT={result_path.name} OK={result.get('ok')}")
        wrote += 1

    print(f"BRIDGE_PROCESSED={wrote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
