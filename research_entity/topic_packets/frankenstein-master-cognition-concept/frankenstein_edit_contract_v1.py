"""Fail-closed existing-file edit contract for Project Frankenstein.

This module is deliberately provider-neutral and network-free.  It turns a model- or
human-proposed unified diff into a candidate mutation that is bound to the exact
preimage bytes, exact repository-relative path, an explicit deletion budget, and Git's
own patch applicability checks before any working-tree mutation is allowed.

It does not commit, push, call a model, inspect secrets, or grant runtime/product credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Final


class EditContractError(RuntimeError):
    """Fail-closed edit-contract rejection with a stable machine-readable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True)
class EditContract:
    path: str
    preimage_sha256: str
    patch: str
    max_deleted_lines: int = 0
    max_added_lines: int | None = None


@dataclass(frozen=True)
class ValidatedEdit:
    path: str
    preimage_sha256: str
    postimage_sha256: str
    patch_sha256: str
    added_lines: int
    deleted_lines: int
    postimage: bytes


_DIFF_HEADER: Final[re.Pattern[str]] = re.compile(r"^diff --git a/(\S+) b/(\S+)\s*$", re.MULTILINE)
_OLD_HEADER: Final[re.Pattern[str]] = re.compile(r"^--- (?:a/)?(\S+)\s*$", re.MULTILINE)
_NEW_HEADER: Final[re.Pattern[str]] = re.compile(r"^\+\+\+ (?:b/)?(\S+)\s*$", re.MULTILINE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_git(repo_root: Path, args: list[str], *, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EditContractError("GIT_EXECUTION_FAILED", type(exc).__name__) from exc


def _repo_root(repo_root: Path) -> Path:
    root = repo_root.resolve()
    proc = _run_git(root, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise EditContractError("NOT_A_GIT_REPOSITORY", proc.stderr.decode(errors="replace")[:300])
    try:
        observed = Path(proc.stdout.decode().strip()).resolve()
    except OSError as exc:
        raise EditContractError("GIT_ROOT_UNRESOLVED", type(exc).__name__) from exc
    if observed != root:
        raise EditContractError("REPOSITORY_ROOT_MISMATCH", f"expected={root} observed={observed}")
    return root


def _resolve_existing_path(repo_root: Path, rel: str) -> Path:
    if not rel or "\x00" in rel or "\n" in rel or "\r" in rel:
        raise EditContractError("INVALID_PATH", repr(rel))
    path_obj = Path(rel)
    if path_obj.is_absolute() or rel.startswith("/"):
        raise EditContractError("ABSOLUTE_PATH_REJECTED", rel)
    root = repo_root.resolve()
    resolved = (root / path_obj).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EditContractError("PATH_ESCAPES_REPOSITORY", rel) from exc
    if not resolved.is_file():
        raise EditContractError("EXISTING_FILE_REQUIRED", rel)
    # Symlink targets outside the repository are already rejected by resolve()/relative_to().
    return resolved


def _extract_patch_path(patch: str) -> str:
    if not patch or "\x00" in patch:
        raise EditContractError("INVALID_PATCH")

    diff_pairs = _DIFF_HEADER.findall(patch)
    if len(diff_pairs) > 1:
        raise EditContractError("MULTI_FILE_PATCH_REJECTED", str(diff_pairs))
    if diff_pairs:
        old, new = diff_pairs[0]
        if old != new:
            raise EditContractError("RENAME_REJECTED", f"{old}->{new}")
        diff_path = old
    else:
        diff_path = ""

    old_headers = _OLD_HEADER.findall(patch)
    new_headers = _NEW_HEADER.findall(patch)
    if len(old_headers) != 1 or len(new_headers) != 1:
        raise EditContractError(
            "SINGLE_EXISTING_FILE_PATCH_REQUIRED",
            f"old_headers={old_headers} new_headers={new_headers}",
        )
    old_path, new_path = old_headers[0], new_headers[0]
    if old_path == "/dev/null" or new_path == "/dev/null":
        raise EditContractError("CREATE_DELETE_PATCH_REJECTED")
    if old_path != new_path:
        raise EditContractError("RENAME_REJECTED", f"{old_path}->{new_path}")
    if diff_path and diff_path != old_path:
        raise EditContractError("PATCH_HEADER_PATH_MISMATCH", f"diff={diff_path} file={old_path}")
    return old_path


def _path_is_clean(repo_root: Path, rel: str) -> None:
    work = _run_git(repo_root, ["diff", "--quiet", "--", rel])
    if work.returncode not in (0, 1):
        raise EditContractError("GIT_DIFF_FAILED", work.stderr.decode(errors="replace")[:300])
    if work.returncode == 1:
        raise EditContractError("WORKTREE_PATH_DIRTY", rel)

    staged = _run_git(repo_root, ["diff", "--cached", "--quiet", "--", rel])
    if staged.returncode not in (0, 1):
        raise EditContractError("GIT_DIFF_CACHED_FAILED", staged.stderr.decode(errors="replace")[:300])
    if staged.returncode == 1:
        raise EditContractError("INDEX_PATH_DIRTY", rel)


def _numstat(repo_root: Path, patch_bytes: bytes, rel: str) -> tuple[int, int]:
    proc = _run_git(repo_root, ["apply", "--numstat", "--", "-"], stdin=patch_bytes)
    if proc.returncode != 0:
        raise EditContractError("PATCH_NUMSTAT_FAILED", proc.stderr.decode(errors="replace")[:500])
    rows = [line for line in proc.stdout.decode(errors="strict").splitlines() if line]
    if len(rows) != 1:
        raise EditContractError("PATCH_NUMSTAT_SINGLE_FILE_REQUIRED", repr(rows))
    parts = rows[0].split("\t", 2)
    if len(parts) != 3 or parts[2] != rel:
        raise EditContractError("PATCH_NUMSTAT_PATH_MISMATCH", rows[0])
    if parts[0] == "-" or parts[1] == "-":
        raise EditContractError("BINARY_PATCH_REJECTED")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise EditContractError("PATCH_NUMSTAT_INVALID", rows[0]) from exc


def _materialize_postimage(repo_root: Path, rel: str, preimage: bytes, patch_bytes: bytes) -> bytes:
    # Apply only inside a temporary non-repository directory. The canonical working tree is untouched.
    with tempfile.TemporaryDirectory(prefix="frankenstein-edit-contract-") as tmp:
        tmp_root = Path(tmp)
        tmp_file = tmp_root / rel
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file.write_bytes(preimage)
        proc = subprocess.run(
            ["git", "apply", "--whitespace=error-all", "--", "-"],
            cwd=tmp_root,
            input=patch_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
        if proc.returncode != 0:
            raise EditContractError("TEMP_PATCH_APPLY_FAILED", proc.stderr.decode(errors="replace")[:500])
        if not tmp_file.is_file():
            raise EditContractError("POSTIMAGE_MISSING", rel)
        return tmp_file.read_bytes()


def validate_edit_contract(repo_root: Path, contract: EditContract) -> ValidatedEdit:
    """Validate an existing-file unified diff without mutating the repository."""
    root = _repo_root(repo_root)
    target = _resolve_existing_path(root, contract.path)
    rel = target.relative_to(root).as_posix()
    if rel != contract.path:
        raise EditContractError("NONCANONICAL_RELATIVE_PATH", f"declared={contract.path} canonical={rel}")

    if contract.max_deleted_lines < 0:
        raise EditContractError("NEGATIVE_DELETION_BUDGET")
    if contract.max_added_lines is not None and contract.max_added_lines < 0:
        raise EditContractError("NEGATIVE_ADDITION_BUDGET")

    preimage = target.read_bytes()
    observed_preimage = sha256_bytes(preimage)
    if not hmac.compare_digest(observed_preimage, contract.preimage_sha256.lower()):
        raise EditContractError(
            "PREIMAGE_HASH_MISMATCH",
            f"expected={contract.preimage_sha256.lower()} observed={observed_preimage}",
        )

    patch_path = _extract_patch_path(contract.patch)
    if patch_path != rel:
        raise EditContractError("PATCH_TARGET_MISMATCH", f"contract={rel} patch={patch_path}")

    _path_is_clean(root, rel)
    patch_bytes = contract.patch.encode("utf-8")

    check = _run_git(root, ["apply", "--check", "--index", "--whitespace=error-all", "--", "-"], stdin=patch_bytes)
    if check.returncode != 0:
        raise EditContractError("GIT_APPLY_CHECK_FAILED", check.stderr.decode(errors="replace")[:500])

    added, deleted = _numstat(root, patch_bytes, rel)
    if deleted > contract.max_deleted_lines:
        raise EditContractError(
            "DELETION_BUDGET_EXCEEDED",
            f"deleted={deleted} budget={contract.max_deleted_lines}",
        )
    if contract.max_added_lines is not None and added > contract.max_added_lines:
        raise EditContractError(
            "ADDITION_BUDGET_EXCEEDED",
            f"added={added} budget={contract.max_added_lines}",
        )

    postimage = _materialize_postimage(root, rel, preimage, patch_bytes)
    if postimage == preimage:
        raise EditContractError("NO_OP_PATCH_REJECTED")

    return ValidatedEdit(
        path=rel,
        preimage_sha256=observed_preimage,
        postimage_sha256=sha256_bytes(postimage),
        patch_sha256=sha256_bytes(patch_bytes),
        added_lines=added,
        deleted_lines=deleted,
        postimage=postimage,
    )


def apply_validated_edit(repo_root: Path, validated: ValidatedEdit) -> Path:
    """Atomically install an already-validated postimage after a final preimage recheck.

    This performs no commit or staging operation.  It exists so a caller can run its own
    feature/module/repository tests before deciding whether any later commit is authorized.
    """
    root = _repo_root(repo_root)
    target = _resolve_existing_path(root, validated.path)
    rel = target.relative_to(root).as_posix()
    if rel != validated.path:
        raise EditContractError("NONCANONICAL_RELATIVE_PATH", f"validated={validated.path} canonical={rel}")

    _path_is_clean(root, rel)
    current = target.read_bytes()
    observed = sha256_bytes(current)
    if not hmac.compare_digest(observed, validated.preimage_sha256):
        raise EditContractError(
            "PREIMAGE_CHANGED_AFTER_VALIDATION",
            f"validated={validated.preimage_sha256} observed={observed}",
        )
    if sha256_bytes(validated.postimage) != validated.postimage_sha256:
        raise EditContractError("VALIDATED_POSTIMAGE_HASH_MISMATCH")

    with tempfile.NamedTemporaryFile(prefix=f".{target.name}.", dir=target.parent, delete=False) as fh:
        temp_path = Path(fh.name)
        fh.write(validated.postimage)
        fh.flush()
    try:
        temp_path.replace(target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return target
