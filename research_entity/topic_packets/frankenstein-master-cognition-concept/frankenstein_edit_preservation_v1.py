"""Deterministic preservation gate for edits to existing text files.

This module is deliberately provider/model agnostic. Generated edits are
candidates: they must satisfy exact preimage identity, declared edit scope, an
explicit deletion budget when old lines are removed/replaced, and exact changed
path closure before they can be considered safe to commit.

A model-proposed contract cannot self-grant full-file replacement authority.
That operation needs both an explicit reason in the contract and a separate
caller-supplied capability from the trusted orchestration/effect boundary.

Evidence boundary: passing this component does not establish whole Frankenstein,
EntityOS, HCU, provider, or training runtime acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Iterable, Sequence
import difflib

SCHEMA = "FRANKENSTEIN_EDIT_PRESERVATION/v1"


class EditPreservationError(ValueError):
    """Raised when an edit fails a deterministic preservation invariant."""


@dataclass(frozen=True)
class LineRange:
    """Inclusive 1-based line range in the PREIMAGE allowed to change.

    For a pure insertion between preimage lines, use a zero-width insertion
    anchor by setting ``start == end`` to the adjacent preimage line. Insertions
    at the beginning use line 1; insertions at EOF use the final preimage line.
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1 or self.end < self.start:
            raise EditPreservationError("invalid declared line range")

    def contains_preimage_span(self, start0: int, end0: int, line_count: int) -> bool:
        """Return whether a difflib preimage span is covered by this range.

        ``start0``/``end0`` are zero-based half-open indexes from SequenceMatcher.
        Insertions have start0 == end0 and are mapped to the nearest preimage line.
        """
        if line_count <= 0:
            return False
        if start0 == end0:
            anchor = min(max(start0 + 1, 1), line_count)
            return self.start <= anchor <= self.end
        first = start0 + 1
        last = end0
        return self.start <= first and last <= self.end


@dataclass(frozen=True)
class EditContract:
    path: str
    preimage_sha256: str
    allowed_preimage_ranges: tuple[LineRange, ...]
    declared_changed_paths: tuple[str, ...]
    allow_full_file_replacement: bool = False
    full_file_replacement_reason: str | None = None
    max_deleted_preimage_lines: int | None = None

    def __post_init__(self) -> None:
        _validate_repo_relative_path(self.path)
        if len(self.preimage_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.preimage_sha256.lower()
        ):
            raise EditPreservationError("preimage_sha256 must be a 64-character hex digest")
        for p in self.declared_changed_paths:
            _validate_repo_relative_path(p)
        if len(self.declared_changed_paths) != len(set(self.declared_changed_paths)):
            raise EditPreservationError("declared_changed_paths contains duplicates")
        if self.path not in self.declared_changed_paths:
            raise EditPreservationError("edited path must be present in declared_changed_paths")
        if self.allow_full_file_replacement and not (
            self.full_file_replacement_reason or ""
        ).strip():
            raise EditPreservationError("full-file replacement requires an explicit reason")
        if self.max_deleted_preimage_lines is not None and self.max_deleted_preimage_lines < 0:
            raise EditPreservationError("max_deleted_preimage_lines cannot be negative")


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _validate_repo_relative_path(path: str) -> None:
    if not path or "\\" in path:
        raise EditPreservationError("path must be a non-empty POSIX repository-relative path")
    p = PurePosixPath(path)
    if p.is_absolute() or any(part in ("", ".", "..") for part in p.parts):
        raise EditPreservationError("absolute, traversal, or ambiguous repository paths are forbidden")
    if str(p) != path:
        raise EditPreservationError("path must be normalized")


def validate_changed_path_set(
    actual_changed_paths: Iterable[str], declared_changed_paths: Sequence[str]
) -> None:
    actual = tuple(sorted(set(actual_changed_paths)))
    declared = tuple(sorted(set(declared_changed_paths)))
    for p in actual + declared:
        _validate_repo_relative_path(p)
    if actual != declared:
        raise EditPreservationError(
            f"changed-file set mismatch: actual={actual!r} declared={declared!r}"
        )


def _changed_preimage_spans(before_lines: list[str], after_lines: list[str]):
    matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            yield tag, i1, i2, j1, j2


