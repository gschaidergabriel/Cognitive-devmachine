from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


RECEIPT_SCHEMA = "FRANKENSTEIN_GUARDED_PATCH_RECEIPT/v1"


class EditGuardError(RuntimeError):
    """Fail-closed rejection of an unsafe or stale edit proposal."""


@dataclass(frozen=True)
class EditPolicy:
    max_patch_bytes: int = 131_072
    max_files: int = 4
    max_hunks_per_file: int = 20
    max_deleted_lines: int = 80
    max_changed_lines_per_file: int = 240
    max_deleted_fraction_large_file: float = 0.25
    large_file_line_floor: int = 20


@dataclass(frozen=True)
class PatchFilePlan:
    path: str
    added_lines: int
    deleted_lines: int
    hunks: int


@dataclass(frozen=True)
class FileReceipt:
    path: str
    before_sha256: str
    after_sha256: str
    added_lines: int
    deleted_lines: int
    hunks: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _normalize_rel_path(raw: str) -> str:
    if not raw or raw.startswith("/") or "\\" in raw:
        raise EditGuardError(f"unsafe path: {raw!r}")
    p = Path(raw)
    if p.is_absolute() or any(part in ("", ".", "..") for part in p.parts):
        raise EditGuardError(f"unsafe path: {raw!r}")
    return p.as_posix()


def _resolve_existing_regular(repo_root: Path, rel: str) -> Path:
    rel = _normalize_rel_path(rel)
    root = repo_root.resolve()
    candidate_lexical = repo_root / rel
    if candidate_lexical.is_symlink():
        raise EditGuardError(f"symlink edits are forbidden: {rel}")
    candidate = candidate_lexical.resolve()
    if candidate == root or root not in candidate.parents:
        raise EditGuardError(f"path escapes repo_root: {rel}")
    if not candidate.is_file():
        raise EditGuardError(f"existing regular file required: {rel}")
    return candidate


def extract_single_unified_diff(response_text: str) -> str:
    """Extract exactly one fenced unified diff and reject surrounding file rewrites."""
    blocks = re.findall(r"```(?:diff|patch)\s*\n(.*?)\n```", response_text, flags=re.DOTALL | re.IGNORECASE)
    if len(blocks) != 1:
        raise EditGuardError(f"expected exactly one fenced diff/patch block, got {len(blocks)}")
    outside = re.sub(r"```(?:diff|patch)\s*\n.*?\n```", "", response_text, flags=re.DOTALL | re.IGNORECASE).strip()
    if outside:
        raise EditGuardError("prose or extra payload outside the patch block is forbidden")
    return blocks[0] + ("\n" if not blocks[0].endswith("\n") else "")


def _parse_patch_plan(patch_text: str, policy: EditPolicy) -> list[PatchFilePlan]:
    encoded = patch_text.encode("utf-8")
    if len(encoded) > policy.max_patch_bytes:
        raise EditGuardError("patch exceeds size budget")

    forbidden_prefixes = (
        "new file mode ", "deleted file mode ", "old mode ", "new mode ",
        "rename from ", "rename to ", "copy from ", "copy to ",
        "GIT binary patch", "Binary files ",
    )
    for line in patch_text.splitlines():
        if line.startswith(forbidden_prefixes):
            raise EditGuardError(f"unsupported patch operation: {line}")

    sections: list[tuple[str, list[str]]] = []
    current_path: str | None = None
    current_lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            if current_path is not None:
                sections.append((current_path, current_lines))
            m = re.fullmatch(r"diff --git a/(\S+) b/(\S+)", line)
            if not m or m.group(1) != m.group(2):
                raise EditGuardError("only same-path modifications are supported")
            current_path = _normalize_rel_path(m.group(1))
            current_lines = [line]
        elif current_path is not None:
            current_lines.append(line)
        elif line.strip():
            raise EditGuardError("patch must start with 'diff --git'")
    if current_path is not None:
        sections.append((current_path, current_lines))

    if not sections:
        raise EditGuardError("empty patch")
    if len(sections) > policy.max_files:
        raise EditGuardError("patch touches too many files")
    if len({path for path, _ in sections}) != len(sections):
        raise EditGuardError("duplicate file sections are forbidden")

    plans: list[PatchFilePlan] = []
    for path, lines in sections:
        old_header = f"--- a/{path}"
        new_header = f"+++ b/{path}"
        if old_header not in lines or new_header not in lines:
            raise EditGuardError(f"exact ---/+++ headers required for {path}")
        added = deleted = hunks = 0
        for line in lines:
            if line.startswith("@@"):
                hunks += 1
            elif line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                deleted += 1
        if hunks == 0:
            raise EditGuardError(f"no hunks for {path}")
        if hunks > policy.max_hunks_per_file:
            raise EditGuardError(f"too many hunks for {path}")
        if deleted > policy.max_deleted_lines:
            raise EditGuardError(f"too many deleted lines for {path}: {deleted}")
        if added + deleted > policy.max_changed_lines_per_file:
            raise EditGuardError(f"too many changed lines for {path}: {added + deleted}")
        plans.append(PatchFilePlan(path=path, added_lines=added, deleted_lines=deleted, hunks=hunks))
    return plans


