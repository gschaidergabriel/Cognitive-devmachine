"""Exact, bounded edits for Frankenstein helper-generated source changes.

This module is intentionally provider-agnostic and contains no network, secret,
provider, subprocess, git, or model calls.  It converts model-readable
SEARCH/REPLACE edit blocks into deterministic file transformations with an
exact-preimage invariant.

Safety model
------------
* Existing files may only be changed through exact SEARCH -> REPLACE spans.
* Every SEARCH must occur exactly once in the *original* file.
* Multiple spans in one file must not overlap.
* The total original text replaced in one file is bounded by policy (25% by
  default), so a helper cannot silently rewrite most of a large file.
* Full-file replacement is rejected by the default policy.
* Before writing, the on-disk SHA-256 must still match the planned preimage.
* New files use an explicit NEW_FILE block and must not already exist.
* Paths resolving outside repo_root are rejected.

The returned receipt is evidence of the exact local transform only.  It is not
runtime/product/training credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import Iterable


EDIT_BLOCK_RE = re.compile(
    r"EDIT:\s*(?P<path>\S+)\s*\n"
    r"<<<<<<< SEARCH\n(?P<search>.*?)\n=======\n(?P<replace>.*?)\n>>>>>>> REPLACE",
    re.DOTALL,
)
NEW_FILE_BLOCK_RE = re.compile(
    r"NEW_FILE:\s*(?P<path>\S+)\s*\n```[a-zA-Z0-9_+.-]*\n(?P<content>.*?)\n```",
    re.DOTALL,
)


class SafeEditError(ValueError):
    """Raised when a proposed edit cannot be admitted safely."""


class StalePreimageError(SafeEditError):
    """Raised when a file changed after planning and before apply."""


@dataclass(frozen=True)
class EditBlock:
    path: str
    search: str
    replace: str


@dataclass(frozen=True)
class NewFileBlock:
    path: str
    content: str


@dataclass(frozen=True)
class SafeEditPolicy:
    max_replaced_fraction: float = 0.25
    max_files: int = 16
    max_edit_blocks: int = 64
    max_new_files: int = 16
    max_total_added_chars: int = 1_000_000

    def validate(self) -> None:
        if not (0.0 < self.max_replaced_fraction < 1.0):
            raise SafeEditError("max_replaced_fraction must be strictly between 0 and 1")
        for name in ("max_files", "max_edit_blocks", "max_new_files", "max_total_added_chars"):
            if getattr(self, name) <= 0:
                raise SafeEditError(f"{name} must be positive")


@dataclass(frozen=True)
class PlannedFileEdit:
    path: str
    resolved_path: Path
    original_text: str
    result_text: str
    original_sha256: str
    result_sha256: str
    original_chars: int
    replaced_chars: int
    replaced_fraction: float
    unchanged_chars: int
    spans: tuple[dict, ...]


@dataclass(frozen=True)
class PlannedNewFile:
    path: str
    resolved_path: Path
    content: str
    result_sha256: str


@dataclass(frozen=True)
class SafeEditPlan:
    repo_root: Path
    edits: tuple[PlannedFileEdit, ...]
    new_files: tuple[PlannedNewFile, ...]

    @property
    def touched_paths(self) -> tuple[str, ...]:
        return tuple([e.path for e in self.edits] + [n.path for n in self.new_files])


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_inside(repo_root: Path, rel_path: str) -> Path:
    if not rel_path or rel_path.startswith("/"):
        raise SafeEditError(f"path must be non-empty and repository-relative: {rel_path!r}")
    root = repo_root.resolve()
    target = (root / rel_path).resolve()
    if target != root and root not in target.parents:
        raise SafeEditError(f"path escapes repo_root: {rel_path}")
    if target == root:
        raise SafeEditError("repository root itself is not an editable file path")
    return target


def parse_safe_edit_response(response_text: str) -> tuple[list[EditBlock], list[NewFileBlock]]:
    """Parse exact edit blocks and explicit new-file blocks from helper text."""
    edits = [
        EditBlock(m.group("path").strip(), m.group("search"), m.group("replace"))
        for m in EDIT_BLOCK_RE.finditer(response_text)
    ]
    new_files = [
        NewFileBlock(m.group("path").strip(), m.group("content"))
        for m in NEW_FILE_BLOCK_RE.finditer(response_text)
    ]
    return edits, new_files


def _plan_one_existing_file(
    path: str,
    target: Path,
    blocks: list[EditBlock],
    policy: SafeEditPolicy,
) -> PlannedFileEdit:
    if not target.is_file():
        raise SafeEditError(f"EDIT target does not exist as a regular file: {path}")
    try:
        original = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SafeEditError(f"EDIT target is not UTF-8 text: {path}") from exc

    span_rows: list[tuple[int, int, EditBlock]] = []
    total_added = 0
    for block in blocks:
        if block.search == "":
            raise SafeEditError(f"empty SEARCH is forbidden: {path}")
        count = original.count(block.search)
        if count != 1:
            raise SafeEditError(
                f"SEARCH must occur exactly once in original file: {path} occurrence_count={count}"
            )
        start = original.index(block.search)
        end = start + len(block.search)
        span_rows.append((start, end, block))
        total_added += max(0, len(block.replace) - len(block.search))

    span_rows.sort(key=lambda row: row[0])
    for prior, current in zip(span_rows, span_rows[1:]):
        if current[0] < prior[1]:
            raise SafeEditError(f"overlapping SEARCH spans are forbidden: {path}")

    replaced_chars = sum(end - start for start, end, _ in span_rows)
    original_chars = len(original)
    if original_chars == 0:
        raise SafeEditError(f"empty existing file cannot be rewritten via EDIT; use an explicit manual path: {path}")
    replaced_fraction = replaced_chars / original_chars
    if replaced_fraction > policy.max_replaced_fraction:
        raise SafeEditError(
            f"edit budget exceeded for {path}: replaced_fraction={replaced_fraction:.6f} "
            f"limit={policy.max_replaced_fraction:.6f}"
        )
    if total_added > policy.max_total_added_chars:
        raise SafeEditError(f"added-text budget exceeded for {path}")

    # Apply from the end so original offsets remain valid.  This construction
    # proves every byte/character outside the declared original spans survives.
    result = original
    receipt_spans: list[dict] = []
    for start, end, block in reversed(span_rows):
        result = result[:start] + block.replace + result[end:]
    for start, end, block in span_rows:
        receipt_spans.append(
            {
                "start": start,
                "end": end,
                "search_sha256": _sha256_text(block.search),
                "replace_sha256": _sha256_text(block.replace),
                "search_chars": len(block.search),
                "replace_chars": len(block.replace),
            }
        )

    return PlannedFileEdit(
        path=path,
        resolved_path=target,
        original_text=original,
        result_text=result,
        original_sha256=_sha256_text(original),
        result_sha256=_sha256_text(result),
        original_chars=original_chars,
        replaced_chars=replaced_chars,
        replaced_fraction=replaced_fraction,
        unchanged_chars=original_chars - replaced_chars,
        spans=tuple(receipt_spans),
    )


def plan_safe_edits(
    repo_root: Path,
    edits: Iterable[EditBlock],
    new_files: Iterable[NewFileBlock] = (),
    *,
    policy: SafeEditPolicy | None = None,
) -> SafeEditPlan:
    """Validate all edits and return an immutable exact-preimage plan."""
    policy = policy or SafeEditPolicy()
    policy.validate()
    repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        raise SafeEditError(f"repo_root is not a directory: {repo_root}")

    edit_list = list(edits)
    new_list = list(new_files)
    if not edit_list and not new_list:
        raise SafeEditError("no EDIT or NEW_FILE blocks supplied")
    if len(edit_list) > policy.max_edit_blocks:
        raise SafeEditError("too many EDIT blocks")
    if len(new_list) > policy.max_new_files:
        raise SafeEditError("too many NEW_FILE blocks")

    grouped: dict[str, list[EditBlock]] = {}
    for block in edit_list:
        grouped.setdefault(block.path, []).append(block)

    new_by_path: dict[str, NewFileBlock] = {}
    for block in new_list:
        if block.path in new_by_path:
            raise SafeEditError(f"duplicate NEW_FILE path: {block.path}")
        new_by_path[block.path] = block

    overlap = set(grouped) & set(new_by_path)
    if overlap:
        raise SafeEditError(f"path cannot be both EDIT and NEW_FILE: {sorted(overlap)}")
    if len(set(grouped) | set(new_by_path)) > policy.max_files:
        raise SafeEditError("too many touched files")

    planned_edits: list[PlannedFileEdit] = []
    for path in sorted(grouped):
        target = _resolve_inside(repo_root, path)
        planned_edits.append(_plan_one_existing_file(path, target, grouped[path], policy))

    planned_new: list[PlannedNewFile] = []
    for path in sorted(new_by_path):
        target = _resolve_inside(repo_root, path)
        if target.exists():
            raise SafeEditError(f"NEW_FILE target already exists: {path}")
        content = new_by_path[path].content
        planned_new.append(
            PlannedNewFile(path, target, content, _sha256_text(content))
        )

    return SafeEditPlan(repo_root, tuple(planned_edits), tuple(planned_new))


def _write_text_via_sibling_temp(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.safeedit-", dir=str(target.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def apply_safe_edit_plan(plan: SafeEditPlan) -> dict:
    """Apply a validated plan after re-checking exact preimages.

    All validation and stale-preimage checks occur before the first write.
    A best-effort rollback restores touched existing files and removes newly
    created targets if a write fails mid-apply.
    """
    for edit in plan.edits:
        try:
            current = edit.resolved_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise StalePreimageError(f"cannot re-read preimage: {edit.path}") from exc
        if _sha256_text(current) != edit.original_sha256:
            raise StalePreimageError(f"preimage changed after planning: {edit.path}")
    for new_file in plan.new_files:
        if new_file.resolved_path.exists():
            raise StalePreimageError(f"NEW_FILE appeared after planning: {new_file.path}")

    written_existing: list[PlannedFileEdit] = []
    written_new: list[PlannedNewFile] = []
    try:
        for edit in plan.edits:
            _write_text_via_sibling_temp(edit.resolved_path, edit.result_text)
            written_existing.append(edit)
        for new_file in plan.new_files:
            _write_text_via_sibling_temp(new_file.resolved_path, new_file.content)
            written_new.append(new_file)
    except Exception:
        for new_file in reversed(written_new):
            try:
                new_file.resolved_path.unlink(missing_ok=True)
            except OSError:
                pass
        for edit in reversed(written_existing):
            try:
                _write_text_via_sibling_temp(edit.resolved_path, edit.original_text)
            except OSError:
                pass
        raise

    return {
        "schema": "FRANKENSTEIN_SAFE_EDIT_RECEIPT/v1",
        "touched_paths": list(plan.touched_paths),
        "existing_file_edits": [
            {
                "path": edit.path,
                "original_sha256": edit.original_sha256,
                "result_sha256": edit.result_sha256,
                "original_chars": edit.original_chars,
                "replaced_chars": edit.replaced_chars,
                "replaced_fraction": edit.replaced_fraction,
                "unchanged_chars": edit.unchanged_chars,
                "spans": list(edit.spans),
            }
            for edit in plan.edits
        ],
        "new_files": [
            {"path": f.path, "result_sha256": f.result_sha256, "chars": len(f.content)}
            for f in plan.new_files
        ],
        "scope": "EXACT_LOCAL_TEXT_TRANSFORM_ONLY",
        "promotion": "NONE",
    }


def parse_plan_apply(
    repo_root: Path,
    response_text: str,
    *,
    policy: SafeEditPolicy | None = None,
) -> dict:
    """Convenience entrypoint for a provider/model response already in hand."""
    edits, new_files = parse_safe_edit_response(response_text)
    plan = plan_safe_edits(repo_root, edits, new_files, policy=policy)
    return apply_safe_edit_plan(plan)
