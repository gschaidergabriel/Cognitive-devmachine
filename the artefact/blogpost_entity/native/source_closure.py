#!/usr/bin/env python3
"""Deterministic identity for the local C source closure of Mini Entity.

The native entry unit intentionally includes split repository-local ``.inc`` files.
Artifact provenance must therefore bind the transitive local include closure, not only
``mini_entity.c``. System ``<...>`` headers are dependency/toolchain identity and are
recorded separately by the native builder.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


_LOCAL_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.MULTILINE)
_DEFINE_STRING_RE = re.compile(r'^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\s+"([^"]*)"', re.MULTILINE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relative_inside(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:{path}") from exc


def collect_local_source_closure(entry: Path) -> tuple[Path, list[Path]]:
    """Return source root and sorted transitive repository-local include files.

    Quoted includes are treated as source inputs and must resolve to regular files under
    the entry unit's directory. Missing, symlink-resolved escaping, or non-UTF-8 local
    inputs fail closed. Angle-bracket headers are intentionally excluded here because
    compiler/pkg-config/runtime-library identities are captured by the build wrapper.
    """

    entry = entry.resolve()
    if not entry.is_file():
        raise RuntimeError(f"SOURCE_MISSING:{entry}")
    root = entry.parent.resolve()
    pending = [entry]
    visited: set[Path] = set()

    while pending:
        current = pending.pop()
        current = current.resolve()
        _relative_inside(current, root)
        if current in visited:
            continue
        if not current.is_file():
            raise RuntimeError(f"LOCAL_SOURCE_NOT_REGULAR:{current}")
        try:
            text = current.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"LOCAL_SOURCE_NOT_UTF8:{current}") from exc
        visited.add(current)
        for include_name in _LOCAL_INCLUDE_RE.findall(text):
            child = (current.parent / include_name).resolve()
            _relative_inside(child, root)
            if not child.is_file():
                rel = current.relative_to(root).as_posix()
                raise RuntimeError(f"LOCAL_INCLUDE_MISSING:{rel}:{include_name}")
            pending.append(child)

    return root, sorted(visited, key=lambda p: p.relative_to(root).as_posix())


def source_closure_identity(entry: Path) -> dict[str, Any]:
    root, files = collect_local_source_closure(entry)
    manifest = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in files
    ]
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    closure_sha256 = hashlib.sha256(canonical).hexdigest()
    entry_resolved = entry.resolve()
    return {
        "root": str(root),
        "entry_path": entry_resolved.relative_to(root).as_posix(),
        "entry_sha256": sha256_file(entry_resolved),
        "closure_sha256": closure_sha256,
        "files": manifest,
    }


def find_defined_string(entry: Path, macro_name: str) -> str | None:
    """Find one consistent quoted macro definition across the local source closure."""

    root, files = collect_local_source_closure(entry)
    values: set[str] = set()
    for path in files:
        text = path.read_text(encoding="utf-8")
        for name, value in _DEFINE_STRING_RE.findall(text):
            if name == macro_name:
                values.add(value)
    if not values:
        return None
    if len(values) != 1:
        raise RuntimeError(
            "AMBIGUOUS_MACRO_DEFINITION:{}:{}".format(macro_name, ",".join(sorted(values)))
        )
    return next(iter(values))
