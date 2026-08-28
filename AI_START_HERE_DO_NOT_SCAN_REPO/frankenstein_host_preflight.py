#!/usr/bin/env python3
"""Read-only Triggerword-3 host/repository preflight.

Purpose: prove only what can be proved without network access, secret lookup,
provider calls, repository mutation, hook firing, persistent-state writes, or
real effects. Because those lifecycle claims are deliberately not exercised,
this preflight can never classify an integration as NATIVE or ADAPTED by
itself.
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

MARKERS = ("research_entity", "the artefact", "AI_START_HERE_DO_NOT_SCAN_REPO")
AUTHORITY_FILES = (
    "CLAY_EXECUTION_AUTHORITY.md",
    "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
    "research_entity/rooms/PROGRAM_STATE.json",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)
INBOX_RELATIVE_PATH = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"


def is_repo_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in MARKERS)


def find_root(start: Path) -> Path | None:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if is_repo_root(candidate):
            return candidate
    return None


def _run_git(root: Path, *args: str) -> tuple[bool, str]:
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


def resolve_inbox_and_steering(root: Path) -> dict[str, Any]:
    """Resolve current inbox and its steering pointer, rejecting path escape."""
    repo_root = root.resolve()
    inbox_path = repo_root / INBOX_RELATIVE_PATH
    try:
        inbox = json.loads(inbox_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "verified": False,
            "inbox_path": str(inbox_path),
            "steering_pointer": None,
            "steering_path": None,
            "reason": f"INBOX_UNREADABLE:{type(exc).__name__}",
            "inbox": None,
        }

    pointer = inbox.get("steering")
    if not isinstance(pointer, str) or not pointer.strip():
        return {
            "verified": False,
            "inbox_path": str(inbox_path),
            "steering_pointer": pointer,
            "steering_path": None,
            "reason": "STEERING_POINTER_MISSING_OR_INVALID",
            "inbox": inbox,
        }

    rel = Path(pointer)
    if rel.is_absolute():
        return {
            "verified": False,
            "inbox_path": str(inbox_path),
            "steering_pointer": pointer,
            "steering_path": None,
            "reason": "STEERING_POINTER_ABSOLUTE_REJECTED",
            "inbox": inbox,
        }

    steering_path = (repo_root / rel).resolve()
    try:
        steering_path.relative_to(repo_root)
    except ValueError:
        return {
            "verified": False,
            "inbox_path": str(inbox_path),
            "steering_pointer": pointer,
            "steering_path": str(steering_path),
            "reason": "STEERING_POINTER_ESCAPES_REPOSITORY",
            "inbox": inbox,
        }

    if not steering_path.is_file():
        return {
            "verified": False,
            "inbox_path": str(inbox_path),
            "steering_pointer": pointer,
            "steering_path": str(steering_path),
            "reason": "STEERING_TARGET_MISSING",
            "inbox": inbox,
        }

    return {
        "verified": True,
        "inbox_path": str(inbox_path),
        "steering_pointer": pointer,
        "steering_path": str(steering_path),
        "reason": "OK",
        "inbox": inbox,
    }


def provider_action_class(inbox: dict[str, Any] | None) -> tuple[str, str]:
    """Classify provider orchestration strictly from explicit current inbox fields."""
    if not isinstance(inbox, dict):
        return "BLOCKED", "CURRENT_AUTHORITY_UNRESOLVED"
    free_only = inbox.get("free_only")
    if not isinstance(free_only, dict):
        return "BLOCKED", "FREE_ONLY_AUTHORITY_BLOCK_MISSING"
    if free_only.get("free_swarm_owner_emergency_stop") is True:
        return "BLOCKED", "FREE_SWARM_OWNER_EMERGENCY_STOP"
    if free_only.get("provider_routes_admitted") is not True:
        return "BLOCKED", "PROVIDER_ROUTES_NOT_EXPLICITLY_ADMITTED"
    # This read-only preflight still does not prove provider execution safety.
    return "DEGRADED", "SOURCE_AUTHORITY_APPEARS_OPEN_BUT_EXECUTION_NOT_PROBED"


def repository_preflight_class(
    root: Path | None,
    authority_files_present: dict[str, bool],
    authority_verified: bool,
    git_verified: bool,
) -> tuple[str, str]:
    """Return only BLOCKED or DEGRADED; read-only probing cannot prove NATIVE/ADAPTED."""
    if root is None:
        return "BLOCKED", "REPOSITORY_ROOT_UNRESOLVED"
    if not all(authority_files_present.values()):
        return "BLOCKED", "REQUIRED_AUTHORITY_FILE_MISSING"
    if not authority_verified:
        return "BLOCKED", "CURRENT_STEERING_AUTHORITY_UNRESOLVED"
    if not git_verified:
        return "DEGRADED", "AUTHORITY_READABLE_BUT_GIT_IDENTITY_UNVERIFIED"
    return "DEGRADED", "READ_ONLY_PREFLIGHT_CANNOT_PROVE_LIFECYCLE_STATE_OR_EFFECTS"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="Known repository root; otherwise search from cwd upward. No guessed home/Downloads path.",
    )
    args = parser.parse_args()

    root = args.root.resolve() if args.root else find_root(Path.cwd())
    if root is not None and not is_repo_root(root):
        root = None

    authority_files_present = {
        path: bool(root and (root / path).is_file()) for path in AUTHORITY_FILES
    }
    authority = (
        resolve_inbox_and_steering(root)
        if root is not None
        else {
            "verified": False,
            "inbox_path": None,
            "steering_pointer": None,
            "steering_path": None,
            "reason": "REPOSITORY_ROOT_UNRESOLVED",
            "inbox": None,
        }
    )

    git_verified = False
    git_head = None
    git_dirty = None
    git_root_matches = None
    git_error = None
    if root is not None:
        ok_root, value_root = _run_git(root, "rev-parse", "--show-toplevel")
        if ok_root:
            try:
                git_root_matches = Path(value_root).resolve() == root.resolve()
            except OSError:
                git_root_matches = False
        else:
            git_error = value_root

        ok_head, value_head = _run_git(root, "rev-parse", "HEAD")
        if ok_head:
            git_head = value_head
        elif git_error is None:
            git_error = value_head

        ok_status, value_status = _run_git(root, "status", "--porcelain")
        if ok_status:
            git_dirty = bool(value_status)
        elif git_error is None:
            git_error = value_status

        git_verified = bool(ok_root and git_root_matches and ok_head and ok_status)

    repo_class, repo_reason = repository_preflight_class(
        root,
        authority_files_present,
        bool(authority["verified"]),
        git_verified,
    )
    provider_class, provider_reason = provider_action_class(authority.get("inbox"))

    inbox = authority.get("inbox") or {}
    free_only = inbox.get("free_only") if isinstance(inbox, dict) else None
    free_only = free_only if isinstance(free_only, dict) else {}

    result: dict[str, Any] = {
        "schema": "FRANKENSTEIN_HOST_PREFLIGHT/v3",
        "mode": "READ_ONLY_NO_NETWORK_NO_SECRETS_NO_WRITES_NO_EFFECTS",
        "root": str(root) if root else None,
        "markers": {m: bool(root and (root / m).exists()) for m in MARKERS},
        "authority_files": authority_files_present,
        "authority": {
            "verified": bool(authority["verified"]),
            "reason": authority["reason"],
            "inbox_path": authority["inbox_path"],
            "steering_pointer": authority["steering_pointer"],
            "steering_path": authority["steering_path"],
            "schema_version": inbox.get("schema_version"),
            "supervisor_delta": inbox.get("supervisor_delta"),
        },
        "git": {
            "binary_present": shutil.which("git") is not None,
            "verified": git_verified,
            "root_matches": git_root_matches,
            "head": git_head,
            "dirty": git_dirty,
            "error": git_error,
        },
        "observed_capabilities": {
            "filesystem_readable": bool(root and os.access(root, os.R_OK)),
            "filesystem_write_permission_hint": bool(root and os.access(root, os.W_OK)),
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "lifecycle_hooks_verified": False,
            "durable_cross_session_state_verified": False,
            "effect_result_reentry_verified": False,
            "external_network_probed": False,
            "secret_lookup_performed": False,
        },
        "repository_entry": {
            "classification": repo_class,
            "reason": repo_reason,
            "final_native_or_adapted_claim_allowed": False,
        },
        "provider_orchestration": {
            "classification": provider_class,
            "reason": provider_reason,
            "provider_routes_admitted": free_only.get("provider_routes_admitted"),
            "together_forbidden": free_only.get("together_forbidden"),
            "free_swarm_owner_emergency_stop": free_only.get("free_swarm_owner_emergency_stop"),
            "remaining_together_paid_runs_authorized": free_only.get(
                "remaining_together_paid_runs_authorized"
            ),
        },
        "promotion_boundary": (
            "This tool is a read-only preflight. NATIVE or ADAPTED requires separate observed "
            "host-specific proof of the claimed lifecycle/state/effect mechanism."
        ),
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if repo_class == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
