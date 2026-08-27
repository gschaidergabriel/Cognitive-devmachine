#!/usr/bin/env python3
"""Read-only Triggerword-3 host/repository capability preflight.

This tool deliberately performs no network/provider calls, secret lookup,
repository mutation, lifecycle-hook firing, persistent-state write, or real
effect. It can therefore establish only a bounded repository/authority
preflight. It must never mint NATIVE or ADAPTED installation status by itself.
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
    """Resolve the inbox-selected steering file without allowing path escape."""
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
            "inbox": None,
        }

    pointer = inbox.get("steering")
    if not isinstance(pointer, str) or not pointer.strip():
        return {
            "verified": False,
            "pointer": pointer,
            "resolved_path": None,
            "reason": "STEERING_POINTER_MISSING_OR_INVALID",
            "inbox": inbox,
        }

    pointer_path = Path(pointer)
    if pointer_path.is_absolute():
        return {
            "verified": False,
            "pointer": pointer,
            "resolved_path": None,
            "reason": "STEERING_POINTER_ABSOLUTE_REJECTED",
            "inbox": inbox,
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
            "inbox": inbox,
        }

    present = resolved.is_file()
    return {
        "verified": present,
        "pointer": pointer,
        "resolved_path": str(resolved),
        "reason": "OK" if present else "STEERING_TARGET_MISSING",
        "inbox": inbox,
    }


def provider_action_class(inbox: dict[str, Any] | None) -> tuple[str, str]:
    """Classify provider orchestration from explicit current inbox fields only."""
    if not isinstance(inbox, dict):
        return "BLOCKED", "CURRENT_AUTHORITY_UNRESOLVED"
    free_only = inbox.get("free_only")
    if not isinstance(free_only, dict):
        return "BLOCKED", "FREE_ONLY_AUTHORITY_BLOCK_MISSING"
    if free_only.get("free_swarm_owner_emergency_stop") is True:
        return "BLOCKED", "FREE_SWARM_OWNER_EMERGENCY_STOP"
    if free_only.get("provider_routes_admitted") is not True:
        return "BLOCKED", "PROVIDER_ROUTES_NOT_EXPLICITLY_ADMITTED"
    return "DEGRADED", "SOURCE_AUTHORITY_APPEARS_OPEN_BUT_EXECUTION_NOT_PROBED"


def classify(
    root: Path | None,
    authority_present: dict[str, bool],
    git_ok: bool,
    steering_verified: bool,
) -> str:
    """Compatibility classifier: read-only preflight returns only BLOCKED/DEGRADED."""
    if root is None:
        return "BLOCKED"
    if not all(authority_present.values()) or not steering_verified:
        return "BLOCKED"
    # Even a clean, readable Git repository does not prove hook/state/effect lifecycle.
    return "DEGRADED"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="Known repository root; otherwise search from cwd upward; no guessed home/Downloads path.",
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
            "inbox": None,
        }
    )

    git_root_ok = False
    git_head_ok = False
    git_status_ok = False
    git_head = None
    git_dirty = None
    git_error = None
    if root is not None:
        ok, value = run_git(root, "rev-parse", "--show-toplevel")
        if ok:
            try:
                git_root_ok = Path(value).resolve() == root.resolve()
            except OSError:
                git_root_ok = False
        else:
            git_error = value

        ok, value = run_git(root, "rev-parse", "HEAD")
        git_head_ok = ok
        if ok:
            git_head = value
        elif git_error is None:
            git_error = value

        ok, value = run_git(root, "status", "--porcelain")
        git_status_ok = ok
        if ok:
            git_dirty = bool(value)
        elif git_error is None:
            git_error = value

    git_ok = bool(git_root_ok and git_head_ok and git_status_ok)
    installation_class = classify(
        root, authority_present, git_ok, bool(steering["verified"])
    )
    provider_class, provider_reason = provider_action_class(steering.get("inbox"))

    inbox = steering.get("inbox") if isinstance(steering.get("inbox"), dict) else {}
    free_only = inbox.get("free_only") if isinstance(inbox, dict) else None
    free_only = free_only if isinstance(free_only, dict) else {}

    if root is None:
        next_action = "Resolve the actual repository root before any installation claim."
    elif not all(authority_present.values()) or not steering["verified"]:
        next_action = "Resolve all required current authority surfaces and inbox-selected steering."
    elif not git_ok:
        next_action = "Verify exact Git root, HEAD, and status; remain DEGRADED."
    else:
        next_action = (
            "Run a separate host-specific witness for real lifecycle hook firing, durable state "
            "when claimed, and effect/result re-entry before NATIVE or ADAPTED classification."
        )

    result: dict[str, Any] = {
        "schema": "FRANKENSTEIN_HOST_PREFLIGHT/v3",
        "mode": "READ_ONLY_NO_NETWORK_NO_SECRETS_NO_WRITES_NO_EFFECTS",
        "root": str(root) if root else None,
        "markers": {m: bool(root and (root / m).exists()) for m in MARKERS},
        "authority_files": authority_present,
        "dynamic_steering": {
            key: steering.get(key)
            for key in ("verified", "pointer", "resolved_path", "reason")
        },
        "authority_snapshot": {
            "schema_version": inbox.get("schema_version") if isinstance(inbox, dict) else None,
            "supervisor_delta": inbox.get("supervisor_delta") if isinstance(inbox, dict) else None,
        },
        "git": {
            "binary_present": shutil.which("git") is not None,
            "root_verified": git_root_ok,
            "head_verified": git_head_ok,
            "status_verified": git_status_ok,
            "verified": git_ok,
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
            "repository_write_tested": False,
        },
        "installation_class": installation_class,
        "native_or_adapted_claim_allowed": False,
        "native_boundaries_unverified": list(NATIVE_BOUNDARIES),
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
        "promotion_fence": (
            "Read-only source/repository evidence cannot mint NATIVE or ADAPTED lifecycle status; "
            "source/config/model self-report cannot substitute for observed hook/state/effect receipts."
        ),
        "credit_boundary": (
            "Zero provider-runtime, whole EntityOS/HCU, full HCU, Physical GRID10, Global J-Space, "
            "model, canonical-semantics, or training credit is granted."
        ),
        "next": next_action,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if installation_class == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
