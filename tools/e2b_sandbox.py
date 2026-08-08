#!/usr/bin/env python3
"""E2B isolated sandbox adapter for FRANK/RAE.

The adapter uses the canonical RAE secret loader, injects E2B_API_KEY only into the
current process, creates an isolated E2B Linux sandbox, runs a command, and terminates
the sandbox. Secret values are never printed.

For ClayCode/compiler research prefer `run_python()` instead of manually constructing
`python3 -c` shell commands; it applies shell-safe quoting for multiline source.

Requires: pip install e2b
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret, secret_source  # noqa: E402


def _sdk():
    try:
        from e2b import Sandbox
    except ImportError as exc:
        raise RuntimeError("E2B SDK missing; install with: pip install e2b") from exc
    return Sandbox


def run_command(command: str, *, timeout: int = 30) -> dict:
    key = get_secret("E2B_API_KEY")
    os.environ["E2B_API_KEY"] = key
    Sandbox = _sdk()
    sandbox = None
    try:
        sandbox = Sandbox.create(timeout=60)
        result = sandbox.commands.run(command, timeout=timeout)
        return {
            "provider": "E2B",
            "tool": "e2b_sandbox",
            "evidence_class": "runtime_experiment",
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
        }
    finally:
        if sandbox is not None:
            try:
                sandbox.kill()
            except Exception:
                pass


def run_python(code: str, *, timeout: int = 30, args: list[str] | None = None) -> dict:
    """Execute multiline Python source safely in a fresh E2B sandbox."""
    if not code or len(code.encode("utf-8")) > 200_000:
        raise ValueError("Python code must be 1..200000 UTF-8 bytes")
    argv = "".join(" " + shlex.quote(str(arg)) for arg in (args or []))
    command = "python3 -c " + shlex.quote(code) + argv
    return run_command(command, timeout=timeout)


def smoke_test() -> dict:
    result = run_python("print('RAE_E2B_OK:' + str(6*7))")
    if result.get("exit_code") != 0 or result.get("stdout") != "RAE_E2B_OK:42\n":
        raise RuntimeError("E2B smoke test did not return expected output")
    return {
        "schema_version": "1.1",
        "provider": "E2B",
        "tool": "e2b_sandbox",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("E2B_API_KEY"),
        "credential_value_persisted_here": False,
        "verification_class": "isolated_multiline_python_execution",
        "test": "Python sentinel through run_python",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run code/commands in an isolated E2B sandbox")
    ap.add_argument("command", nargs="?", help="command or Python source to execute")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--python", action="store_true", help="treat command argument as multiline Python source")
    args = ap.parse_args()
    if args.smoke_test:
        out = smoke_test()
    else:
        if not args.command:
            ap.error("command is required unless --smoke-test is used")
        out = run_python(args.command, timeout=args.timeout) if args.python else run_command(args.command, timeout=args.timeout)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
