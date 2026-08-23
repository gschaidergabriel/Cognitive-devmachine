#!/usr/bin/env python3
"""Verified lookup-key bridge for MiniUnifiedDB cognition turn bindings.

A TURN_REF is an untrusted lookup assertion, never durable authority.  The exact
causal turn id and task text are revalidated against the existing same-database
MiniUnifiedDB cognition binding before any value may feed Cognitive Fabric prepare.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = "MINI_ENTITY_COGNITION_TURN_REF/v1"
TURN_REF_KEYS = {"schema", "causal_turn_id", "task_text", "task_sha256"}


class TurnRefError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise TurnRefError(message)


def normalize_turn_ref(value: Any) -> dict[str, str]:
    _need(type(value) is dict, "TURN_REF_OBJECT_REQUIRED")
    _need(set(value) == TURN_REF_KEYS, "TURN_REF_FIELDS_MISMATCH")
    _need(value.get("schema") == SCHEMA, "TURN_REF_SCHEMA_MISMATCH")
    causal_turn_id = value.get("causal_turn_id")
    task_text = value.get("task_text")
    task_sha256 = value.get("task_sha256")
    _need(type(causal_turn_id) is str and bool(causal_turn_id.strip()), "CAUSAL_TURN_ID_REQUIRED")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    expected = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    _need(task_sha256 == expected, "TURN_REF_TASK_DIGEST_MISMATCH")
    return {
        "schema": SCHEMA,
        "causal_turn_id": causal_turn_id.strip(),
        "task_text": task_text,
        "task_sha256": expected,
    }


def _load_store():
    path = Path(__file__).resolve().parent / "miniunifieddb_cognition_store_v1.py"
    spec = importlib.util.spec_from_file_location("miniunifieddb_cognition_store_v1", path)
    if spec is None or spec.loader is None:
        raise TurnRefError("COGNITION_STORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_turn_ref(
    entity_db: str | Path,
    *,
    entity_generation: int,
    turn_ref: dict[str, Any],
    store: Any | None = None,
) -> dict[str, Any]:
    """Resolve exact prepare material from MiniUnifiedDB, never from prompt/profile fields."""
    ref = normalize_turn_ref(turn_ref)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    store_module = store if store is not None else _load_store()
    path = Path(entity_db).resolve()
    _need(path.is_file(), "MINIUNIFIEDDB_NOT_FOUND")
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        resolved = store_module.resolve_prepare_binding(
            db,
            entity_generation=entity_generation,
            causal_turn_id=ref["causal_turn_id"],
            task_text=ref["task_text"],
        )
    except Exception as exc:
        raise TurnRefError(f"TURN_REF_NOT_CANONICALLY_BOUND:{type(exc).__name__}:{exc}") from exc
    finally:
        db.close()

    _need(type(resolved) is dict and resolved.get("ok") is True, "PREPARE_BINDING_RESOLUTION_FAILED")
    _need(resolved.get("entity_generation") == entity_generation, "RESOLVED_GENERATION_MISMATCH")
    _need(resolved.get("causal_turn_id") == ref["causal_turn_id"], "RESOLVED_CAUSAL_TURN_MISMATCH")
    _need(resolved.get("task_sha256") == ref["task_sha256"], "RESOLVED_TASK_DIGEST_MISMATCH")
    return resolved


__all__ = ["SCHEMA", "TurnRefError", "normalize_turn_ref", "resolve_turn_ref"]
