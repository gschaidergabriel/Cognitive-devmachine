#!/usr/bin/env python3
"""Replay-stable causal identity primitive for historical Free-Swarm evidence.

This module is additive and non-authoritative by itself. It separates a replay-stable
causal event identity from the legacy concrete source/admission identity used by the
historical backfill. Integration must preserve legacy IDs rather than silently rewrite
them.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "CLAY_FREE_SWARM_CAUSAL_EVENT_IDENTITY/v2"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def logical_source_path(artifact_root: Path | str, source_path: Path | str) -> str:
    """Return a root-relocatable POSIX path, failing closed outside artifact_root."""
    root = Path(artifact_root).resolve(strict=False)
    source = Path(source_path).resolve(strict=False)
    try:
        rel = source.relative_to(root)
    except ValueError as exc:
        raise ValueError("SOURCE_PATH_OUTSIDE_ARTIFACT_ROOT") from exc
    logical = rel.as_posix()
    if not logical or logical == ".":
        raise ValueError("SOURCE_PATH_IS_ARTIFACT_ROOT")
    parts = PurePosixPath(logical).parts
    if logical.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("LOGICAL_SOURCE_PATH_INVALID")
    return logical


def causal_event_id(
    row: dict[str, Any], *, logical_path: str, line_no: int, text_sha256: str
) -> str:
    """Derive v2 causal identity without concrete artifact-root or transport paths."""
    if not isinstance(row, dict):
        raise TypeError("ROW_MUST_BE_DICT")
    try:
        line = int(line_no)
    except (TypeError, ValueError) as exc:
        raise ValueError("LINE_NO_INVALID") from exc
    if line <= 0:
        raise ValueError("LINE_NO_INVALID")
    digest = str(text_sha256 or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("TEXT_SHA256_INVALID")
    path = str(logical_path or "").strip()
    parts = PurePosixPath(path).parts
    if not path or path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("LOGICAL_SOURCE_PATH_INVALID")
    payload = {
        "schema": SCHEMA,
        "logical_source_path": path,
        "line_no": line,
        "worker_schema": row.get("schema"),
        "worker_id": row.get("worker_id"),
        "worker_serial": row.get("worker_serial"),
        "ts": row.get("ts"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "repo_head_at_prompt": row.get("repo_head_at_prompt"),
        "text_sha256": digest,
    }
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def derive_identity_pair(
    artifact_root: Path | str,
    source_path: Path | str,
    row: dict[str, Any],
    *,
    line_no: int,
    text_sha256: str,
    legacy_source_event_id: str | None = None,
) -> dict[str, Any]:
    """Return an additive identity envelope; never reinterpret a legacy ID in place."""
    logical = logical_source_path(artifact_root, source_path)
    return {
        "schema": SCHEMA,
        "causal_event_id": causal_event_id(
            row, logical_path=logical, line_no=line_no, text_sha256=text_sha256
        ),
        "legacy_source_event_id": str(legacy_source_event_id or "") or None,
        "logical_source_path": logical,
        "line_no": int(line_no),
    }
