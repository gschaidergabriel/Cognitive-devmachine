#!/usr/bin/env python3
"""Read-only Triggerword-3 host/repository capability preflight.

No network calls. No provider calls. No secret lookup. No repository writes.

This preflight can establish a repository/authority *adapter* surface. It cannot
establish NATIVE lifecycle integration because it deliberately does not trigger
or verify lifecycle hooks, cross-session durable state, or effect/result
receipts. Those boundaries require a host-specific witness produced or
independently verified by the claimed mechanism.
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
INBOX_RELATIVE_PATH = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

# These are intentionally not probed by this read-only preflight. Their absence
# from the probe is itself a promotion fence: no caller may upgrade ADAPTED to
# NATIVE from repo/authority/Git presence alone.
NATIVE_BOUNDARIES = (
    "real_lifecycle_hook_firing",
    "cross_session_durable_state_when_claimed",
    "effect_or_result_receipt_when_claimed",
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


def resolve_dynamic_steering(root: Path) -> dict[str, Any]:
    """Resolve the steering path selected by the current inbox, fail-closed."""
    repo_root = root.resolve()
    inbox_path = repo_root / INBOX_RELATIVE_PATH
    try:
        inbox = json.loads(inbox_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "verified": False,
            "pointer": None,
            "resolved_path": None,
            "reason": f"INBOX_UNREADABLE:{type(exc).__name__}",
        }

    pointer = inbox.get("steering")
    if not isinstance(pointer, str) or not pointer.strip():
        return {
            "verified": False,
            "pointer": pointer,
            "resolved_path": None,
            "reason": "STEERING_POINTER_MISSING_OR_INVALID",
        }

    pointer_path = Path(pointer)
    if pointer_path.is_absolute():
        return {
            "verified": False,
            "pointer": pointer,
            "resolved_path": None,
            "reason": "STEERING_POINTER_ABSOLUTE_REJECTED",
        }

    resolved = (repo_root / pointer_path).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        return {
            "verified": False,
            "pointer": pointer,
            "resolved_path": str(resolved),
            "reason": "STEERING_POINTER_ESCAPES_REPOSITORY",
        }

    present = resolved.is_file()
    return {
        "verified": present,
        "pointer": pointer,
        "resolved_path": str(resolved),
        "reason": "OK" if present else "STEERING_TARGET_MISSING",
    }


def classify(
    root: Path | None,
    authority_present: dict[str, bool],
    git_ok: bool,
    steering_verified: bool,
) -> str:
    """Classify only what this read-only preflight can actually establish.

    NATIVE is intentionally unreachable here. A repository with current
    authority and Git identity is an ADAPTED source/research integration until
    a host-specific lifecycle/state/effect witness is independently verified.
    """
    if root is None:
        return "BLOCKED"
    if all(authority_present.values()) and steering_verified and git_ok:
        return "ADAPTED"
    return "DEGRADED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        help="Known repository root; otherwise search from cwd upward",
    )
    args = parser.parse_args()

    root = args.root.resolve() if args.root else find_root(Path.cwd())
    if root is not None and not is_repo_root(root):
        root = None

    authority_present = {
        path: bool(root and (root / path).is_file()) for path in AUTHORITY_FILES
    }
    steering = (
        resolve_dynamic_steering(root)
        if root is not None
        else {
            "verified": False,
            "pointer": None,
            "resolved_path": None,
            "reason": "REPOSITORY_ROOT_UNRESOLVED",
        }
    )

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

    authority_ready = all(authority_present.values()) and bool(steering["verified"])
    installation_class = classify(
        root, authority_present, git_ok, bool(steering["verified"])
    )

    if root is None:
        next_action = "Resolve the repository root before any execution claim."
    elif not authority_ready:
        next_action = (
            "Resolve missing/current authority surfaces, including the "
            "inbox-selected steering file."
        )
    elif not git_ok:
        next_action = (
            "Verify the current Git repository/head; remain DEGRADED until that succeeds."
        )
    else:
        next_action = (
            "Repository/authority adapter preflight is satisfied. If NATIVE is claimed, "
            "run a host-specific witness for real lifecycle hook firing, required "
            "cross-session durable state, and claimed effect/result receipts."
        )

    result: dict[str, Any] = {
        "schema": "FRANKENSTEIN_HOST_PREFLIGHT/v2",
        "mode": "READ_ONLY_NO_NETWORK_NO_SECRETS_NO_WRITES",
        "root": str(root) if root else None,
        "markers": {m: bool(root and (root / m).exists()) for m in MARKERS},
        "authority_files": authority_present,
        "dynamic_steering": steering,
        "capabilities": {
            "can_read_files": bool(root and os.access(root, os.R_OK)),
            "repo_path_writable_by_os": bool(root and os.access(root, os.W_OK)),
            "repo_write_was_tested": False,
            "can_run_local_commands": True,
            "git_binary_present": shutil.which("git") is not None,
            "git_repo_verified": git_ok,
            "can_access_github": "NOT_PROBED",
            "cross_session_durable_state": "NOT_PROBED",
            "external_network": "NOT_PROBED",
            "package_installation": "NOT_PROBED",
            "lifecycle_hook_firing": "NOT_PROBED",
            "effect_or_result_receipt": "NOT_PROBED",
        },
        "git": {"head": git_head, "dirty": git_dirty},
        "installation_class": installation_class,
        "native_possible_from_this_preflight": False,
        "native_boundaries_unverified": list(NATIVE_BOUNDARIES),
        "promotion_fence": (
            "Repo/authority/Git presence can establish at most ADAPTED here. "
            "A boolean flag, model self-report, source/config presence, or manually "
            "asserted observation cannot establish NATIVE lifecycle integration."
        ),
        "credit_boundary": (
            "This preflight grants zero provider-runtime, whole EntityOS/HCU, full HCU, "
            "GRID10, Global J-Space, model, or training credit."
        ),
        "next": next_action,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if installation_class != "BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
