#!/usr/bin/env python3
"""Lint active execution surfaces for references to superseded _vN tool variants."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_version_index_generate import build_index, serialize

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "research_entity" / "tooling" / "TOOL_VERSION_INDEX.json"
DEFAULT_ALLOWLIST = ROOT / "research_entity" / "tooling" / "TOOL_VERSION_HISTORICAL_ALLOWLIST.json"

ACTIVE_PREFIXES = (
    ".github/workflows/",
    ".claude/hooks/",
    "rae_core/",
    "tools/",
)
ACTIVE_ROOT_FILES = {"rae.py"}
TEXT_SUFFIXES = {".py", ".yml", ".yaml", ".json", ".toml", ".sh"}


def _rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def active_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for prefix in ACTIVE_PREFIXES:
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                found.append(path)
    for name in ACTIVE_ROOT_FILES:
        path = root / name
        if path.is_file():
            found.append(path)
    return sorted(set(found), key=lambda p: _rel(p, root))


def load_allowlist(path: Path) -> tuple[dict[tuple[str, str], str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return {}, []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, [f"allowlist_invalid_json: {exc}"]
    if doc.get("schema") != "TOOL_VERSION_HISTORICAL_ALLOWLIST/v1":
        errors.append("allowlist_bad_schema")
    entries: dict[tuple[str, str], str] = {}
    for i, row in enumerate(doc.get("entries", []), 1):
        referrer = row.get("referrer")
        tool = row.get("tool")
        reason = row.get("reason")
        if not isinstance(referrer, str) or not isinstance(tool, str):
            errors.append(f"allowlist_entry_{i}_missing_referrer_or_tool")
            continue
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"allowlist_entry_{i}_missing_reason")
            continue
        key = (referrer, tool)
        if key in entries:
            errors.append(f"allowlist_duplicate:{referrer}:{tool}")
        entries[key] = reason.strip()
    return entries, errors


def lint_root(root: Path, index_path: Path, allowlist_path: Path) -> dict[str, Any]:
    root = root.resolve()
    expected = build_index(root)
    errors: list[str] = []
    if not index_path.exists():
        return {"ok": False, "errors": ["index_missing"], "stale_references": [], "allowed_references": []}
    try:
        actual_text = index_path.read_text(encoding="utf-8")
        actual = json.loads(actual_text)
    except Exception as exc:
        return {"ok": False, "errors": [f"index_invalid:{exc}"], "stale_references": [], "allowed_references": []}
    if actual_text != serialize(expected):
        errors.append("index_not_current_or_not_canonical")

    ambiguous = [g["family"] for g in expected["groups"] if g["ambiguous_highest_version"]]
    if ambiguous:
        errors.append("ambiguous_highest_versions:" + ",".join(ambiguous))

    superseded = [row["path"] for row in expected["tools"] if row["status"] == "SUPERSEDED"]
    allow, allow_errors = load_allowlist(allowlist_path)
    errors.extend(allow_errors)

    stale = []
    allowed = []
    observed_pairs = set()
    for path in active_files(root):
        rel = _rel(path, root)
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        for tool in superseded:
            if rel == tool:
                continue
            basename = Path(tool).name
            if tool not in text and basename not in text:
                continue
            pair = (rel, tool)
            observed_pairs.add(pair)
            rec = {"referrer": rel, "tool": tool}
            if pair in allow:
                rec["reason"] = allow[pair]
                allowed.append(rec)
            else:
                stale.append(rec)

    superseded_set = set(superseded)
    for pair, reason in sorted(allow.items()):
        referrer, tool = pair
        if tool not in superseded_set:
            errors.append(f"allowlist_tool_not_superseded:{referrer}:{tool}")
        elif pair not in observed_pairs:
            errors.append(f"allowlist_entry_not_observed:{referrer}:{tool}")

    if stale:
        errors.append(f"unallowlisted_superseded_references:{len(stale)}")

    return {
        "schema": "TOOL_VERSION_INDEX_LINT_RESULT/v1",
        "ok": not errors,
        "errors": errors,
        "inventory": expected["inventory"],
        "active_file_count": len(active_files(root)),
        "stale_references": sorted(stale, key=lambda r: (r["referrer"], r["tool"])),
        "allowed_references": sorted(allowed, key=lambda r: (r["referrer"], r["tool"])),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--index", default=None)
    ap.add_argument("--allowlist", default=None)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    index = Path(args.index).resolve() if args.index else root / "research_entity" / "tooling" / "TOOL_VERSION_INDEX.json"
    allowlist = Path(args.allowlist).resolve() if args.allowlist else root / "research_entity" / "tooling" / "TOOL_VERSION_HISTORICAL_ALLOWLIST.json"
    result = lint_root(root, index, allowlist)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
