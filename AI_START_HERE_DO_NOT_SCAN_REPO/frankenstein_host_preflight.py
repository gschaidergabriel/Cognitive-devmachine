#!/usr/bin/env python3
"""Read-only Triggerword-3 host/repository preflight.

This tool deliberately performs no network access, provider calls, secret lookup,
repository mutation, lifecycle-hook firing, durable-state write, or real effect.
Therefore it can establish at most DEGRADED integration readiness. NATIVE and
ADAPTED require separate executable host-specific witnesses.
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
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)
INBOX_RELATIVE_PATH = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

UNVERIFIED_EXECUTABLE_BOUNDARIES = (
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
    """Resolve the inbox-selected steering file while rejecting path escape."""
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


def resolve_dynamic_steering(root: Path) -> dict[str, Any]:
    """Compatibility view for callers of the v1 helper name."""
    state = resolve_inbox_and_steering(root)
    return {
        "verified": state["verified"],
        "pointer": state["steering_pointer"],
        "resolved_path": state["steering_path"],
        "reason": state["reason"],
    }


def provider_action_class(inbox: dict[str, Any] | None) -> tuple[str, str]:
    """Classify provider orchestration only from explicit current inbox fields."""
    if not isinstance(inbox, dict):
        return "BLOCKED", "CURRENT_AUTHORITY_UNRESOLVED"
    free_only = inbox.get("free_only")
    if not isinstance(free_only, dict):
        return "BLOCKED", "FREE_ONLY_AUTHORITY_BLOCK_MISSING"
    if free_only.get("free_swarm_owner_emergency_stop") is True:
        return "BLOCKED", "FREE_SWARM_OWNER_EMERGENCY_STOP"
    if free_only.get("provider_routes_admitted") is not True:
        return "BLOCKED", "PROVIDER_ROUTES_NOT_EXPLICITLY_ADMITTED"
    if free_only.get("no_paid_fallback") is not True:
        return "BLOCKED", "NO_PAID_FALLBACK_NOT_EXPLICIT"
    if free_only.get("together_forbidden") is not True:
        return "BLOCKED", "TOGETHER_FORBIDDEN_NOT_EXPLICIT"
    return "DEGRADED", "SOURCE_AUTHORITY_APPEARS_OPEN_BUT_EXECUTION_NOT_PROBED"


def repository_preflight_class(
    root: Path | None,
    authority_files_present: dict[str, bool],
    authority_verified: bool,
    git_verified: bool,
) -> tuple[str, str]:
    """Read-only preflight may return only BLOCKED or DEGRADED."""
    if root is None:
        return "BLOCKED", "REPOSITORY_ROOT_UNRESOLVED"
    if not all(authority_files_present.values()):
        return "BLOCKED", "REQUIRED_AUTHORITY_FILE_MISSING"
    if not authority_verified:
        return "BLOCKED", "CURRENT_STEERING_AUTHORITY_UNRESOLVED"
    if not git_verified:
        return "DEGRADED", "AUTHORITY_READABLE_BUT_GIT_IDENTITY_UNVERIFIED"
    return "DEGRADED", "READ_ONLY_PREFLIGHT_CANNOT_PROVE_LIFECYCLE_STATE_OR_EFFECTS"


def classify(
    root: Path | None,
    authority_present: dict[str, bool],
    git_ok: bool,
    steering_verified: bool,
) -> str:
    """Compatibility wrapper; intentionally cannot mint NATIVE or ADAPTED."""
    status, _ = repository_preflight_class(
        root, authority_present, steering_verified, git_ok
    )
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="Known repository root; otherwise search upward from cwd. Never guess Downloads/home/CWD clone paths.",
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

    result: dict[str, Any] = {
        "schema": "FRANKENSTEIN_HOST_PREFLIGHT/v3",
        "mode": "READ_ONLY_NO_NETWORK_NO_SECRETS_NO_WRITES",
        "root": str(root) if root else None,
        "markers": {m: bool(root and (root / m).exists()) for m in MARKERS},
        "authority_files": authority_files_present,
        "authority": {
            key: value for key, value in authority.items() if key != "inbox"
        },
        "capabilities": {
            "can_read_files": bool(root and os.access(root, os.R_OK)),
            "repo_path_writable_by_os": bool(root and os.access(root, os.W_OK)),
            "repo_write_was_tested": False,
            "can_run_local_commands": True,
            "git_binary_present": shutil.which("git") is not None,
            "git_repo_verified": git_verified,
            "can_access_github": "NOT_PROBED",
            "cross_session_durable_state": "NOT_PROBED",
            "external_network": "NOT_PROBED",
            "package_installation": "NOT_PROBED",
            "lifecycle_hook_firing": "NOT_PROBED",
            "effect_or_result_receipt": "NOT_PROBED",
        },
        "git": {
            "head": git_head,
            "dirty": git_dirty,
            "root_matches": git_root_matches,
            "error": git_error,
        },
        "repository_preflight": {"class": repo_class, "reason": repo_reason},
        "provider_orchestration": {
            "class": provider_class,
            "reason": provider_reason,
            "execution_probed": False,
        },
        "installation_class": repo_class,
        "native_or_adapted_possible_from_this_preflight": False,
        "executable_boundaries_unverified": list(UNVERIFIED_EXECUTABLE_BOUNDARIES),
        "promotion_fence": (
            "Read-only repository/authority/Git evidence cannot mint NATIVE or ADAPTED. "
            "Those classes require host-specific executable lifecycle/state/effect witnesses."
        ),
        "credit_boundary": (
            "This preflight grants zero provider-runtime, whole EntityOS/HCU, full HCU, "
            "physical-grid, Global J-Space, model, canonical-semantics, or training credit."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if repo_class == "DEGRADED" else 2


if __name__ == "__main__":
    sys.exit(main())
