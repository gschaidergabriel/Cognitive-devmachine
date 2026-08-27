"""Fail-closed exact-splice editor for Frankenstein direct-dispatch work.

This module is intentionally independent from the provider-authored orchestrator donor.
It exists because a whole-file model rewrite can preserve enough length to evade a
simple shrink-ratio guard while still deleting unrelated code.

Contract for EXISTING files:
- caller supplies the exact UTF-8 preimage SHA-256;
- every edit names an exact, non-empty ``find`` string that occurs exactly once in
  the preimage;
- edit spans must not overlap;
- the union of touched preimage spans is bounded (35% by default);
- bytes outside the declared spans are preserved by construction;
- mutation is atomic and only occurs after all validation passes.

New files are deliberately out of scope; they do not have an existing preimage to
protect and should use a separate create-file path.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Mapping, Sequence

SCHEMA = "FRANKENSTEIN_EXACT_PATCH/v1"
DEFAULT_MAX_TOUCHED_FRACTION = 0.35
MAX_EDITS = 32


class ExactPatchError(RuntimeError):
    """Raised before mutation when an exact-patch invariant is not satisfied."""


@dataclass(frozen=True)
class ResolvedEdit:
    start: int
    end: int
    find: str
    replace: str


@dataclass(frozen=True)
class PatchPlan:
    path: str
    preimage_sha256: str
    postimage_sha256: str
    touched_chars: int
    touched_fraction: float
    edits: tuple[ResolvedEdit, ...]
    postimage: str


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_existing_path(repo_root: Path, rel_path: str) -> Path:
    if not isinstance(rel_path, str) or not rel_path.strip():
        raise ExactPatchError("PATCH_PATH_EMPTY")
    root = repo_root.resolve()
    lexical = root / rel_path
    if lexical.is_symlink():
        raise ExactPatchError("PATCH_TARGET_SYMLINK_FORBIDDEN")
    target = lexical.resolve()
    if target == root or root not in target.parents:
        raise ExactPatchError("PATCH_PATH_OUTSIDE_REPO")
    if not target.is_file():
        raise ExactPatchError("PATCH_TARGET_MUST_BE_EXISTING_FILE")
    return target


def _validated_edits(original: str, raw_edits: Sequence[Mapping[str, Any]]) -> tuple[ResolvedEdit, ...]:
    if not isinstance(raw_edits, Sequence) or isinstance(raw_edits, (str, bytes)):
        raise ExactPatchError("PATCH_EDITS_MUST_BE_SEQUENCE")
    if not raw_edits:
        raise ExactPatchError("PATCH_EDITS_EMPTY")
    if len(raw_edits) > MAX_EDITS:
        raise ExactPatchError("PATCH_TOO_MANY_EDITS")

    resolved: list[ResolvedEdit] = []
    for idx, raw in enumerate(raw_edits):
        if not isinstance(raw, Mapping):
            raise ExactPatchError(f"PATCH_EDIT_{idx}_NOT_OBJECT")
        find = raw.get("find")
        replace = raw.get("replace")
        if not isinstance(find, str) or not find:
            raise ExactPatchError(f"PATCH_EDIT_{idx}_FIND_EMPTY")
        if not isinstance(replace, str):
            raise ExactPatchError(f"PATCH_EDIT_{idx}_REPLACE_NOT_STRING")
        count = original.count(find)
        if count != 1:
            raise ExactPatchError(f"PATCH_EDIT_{idx}_FIND_NOT_UNIQUE:{count}")
        start = original.index(find)
        resolved.append(ResolvedEdit(start=start, end=start + len(find), find=find, replace=replace))

    resolved.sort(key=lambda e: (e.start, e.end))
    for left, right in zip(resolved, resolved[1:]):
        if right.start < left.end:
            raise ExactPatchError("PATCH_EDIT_SPANS_OVERLAP")
    return tuple(resolved)


def plan_exact_patch(
    repo_root: Path,
    patch: Mapping[str, Any],
    *,
    max_touched_fraction: float = DEFAULT_MAX_TOUCHED_FRACTION,
) -> PatchPlan:
    """Validate a patch completely and return its deterministic postimage.

    This function performs no write. ``max_touched_fraction`` is a caller policy
    knob for trusted/manual contexts; automatic Frankenstein dispatch should keep
    the default 0.35 bound.
    """
    if not isinstance(patch, Mapping):
        raise ExactPatchError("PATCH_NOT_OBJECT")
    if patch.get("schema") != SCHEMA:
        raise ExactPatchError("PATCH_SCHEMA_MISMATCH")
    if not (0.0 < max_touched_fraction <= 1.0):
        raise ExactPatchError("PATCH_MAX_TOUCHED_FRACTION_INVALID")

    rel_path = patch.get("path")
    target = _safe_existing_path(repo_root, rel_path)
    try:
        original = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ExactPatchError("PATCH_TARGET_NOT_UTF8") from exc

    expected_preimage = patch.get("preimage_sha256")
    if not isinstance(expected_preimage, str) or len(expected_preimage) != 64:
        raise ExactPatchError("PATCH_PREIMAGE_SHA256_INVALID")
    actual_preimage = sha256_text(original)
    if actual_preimage != expected_preimage.lower():
        raise ExactPatchError("PATCH_PREIMAGE_SHA256_MISMATCH")

    edits = _validated_edits(original, patch.get("edits", []))
    touched_chars = sum(edit.end - edit.start for edit in edits)
    touched_fraction = touched_chars / max(1, len(original))
    if touched_fraction > max_touched_fraction:
        raise ExactPatchError(
            f"PATCH_TOUCHED_FRACTION_EXCEEDED:{touched_fraction:.6f}>{max_touched_fraction:.6f}"
        )

    postimage = original
    for edit in reversed(edits):
        postimage = postimage[: edit.start] + edit.replace + postimage[edit.end :]

    rebuilt_parts: list[str] = []
    cursor = 0
    for edit in edits:
        rebuilt_parts.append(original[cursor : edit.start])
        rebuilt_parts.append(edit.replace)
        cursor = edit.end
    rebuilt_parts.append(original[cursor:])
    rebuilt = "".join(rebuilt_parts)
    if rebuilt != postimage:
        raise ExactPatchError("PATCH_UNCHANGED_REGION_INVARIANT_FAILED")

    return PatchPlan(
        path=rel_path,
        preimage_sha256=actual_preimage,
        postimage_sha256=sha256_text(postimage),
        touched_chars=touched_chars,
        touched_fraction=touched_fraction,
        edits=edits,
        postimage=postimage,
    )


def apply_exact_patch(
    repo_root: Path,
    patch: Mapping[str, Any],
    *,
    max_touched_fraction: float = DEFAULT_MAX_TOUCHED_FRACTION,
) -> PatchPlan:
    """Atomically apply a fully validated exact patch to one existing file."""
    plan = plan_exact_patch(repo_root, patch, max_touched_fraction=max_touched_fraction)
    target = _safe_existing_path(repo_root, plan.path)

    current = target.read_text(encoding="utf-8")
    if sha256_text(current) != plan.preimage_sha256:
        raise ExactPatchError("PATCH_PREIMAGE_CHANGED_BEFORE_WRITE")

    mode = stat.S_IMODE(target.stat().st_mode)
    parent = target.parent
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=parent, prefix=f".{target.name}.", suffix=".patch.tmp", delete=False
        ) as tmp:
            tmp.write(plan.postimage)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_name = tmp.name
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, target)
        tmp_name = None
        try:
            dir_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass

    final = target.read_text(encoding="utf-8")
    if sha256_text(final) != plan.postimage_sha256:
        raise ExactPatchError("PATCH_POSTIMAGE_SHA256_MISMATCH_AFTER_WRITE")
    return plan


def parse_patch_json(text: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExactPatchError("PATCH_JSON_INVALID") from exc
    if not isinstance(payload, Mapping):
        raise ExactPatchError("PATCH_JSON_NOT_OBJECT")
    return payload
