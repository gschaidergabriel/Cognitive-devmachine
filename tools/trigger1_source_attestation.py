#!/usr/bin/env python3
"""Fail-closed Git source attestation for exact local Trigger-1 runtimes.

This helper is deliberately model-agnostic. It binds the checked-out commit, commit
tree and the complete porcelain-v1 working-tree status before any model load. A
clean checkout is represented explicitly as ``repo_dirty == False`` plus the
SHA-256 of the empty status payload. Callers must fail closed on dirty source when
claiming exact-current runtime evidence.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any


def _git(root: Path, *args: str) -> str:
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
    return proc.stdout.strip()


def _git_sha(value: str, field: str) -> str:
    if len(value) != 40:
        raise RuntimeError(f"SOURCE_IDENTITY_INVALID_{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(f"SOURCE_IDENTITY_INVALID_{field}") from exc
    return value


def exact_source_identity(root: Path) -> dict[str, Any]:
    """Return exact Git source identity without collapsing a clean status to UNKNOWN."""
    resolved = root.resolve()
    head = _git_sha(_git(resolved, "rev-parse", "HEAD"), "HEAD")
    tree = _git_sha(_git(resolved, "rev-parse", "HEAD^{tree}"), "TREE")
    status = _git(resolved, "status", "--porcelain=v1", "--untracked-files=all")
    return {
        "repo_head": head,
        "repo_tree": tree,
        "repo_dirty": bool(status),
        "repo_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    }


def require_clean_source(root: Path) -> dict[str, Any]:
    identity = exact_source_identity(root)
    if identity["repo_dirty"] is not False:
        raise RuntimeError("DIRTY_SOURCE_TREE_FAIL_CLOSED")
    return identity
