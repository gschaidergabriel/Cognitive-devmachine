#!/usr/bin/env python3
"""Deterministic guard for safe edits to existing repository files.

This module is intentionally provider-free.  It treats model/tool output as a proposal,
not repository truth.  Existing-file mutation receives credit only when the exact preimage
is bound and every changed old-file region is inside an explicitly declared edit scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import PurePosixPath
from typing import Iterable, Sequence

SCHEMA = "PREIMAGE_BOUND_EDIT_GUARD/v1"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_repo_path(path: str) -> bool:
    p = PurePosixPath(path)
    return bool(path) and not p.is_absolute() and ".." not in p.parts and "." not in p.parts[:1]


def _normalize_ranges(ranges: Iterable[Sequence[int]], old_line_count: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for item in ranges:
        if len(item) != 2:
            raise ValueError("each allowed_old_line_range must contain [start,end]")
        start, end = int(item[0]), int(item[1])
        if start < 1 or end < start or end > max(1, old_line_count):
            raise ValueError("allowed_old_line_range outside preimage")
        out.append((start, end))
    out.sort()
    for i in range(1, len(out)):
        if out[i][0] <= out[i - 1][1]:
            raise ValueError("allowed_old_line_ranges overlap")
    return out


def _span_allowed(old_i1: int, old_i2: int, ranges: list[tuple[int, int]], old_line_count: int) -> bool:
    """SequenceMatcher old indexes are zero-based half-open.

    For pure insertions i1==i2, bind the insertion to the adjacent old line.  This avoids
    an unscoped insertion at EOF/BOF while still permitting a narrow additive edit.
    """
    if old_i1 == old_i2:
        anchor = 1 if old_i1 == 0 else min(old_line_count, old_i1)
        return any(start <= anchor <= end for start, end in ranges)
    start_line = old_i1 + 1
    end_line = old_i2
    return any(start <= start_line and end_line <= end for start, end in ranges)


@dataclass(frozen=True)
class EditDecision:
    accepted: bool
    reason: str
    receipt: dict


def evaluate_edit(
    *,
    path: str,
    preimage_text: str,
    proposed_text: str,
    expected_preimage_sha256: str,
    current_text: str | None = None,
    allowed_old_line_ranges: Iterable[Sequence[int]],
    explicit_broad_deletion: bool = False,
    max_undeclared_deletion_fraction: float = 0.35,
) -> EditDecision:
    if not _safe_repo_path(path):
        return EditDecision(False, "UNSAFE_PATH", {"schema": SCHEMA, "path": path})

    pre_hash = sha256_text(preimage_text)
    proposed_hash = sha256_text(proposed_text)
    current_hash = sha256_text(current_text if current_text is not None else preimage_text)
    base_receipt = {
        "schema": SCHEMA,
        "path": path,
        "preimage_sha256": pre_hash,
        "proposed_sha256": proposed_hash,
        "current_sha256": current_hash,
        "provider_calls": 0,
        "secret_lookups": 0,
    }

    if expected_preimage_sha256 != pre_hash:
        return EditDecision(False, "EXPECTED_PREIMAGE_HASH_MISMATCH", base_receipt)
    if current_hash != pre_hash:
        return EditDecision(False, "STALE_PREIMAGE", base_receipt)

    old_lines = preimage_text.splitlines(keepends=True)
    new_lines = proposed_text.splitlines(keepends=True)
    try:
        ranges = _normalize_ranges(allowed_old_line_ranges, len(old_lines))
    except ValueError as exc:
        base_receipt["error"] = str(exc)
        return EditDecision(False, "INVALID_DECLARED_SCOPE", base_receipt)
    if not ranges:
        return EditDecision(False, "NO_DECLARED_EDIT_SCOPE", base_receipt)

    matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    changed_ops: list[dict] = []
    deleted_old_lines = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        allowed = _span_allowed(i1, i2, ranges, max(1, len(old_lines)))
        changed_ops.append({
            "tag": tag,
            "old_start": i1 + 1,
            "old_end": i2,
            "new_start": j1 + 1,
            "new_end": j2,
            "scope_allowed": allowed,
        })
        if tag in {"delete", "replace"}:
            deleted_old_lines += i2 - i1
        if not allowed:
            base_receipt.update({"declared_ranges": ranges, "changed_ops": changed_ops})
            return EditDecision(False, "CHANGE_OUTSIDE_DECLARED_SCOPE", base_receipt)

    deletion_fraction = deleted_old_lines / max(1, len(old_lines))
    base_receipt.update({
        "declared_ranges": ranges,
        "changed_ops": changed_ops,
        "old_line_count": len(old_lines),
        "new_line_count": len(new_lines),
        "deleted_old_lines": deleted_old_lines,
        "deletion_fraction": deletion_fraction,
        "explicit_broad_deletion": bool(explicit_broad_deletion),
    })
    if deletion_fraction > max_undeclared_deletion_fraction and not explicit_broad_deletion:
        return EditDecision(False, "BROAD_DELETION_NOT_EXPLICITLY_AUTHORIZED", base_receipt)

    if pre_hash == proposed_hash:
        return EditDecision(False, "NO_CHANGE", base_receipt)

    base_receipt["accepted"] = True
    return EditDecision(True, "ACCEPTED_EDIT_PROPOSAL", base_receipt)


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate an existing-file edit contract")
    ap.add_argument("--contract", required=True, help="JSON contract with path/preimage/proposed/scope")
    args = ap.parse_args()
    data = json.load(open(args.contract, "r", encoding="utf-8"))
    decision = evaluate_edit(
        path=data["path"],
        preimage_text=data["preimage_text"],
        proposed_text=data["proposed_text"],
        expected_preimage_sha256=data["expected_preimage_sha256"],
        current_text=data.get("current_text"),
        allowed_old_line_ranges=data["allowed_old_line_ranges"],
        explicit_broad_deletion=bool(data.get("explicit_broad_deletion", False)),
        max_undeclared_deletion_fraction=float(data.get("max_undeclared_deletion_fraction", 0.35)),
    )
    print(json.dumps({"accepted": decision.accepted, "reason": decision.reason, **decision.receipt}, sort_keys=True))
    return 0 if decision.accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