def _validate_declared_ranges(ranges: Sequence[LineRange], line_count: int) -> None:
    if line_count == 0:
        if ranges:
            raise EditPreservationError(
                "empty preimage cannot declare line ranges; use the explicit full-file capability"
            )
        return
    for item in ranges:
        if item.end > line_count:
            raise EditPreservationError(
                f"declared line range exceeds preimage: {item.start}-{item.end} > {line_count}"
            )


def validate_edit(
    preimage: str,
    postimage: str,
    contract: EditContract,
    *,
    full_file_replacement_capability: bool = False,
) -> dict:
    """Validate one existing-file edit and return a deterministic receipt payload.

    The gate binds the edit to the exact preimage digest. Unless a separately
    authorized full-file replacement is admitted, every changed preimage span
    must fall within a declared range. Any deletion/replacement of old lines
    requires an explicit deletion budget; the budget is defense in depth and
    never substitutes for declared scope.
    """
    actual_preimage_sha = sha256_text(preimage)
    if actual_preimage_sha != contract.preimage_sha256.lower():
        raise EditPreservationError(
            f"stale or wrong preimage: expected={contract.preimage_sha256.lower()} actual={actual_preimage_sha}"
        )

    before_lines = preimage.splitlines(keepends=True)
    after_lines = postimage.splitlines(keepends=True)
    _validate_declared_ranges(contract.allowed_preimage_ranges, len(before_lines))

    if contract.allow_full_file_replacement and not full_file_replacement_capability:
        raise EditPreservationError(
            "full-file replacement contract cannot self-authorize; trusted capability required"
        )

    changed = list(_changed_preimage_spans(before_lines, after_lines))
    deleted_preimage_lines = 0
    changed_preimage_lines: set[int] = set()
    scope_violations: list[tuple[str, int, int, int, int]] = []

    for tag, i1, i2, j1, j2 in changed:
        if tag in ("delete", "replace"):
            deleted_preimage_lines += i2 - i1
        changed_preimage_lines.update(range(i1, i2))
        if contract.allow_full_file_replacement:
            continue
        if not any(
            r.contains_preimage_span(i1, i2, len(before_lines))
            for r in contract.allowed_preimage_ranges
        ):
            scope_violations.append((tag, i1, i2, j1, j2))

    if scope_violations:
        raise EditPreservationError(
            "edit touches undeclared preimage regions: " + repr(scope_violations)
        )

    # A contract that declares ordinary ranges must not silently turn an actual
    # complete replacement of all preimage lines into a normal scoped edit.
    if (
        before_lines
        and changed
        and len(changed_preimage_lines) == len(before_lines)
        and not contract.allow_full_file_replacement
    ):
        raise EditPreservationError(
            "actual full-file replacement requires explicit separate authorization"
        )

    if deleted_preimage_lines and contract.max_deleted_preimage_lines is None:
        raise EditPreservationError(
            "deletion/replacement requires an explicit max_deleted_preimage_lines budget"
        )
    if (
        contract.max_deleted_preimage_lines is not None
        and deleted_preimage_lines > contract.max_deleted_preimage_lines
    ):
        raise EditPreservationError(
            f"declared deletion budget exceeded: deleted={deleted_preimage_lines} "
            f"budget={contract.max_deleted_preimage_lines}"
        )

    # Full replacement authorization must be genuinely explicit; an empty range
    # list does not silently widen scope.
    if changed and not contract.allow_full_file_replacement and not contract.allowed_preimage_ranges:
        raise EditPreservationError("changed existing file without any declared edit range")

    return {
        "schema": SCHEMA,
        "path": contract.path,
        "preimage_sha256": actual_preimage_sha,
        "postimage_sha256": sha256_text(postimage),
        "preimage_line_count": len(before_lines),
        "postimage_line_count": len(after_lines),
        "changed_opcode_count": len(changed),
        "changed_preimage_line_count": len(changed_preimage_lines),
        "deleted_preimage_lines": deleted_preimage_lines,
        "full_file_replacement_authorized": bool(
            contract.allow_full_file_replacement and full_file_replacement_capability
        ),
        "preservation_gate": "PASS",
    }


def validate_candidate(
    preimage: str,
    postimage: str,
    contract: EditContract,
    *,
    actual_changed_paths: Iterable[str],
    full_file_replacement_capability: bool = False,
) -> dict:
    """Atomic candidate gate: file-set closure plus per-file preservation."""
    validate_changed_path_set(actual_changed_paths, contract.declared_changed_paths)
    return validate_edit(
        preimage,
        postimage,
        contract,
        full_file_replacement_capability=full_file_replacement_capability,
    )
