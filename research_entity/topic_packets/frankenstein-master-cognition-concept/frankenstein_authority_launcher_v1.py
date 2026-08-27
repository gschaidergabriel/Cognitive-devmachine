#!/usr/bin/env python3
"""Canonical fail-closed launcher for the provider-capable Frankenstein roles.

This launcher exists because the original 2026-08-27 Bauleiter and Bugfix
scripts import provider-capable fallback code directly. Under supervisor
9.13 HARD_OFF they are quarantined and MUST NOT be invoked directly.

The launcher performs the repository's canonical provider-authority gate in a
separate standard-library subprocess before importing or executing either
target. Any blocked, missing, stale, malformed, timed-out, or otherwise
ambiguous gate result stops with exit 77 and an explicit zero-boundary receipt.

No credential lookup, provider SDK import, network request, Aider invocation,
provider-model selection, or target import occurs on the blocked path.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_PATH = REPO_ROOT / "tools" / "freepool_fallback_provider_gate_v1.py"
TARGETS = {
    "bauleiter": Path(__file__).resolve().parent / "frankenstein_orchestrator_v1.py",
    "bugfix": Path(__file__).resolve().parent / "frankenstein_bugfix_v1.py",
}
BLOCK_EXIT = 77
GATE_TIMEOUT_SECONDS = 30.0


def _run_gate() -> tuple[int, dict[str, Any], str]:
    """Run the canonical gate without importing any provider-capable target."""
    try:
        proc = subprocess.run(
            [sys.executable, str(GATE_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BLOCK_EXIT, {
            "admitted": False,
            "reason": f"GATE_EXECUTION_FAILED:{type(exc).__name__}",
        }, str(exc)

    try:
        record = json.loads((proc.stdout or "").strip())
        if not isinstance(record, dict):
            raise ValueError("gate output root is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        record = {
            "admitted": False,
            "reason": f"MALFORMED_GATE_OUTPUT:{type(exc).__name__}",
        }
    return proc.returncode, record, proc.stderr or ""


def _blocked_receipt(mode: str, gate_rc: int, gate_record: dict[str, Any], gate_stderr: str) -> dict[str, Any]:
    return {
        "schema": "FRANKENSTEIN_AUTHORITY_LAUNCH_RECEIPT/v1",
        "mode": mode,
        "admitted": False,
        "reason": gate_record.get("reason", "UNKNOWN_OR_MALFORMED_GATE_RESULT"),
        "gate_returncode": gate_rc,
        "gate_schema": gate_record.get("schema"),
        "authority_schema_version": gate_record.get("authority_schema_version")
        or gate_record.get("schema_version"),
        "runtime_provider_authority": gate_record.get("runtime_provider_authority"),
        "required_caller_behavior": "STOP_BEFORE_SECRET_LOOKUP_PROVIDER_IMPORT_NETWORK_OR_AIDER_FALLBACK",
        "provider_calls": 0,
        "secret_lookups": 0,
        "target_imports": 0,
        "target_processes_started": 0,
        "gate_stderr_present": bool(gate_stderr.strip()),
    }


def _exec_target(mode: str, target_args: list[str]) -> None:
    """Replace this process with the target only after explicit admission."""
    target = TARGETS[mode]
    if not target.is_file():
        raise FileNotFoundError(f"Frankenstein target missing: {target}")
    os.execv(sys.executable, [sys.executable, str(target), *target_args])


def launch(mode: str, target_args: list[str]) -> int:
    gate_rc, gate_record, gate_stderr = _run_gate()
    admitted = gate_rc == 0 and gate_record.get("admitted") is True
    if not admitted:
        print(json.dumps(_blocked_receipt(mode, gate_rc, gate_record, gate_stderr), sort_keys=True))
        return BLOCK_EXIT

    admission = {
        "schema": "FRANKENSTEIN_AUTHORITY_LAUNCH_ADMISSION/v1",
        "mode": mode,
        "admitted": True,
        "reason": gate_record.get("reason"),
        "authority_schema_version": gate_record.get("authority_schema_version")
        or gate_record.get("schema_version"),
        "runtime_provider_authority": gate_record.get("runtime_provider_authority"),
        "boundary": "TARGET_EXECUTION_ALLOWED_ONLY_AFTER_THIS_GATE",
    }
    print(json.dumps(admission, sort_keys=True), flush=True)
    _exec_target(mode, target_args)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed authority launcher for Frankenstein Bauleiter/Bugfix roles."
    )
    parser.add_argument("mode", choices=sorted(TARGETS))
    parser.add_argument(
        "target_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the target after an optional '--' separator.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    target_args = list(args.target_args)
    if target_args[:1] == ["--"]:
        target_args = target_args[1:]
    return launch(args.mode, target_args)


if __name__ == "__main__":
    raise SystemExit(main())
