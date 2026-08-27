#!/usr/bin/env python3
"""Read-only root migration inventory for Triggerword 3.

The script does not move, delete, rewrite, execute, import, or network-call project
code. It walks the current checkout, classifies top-level entries conservatively,
and searches likely text files for exact references to non-public root paths.
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
    ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".service", ".timer", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".clay",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
MAX_TEXT_BYTES = 2_000_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
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
    if path.is_file() and name.endswith((".md", ".txt", ".json", ".yaml", ".yml", ".toml")):
        return "EVIDENCE_OR_CONTROL_UNKNOWN"
    if path.is_dir():
        return "SOURCE_OR_ARCHIVE_UNKNOWN"
    return "UNKNOWN"


def iter_text_files(root: Path):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        b = Path(base)
        for name in files:
            p = b / name
            try:
                if p.suffix.lower() not in TEXT_EXTS or p.stat().st_size > MAX_TEXT_BYTES:
                    continue
            except OSError:
                continue
            yield p


def reference_variants(name: str) -> tuple[str, ...]:
    if name.startswith("."):
        return (name + "/", name)
    return (name + "/", "./" + name + "/", name)


def references_for(root: Path, target_name: str, text_files: list[Path]) -> list[dict]:
    refs: list[dict] = []
    variants = reference_variants(target_name)
    for p in text_files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(v in line for v in variants):
                hits.append(lineno)
        if hits:
            refs.append({
                "path": str(p.relative_to(root)),
                "line_numbers": hits[:100],
                "truncated": len(hits) > 100,
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
        item = {
            "path": path.name,
            "type": "directory" if path.is_dir() else "file",
            "class": cls,
            "move_status": "RETAIN" if cls in {"PUBLIC_ENTRY", "HOST_REQUIRED", "GITHUB_REQUIRED"} else "UNKNOWN_FAIL_CLOSED",
            "proposed_destination": None if cls in {"PUBLIC_ENTRY", "HOST_REQUIRED", "GITHUB_REQUIRED"} else f"DEV_SOURCE_RESEARCH/repository/{path.name}",
            "references": references_for(root, path.name, text_files) if path.name not in PUBLIC else [],
        }
        if path.is_file():
            try:
                item["size_bytes"] = path.stat().st_size
                item["sha256"] = sha256_file(path)
            except OSError as exc:
                item["hash_error"] = type(exc).__name__
        entries.append(item)

    unresolved = [x["path"] for x in entries if x["move_status"] == "UNKNOWN_FAIL_CLOSED"]
    return {
        "schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v1",
        "repo_root": str(root),
        "read_only": True,
        "public_target": sorted(PUBLIC),
        "strict_physical_target_reached": set(x["path"] for x in entries) == PUBLIC,
        "entries": entries,
        "unresolved_fail_closed": unresolved,
        "acceptance": "PASS" if not unresolved and set(x["path"] for x in entries) == PUBLIC else "IN_PROGRESS",
        "notes": [
            "Text references are candidate dependencies, not proof of runtime use.",
            "HOST_REQUIRED and GITHUB_REQUIRED are conservative classifications pending host/tool-specific proof.",
            "This script performs no relocation or mutation."
        ],
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", required=True, help="absolute or relative repository root")
    p.add_argument("--pretty", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    root = Path(args.repo_root)
    if not root.is_dir():
        print(json.dumps({"schema": "TRIGGERWORD3_ROOT_MIGRATION_INVENTORY/v1", "error": "repo root is not a directory"}))
        return 2
    data = build_inventory(root)
    print(json.dumps(data, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
