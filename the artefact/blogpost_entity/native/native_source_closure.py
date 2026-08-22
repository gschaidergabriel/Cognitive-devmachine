#!/usr/bin/env python3
"""Deterministically bind the local native Mini Entity source closure.

The native entry unit may include repository-local split source files. Artifact identity
must therefore bind every local source byte that can affect compilation, not only the
small top-level translation-unit file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

_INCLUDE_RE = re.compile(rb'^\s*#\s*include\s+(.+?)\s*$', re.MULTILINE)
_QUOTED_INCLUDE_RE = re.compile(rb'^"([^"\r\n]+)"(?:\s*/[/*].*)?$')
_MINI_VERSION_RE = re.compile(
    rb'^\s*#\s*define\s+MINI_VERSION\s+"([^"\r\n]+)"\s*$',
    re.MULTILINE,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _lexical_absolute(path: Path) -> Path:
    """Normalize dot segments without following symlinks."""
    return Path(os.path.abspath(path))


def _reject_symlink_chain(root: Path, path: Path) -> None:
    lexical = _lexical_absolute(path)
    if not _inside(root, lexical):
        raise ValueError(f"LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:{path}")
    current = root
    for part in lexical.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"LOCAL_INCLUDE_SYMLINK_FORBIDDEN:{current}")


def source_files(entry: Path) -> list[Path]:
    """Return every repository-local quoted include reachable from *entry*.

    Angle-bracket includes are treated as external compiler/package dependencies and are
    intentionally excluded. Macro/dynamic include syntax fails closed because silently
    omitting such a dependency would make the provenance digest incomplete.
    """
    requested_entry = Path(entry)
    if requested_entry.is_symlink():
        raise ValueError(f"SOURCE_SYMLINK_FORBIDDEN:{requested_entry}")
    entry = requested_entry.resolve()
    root = entry.parent.resolve()
    if not entry.is_file():
        raise ValueError(f"SOURCE_NOT_REGULAR:{entry}")

    pending = [entry]
    seen: set[Path] = set()
    ordered: list[Path] = []
    while pending:
        path = pending.pop()
        _reject_symlink_chain(root, path)
        resolved = path.resolve()
        if resolved in seen:
            continue
        if not _inside(root, resolved):
            raise ValueError(f"LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:{resolved}")
        if not resolved.is_file():
            raise ValueError(f"LOCAL_INCLUDE_NOT_REGULAR:{resolved}")
        seen.add(resolved)
        ordered.append(resolved)
        data = resolved.read_bytes()
        for raw in _INCLUDE_RE.findall(data):
            token = raw.strip()
            if token.startswith(b"<") and token.endswith(b">"):
                continue
            match = _QUOTED_INCLUDE_RE.fullmatch(token)
            if not match:
                raise ValueError(
                    "UNSUPPORTED_INCLUDE_SYNTAX:{}:{}".format(
                        resolved.relative_to(root).as_posix(),
                        token.decode("utf-8", "backslashreplace"),
                    )
                )
            include_text = match.group(1).decode("utf-8", "strict")
            child = resolved.parent / include_text
            _reject_symlink_chain(root, child)
            child_resolved = child.resolve()
            if not _inside(root, child_resolved):
                raise ValueError(f"LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:{include_text}")
            pending.append(child)
    return sorted(ordered, key=lambda item: item.relative_to(root).as_posix())


def describe_source_closure(entry: Path) -> list[dict[str, Any]]:
    requested_entry = Path(entry)
    entry = requested_entry.resolve()
    root = entry.parent.resolve()
    out: list[dict[str, Any]] = []
    for path in source_files(requested_entry):
        data = path.read_bytes()
        out.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_bytes(data),
                "size": len(data),
            }
        )
    return out


def source_closure_sha256(description: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        description,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return sha256_bytes(canonical)


def declared_mini_version(entry: Path) -> str | None:
    versions: set[str] = set()
    for path in source_files(entry):
        for raw in _MINI_VERSION_RE.findall(path.read_bytes()):
            versions.add(raw.decode("utf-8", "strict"))
    if not versions:
        return None
    if len(versions) != 1:
        raise ValueError("AMBIGUOUS_MINI_VERSION:" + ",".join(sorted(versions)))
    return next(iter(versions))
