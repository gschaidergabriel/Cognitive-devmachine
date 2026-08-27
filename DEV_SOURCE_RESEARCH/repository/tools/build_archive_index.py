#!/usr/bin/env python3
"""Deterministic metadata index for the Frankenstein/EntityOS research archive.

The index is derived metadata only. It never edits source files and never decides truth.
It is designed so large archives can remain discoverable without copying their content
into narrative documentation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

SCHEMA = "FRANKENSTEIN_RESEARCH_ARCHIVE_INDEX/v1"
DEFAULT_ROOTS = (
    "research_entity",
    "research_sources",
    "receipts",
    "frank_reference",
    "benchmarks",
    "runtime_checks",
    "schemas",
    "tests",
)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".ndjson", ".py", ".toml", ".yaml", ".yml",
    ".clay", ".csv", ".tsv", ".ini", ".cfg", ".sh", ".sql",
}
SKIP_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def first_heading(path: Path, max_bytes: int = 64 * 1024) -> str | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    try:
        raw = path.open("rb").read(max_bytes)
        text = raw.decode("utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            value = stripped.lstrip("#").strip()
            if value:
                return value[:240]
    return None


def classify(rel: str) -> list[str]:
    p = rel.lower()
    labels: list[str] = []
    rules = (
        ("research_entity/claycode/autonomous/supervisor_", "authority_or_steering"),
        ("research_entity/continuity/", "continuity"),
        ("research_entity/topic_packets/", "topic_packet"),
        ("receipt", "receipt_or_evidence"),
        ("test", "test"),
        ("benchmark", "benchmark"),
        ("jspace", "jspace"),
        ("gwt", "gwt"),
        ("grid10", "grid10"),
        ("hcu", "hcu"),
        ("entityos", "entityos"),
        ("training", "training"),
        ("lora", "training"),
        ("iapt", "training"),
        ("soma", "training"),
        ("free_swarm", "free_swarm"),
        ("free swarm", "free_swarm"),
        ("distillery", "distillery"),
        ("forge", "forge"),
        ("frank", "historical_frank_or_frankenstein"),
        ("xeno", "xeno_compatibility"),
        ("claycode", "claycode"),
        ("unifieddb", "unifieddb"),
        ("hyperposition", "hyperposition"),
        ("grf", "grf"),
    )
    for needle, label in rules:
        if needle in p and label not in labels:
            labels.append(label)
    if not labels:
        labels.append("uncategorized")
    return labels


def iter_files(repo_root: Path, roots: Iterable[str]) -> Iterable[Path]:
    for root_name in sorted(set(roots)):
        root = repo_root / root_name
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIR_NAMES)
            base = Path(dirpath)
            for name in sorted(filenames):
                path = base / name
                if path.is_symlink():
                    continue
                if path.is_file():
                    yield path


def build_index(repo_root: Path, roots: Iterable[str], max_hash_bytes: int | None = None) -> dict:
    repo_root = repo_root.resolve()
    entries = []
    for path in iter_files(repo_root, roots):
        rel = path.relative_to(repo_root).as_posix()
        size = path.stat().st_size
        if max_hash_bytes is not None and size > max_hash_bytes:
            digest = None
            hash_status = "SKIPPED_OVERSIZE"
        else:
            digest = sha256_file(path)
            hash_status = "SHA256"
        entries.append({
            "path": rel,
            "size_bytes": size,
            "sha256": digest,
            "hash_status": hash_status,
            "suffix": path.suffix.lower(),
            "heading": first_heading(path),
            "labels": classify(rel),
        })
    entries.sort(key=lambda e: e["path"])
    roots_present = [r for r in sorted(set(roots)) if (repo_root / r).exists()]
    return {
        "schema": SCHEMA,
        "derived_not_authority": True,
        "repo_root_name": repo_root.name,
        "roots_requested": sorted(set(roots)),
        "roots_present": roots_present,
        "entry_count": len(entries),
        "entries": entries,
    }


def write_json_atomic(out_path: Path, payload: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, out_path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo_root", nargs="?", default=".")
    p.add_argument("--root", dest="roots", action="append", default=None,
                   help="archive root relative to repo; repeatable")
    p.add_argument("--output", default="DEV_SOURCE_RESEARCH/archive/RESEARCH_ARCHIVE_INDEX.json")
    p.add_argument("--max-hash-bytes", type=int, default=None,
                   help="skip hashing files larger than this many bytes; default hashes all files")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    roots = args.roots or list(DEFAULT_ROOTS)
    payload = build_index(repo_root, roots, args.max_hash_bytes)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    write_json_atomic(output, payload)
    print(json.dumps({"schema": SCHEMA, "entries": payload["entry_count"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())