"""Fail-closed patch integrity gate for Frankenstein existing-file edits.

This module is deliberately provider-independent. It does not call models, read
secrets, use the network, or grant runtime/product authority.

Design:
- existing files may be modified only through a unified Git patch;
- every touched file must be declared with an exact SHA-256 preimage;
- create/delete/rename/mode/binary patches are rejected;
- Git must prove the patch applies cleanly before mutation;
- every changed path must be exactly one declared path;
- suspiciously broad deletion is rejected unless a higher-level caller
  explicitly opts into a different policy;
- post-apply `git diff --check` and reverse-apply checks must pass;
- any post-apply failure restores the exact preimage bytes.

The gate is a modification primitive, not a semantic reviewer. Passing it proves
edit/provenance integrity at this boundary, not that the edit is correct.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
from typing import Mapping


class EditIntegrityError(RuntimeError):
    """Raised when an edit violates a fail-closed integrity invariant."""


@dataclass(frozen=True)
class EditPolicy:
    max_files: int = 8
    max_patch_bytes: int = 256 * 1024
    max_deleted_fraction_per_file: float = 0.35
    max_deleted_lines_per_file: int = 200


@dataclass(frozen=True)
class EditReceipt:
    schema: str
    paths: tuple[str, ...]
    preimage_sha256: dict[str, str]
    postimage_sha256: dict[str, str]
    patch_sha256: str
    git_diff_check: str
    reverse_apply_check: str
    scope: str = "EXISTING_FILE_PATCH_INTEGRITY_ONLY"

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "paths": list(self.paths),
            "preimage_sha256": dict(self.preimage_sha256),
            "postimage_sha256": dict(self.postimage_sha256),
            "patch_sha256": self.patch_sha256,
            "git_diff_check": self.git_diff_check,
            "reverse_apply_check": self.reverse_apply_check,
            "scope": self.scope,
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_relpath(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise EditIntegrityError("invalid declared path")
    p = PurePosixPath(raw)
    if p.is_absolute() or any(part in ("", ".", "..") for part in p.parts):
        raise EditIntegrityError(f"unsafe declared path: {raw!r}")
    return p.as_posix()


def _git(repo_root: Path, args: list[str], *, patch: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        input=patch,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _require_git_root(repo_root: Path) -> None:
    cp = _git(repo_root, ["rev-parse", "--show-toplevel"])
    if cp.returncode != 0:
        raise EditIntegrityError(f"not a git worktree: {cp.stderr.decode(errors='replace').strip()}")
    observed = Path(cp.stdout.decode().strip()).resolve()
    if observed != repo_root.resolve():
        raise EditIntegrityError(f"repo_root is not the worktree root: {observed}")


def _regular_repo_file(repo_root: Path, path: str) -> Path:
    """Resolve a declared path without permitting a symlink hop.

    Checking only ``full.is_symlink()`` is insufficient because an ancestor
    directory can itself be a symlink to outside the worktree. Reject every
    symlink component and require the strict resolved file to remain below
    the exact Git root.
    """
    current = repo_root
    for part in PurePosixPath(path).parts:
        current = current / part
        if current.is_symlink():
            raise EditIntegrityError(f"symlink path component forbidden: {path}")
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise EditIntegrityError(f"declared path cannot be resolved: {path}") from exc
    if repo_root not in resolved.parents:
        raise EditIntegrityError(f"declared path resolves outside repo_root: {path}")
    if not resolved.is_file():
        raise EditIntegrityError(f"declared path is not a regular existing file: {path}")
    return current


def _numstat(repo_root: Path, patch: bytes) -> dict[str, tuple[int, int]]:
    cp = _git(repo_root, ["apply", "--numstat", "-z", "-"], patch=patch)
    if cp.returncode != 0:
        raise EditIntegrityError(f"cannot inspect patch numstat: {cp.stderr.decode(errors='replace').strip()}")
    out: dict[str, tuple[int, int]] = {}
    for raw in cp.stdout.split(b"\x00"):
        if not raw:
            continue
        try:
            add_s, del_s, path_b = raw.split(b"\t", 2)
            path = _normalize_relpath(path_b.decode("utf-8"))
            if add_s == b"-" or del_s == b"-":
                raise EditIntegrityError(f"binary patch forbidden: {path}")
            added, deleted = int(add_s), int(del_s)
        except (ValueError, UnicodeDecodeError) as exc:
            raise EditIntegrityError("malformed patch numstat") from exc
        if path in out:
            raise EditIntegrityError(f"duplicate patch path: {path}")
        out[path] = (added, deleted)
    if not out:
        raise EditIntegrityError("patch changes no files")
    return out


def _reject_structural_patch(repo_root: Path, patch: bytes) -> None:
    cp = _git(repo_root, ["apply", "--summary", "-"], patch=patch)
    if cp.returncode != 0:
        raise EditIntegrityError(f"cannot inspect patch summary: {cp.stderr.decode(errors='replace').strip()}")
    if cp.stdout.strip():
        raise EditIntegrityError(
            "create/delete/rename/mode-changing patch forbidden: "
            + cp.stdout.decode(errors="replace").strip()
        )


def apply_existing_file_patch(
    repo_root: Path,
    patch: bytes,
    expected_preimage_sha256: Mapping[str, str],
    *,
    policy: EditPolicy = EditPolicy(),
) -> EditReceipt:
    """Apply one bounded patch to existing files with exact preimage binding.

    This function mutates only after all preflight checks pass. If any
    post-apply invariant fails, it restores the exact preimage bytes.
    """
    repo_root = repo_root.resolve()
    _require_git_root(repo_root)

    if not isinstance(patch, (bytes, bytearray)) or not patch:
        raise EditIntegrityError("patch must be non-empty bytes")
    patch = bytes(patch)
    if len(patch) > policy.max_patch_bytes:
        raise EditIntegrityError("patch exceeds max_patch_bytes")

    declared: dict[str, str] = {}
    for raw_path, digest in expected_preimage_sha256.items():
        path = _normalize_relpath(raw_path)
        if path in declared:
            raise EditIntegrityError(f"duplicate declared path: {path}")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise EditIntegrityError(f"invalid SHA-256 for {path}")
        declared[path] = digest

    if not declared:
        raise EditIntegrityError("at least one preimage must be declared")
    if len(declared) > policy.max_files:
        raise EditIntegrityError("too many declared files")

    snapshots: dict[str, bytes] = {}
    line_counts: dict[str, int] = {}
    for path, expected in declared.items():
        full = _regular_repo_file(repo_root, path)
        data = full.read_bytes()
        actual = sha256_bytes(data)
        if actual != expected:
            raise EditIntegrityError(f"preimage SHA-256 mismatch for {path}: expected {expected}, got {actual}")
        snapshots[path] = data
        line_counts[path] = len(data.splitlines())

    _reject_structural_patch(repo_root, patch)
    stats = _numstat(repo_root, patch)
    if set(stats) != set(declared):
        extra = sorted(set(stats) - set(declared))
        missing = sorted(set(declared) - set(stats))
        raise EditIntegrityError(f"patch/declaration path mismatch: extra={extra} missing={missing}")

    for path, (_added, deleted) in stats.items():
        old_lines = line_counts[path]
        if deleted > policy.max_deleted_lines_per_file:
            raise EditIntegrityError(f"deletion budget exceeded for {path}: {deleted}")
        if old_lines and deleted / old_lines > policy.max_deleted_fraction_per_file:
            raise EditIntegrityError(
                f"deletion fraction exceeded for {path}: {deleted}/{old_lines}"
            )

    cp = _git(repo_root, ["apply", "--check", "--whitespace=error-all", "-"], patch=patch)
    if cp.returncode != 0:
        raise EditIntegrityError(f"git apply --check failed: {cp.stderr.decode(errors='replace').strip()}")

    cp = _git(repo_root, ["apply", "--whitespace=error-all", "-"], patch=patch)
    if cp.returncode != 0:
        raise EditIntegrityError(f"git apply failed after successful precheck: {cp.stderr.decode(errors='replace').strip()}")

    try:
        post: dict[str, str] = {}
        changed = False
        for path, old in snapshots.items():
            full = _regular_repo_file(repo_root, path)
            new = full.read_bytes()
            if new != old:
                changed = True
            post[path] = sha256_bytes(new)
        if not changed:
            raise EditIntegrityError("patch produced no byte change")

        cp = _git(repo_root, ["diff", "--check", "--", *sorted(declared)])
        if cp.returncode != 0:
            detail = (cp.stdout + cp.stderr).decode(errors="replace").strip()
            raise EditIntegrityError(f"git diff --check failed: {detail}")

        cp = _git(repo_root, ["apply", "--reverse", "--check", "-"], patch=patch)
        if cp.returncode != 0:
            raise EditIntegrityError(
                "reverse-apply check failed after mutation: "
                + cp.stderr.decode(errors="replace").strip()
            )

        return EditReceipt(
            schema="FRANKENSTEIN_EDIT_INTEGRITY_RECEIPT/v1",
            paths=tuple(sorted(declared)),
            preimage_sha256={p: declared[p] for p in sorted(declared)},
            postimage_sha256={p: post[p] for p in sorted(declared)},
            patch_sha256=sha256_bytes(patch),
            git_diff_check="PASS",
            reverse_apply_check="PASS",
        )
    except Exception:
        for path, data in snapshots.items():
            (repo_root / path).write_bytes(data)
        raise
