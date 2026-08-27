"""Fail-closed patch application for Frankenstein direct-dispatch edits.

This module is intentionally provider-independent. It does not call a model,
load credentials, or make network requests. It accepts a unified diff plus
explicit preimage hashes, applies the patch only to a clean Git checkout, runs
a caller-supplied verification argv, and leaves the checkout unchanged on any
failure.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


class SafeEditError(RuntimeError):
    """Raised when a proposed edit cannot satisfy the fail-closed contract."""


@dataclass(frozen=True)
class SafeEditReceipt:
    head_before: str
    changed_paths: tuple[str, ...]
    preimage_sha256: Mapping[str, str | None]
    postimage_sha256: Mapping[str, str]
    verify_returncode: int


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo_root: Path, *args: str, input_text: str | None = None,
         check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
    )


def _normalize_relpath(repo_root: Path, rel: str) -> str:
    if not rel or rel.startswith("/") or "\x00" in rel:
        raise SafeEditError(f"invalid repository path: {rel!r}")
    candidate = (repo_root / rel).resolve()
    root = repo_root.resolve()
    if candidate != root and root not in candidate.parents:
        raise SafeEditError(f"path escapes repository: {rel}")
    normalized = candidate.relative_to(root).as_posix()
    if normalized in {"", "."}:
        raise SafeEditError("repository root is not an editable file path")
    return normalized


def changed_paths_from_patch(patch_text: str) -> tuple[str, ...]:
    """Return paths declared by ordinary ``diff --git`` headers.

    Rename/copy patches are rejected because their multi-identity semantics are
    unnecessary for one-package direct dispatch and harder to roll back safely.
    """
    if not patch_text.strip():
        raise SafeEditError("empty patch")
    if re.search(r"^(rename|copy) (from|to) ", patch_text, flags=re.MULTILINE):
        raise SafeEditError("rename/copy patches are not admitted")
    paths: list[str] = []
    for line in patch_text.splitlines():
        if not line.startswith("diff --git "):
            continue
        match = re.fullmatch(r"diff --git a/(\S+) b/(\S+)", line)
        if not match or match.group(1) != match.group(2):
            raise SafeEditError(f"unsupported diff header: {line}")
        paths.append(match.group(1))
    if not paths:
        raise SafeEditError("patch has no diff --git file headers")
    if len(paths) != len(set(paths)):
        raise SafeEditError("duplicate file patch headers are not admitted")
    return tuple(paths)


def _status_paths(repo_root: Path) -> tuple[str, ...]:
    result = _git(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        payload = line[3:]
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        paths.append(payload)
    return tuple(sorted(set(paths)))


def _rollback_clean(repo_root: Path, allowed_paths: Sequence[str]) -> None:
    _git(repo_root, "reset", "--hard", "HEAD", check=False)
    if allowed_paths:
        _git(repo_root, "clean", "-fd", "--", *allowed_paths, check=False)


def safe_apply_verified_patch(
    repo_root: Path,
    patch_text: str,
    *,
    allowed_paths: Sequence[str],
    base_sha256: Mapping[str, str | None],
    verify_argv: Sequence[str],
    verify_timeout_seconds: int = 300,
) -> SafeEditReceipt:
    """Apply one exact-preimage unified diff and verify it before commit.

    Safety contract:
    * checkout must be clean before mutation;
    * patch paths must be an exact subset of caller-approved paths;
    * every existing target must match its full-file SHA-256 preimage;
    * every new target must be explicitly declared with ``None`` preimage;
    * ``git apply --check`` must accept the exact diff against those bytes;
    * verification and ``git diff --check`` must both pass;
    * no path outside the approved set may change;
    * on any post-apply failure, the clean pre-call checkout is restored.

    Exact full-file preimage hashing plus Git's contextual patch application is
    the unchanged-region invariant: a stale or fabricated whole-file rewrite
    cannot silently replace unrelated code while still being treated as the
    requested narrow edit.
    """
    repo_root = repo_root.resolve()
    if not (repo_root / ".git").exists():
        raise SafeEditError(f"not a Git checkout: {repo_root}")
    if _status_paths(repo_root):
        raise SafeEditError("refusing to edit a dirty checkout")
    if not verify_argv:
        raise SafeEditError("verification argv is required")

    approved = tuple(_normalize_relpath(repo_root, p) for p in allowed_paths)
    if len(approved) != len(set(approved)):
        raise SafeEditError("duplicate approved paths")
    patch_paths = tuple(_normalize_relpath(repo_root, p) for p in changed_paths_from_patch(patch_text))
    if not set(patch_paths).issubset(set(approved)):
        extra = sorted(set(patch_paths) - set(approved))
        raise SafeEditError(f"patch changes unapproved paths: {extra}")

    preimages: dict[str, str | None] = {}
    for rel in patch_paths:
        target = repo_root / rel
        expected = base_sha256.get(rel, "__MISSING__")
        if expected == "__MISSING__":
            raise SafeEditError(f"missing base_sha256 declaration for {rel}")
        if target.exists():
            actual = sha256_file(target)
            if expected is None or expected != actual:
                raise SafeEditError(f"preimage SHA-256 mismatch for {rel}")
            preimages[rel] = actual
        else:
            if expected is not None:
                raise SafeEditError(f"new file {rel} must declare base_sha256=None")
            preimages[rel] = None

    head_before = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    check_result = _git(
        repo_root, "apply", "--check", "--whitespace=error-all", "-",
        input_text=patch_text, check=False,
    )
    if check_result.returncode != 0:
        raise SafeEditError(f"git apply --check rejected patch: {check_result.stderr.strip()[-500:]}")

    applied = False
    try:
        apply_result = _git(
            repo_root, "apply", "--whitespace=error-all", "-",
            input_text=patch_text, check=False,
        )
        if apply_result.returncode != 0:
            raise SafeEditError(f"git apply rejected patch: {apply_result.stderr.strip()[-500:]}")
        applied = True

        changed = _status_paths(repo_root)
        if not changed:
            raise SafeEditError("patch produced no working-tree change")
        if not set(changed).issubset(set(approved)):
            raise SafeEditError(
                f"working tree changed unapproved paths: {sorted(set(changed) - set(approved))}"
            )

        verify_env = dict(os.environ)
        verify_env["PATH"] = os.path.dirname(os.sys.executable) + os.pathsep + verify_env.get("PATH", "")
        verify = subprocess.run(
            list(verify_argv),
            cwd=str(repo_root),
            env=verify_env,
            capture_output=True,
            text=True,
            timeout=verify_timeout_seconds,
        )
        if verify.returncode != 0:
            raise SafeEditError(
                f"verification failed rc={verify.returncode}: {verify.stderr.strip()[-500:]}"
            )

        diff_check = _git(repo_root, "diff", "--check", check=False)
        if diff_check.returncode != 0:
            raise SafeEditError(f"git diff --check failed: {diff_check.stdout.strip()[-500:]}")

        postimages = {
            rel: sha256_file(repo_root / rel)
            for rel in changed
            if (repo_root / rel).is_file()
        }
        return SafeEditReceipt(
            head_before=head_before,
            changed_paths=changed,
            preimage_sha256=preimages,
            postimage_sha256=postimages,
            verify_returncode=verify.returncode,
        )
    except Exception:
        if applied:
            _rollback_clean(repo_root, approved)
        raise


def donor_dispatch_uses_safe_patch(source_text: str) -> bool:
    """Static fail-closed gate for the quarantined direct-dispatch donor.

    The provider-authored donor is not considered safe merely because this
    module exists. Its ``dispatch_helper_task_direct`` function must actually
    call ``safe_apply_verified_patch`` and must not call legacy whole-file
    ``apply_file_blocks`` directly.
    """
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return False
    target = next(
        (
            n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == "dispatch_helper_task_direct"
        ),
        None,
    )
    if target is None:
        return False
    calls_safe = False
    calls_legacy = False
    for node in ast.walk(target):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute)
            else ""
        )
        calls_safe = calls_safe or name == "safe_apply_verified_patch"
        calls_legacy = calls_legacy or name == "apply_file_blocks"
    return calls_safe and not calls_legacy
