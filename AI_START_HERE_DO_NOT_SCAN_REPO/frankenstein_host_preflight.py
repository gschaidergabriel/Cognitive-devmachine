#!/usr/bin/env python3
"""Read-only Triggerword-3 host/repository capability preflight.

No network calls. No provider calls. No secret lookup. No repository writes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

MARKERS = ("research_entity", "the artefact")
AUTHORITY_FILES = (
    "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
    "research_entity/rooms/PROGRAM_STATE.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)


def is_repo_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in MARKERS)


def find_root(start: Path) -> Path | None:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if is_repo_root(candidate):
            return candidate
    return None


def run_git(root: Path, *args: str) -> tuple[bool, str]:
    if shutil.which("git") is None:
        return False, "git_not_found"
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"git_error:{type(exc).__name__}"
    if proc.returncode != 0:
        return False, proc.stderr.strip()[:500] or f"git_exit_{proc.returncode}"
    return True, proc.stdout.strip()


def classify(root: Path | None, authority_present: dict[str, bool], git_ok: bool) -> str:
    if root is None:
        return "BLOCKED"
    if all(authority_present.values()) and git_ok:
        return "NATIVE"
    if all(authority_present.values()):
        return "ADAPTED"
    return "DEGRADED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, help="Known repository root; otherwise search from cwd upward")
    args = parser.parse_args()

    root = args.root.resolve() if args.root else find_root(Path.cwd())
    if root is not None and not is_repo_root(root):
        root = None

    authority_present = {
        path: bool(root and (root / path).is_file()) for path in AUTHORITY_FILES
    }

    git_ok = False
    git_head = None
    git_dirty = None
    if root is not None:
        ok, value = run_git(root, "rev-parse", "HEAD")
        git_ok = ok
        git_head = value if ok else None
        if ok:
            status_ok, status_value = run_git(root, "status", "--porcelain")
            git_dirty = bool(status_value) if status_ok else None

    result: dict[str, Any] = {
        "schema": "FRANKENSTEIN_HOST_PREFLIGHT/v1",
        "mode": "READ_ONLY_NO_NETWORK_NO_SECRETS",
        "root": str(root) if root else None,
        "markers": {m: bool(root and (root / m).exists()) for m in MARKERS},
        "authority_files": authority_present,
        "capabilities": {
            "can_read_files": bool(root and os.access(root, os.R_OK)),
            "can_write_repo": bool(root and os.access(root, os.W_OK)),
            "can_run_local_commands": True,
            "git_binary_present": shutil.which("git") is not None,
            "git_repo_verified": git_ok,
            "can_access_github": "NOT_PROBED",
            "can_persist_state": "NOT_PROBED",
            "can_call_external_network": "NOT_PROBED",
            "can_install_packages": "NOT_PROBED",
            "can_receive_hooks_events": "NOT_PROBED"
        },
        "git": {"head": git_head, "dirty": git_dirty},
        "installation_class": classify(root, authority_present, git_ok),
        "next": (
            "Read current authority and task-relevant source only."
            if root and all(authority_present.values())
            else "Resolve missing repository/authority surfaces before execution claims."
        )
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["installation_class"] != "BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
