#!/usr/bin/env python3
"""Fail-closed Git source attestation for exact local Trigger-1 runtimes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any


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


def _git_sha(value: str, field: str) -> str:
    if len(value) != 40:
        raise RuntimeError(f"SOURCE_IDENTITY_INVALID_{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(f"SOURCE_IDENTITY_INVALID_{field}") from exc
    return value


def exact_source_identity(root: Path) -> dict[str, Any]:
    """Bind HEAD, commit tree and the complete porcelain status payload."""
    resolved = root.resolve()
    head = _git_sha(_git(resolved, "rev-parse", "HEAD"), "HEAD")
    tree = _git_sha(_git(resolved, "rev-parse", "HEAD^{tree}"), "TREE")
    status = _git(resolved, "status", "--porcelain=v1", "--untracked-files=all", strip=False)
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
