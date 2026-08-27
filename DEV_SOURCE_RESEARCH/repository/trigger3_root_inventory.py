#!/usr/bin/env python3
"""Read-only Triggerword 3 root topology/reference inventory.

Run from any directory inside a real Git checkout. The script resolves the repository
from its own path, asks Git for tracked top-level entries and exact object identities,
then uses literal `git grep` to sample references to each root path. It never moves,
renames, edits, stages, commits, installs, calls providers, or reads secrets.

Unknown dependency classes deliberately remain UNKNOWN. The audit is a migration gate,
not a tool for making the target tree look clean by assumption.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PUBLIC_ENTRY = {
    "README.md",
    "HUMAN_READ_THIS",
    "DEV_SOURCE_RESEARCH",
    "AI_START_HERE_DO_NOT_SCAN_REPO",
}
HOST_REQUIRED = {"CLAUDE.md", "AGENTS.md"}
GITHUB_REQUIRED = {".github", ".gitignore", ".gitattributes"}
CURRENT_CONTROL = {
    "CLAY_EXECUTION_AUTHORITY.md",
    "AUTHORITATIVE_STATE_RESOLUTION.md",
    "000_CLAY_CURRENT.md",
}


def root_from_script() -> Path:
    # .../<repo>/DEV_SOURCE_RESEARCH/repository/trigger3_root_inventory.py
    return Path(__file__).resolve().parents[2]


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_checkout(root: Path) -> None:
    proc = git(root, "rev-parse", "--is-inside-work-tree", check=False)
    if proc.returncode != 0 or proc.stdout.strip() != "true":
        raise RuntimeError(f"not a Git checkout: {root}")


def top_level_entries(root: Path) -> list[dict[str, str]]:
    proc = git(root, "ls-tree", "HEAD")
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        # <mode> SP <type> SP <object> TAB <file>
        meta, path = line.split("\t", 1)
        mode, obj_type, sha = meta.split(" ", 2)
        rows.append({"path": path, "mode": mode, "object_type": obj_type, "object_sha": sha})
    return rows


def classify(path: str) -> tuple[str, str]:
    if path in PUBLIC_ENTRY:
        return "PUBLIC_ENTRY", "retain_at_public_root"
    if path in HOST_REQUIRED:
        return "HOST_REQUIRED", "retain_or_prove_host_adapter_before_move"
    if path in GITHUB_REQUIRED:
        return "GITHUB_REQUIRED", "retain_as_operational_exception_unless_platform_replacement_proven"
    if path in CURRENT_CONTROL:
        return "CURRENT_CONTROL", "inventory_all_consumers_before_move_or_minimal_pointer"
    if path.startswith("."):
        return "UNKNOWN", "hidden_root_surface_requires_dependency_review"
    return "UNKNOWN", "no_move_until_consumers_and_runtime_role_are_resolved"


def literal_references(root: Path, needle: str, limit: int) -> dict[str, Any]:
    # `--` terminates git-grep options. Literal fixed-string search avoids regex surprises.
    proc = git(root, "grep", "-n", "-F", "--", needle, check=False)
    if proc.returncode not in (0, 1):
        return {"count_lower_bound": 0, "sample": [], "truncated": False, "error": proc.stderr.strip()}

    lines = [line for line in proc.stdout.splitlines() if line]
    sample: list[str] = []
    for line in lines:
        # Do not count the migration documents merely referring to the path as a consumer
        # signal when a more specific source exists. Keep them in the raw count but mark
        # the sample honestly; human review decides whether a hit is operational.
        sample.append(line)
        if len(sample) >= limit:
            break
    return {
        "count": len(lines),
        "sample": sample,
        "truncated": len(lines) > limit,
        "interpretation": "textual reference candidate only; not automatically a runtime dependency",
    }


def build_inventory(root: Path, reference_limit: int) -> dict[str, Any]:
    require_checkout(root)
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    dirty = bool(git(root, "status", "--porcelain=v1").stdout.strip())

    entries: list[dict[str, Any]] = []
    for row in top_level_entries(root):
        path = row["path"]
        category, action = classify(path)
        refs = literal_references(root, path, reference_limit)
        entries.append(
            {
                **row,
                "class": category,
                "default_action": action,
                "text_reference_candidates": refs,
                "move_status": "RETAIN" if category == "PUBLIC_ENTRY" else "BLOCKED_PENDING_REVIEW",
            }
        )

    unknown = sum(1 for item in entries if item["class"] == "UNKNOWN")
    return {
        "schema": "TRIGGERWORD3_ROOT_INVENTORY/v1",
        "repository_root": str(root),
        "git_head": head,
        "git_branch": branch,
        "working_tree_dirty": dirty,
        "read_only_audit": True,
        "target_public_root": sorted(PUBLIC_ENTRY),
        "entries": entries,
        "summary": {
            "top_level_tracked_entries": len(entries),
            "unknown_dependency_class": unknown,
            "move_actions_executed": 0,
            "acceptance": "BLOCKED_PENDING_REVIEW" if unknown else "INVENTORY_COMPLETE_REVIEW_STILL_REQUIRED",
        },
        "evidence_boundary": (
            "Literal Git references are dependency candidates, not proof of runtime consumption. "
            "A path remains blocked until host/workflow/import/runtime consumers are resolved."
        ),
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Read-only Triggerword 3 root dependency inventory")
    p.add_argument("--reference-limit", type=int, default=12, help="max textual reference samples per top-level path")
    p.add_argument("--out", help="optional JSON output path; stdout is always available if omitted")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.reference_limit < 0:
        raise SystemExit("--reference-limit must be >= 0")
    root = root_from_script()
    try:
        inventory = build_inventory(root, args.reference_limit)
    except (RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(json.dumps({"schema": "TRIGGERWORD3_ROOT_INVENTORY/v1", "error": str(exc)}, indent=2))
        return 2

    payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = Path.cwd() / out
        out.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
