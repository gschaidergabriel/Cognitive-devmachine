"""Fail-closed patch transaction primitive for Frankenstein existing-file edits.

This module is deliberately provider-free. It does not call models, inspect secrets,
or perform network I/O. Existing files are modified only through exact-path unified
patches bound to caller-supplied SHA-256 preimages. A verifier can accept the whole
patch set; verifier failure or exception restores byte-identical preimages.

Scope: source/component safety primitive only. It does not grant provider authority,
execution authority, or product/runtime credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
from typing import Callable, Mapping


class SafeEditError(RuntimeError):
    """Base class for fail-closed edit rejection."""


class InvalidRepository(SafeEditError):
    pass


class UnsafePath(SafeEditError):
    pass


class PreimageMismatch(SafeEditError):
    pass


class InvalidPatch(SafeEditError):
    pass


class PatchCheckFailed(SafeEditError):
    pass


class VerificationFailed(SafeEditError):
    pass


@dataclass(frozen=True)
class FileDigest:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class PatchReceipt:
    schema: str
    files: tuple[FileDigest, ...]
    postimage_sha256: tuple[tuple[str, str], ...]
    verifier_ran: bool
    verifier_passed: bool


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_root(repo_root: Path) -> Path:
    root = repo_root.resolve()
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise InvalidRepository("repo_root is not a Git work tree")
    try:
        observed = Path(proc.stdout.strip()).resolve()
    except OSError as exc:
        raise InvalidRepository("cannot resolve Git work-tree root") from exc
    if observed != root:
        raise InvalidRepository("repo_root must be the exact Git work-tree root")
    return root


def _normalize_relative_path(rel_path: str) -> str:
    if not rel_path or "\\" in rel_path:
        raise UnsafePath("path must be a non-empty POSIX-style repo-relative path")
    pure = PurePosixPath(rel_path)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise UnsafePath("absolute, empty, dot, and traversal paths are forbidden")
    normalized = pure.as_posix()
    if normalized.startswith(".git/") or normalized == ".git":
        raise UnsafePath(".git paths are forbidden")
    return normalized


def _resolve_existing_regular_file(root: Path, rel_path: str) -> Path:
    rel = _normalize_relative_path(rel_path)
    target = (root / rel).resolve()
    if root not in target.parents:
        raise UnsafePath(f"path escapes repo_root: {rel}")
    raw_target = root / rel
    if raw_target.is_symlink():
        raise UnsafePath(f"symlink targets are forbidden: {rel}")
    if not target.is_file():
        raise UnsafePath(f"existing regular file required: {rel}")
    return target


def snapshot_existing_files(repo_root: Path, rel_paths: list[str] | tuple[str, ...]) -> dict[str, FileDigest]:
    """Return exact SHA-256 preimages for existing regular files."""
    root = _repo_root(repo_root)
    out: dict[str, FileDigest] = {}
    for raw in rel_paths:
        rel = _normalize_relative_path(raw)
        if rel in out:
            raise UnsafePath(f"duplicate target path: {rel}")
        data = _resolve_existing_regular_file(root, rel).read_bytes()
        out[rel] = FileDigest(rel, _sha256_bytes(data), len(data))
    if not out:
        raise UnsafePath("at least one existing file is required")
    return out


def _validate_single_file_patch(rel_path: str, patch_text: str) -> str:
    """Validate a deliberately narrow one-existing-file unified diff."""
    rel = _normalize_relative_path(rel_path)
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise InvalidPatch(f"empty patch for {rel}")
    if "\x00" in patch_text:
        raise InvalidPatch(f"NUL byte in patch for {rel}")

    forbidden_markers = (
        "GIT binary patch",
        "Binary files ",
        "rename from ",
        "rename to ",
        "copy from ",
        "copy to ",
        "new file mode ",
        "deleted file mode ",
        "old mode ",
        "new mode ",
        "--- /dev/null",
        "+++ /dev/null",
    )
    if any(marker in patch_text for marker in forbidden_markers):
        raise InvalidPatch(f"rename/copy/mode/binary/create/delete patch forbidden for existing file: {rel}")

    lines = patch_text.splitlines()
    old_headers = [line for line in lines if line.startswith("--- ")]
    new_headers = [line for line in lines if line.startswith("+++ ")]
    if len(old_headers) != 1 or len(new_headers) != 1:
        raise InvalidPatch(f"patch must contain exactly one ---/+++ file header pair: {rel}")
    expected_old = f"--- a/{rel}"
    expected_new = f"+++ b/{rel}"
    if old_headers[0] != expected_old or new_headers[0] != expected_new:
        raise InvalidPatch(f"patch header path must match exact target {rel}")
    if not any(line.startswith("@@ ") for line in lines):
        raise InvalidPatch(f"patch has no unified-diff hunk: {rel}")

    diff_headers = [line for line in lines if line.startswith("diff --git ")]
    if diff_headers and diff_headers != [f"diff --git a/{rel} b/{rel}"]:
        raise InvalidPatch(f"diff --git header must name only exact target {rel}")

    return patch_text if patch_text.endswith("\n") else patch_text + "\n"


def _assert_preimages(root: Path, expected_sha256: Mapping[str, str]) -> dict[str, bytes]:
    snapshots: dict[str, bytes] = {}
    for raw_rel, expected in expected_sha256.items():
        rel = _normalize_relative_path(raw_rel)
        target = _resolve_existing_regular_file(root, rel)
        data = target.read_bytes()
        actual = _sha256_bytes(data)
        if actual != expected:
            raise PreimageMismatch(f"preimage SHA-256 mismatch for {rel}: expected {expected}, observed {actual}")
        snapshots[rel] = data
    return snapshots


def _restore_snapshots(root: Path, snapshots: Mapping[str, bytes]) -> None:
    errors: list[str] = []
    for rel, data in snapshots.items():
        try:
            (root / rel).write_bytes(data)
        except OSError as exc:
            errors.append(f"{rel}: {exc}")
    if errors:
        raise SafeEditError("rollback failed: " + "; ".join(errors))


def transactional_apply_patch_set(
    repo_root: Path,
    patches: Mapping[str, str],
    expected_sha256: Mapping[str, str],
    *,
    verifier: Callable[[], bool] | None = None,
) -> PatchReceipt:
    """Atomically-at-the-caller-level apply existing-file patches.

    All targets must be existing regular non-symlink files. Every target is
    bound to an exact preimage SHA-256. Every patch must be a one-file
    unified diff whose old/new paths exactly match that target. `git apply
    --check` must pass for the complete patch set, then the preimage hashes
    are checked a second time immediately before `git apply` (TOCTOU fence).

    If `verifier` returns false or raises, every target is restored to its
    exact byte preimage. The receipt intentionally stores hashes/sizes, not
    source contents.
    """
    root = _repo_root(repo_root)
    if not patches:
        raise InvalidPatch("at least one patch is required")

    normalized_patches: dict[str, str] = {}
    for raw_rel, patch_text in patches.items():
        rel = _normalize_relative_path(raw_rel)
        if rel in normalized_patches:
            raise InvalidPatch(f"duplicate patch target: {rel}")
        normalized_patches[rel] = _validate_single_file_patch(rel, patch_text)

    expected = {_normalize_relative_path(k): v for k, v in expected_sha256.items()}
    if set(expected) != set(normalized_patches):
        raise PreimageMismatch("expected_sha256 keys must exactly match patch targets")
    for rel, digest in expected.items():
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise PreimageMismatch(f"expected SHA-256 must be 64 lowercase hex characters: {rel}")

    snapshots = _assert_preimages(root, expected)
    combined = "".join(normalized_patches[rel] for rel in sorted(normalized_patches))

    check = subprocess.run(
        ["git", "-C", str(root), "apply", "--check", "--whitespace=error-all", "-"],
        input=combined,
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        raise PatchCheckFailed(check.stderr.strip() or "git apply --check failed")

    # Second check closes the model-call / validation / apply TOCTOU window.
    _assert_preimages(root, expected)

    apply = subprocess.run(
        ["git", "-C", str(root), "apply", "--whitespace=error-all", "-"],
        input=combined,
        capture_output=True,
        text=True,
    )
    if apply.returncode != 0:
        # git apply is normally all-or-none, but restore exact preimages anyway.
        _restore_snapshots(root, snapshots)
        raise PatchCheckFailed(apply.stderr.strip() or "git apply failed after successful --check")

    verifier_ran = verifier is not None
    verifier_passed = False
    try:
        if verifier is not None:
            verifier_passed = bool(verifier())
            if not verifier_passed:
                raise VerificationFailed("verifier rejected patched work tree")
        else:
            verifier_passed = True
    except BaseException:
        _restore_snapshots(root, snapshots)
        raise

    preimages = tuple(
        FileDigest(rel, expected[rel], len(snapshots[rel]))
        for rel in sorted(snapshots)
    )
    postimages = tuple(
        (rel, _sha256_bytes((root / rel).read_bytes()))
        for rel in sorted(snapshots)
    )
    return PatchReceipt(
        schema="FRANKENSTEIN_SAFE_EDIT_RECEIPT/v1",
        files=preimages,
        postimage_sha256=postimages,
        verifier_ran=verifier_ran,
        verifier_passed=verifier_passed,
    )
