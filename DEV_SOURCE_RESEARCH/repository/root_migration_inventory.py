#!/usr/bin/env python3
"""Canonical read-only Triggerword 3 root migration inventory.

This fuses the two parallel audit approaches that appeared during Triggerword 3:

* Git supplies the tracked top-level paths and exact object identities;
* fixed-string `git grep` supplies bounded textual dependency candidates;
* host/GitHub fixed-location surfaces are classified conservatively;
* unknowns fail closed;
* no move, rename, edit, stage, commit, package install, provider call, secret read,
  or project-code import is performed.

Text references are dependency candidates, not proof of runtime consumption. The audit
is a migration gate, not authority to make the root look clean by assumption.
"""
from __future__ import annotations

import argparse
import json
import shutil
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
HOST_REQUIRED = {"CLAUDE.md", "AGENTS.md", ".claude"}
GITHUB_REQUIRED = {".github", ".gitignore", ".gitattributes"}
CURRENT_CONTROL = {
    "CLAY_EXECUTION_AUTHORITY.md",
    "AUTHORITATIVE_STATE_RESOLUTION.md",
    "000_CLAY_CURRENT.md",
}


def script_repo_root() -> Path:
    # .../<repo>/DEV_SOURCE_RESEARCH/repository/root_migration_inventory.py
    return Path(__file__).resolve().parents[2]


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_git_checkout(root: Path) -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git executable not found")
    probe = run_git(root, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        raise RuntimeError(f"not a Git checkout: {root}")


def tracked_root_entries(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    proc = run_git(root, "ls-tree", "HEAD")
    for line in proc.stdout.splitlines():
        if not line:
            continue
        # Git ls-tree: <mode> SP <type> SP <object> TAB <path>
        meta, path = line.split("\t", 1)
        mode, object_type, object_sha = meta.split(" ", 2)
        rows.append(
            {
                "path": path,
                "mode": mode,
                "object_type": object_type,
                "object_sha": object_sha,
            }
        )
    return rows


def classify(path: str) -> tuple[str, str, str]:
    if path in PUBLIC_ENTRY:
        return "PUBLIC_ENTRY", "RETAIN", "retain_at_public_root"
    if path in HOST_REQUIRED:
        return "HOST_REQUIRED", "RETAIN_PENDING_ADAPTER", "retain_or_prove_host_discovery_adapter_before_move"
    if path in GITHUB_REQUIRED:
        return "GITHUB_REQUIRED", "RETAIN_PENDING_PLATFORM_REPLACEMENT", "retain_unless_platform_behavior_is_replaced_and_proven"
    if path in CURRENT_CONTROL:
        return "CURRENT_CONTROL", "BLOCKED_PENDING_CONSUMER_AUDIT", "inventory_every_consumer_before_move_or_minimal_pointer"
    if path.startswith("."):
        return "UNKNOWN", "BLOCKED_UNKNOWN_DEPENDENCY", "hidden_root_surface_requires_dependency_review"
    return "UNKNOWN", "BLOCKED_UNKNOWN_DEPENDENCY", "no_move_until_host_workflow_import_runtime_consumers_are_resolved"


def literal_reference_candidates(root: Path, target: str, limit: int) -> dict[str, Any]:
    # Fixed-string search across tracked files only. Return code 1 means no matches.
    proc = run_git(root, "grep", "-n", "-F", "--", target, check=False)
    if proc.returncode not in (0, 1):
        return {
            "count": None,
            "sample": [],
            "truncated": False,
            "error": proc.stderr.strip(),
            "interpretation": "git grep transport/tool failure; dependency remains unresolved",
        }

    lines = [line for line in proc.stdout.splitlines() if line]
    sample = lines[:limit] if limit else []
    return {
        "count": len(lines),
        "sample": sample,
        "truncated": len(lines) > len(sample),
        "interpretation": "literal tracked-text reference candidate only; not automatically a runtime dependency",
    }


def build_inventory(root: Path, reference_limit: int) -> dict[str, Any]:
    root = root.resolve()
    require_git_checkout(root)

    head = run_git(root, "rev-parse", "HEAD").stdout.strip()
    branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    dirty = bool(run_git(root, "status", "--porcelain=v1").stdout.strip())

    entries: list[dict[str, Any]] = []
    for row in tracked_root_entries(root):
        category, move_status, default_action = classify(row["path"])
        refs = literal_reference_candidates(root, row["path"], reference_limit)
        entries.append(
            {
                **row,
                "class": category,
                "move_status": move_status,
                "default_action": default_action,
                "proposed_destination": None,
                "text_reference_candidates": refs,
            }
        )

    tracked_names = {item["path"] for item in entries}
    unknown = [item["path"] for item in entries if item["class"] == "UNKNOWN"]
    missing_public = sorted(PUBLIC_ENTRY - tracked_names)
    extra_physical = sorted(tracked_names - PUBLIC_ENTRY)

    return {
        "schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v2",
        "repository_root": str(root),
        "git_head": head,
        "git_branch": branch,
        "working_tree_dirty": dirty,
        "tracked_source_only": True,
        "read_only_audit": True,
        "network_calls_performed": 0,
        "provider_calls_performed": 0,
        "secret_lookups_performed": 0,
        "move_actions_executed": 0,
        "target_public_root": sorted(PUBLIC_ENTRY),
        "entries": entries,
        "summary": {
            "top_level_tracked_entries": len(entries),
            "missing_public_entries": missing_public,
            "extra_physical_root_entries": extra_physical,
            "unknown_dependency_class": unknown,
            "strict_physical_target_reached": not missing_public and not extra_physical,
            "canonical_public_layer_present": not missing_public,
            "acceptance": "BLOCKED_PENDING_REVIEW" if unknown or missing_public else "INVENTORY_COMPLETE_REVIEW_STILL_REQUIRED",
        },
        "evidence_boundary": (
            "Git object identity proves tracked source identity only. Literal text hits are dependency candidates, "
            "not proof of runtime consumption. HOST_REQUIRED/GITHUB_REQUIRED remain conservative until host/platform "
            "behavior is tested. No relocation is authorized by this report."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical read-only Triggerword 3 root inventory")
    parser.add_argument(
        "--repo-root",
        help="optional checkout root; default resolves from this script's repository location",
    )
    parser.add_argument(
        "--reference-limit",
        type=int,
        default=12,
        help="maximum literal tracked-text reference samples per root path",
    )
    parser.add_argument(
        "--out",
        help="optional JSON output path; writing the report is the only optional filesystem mutation",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.reference_limit < 0:
        print(json.dumps({"schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v2", "error": "reference-limit must be >= 0"}))
        return 2

    root = Path(args.repo_root).expanduser() if args.repo_root else script_repo_root()
    try:
        inventory = build_inventory(root, args.reference_limit)
    except (RuntimeError, subprocess.SubprocessError, ValueError, OSError) as exc:
        print(
            json.dumps(
                {
                    "schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v2",
                    "read_only_audit": True,
                    "error": f"{exc.__class__.__name__}: {exc}",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.out:
        output = Path(args.out).expanduser()
        output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
