#!/usr/bin/env python3
"""Fail-closed Git-blob binding for material Forge runtime source.

Runtime-owned telemetry can legitimately dirty tracked repository files, so whole-
worktree cleanliness is not a sound executable-identity predicate. This helper
binds only the declared material source paths to exact committed blobs.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Iterable


def _git(root: Path, *args: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4,
        ).strip()
    except Exception:
        return None
    return value or None


def bind_material_sources(
    repo_root: Path,
    paths: Iterable[str | Path],
    *,
    commit: str = "HEAD",
) -> dict[str, object]:
    """Compare live material bytes to the exact blobs selected by ``commit``."""
    root = Path(repo_root).resolve()
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in paths:
        path = Path(raw)
        try:
            resolved = path.resolve(strict=True)
            rel = resolved.relative_to(root).as_posix()
        except (OSError, ValueError):
            key = str(path)
            if key not in seen:
                seen.add(key)
                rows.append({
                    "path": key,
                    "committed_blob": None,
                    "runtime_blob": None,
                    "blob_match": False,
                    "state": "MISSING_OR_OUTSIDE_REPO",
                })
            continue
        if rel in seen:
            continue
        seen.add(rel)
        committed = _git(root, "rev-parse", f"{commit}:{rel}")
        runtime = _git(root, "hash-object", "--", rel)
        match = bool(committed and runtime and committed == runtime)
        rows.append({
            "path": rel,
            "committed_blob": committed,
            "runtime_blob": runtime,
            "blob_match": match,
            "state": "BOUND" if match else "BLOB_MISMATCH",
        })
    complete = bool(rows) and all(row["blob_match"] is True for row in rows)
    return {
        "schema": "CLAY_FORGE_MATERIAL_SOURCE_BINDING/v1",
        "material_sources_match": complete,
        "material_sources": rows,
        "reason": "MATERIAL_SOURCES_MATCH_HEAD" if complete else "MATERIAL_SOURCE_BLOB_MISMATCH",
    }
