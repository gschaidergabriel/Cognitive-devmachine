#!/usr/bin/env python3
"""Read-only root dependency inventory for Triggerword 3.

No move, delete, rewrite, project import, subprocess, credential access, or network call.
The output is a conservative candidate dependency map, not runtime evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

PUBLIC = {"README.md", "HUMAN_READ_THIS", "DEV_SOURCE_RESEARCH", "AI_START_HERE_DO_NOT_SCAN_REPO"}
HOST_REQUIRED = {"CLAUDE.md", "AGENTS.md", ".claude"}
GITHUB_REQUIRED = {".github", ".gitignore", ".gitattributes"}
TEXT_EXTS = {
    ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".json", ".jsonl",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".service", ".timer",
    ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".clay",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
MAX_TEXT_BYTES = 2_000_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(name: str, path: Path) -> str:
    if name in PUBLIC:
        return "PUBLIC_ENTRY"
    if name in HOST_REQUIRED:
        return "HOST_REQUIRED"
    if name in GITHUB_REQUIRED:
        return "GITHUB_REQUIRED"
    if name.startswith("."):
        return "UNKNOWN"
    if path.is_dir():
        return "SOURCE_OR_ARCHIVE_UNKNOWN"
    if path.is_file() and path.suffix.lower() in TEXT_EXTS:
        return "EVIDENCE_OR_CONTROL_UNKNOWN"
    return "UNKNOWN"


def iter_text_files(root: Path):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        base_path = Path(base)
        for name in files:
            path = base_path / name
            try:
                if path.suffix.lower() not in TEXT_EXTS or path.stat().st_size > MAX_TEXT_BYTES:
                    continue
            except OSError:
                continue
            yield path


def reference_variants(name: str) -> tuple[str, ...]:
    if name.startswith("."):
        return (name + "/", name)
    return (name + "/", "./" + name + "/", name)


def references_for(root: Path, target_name: str, text_files: list[Path]) -> list[dict]:
    variants = reference_variants(target_name)
    refs: list[dict] = []
    for path in text_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(v in line for v in variants):
                lines.append(lineno)
        if lines:
            refs.append({
                "path": str(path.relative_to(root)),
                "line_numbers": lines[:100],
                "truncated": len(lines) > 100,
            })
    return refs


def build_inventory(root: Path) -> dict:
    root = root.resolve()
    text_files = list(iter_text_files(root))
    entries = []
    for path in sorted(root.iterdir(), key=lambda p: p.name):
        if path.name == ".git":
            continue
        cls = classify(path.name, path)
        fixed = cls in {"PUBLIC_ENTRY", "HOST_REQUIRED", "GITHUB_REQUIRED"}
        item = {
            "path": path.name,
            "type": "directory" if path.is_dir() else "file",
            "class": cls,
            "move_status": "RETAIN_PENDING_PROOF" if fixed else "UNKNOWN_FAIL_CLOSED",
            "proposed_destination": None if fixed else f"DEV_SOURCE_RESEARCH/repository/{path.name}",
            "references": [] if path.name in PUBLIC else references_for(root, path.name, text_files),
        }
        if path.is_file():
            try:
                item["size_bytes"] = path.stat().st_size
                item["sha256"] = sha256_file(path)
            except OSError as exc:
                item["hash_error"] = type(exc).__name__
        entries.append(item)

    unresolved = [e["path"] for e in entries if e["move_status"] == "UNKNOWN_FAIL_CLOSED"]
    physical = {e["path"] for e in entries}
    return {
        "schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v1",
        "repo_root": str(root),
        "read_only": True,
        "public_target": sorted(PUBLIC),
        "strict_physical_target_reached": physical == PUBLIC,
        "entries": entries,
        "unresolved_fail_closed": unresolved,
        "acceptance": "PASS" if not unresolved and physical == PUBLIC else "IN_PROGRESS",
        "notes": [
            "Text references are candidate dependencies, not proof of runtime use.",
            "HOST_REQUIRED and GITHUB_REQUIRED are conservative pending host/tool-specific proof.",
            "No relocation or mutation is performed."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Triggerword 3 root dependency inventory")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root)
    if not root.is_dir():
        print(json.dumps({"schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v1", "error": "repo root is not a directory"}))
        return 2
    result = build_inventory(root)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
