#!/usr/bin/env python3
"""Deterministic preservation policy for exact-source patch worktrees.

This module is deliberately not a patch executor. It is a post-apply policy
layer for an already exact-source-bound, isolated git worktree. The caller is
responsible for source rehydration and patch application; this module verifies
that the resulting tracked delta stays inside the declared target set and does
not perform broad deletion/rewrite unless the *controller* explicitly supplies
a different Policy object.

Model/worker payloads are not parsed for policy overrides. A patch can pass
``git apply --check`` and still fail this preservation gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import difflib
from pathlib import Path
import re
import subprocess
from typing import Any

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_ANALYZED_CHARS = 200_000


class PreservationError(ValueError):
    pass


@dataclass(frozen=True)
class Policy:
    max_deleted_fraction: float = 0.25
    deleted_lines_floor: int = 5
    max_net_shrink_fraction: float = 0.20
    net_shrink_lines_floor: int = 5
    max_old_changed_fraction: float = 0.30
    old_changed_chars_floor: int = 200
    max_analyzed_chars: int = MAX_ANALYZED_CHARS

    def validate(self) -> None:
        for name in (
            "max_deleted_fraction",
            "max_net_shrink_fraction",
            "max_old_changed_fraction",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
                raise PreservationError(f"{name} must be within [0, 1]")
        for name in (
            "deleted_lines_floor",
            "net_shrink_lines_floor",
            "old_changed_chars_floor",
            "max_analyzed_chars",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PreservationError(f"{name} must be a non-negative integer")


DEFAULT_POLICY = Policy()


def _git(repo: Path, *args: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        return 125, "", f"{type(exc).__name__}:{exc}"


def _safe_target(raw: str) -> str:
    if not isinstance(raw, str):
        raise PreservationError("target path must be text")
    value = raw.strip()
    if not value or any(ch in value for ch in "\x00\n\r\t"):
        raise PreservationError(f"unsafe target path: {raw!r}")
    path = Path(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise PreservationError(f"unsafe target path: {raw!r}")
    normalized = path.as_posix()
    if normalized.startswith("./"):
        raise PreservationError(f"unsafe target path: {raw!r}")
    return normalized


def _line_count(text: str) -> int:
    return len(text.splitlines())


def _changed_old_chars(before: str, after: str) -> int:
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    return sum(i2 - i1 for tag, i1, i2, _j1, _j2 in matcher.get_opcodes() if tag != "equal")


def _numstat_for(repo: Path, target: str) -> tuple[int, int]:
    rc, out, err = _git(repo, "diff", "--numstat", "--no-renames", "HEAD", "--", target)
    if rc != 0:
        raise PreservationError(f"NUMSTAT_FAILED:{err[-500:]}")
    rows = [line for line in out.splitlines() if line.strip()]
    if len(rows) != 1:
        raise PreservationError(f"TARGET_DIFF_ROW_COUNT:{target}:{len(rows)}")
    parts = rows[0].split("\t", 2)
    if len(parts) != 3 or parts[0] == "-" or parts[1] == "-":
        raise PreservationError(f"BINARY_OR_MALFORMED_NUMSTAT:{target}")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise PreservationError(f"MALFORMED_NUMSTAT:{target}") from exc


def evaluate_worktree(
    repo: Path,
    source_head: str,
    targets: list[str],
    *,
    policy: Policy = DEFAULT_POLICY,
) -> dict[str, Any]:
    """Evaluate an already-applied patch in an exact-source git worktree.

    Fail-closed invariants:
    - worktree HEAD must equal ``source_head`` exactly;
    - the tracked changed-path set must equal the declared target set;
    - each target must exist in the source and remain present after the patch;
    - broad deletion, net shrink, or old-content replacement is rejected;
    - threshold overrides can come only from the caller-supplied ``Policy``.

    The function performs no write, patch application, provider call, secret
    lookup, network request, commit, or effect.
    """
    repo = Path(repo)
    if not repo.is_dir():
        raise PreservationError(f"repo is not a directory: {repo}")
    if not COMMIT_RE.fullmatch(str(source_head or "")):
        raise PreservationError("SOURCE_HEAD_INVALID")
    policy.validate()
    if not targets:
        raise PreservationError("TARGET_SET_EMPTY")

    normalized = [_safe_target(value) for value in targets]
    if len(set(normalized)) != len(normalized):
        raise PreservationError("TARGET_SET_DUPLICATE")

    rc, head, err = _git(repo, "rev-parse", "HEAD")
    if rc != 0:
        raise PreservationError(f"HEAD_UNAVAILABLE:{err[-500:]}")
    if head.strip() != source_head:
        raise PreservationError(f"SOURCE_HEAD_MISMATCH:{head.strip()}")

    rc, changed_text, err = _git(repo, "diff", "--name-only", "--no-renames", "HEAD", "--")
    if rc != 0:
        raise PreservationError(f"CHANGED_PATHS_FAILED:{err[-500:]}")
    changed = {line for line in changed_text.splitlines() if line}
    expected = set(normalized)
    if changed != expected:
        raise PreservationError(
            f"CHANGED_PATH_SET_MISMATCH:expected={sorted(expected)}:observed={sorted(changed)}"
        )

    files: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for target in normalized:
        rc, before, err = _git(repo, "show", f"{source_head}:{target}")
        if rc != 0:
            raise PreservationError(f"SOURCE_TARGET_UNAVAILABLE:{target}:{err[-300:]}")
        path = repo / target
        if not path.is_file():
            violations.append({"path": target, "reason": "FILE_DELETION_REQUIRES_SEPARATE_AUTHORITY"})
            files.append({"path": target, "deleted_file": True})
            continue
        try:
            after = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise PreservationError(f"NON_UTF8_TARGET:{target}") from exc
        if max(len(before), len(after)) > policy.max_analyzed_chars:
            raise PreservationError(f"TARGET_TOO_LARGE_FOR_POLICY:{target}")

        added_lines, deleted_lines = _numstat_for(repo, target)
        before_lines = _line_count(before)
        after_lines = _line_count(after)
        denominator_lines = max(before_lines, 1)
        deleted_fraction = deleted_lines / denominator_lines
        net_shrink_lines = max(0, before_lines - after_lines)
        net_shrink_fraction = net_shrink_lines / denominator_lines
        old_changed_chars = _changed_old_chars(before, after)
        old_changed_fraction = old_changed_chars / max(len(before), 1)

        row = {
            "path": target,
            "before_lines": before_lines,
            "after_lines": after_lines,
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "deleted_fraction": deleted_fraction,
            "net_shrink_lines": net_shrink_lines,
            "net_shrink_fraction": net_shrink_fraction,
            "old_changed_chars": old_changed_chars,
            "old_changed_fraction": old_changed_fraction,
        }
        files.append(row)

        if deleted_lines > policy.deleted_lines_floor and deleted_fraction > policy.max_deleted_fraction:
            violations.append({"path": target, "reason": "DELETION_FRACTION_EXCEEDED", "observed": deleted_fraction})
        if net_shrink_lines > policy.net_shrink_lines_floor and net_shrink_fraction > policy.max_net_shrink_fraction:
            violations.append({"path": target, "reason": "NET_SHRINK_FRACTION_EXCEEDED", "observed": net_shrink_fraction})
        if old_changed_chars > policy.old_changed_chars_floor and old_changed_fraction > policy.max_old_changed_fraction:
            violations.append({"path": target, "reason": "OLD_CONTENT_CHANGE_FRACTION_EXCEEDED", "observed": old_changed_fraction})

    return {
        "schema": "PATCH_PRESERVATION_POLICY_RECEIPT/v1",
        "ok": not violations,
        "reason": None if not violations else "PRESERVATION_POLICY_REJECTED",
        "source_head": source_head,
        "targets": normalized,
        "policy": asdict(policy),
        "policy_authority": "CONTROLLER_ARGUMENT_ONLY_NOT_WORKER_PAYLOAD",
        "files": files,
        "violations": violations,
    }
