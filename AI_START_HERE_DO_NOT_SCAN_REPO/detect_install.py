#!/usr/bin/env python3
"""Bounded Project Frankenstein installer/capability detector.

No network. No provider credential lookup. No repository-wide scan.
Starts from this file, discovers the repository by walking parents, inspects a
small declared file set, optionally performs a local write/readback/remove
probe, and emits JSON. It never reports NATIVE merely because a CLI exists.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
KNOWN_SENTINELS = (
    "CLAY_EXECUTION_AUTHORITY.md",
    "research_entity",
    "AI_START_HERE_DO_NOT_SCAN_REPO",
)
HOST_COMMANDS = {
    "claude_code": ("claude",),
    "codex_cli": ("codex",),
    "hermes_agent": ("hermes", "hermes-agent", "hermes_agent"),
}


def discover_repo_root() -> Path:
    for candidate in (HERE.parent, *HERE.parents):
        hits = 0
        for sentinel in KNOWN_SENTINELS:
            if (candidate / sentinel).exists():
                hits += 1
        if (candidate / ".git").exists() or hits >= 2:
            return candidate
    raise RuntimeError("repo root not found from installer location")


def command_path(candidates: tuple[str, ...]) -> str | None:
    for command in candidates:
        found = shutil.which(command)
        if found:
            return found
    return None


def git_probe(root: Path) -> dict[str, Any]:
    git = shutil.which("git")
    if not git:
        return {"available": False}
    try:
        proc = subprocess.run(
            [git, "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return {
            "available": True,
            "returncode": proc.returncode,
            "repo_bound": proc.returncode == 0 and Path(proc.stdout.strip()).resolve() == root.resolve(),
        }
    except Exception as exc:  # detector must report, not crash
        return {"available": True, "repo_bound": False, "error": type(exc).__name__}


def write_readback_probe(root: Path) -> dict[str, Any]:
    probe_dir = root / ".frankenstein_install_probe"
    probe_dir.mkdir(exist_ok=True)
    fd, raw_path = tempfile.mkstemp(prefix="probe_", suffix=".json", dir=probe_dir)
    path = Path(raw_path)
    payload = {
        "schema": "FRANKENSTEIN_INSTALL_WRITE_PROBE/v1",
        "nonce": os.urandom(16).hex(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        reopened = json.loads(path.read_text(encoding="utf-8"))
        ok = reopened == payload
        return {"attempted": True, "write_readback_verified": ok}
    finally:
        try:
            path.unlink(missing_ok=True)
            probe_dir.rmdir()
        except OSError:
            # cleanup failure is reported by residue, not silently promoted
            pass


def read_supervisor_state(root: Path) -> dict[str, Any]:
    path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    if not path.is_file():
        return {"present": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "parsed": False, "error": type(exc).__name__}
    free_only = data.get("free_only") if isinstance(data.get("free_only"), dict) else {}
    return {
        "present": True,
        "parsed": True,
        "schema_version": data.get("schema_version"),
        "provider_routes_admitted": free_only.get("provider_routes_admitted"),
        "free_swarm_owner_emergency_stop": free_only.get("free_swarm_owner_emergency_stop"),
        "together_forbidden": free_only.get("together_forbidden"),
        "no_paid_fallback": free_only.get("no_paid_fallback"),
    }


def base_host_detection(root: Path) -> dict[str, Any]:
    return {
        "claude_code": {
            "command": command_path(HOST_COMMANDS["claude_code"]),
            "project_instruction_file": (root / "CLAUDE.md").is_file(),
            "project_directory": (root / ".claude").is_dir(),
        },
        "codex_cli": {
            "command": command_path(HOST_COMMANDS["codex_cli"]),
            "project_instruction_file": (root / "AGENTS.md").is_file(),
        },
        "hermes_agent": {
            "command": command_path(HOST_COMMANDS["hermes_agent"]),
        },
        "web_hosts": {
            "chatgpt_web": "NOT_LOCALLY_DETECTABLE",
            "claude_web": "NOT_LOCALLY_DETECTABLE",
            "grok_web": "NOT_LOCALLY_DETECTABLE",
        },
    }


def classify(report: dict[str, Any]) -> str:
    # This detector deliberately cannot prove a real host lifecycle hook fired.
    # Therefore it never emits NATIVE by itself.
    if not report["repo"]["minimum_files_present"]:
        return "BLOCKED"
    if report.get("write_probe", {}).get("write_readback_verified"):
        any_cli = any(
            report["hosts"][name].get("command")
            for name in ("claude_code", "codex_cli", "hermes_agent")
        )
        return "ADAPTED" if any_cli else "DEGRADED"
    return "DEGRADED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--probe-write",
        action="store_true",
        help="perform bounded local create+fsync+reopen+delete proof inside repo",
    )
    args = parser.parse_args()

    try:
        root = discover_repo_root()
    except RuntimeError as exc:
        print(json.dumps({"schema": "FRANKENSTEIN_INSTALL_DETECTION/v1", "classification": "BLOCKED", "error": str(exc)}))
        return 2

    minimum = [
        root / "CLAY_EXECUTION_AUTHORITY.md",
        root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        root / "AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json",
    ]
    report: dict[str, Any] = {
        "schema": "FRANKENSTEIN_INSTALL_DETECTION/v1",
        "repo": {
            "root": str(root),
            "minimum_files_present": all(path.exists() for path in minimum),
            "git": git_probe(root),
        },
        "hosts": base_host_detection(root),
        "authority": read_supervisor_state(root),
        "write_probe": {"attempted": False},
        "proof_limits": [
            "CLI presence does not prove host loaded project instructions",
            "this detector does not prove a native lifecycle hook fired",
            "this detector performs no provider/network/credential probe",
            "NATIVE requires a separate real host-hook/state/effect receipt",
        ],
    }
    if args.probe_write:
        try:
            report["write_probe"] = write_readback_probe(root)
        except Exception as exc:
            report["write_probe"] = {"attempted": True, "write_readback_verified": False, "error": type(exc).__name__}

    report["classification"] = classify(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["classification"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
