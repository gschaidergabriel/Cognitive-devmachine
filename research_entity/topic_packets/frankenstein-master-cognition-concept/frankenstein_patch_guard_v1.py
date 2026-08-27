#!/usr/bin/env python3
"""Deterministic preflight guard for model-produced Git patches.

This module is intentionally provider-independent and write-free. It validates a
unified Git patch against an exact repository HEAD, per-file base digests, an
explicit path allowlist and bounded change budgets, then asks `git apply --check
--index` whether the patch applies cleanly to the current index/worktree.

Passing this guard does NOT apply a patch and does NOT establish runtime/product
credit. It only proves the declared source mutation is bounded and applicable at
the exact checked source identity.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


class PatchGuardError(RuntimeError):
    """Raised when a patch violates a fail-closed mutation invariant."""


@dataclass(frozen=True)
class PatchPolicy:
    expected_head: str
    allowed_paths: tuple[str, ...]
    expected_base_sha256: Mapping[str, str | None]
    max_patch_bytes: int = 256_000
    max_files: int = 4
    max_added_lines: int = 300
    max_deleted_lines: int = 80
    max_total_changed_lines: int = 360
    max_deleted_fraction: float = 0.25
    allow_new_files: bool = True
    allow_file_deletes: bool = False
    allow_renames_or_copies: bool = False


def _run_git(repo_root: Path, args: list[str], *, patch: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        input=patch,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise PatchGuardError(f"git {' '.join(args)} failed: {detail}")
    return proc


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_policy_path(raw: str) -> str:
    if (
        not raw
        or raw != raw.strip()
        or "\x00" in raw
        or "\\" in raw
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw)
    ):
        raise PatchGuardError(f"unsafe path spelling: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PatchGuardError(f"unsafe repository-relative path: {raw!r}")
    if ".git" in path.parts:
        raise PatchGuardError(f"refusing Git metadata path: {raw!r}")
    return path.as_posix()


def _assert_path_contained(repo_root: Path, rel: str, *, may_be_new: bool) -> Path:
    root = repo_root.resolve()
    target = root / rel
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            raise PatchGuardError(f"refusing symlink target: {rel}")
        resolved = target.resolve()
    else:
        if not may_be_new:
            raise PatchGuardError(f"expected existing path is missing: {rel}")
        parent = target.parent.resolve()
        try:
            parent.relative_to(root)
        except ValueError as exc:
            raise PatchGuardError(f"new path escapes repository: {rel}") from exc
        resolved = target
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PatchGuardError(f"path escapes repository: {rel}") from exc
    return target


def _reject_unsupported_patch_features(patch_text: str, policy: PatchPolicy) -> None:
    if "GIT binary patch" in patch_text or "Binary files " in patch_text:
        raise PatchGuardError("binary patches are forbidden")
    if not policy.allow_renames_or_copies:
        for marker in ("rename from ", "rename to ", "copy from ", "copy to ", "similarity index "):
            if marker in patch_text:
                raise PatchGuardError("rename/copy patches are forbidden")
    if not policy.allow_file_deletes and "deleted file mode " in patch_text:
        raise PatchGuardError("file deletion patches are forbidden")
    if "old mode " in patch_text or "new mode " in patch_text:
        raise PatchGuardError("existing-file mode changes are forbidden")
    for line in patch_text.splitlines():
        if line.startswith("new file mode ") and line != "new file mode 100644":
            raise PatchGuardError("new files must be regular non-executable mode 100644")


def _numstat(repo_root: Path, patch: bytes) -> list[tuple[int, int, str]]:
    proc = _run_git(repo_root, ["apply", "--numstat", "-z", "-"], patch=patch)
    records: list[tuple[int, int, str]] = []
    for record in proc.stdout.split(b"\x00"):
        if not record:
            continue
        parts = record.split(b"\t", 2)
        if len(parts) != 3:
            raise PatchGuardError("could not parse git apply --numstat output")
        added_raw, deleted_raw, path_raw = parts
        if added_raw == b"-" or deleted_raw == b"-":
            raise PatchGuardError("binary patch statistics are forbidden")
        try:
            added = int(added_raw)
            deleted = int(deleted_raw)
            path = path_raw.decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PatchGuardError("invalid patch numstat record") from exc
        records.append((added, deleted, _normalize_policy_path(path)))
    if not records:
        raise PatchGuardError("patch changes no files")
    return records


def preflight_patch(repo_root: str | os.PathLike[str], patch_text: str, policy: PatchPolicy) -> dict:
    """Validate a patch without applying it; return an evidence-oriented report."""
    repo = Path(repo_root).resolve()
    if not repo.is_dir():
        raise PatchGuardError("repository root is not a directory")

    patch = patch_text.encode("utf-8")
    if not patch or len(patch) > policy.max_patch_bytes:
        raise PatchGuardError("patch byte budget exceeded or patch is empty")

    actual_root = Path(_run_git(repo, ["rev-parse", "--show-toplevel"]).stdout.decode().strip()).resolve()
    if actual_root != repo:
        raise PatchGuardError(f"repo_root mismatch: expected {repo}, git reports {actual_root}")

    actual_head = _run_git(repo, ["rev-parse", "HEAD"]).stdout.decode().strip()
    if actual_head != policy.expected_head:
        raise PatchGuardError(f"HEAD mismatch: expected {policy.expected_head}, got {actual_head}")

    allowed = {_normalize_policy_path(path) for path in policy.allowed_paths}
    if not allowed:
        raise PatchGuardError("allowed_paths must not be empty")
    base_map = {_normalize_policy_path(path): digest for path, digest in policy.expected_base_sha256.items()}
    if set(base_map) != allowed:
        raise PatchGuardError("expected_base_sha256 keys must exactly equal allowed_paths")
    if not 0.0 <= policy.max_deleted_fraction <= 1.0:
        raise PatchGuardError("max_deleted_fraction must be between 0.0 and 1.0")

    _reject_unsupported_patch_features(patch_text, policy)
    records = _numstat(repo, patch)
    touched = [path for _, _, path in records]
    if len(records) > policy.max_files:
        raise PatchGuardError(f"file budget exceeded: {len(records)} > {policy.max_files}")
    if len(set(touched)) != len(touched):
        raise PatchGuardError("patch reports the same path more than once")
    unauthorized = sorted(set(touched) - allowed)
    if unauthorized:
        raise PatchGuardError(f"patch touches unauthorized paths: {unauthorized}")
    stats_by_path = {path: (added, deleted) for added, deleted, path in records}

    added_total = sum(added for added, _, _ in records)
    deleted_total = sum(deleted for _, deleted, _ in records)
    if added_total > policy.max_added_lines:
        raise PatchGuardError(f"addition budget exceeded: {added_total} > {policy.max_added_lines}")
    if deleted_total > policy.max_deleted_lines:
        raise PatchGuardError(f"deletion budget exceeded: {deleted_total} > {policy.max_deleted_lines}")
    if added_total + deleted_total > policy.max_total_changed_lines:
        raise PatchGuardError(
            f"total change budget exceeded: {added_total + deleted_total} > {policy.max_total_changed_lines}"
        )

    base_evidence: dict[str, dict] = {}
    for rel in sorted(allowed):
        expected = base_map[rel]
        target = _assert_path_contained(repo, rel, may_be_new=policy.allow_new_files and expected is None)
        exists = target.exists()
        if expected is None:
            if exists:
                raise PatchGuardError(f"path declared new but already exists: {rel}")
            if not policy.allow_new_files:
                raise PatchGuardError(f"new files forbidden by policy: {rel}")
            base_evidence[rel] = {"exists": False, "sha256": None}
        else:
            if not exists:
                raise PatchGuardError(f"expected base file missing: {rel}")
            actual_digest = _sha256(target)
            if actual_digest != expected:
                raise PatchGuardError(f"base SHA-256 mismatch for {rel}: expected {expected}, got {actual_digest}")
            base_line_count = sum(1 for _ in target.open("rb"))
            deleted_for_path = stats_by_path.get(rel, (0, 0))[1]
            deleted_fraction = (deleted_for_path / base_line_count) if base_line_count else 0.0
            if deleted_fraction > policy.max_deleted_fraction:
                raise PatchGuardError(
                    f"relative deletion budget exceeded for {rel}: "
                    f"{deleted_for_path}/{base_line_count} = {deleted_fraction:.3f} > "
                    f"{policy.max_deleted_fraction:.3f}"
                )
            base_evidence[rel] = {
                "exists": True,
                "sha256": actual_digest,
                "line_count": base_line_count,
                "deleted_fraction": deleted_fraction,
            }

    # `--index` requires the index and working-tree copies for touched tracked
    # paths to agree. This catches a second class of lost-update/dirty-tree
    # hazards in addition to the explicit SHA-256 binding above.
    _run_git(repo, ["apply", "--check", "--index", "--whitespace=error-all", "-"], patch=patch)

    return {
        "schema": "FRANKENSTEIN_PATCH_GUARD_PREFLIGHT/v1",
        "applied": False,
        "repo_root": str(repo),
        "head": actual_head,
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
        "files": [
            {"path": path, "added_lines": added, "deleted_lines": deleted, "base": base_evidence[path]}
            for added, deleted, path in records
        ],
        "totals": {
            "files": len(records),
            "added_lines": added_total,
            "deleted_lines": deleted_total,
            "changed_lines": added_total + deleted_total,
        },
        "git_apply_check_index": "PASS",
    }
