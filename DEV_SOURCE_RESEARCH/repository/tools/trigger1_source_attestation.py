#!/usr/bin/env python3
"""Fail-closed Git source attestation for exact local Trigger-1 runtimes.

The Trigger-1 compatibility fields are preserved, but the canonical dirty-state binding
is delegated to the reusable CLAY_GIT_SOURCE_IDENTITY/v1 primitive so tracked diff bytes
and untracked file contents are cryptographically bound rather than only path/status shape.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any

from git_source_identity_v1 import source_identity


def _git(root: Path, *args: str, strip: bool = True) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        raise RuntimeError(f"SOURCE_IDENTITY_GIT_FAILURE:{type(exc).__name__}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"SOURCE_IDENTITY_GIT_NONZERO:{args[0] if args else 'UNKNOWN'}:{proc.returncode}")
    return proc.stdout.strip() if strip else proc.stdout


def exact_source_identity(root: Path) -> dict[str, Any]:
    """Bind HEAD/tree plus compatibility status and byte-exact dirty-state identity."""
    resolved = root.resolve()
    exact = source_identity(resolved)
    status = _git(resolved, "status", "--porcelain=v1", "--untracked-files=all", strip=False)
    return {
        "repo_head": exact["repo_head"],
        "repo_tree": exact["repo_tree"],
        "repo_dirty": bool(exact["dirty_state"]["dirty"]),
        # Compatibility field retained for existing receipts/tests.
        "repo_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        # Strong fields: bind actual tracked diff bytes and untracked content identities.
        "repo_dirty_state_sha256": exact["dirty_state_sha256"],
        "source_identity_sha256": exact["source_identity_sha256"],
        "source_identity_schema": exact["schema"],
    }


def require_clean_source(root: Path) -> dict[str, Any]:
    identity = exact_source_identity(root)
    if identity["repo_dirty"] is not False:
        raise RuntimeError("DIRTY_SOURCE_TREE_FAIL_CLOSED")
    return identity
