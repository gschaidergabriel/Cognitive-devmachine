#!/usr/bin/env python3
"""Apply -> verify -> exact rollback transaction over the canonical patch preflight.

This module does not define another patch-policy authority. It delegates all
source identity, path, patch-feature and change-budget admission to
`frankenstein_patch_guard_v1.preflight_patch`, then provides the missing
write lifecycle: apply, post-apply sanity checks, argv-only verification, and
byte-exact rollback for touched files on any failure.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from frankenstein_patch_guard_v1 import PatchPolicy, preflight_patch


RECEIPT_SCHEMA = "FRANKENSTEIN_PATCH_TRANSACTION/v1"


class PatchTransactionError(RuntimeError):
    """Raised when an admitted patch cannot complete its write/verify lifecycle."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _run_git(repo: Path, args: Sequence[str], *, patch: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=patch,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _restore(repo: Path, snapshots: dict[str, bytes | None]) -> None:
    """Restore touched file bytes only; leave unrelated dirty/staged state intact."""
    for rel, before in snapshots.items():
        path = repo / rel
        if before is None:
            if path.exists() or path.is_symlink():
                if path.is_dir():
                    raise PatchTransactionError(f"rollback refuses unexpected directory at new-file path: {rel}")
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(before)


def apply_verified_patch(
    repo_root: str | os.PathLike[str],
    patch_text: str,
    policy: PatchPolicy,
    *,
    verification_argv: Sequence[str],
    timeout_seconds: int = 300,
) -> dict:
    """Apply an admissible patch, verify it, or restore exact preimage bytes.

    `preflight_patch` is deliberately called inside this function immediately
    before snapshots and mutation, so callers cannot bypass current HEAD/base/
    allowlist/budget/dirty-index checks by presenting an old preflight receipt.
    """
    if not verification_argv or any(not isinstance(arg, str) or not arg for arg in verification_argv):
        raise PatchTransactionError("verification_argv must be a non-empty argv sequence")

    repo = Path(repo_root).resolve()
    preflight = preflight_patch(repo, patch_text, policy)
    touched = [entry["path"] for entry in preflight["files"]]

    snapshots: dict[str, bytes | None] = {}
    for entry in preflight["files"]:
        path = repo / entry["path"]
        snapshots[entry["path"]] = path.read_bytes() if entry["base"]["exists"] else None

    applied = _run_git(repo, ["apply", "--whitespace=error-all", "-"], patch=patch_text)
    if applied.returncode != 0:
        _restore(repo, snapshots)
        raise PatchTransactionError(
            "git apply failed after successful preflight "
            f"rc={applied.returncode} stderr_sha256={_sha256_bytes(applied.stderr.encode())}"
        )

    try:
        reverse = _run_git(repo, ["apply", "--reverse", "--check", "--whitespace=error-all", "-"], patch=patch_text)
        if reverse.returncode != 0:
            raise PatchTransactionError(
                "post-apply reverse check failed "
                f"rc={reverse.returncode} stderr_sha256={_sha256_bytes(reverse.stderr.encode())}"
            )

        diff_check = _run_git(repo, ["diff", "--check", "--", *touched])
        if diff_check.returncode != 0:
            raise PatchTransactionError(
                "git diff --check failed "
                f"rc={diff_check.returncode} stderr_sha256={_sha256_bytes(diff_check.stderr.encode())}"
            )

        verify_env = dict(os.environ)
        verify_env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + verify_env.get("PATH", "")
        verify = subprocess.run(
            list(verification_argv),
            cwd=str(repo),
            env=verify_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
        if verify.returncode != 0:
            raise PatchTransactionError(
                "verification failed "
                f"rc={verify.returncode} stdout_sha256={_sha256_bytes(verify.stdout.encode())} "
                f"stderr_sha256={_sha256_bytes(verify.stderr.encode())}"
            )
    except Exception:
        _restore(repo, snapshots)
        raise

    files = []
    for entry in preflight["files"]:
        path = repo / entry["path"]
        if not path.is_file() or path.is_symlink():
            _restore(repo, snapshots)
            raise PatchTransactionError(f"post-verify path is not a regular file: {entry['path']}")
        files.append({
            "path": entry["path"],
            "before_sha256": entry["base"]["sha256"],
            "after_sha256": _sha256_file(path),
            "added_lines": entry["added_lines"],
            "deleted_lines": entry["deleted_lines"],
        })

    argv_json = json.dumps(list(verification_argv), ensure_ascii=False, separators=(",", ":")).encode()

    return {
        "schema": RECEIPT_SCHEMA,
        "status": "APPLIED_AND_VERIFIED_NOT_COMMITTED",
        "head": preflight["head"],
        "patch_sha256": preflight["patch_sha256"],
        "preflight_schema": preflight["schema"],
        "git_apply_check_index": preflight["git_apply_check_index"],
        "files": files,
        "verification": {
            "executable_basename": Path(verification_argv[0]).name,
            "argc": len(verification_argv),
            "argv_sha256": _sha256_bytes(argv_json),
            "returncode": verify.returncode,
            "stdout_sha256": _sha256_bytes(verify.stdout.encode()),
            "stderr_sha256": _sha256_bytes(verify.stderr.encode()),
            "stdout_bytes": len(verify.stdout.encode()),
            "stderr_bytes": len(verify.stderr.encode()),
        },
        "commit_performed": False,
    }
