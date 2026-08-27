#!/usr/bin/env python3
"""Read-only Triggerword-3 repository-root inventory.

This tool never moves, deletes, rewrites, commits, pushes, imports provider SDKs,
reads secrets, or performs network I/O. It classifies tracked root entries and,
when requested, reports literal Git-grep reference candidates. Literal references
are dependency candidates only; zero literal references is not proof that a path
is safe to move.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

TARGET_SURFACE = {
    "README.md",
    "HUMAN_READ_THIS",
    "DEV_SOURCE_RESEARCH",
    "AI_START_HERE_DO_NOT_SCAN_REPO",
}

SEMANTIC_ROOT = {
    ".github",
    ".gitignore",
    ".claude",
    "AGENTS.md",
    "CLAUDE.md",
}

BOOT_AUTHORITY_HINTS = (
    "AUTHORITY",
    "BOOT",
    "BOOTSTRAP",
    "CURRENT",
    "DIRECTIVE",
    "JOIN",
    "PROJECT_SOURCE",
    "RAE_",
)


class InventoryError(RuntimeError):
    """Inventory could not be resolved without guessing."""


def git(repo: Path, *args: str, allow_nomatch: bool = False) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    allowed = {0, 1} if allow_nomatch else {0}
    if proc.returncode not in allowed:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise InventoryError(f"git {' '.join(args)} failed: {err}")
    return proc.stdout


def repository_root(start: Path) -> Path:
    out = git(start, "rev-parse", "--show-toplevel")
    root = Path(out.decode("utf-8").strip()).resolve()
    if not root.exists():
        raise InventoryError("resolved repository root does not exist")
    return root


def tracked_root_entries(repo: Path) -> list[str]:
    raw = git(repo, "ls-tree", "-z", "--name-only", "HEAD")
    return sorted(
        part.decode("utf-8", errors="surrogateescape")
        for part in raw.split(b"\0")
        if part
    )


def literal_reference_files(repo: Path, root_entry: str) -> list[str]:
    # Read-only heuristic. It intentionally does not claim runtime consumption.
    raw = git(
        repo,
        "grep",
        "-l",
        "-z",
        "-F",
        "--",
        root_entry,
        allow_nomatch=True,
    )
    return sorted(
        part.decode("utf-8", errors="surrogateescape")
        for part in raw.split(b"\0")
        if part
    )


def classify(name: str, reference_count: int | None) -> str:
    if name in TARGET_SURFACE:
        return "TARGET_PUBLIC_SURFACE"
    if name in SEMANTIC_ROOT or name.startswith("."):
        return "SEMANTIC_ROOT_REVIEW_REQUIRED"
    upper = name.upper()
    if any(hint in upper for hint in BOOT_AUTHORITY_HINTS):
        return "BOOT_OR_AUTHORITY_REVIEW_REQUIRED"
    if reference_count is None:
        return "UNRESOLVED_REFERENCES_NOT_SCANNED"
    if reference_count:
        return "BLOCKED_LITERAL_DEPENDENCY_CANDIDATES"
    return "MOVE_CANDIDATE_ZERO_LITERAL_REFS_NOT_PROOF"


def build_inventory(
    repo: Path,
    scan_references: bool,
    max_reference_files: int = 25,
) -> dict[str, Any]:
    head = git(repo, "rev-parse", "HEAD").decode("utf-8").strip()
    entries = tracked_root_entries(repo)
    rows: list[dict[str, Any]] = []

    for name in entries:
        refs: list[str] | None = None
        # References are not useful for the four intended root surfaces.
        if scan_references and name not in TARGET_SURFACE:
            refs = literal_reference_files(repo, name)
        ref_count = None if refs is None else len(refs)
        row: dict[str, Any] = {
            "path": name,
            "classification": classify(name, ref_count),
            "literal_reference_count": ref_count,
        }
        if refs is not None:
            sample_limit = max(0, int(max_reference_files))
            row["literal_reference_files_sample"] = refs[:sample_limit]
            row["literal_reference_files_truncated"] = len(refs) > sample_limit
        rows.append(row)

    categories: dict[str, int] = {}
    for row in rows:
        categories[row["classification"]] = categories.get(row["classification"], 0) + 1

    return {
        "schema": "TRIGGER3_ROOT_INVENTORY/v1",
        "read_only": True,
        "repository": str(repo),
        "head": head,
        "target_public_surface": sorted(TARGET_SURFACE),
        "reference_scan_enabled": scan_references,
        "warning": (
            "Literal Git references are dependency candidates, not runtime-consumption proof. "
            "Zero literal references does not authorize a move."
        ),
        "root_entry_count": len(rows),
        "category_counts": dict(sorted(categories.items())),
        "entries": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        default=".",
        help="Any path inside the Git repository; resolved dynamically.",
    )
    parser.add_argument(
        "--references",
        action="store_true",
        help="Also run read-only git grep for literal dependency candidates.",
    )
    parser.add_argument(
        "--max-reference-files",
        type=int,
        default=25,
        help="Maximum reference-file sample stored per root entry (default: 25).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    args = parser.parse_args()

    try:
        root = repository_root(Path(args.repo).resolve())
        payload = build_inventory(
            root,
            args.references,
            max_reference_files=args.max_reference_files,
        )
    except InventoryError as exc:
        print(json.dumps({"schema": "TRIGGER3_ROOT_INVENTORY/v1", "error": str(exc)}))
        return 2

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