def _policy_digest(policy: EditPolicy) -> str:
    return sha256_bytes(json.dumps(asdict(policy), sort_keys=True, separators=(",", ":")).encode())


def _transaction_id(
    patch_text: str, expected_base_sha256: Mapping[str, str], expected_head_sha: str, policy: EditPolicy
) -> str:
    payload = {
        "patch_sha256": sha256_bytes(patch_text.encode("utf-8")),
        "expected_base_sha256": dict(sorted(expected_base_sha256.items())),
        "expected_head_sha": expected_head_sha,
        "policy_sha256": _policy_digest(policy),
    }
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def apply_guarded_patch(
    repo_root: Path,
    patch_text: str,
    *,
    expected_base_sha256: Mapping[str, str],
    expected_head_sha: str,
    allowed_paths: Sequence[str],
    policy: EditPolicy = EditPolicy(),
) -> dict:
    """Apply a bounded unified diff to exact-base existing files only.

    Safety properties:
    - no full-file replacement API for existing files;
    - exact pre-edit SHA-256 binding for every touched file;
    - path traversal, symlinks, rename/copy/delete/mode/binary edits fail closed;
    - bounded deletion/change budget;
    - `git apply --check` must accept the patch before mutation;
    - receipt binds exact before/after hashes and patch/policy identity.
    """
    root = repo_root.resolve()
    if not (root / ".git").exists():
        raise EditGuardError("repo_root must be a Git working tree root")
    head_proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    if head_proc.returncode != 0:
        raise EditGuardError("cannot resolve repository HEAD")
    actual_head_sha = head_proc.stdout.strip().lower()
    expected_head_sha = expected_head_sha.strip().lower()
    if actual_head_sha != expected_head_sha:
        raise EditGuardError(f"stale repository HEAD: expected {expected_head_sha}, got {actual_head_sha}")

    plans = _parse_patch_plan(patch_text, policy)
    touched = {p.path for p in plans}
    allowed = {_normalize_rel_path(p) for p in allowed_paths}
    if not touched.issubset(allowed):
        raise EditGuardError(f"patch touches paths outside allowlist: {sorted(touched - allowed)}")

    normalized_expected = {_normalize_rel_path(k): v.lower() for k, v in expected_base_sha256.items()}
    missing_hashes = touched - set(normalized_expected)
    if missing_hashes:
        raise EditGuardError(f"missing expected base hash for: {sorted(missing_hashes)}")

    snapshots: dict[str, bytes] = {}
    for plan in plans:
        path = _resolve_existing_regular(root, plan.path)
        data = path.read_bytes()
        snapshots[plan.path] = data
        actual = sha256_bytes(data)
        if actual != normalized_expected[plan.path]:
            raise EditGuardError(f"stale base hash for {plan.path}: expected {normalized_expected[plan.path]}, got {actual}")
        try:
            old_line_count = len(data.decode("utf-8").splitlines())
        except UnicodeDecodeError as exc:
            raise EditGuardError(f"non-UTF8 existing file unsupported: {plan.path}") from exc
        if old_line_count >= policy.large_file_line_floor:
            fraction = plan.deleted_lines / max(1, old_line_count)
            if fraction > policy.max_deleted_fraction_large_file:
                raise EditGuardError(
                    f"deletion fraction too large for {plan.path}: {plan.deleted_lines}/{old_line_count}"
                )

    check = subprocess.run(
        ["git", "-C", str(root), "apply", "--check", "--recount", "--whitespace=nowarn", "-"],
        input=patch_text,
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        raise EditGuardError(f"git apply --check rejected patch: {check.stderr.strip()[-500:]}")

    apply = subprocess.run(
        ["git", "-C", str(root), "apply", "--recount", "--whitespace=nowarn", "-"],
        input=patch_text,
        text=True,
        capture_output=True,
    )
    if apply.returncode != 0:
        for rel, data in snapshots.items():
            _resolve_existing_regular(root, rel).write_bytes(data)
        raise EditGuardError(f"git apply failed after check: {apply.stderr.strip()[-500:]}")

    file_receipts: list[FileReceipt] = []
    for plan in plans:
        path = _resolve_existing_regular(root, plan.path)
        before = sha256_bytes(snapshots[plan.path])
        after = sha256_file(path)
        if before == after:
            for rel, data in snapshots.items():
                _resolve_existing_regular(root, rel).write_bytes(data)
            raise EditGuardError(f"patch produced no content change for {plan.path}")
        file_receipts.append(FileReceipt(
            path=plan.path,
            before_sha256=before,
            after_sha256=after,
            added_lines=plan.added_lines,
            deleted_lines=plan.deleted_lines,
            hunks=plan.hunks,
        ))

    return {
        "schema_version": RECEIPT_SCHEMA,
        "status": "APPLIED_NOT_YET_VERIFIED",
        "transaction_id": _transaction_id(patch_text, normalized_expected, expected_head_sha, policy),
        "git_head_sha": actual_head_sha,
        "patch_sha256": sha256_bytes(patch_text.encode("utf-8")),
        "policy_sha256": _policy_digest(policy),
        "files": [asdict(r) for r in file_receipts],
        "_rollback_snapshots": snapshots,
    }


def apply_and_verify_guarded_patch(
    repo_root: Path,
    patch_text: str,
    *,
    expected_base_sha256: Mapping[str, str],
    expected_head_sha: str,
    allowed_paths: Sequence[str],
    verification_argv: Sequence[str],
    policy: EditPolicy = EditPolicy(),
    timeout_seconds: int = 300,
) -> dict:
    """Apply patch, execute argv-only verification, and byte-restore on failure."""
    if not verification_argv or any(not isinstance(x, str) or not x for x in verification_argv):
        raise EditGuardError("verification_argv must be a non-empty argv sequence")
    receipt = apply_guarded_patch(
        repo_root,
        patch_text,
        expected_base_sha256=expected_base_sha256,
        expected_head_sha=expected_head_sha,
        allowed_paths=allowed_paths,
        policy=policy,
    )
    snapshots = receipt.pop("_rollback_snapshots")
    root = repo_root.resolve()
    verify_env = dict(os.environ)
    verify_env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + verify_env.get("PATH", "")
    try:
        proc = subprocess.run(
            list(verification_argv),
            cwd=str(root),
            env=verify_env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except Exception:
        for rel, data in snapshots.items():
            _resolve_existing_regular(root, rel).write_bytes(data)
        raise
    if proc.returncode != 0:
        for rel, data in snapshots.items():
            _resolve_existing_regular(root, rel).write_bytes(data)
        raise EditGuardError(
            "verification failed "
            f"rc={proc.returncode} stdout_sha256={sha256_bytes(proc.stdout.encode())} "
            f"stderr_sha256={sha256_bytes(proc.stderr.encode())}"
        )
    receipt["status"] = "APPLIED_AND_VERIFIED"
    receipt["verification"] = {
        "argv": list(verification_argv),
        "returncode": proc.returncode,
        "stdout_sha256": sha256_bytes(proc.stdout.encode()),
        "stderr_sha256": sha256_bytes(proc.stderr.encode()),
        "stdout_bytes": len(proc.stdout.encode()),
        "stderr_bytes": len(proc.stderr.encode()),
    }
    return receipt
