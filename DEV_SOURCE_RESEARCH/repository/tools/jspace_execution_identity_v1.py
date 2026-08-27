"""Execution identity helpers for J-Space model-local runtime rows."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MODEL_EXECUTION_SCHEMA = "JSPACE_MODEL_EXECUTION_ID/v1"


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def model_execution_material(runtime_session_id: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": MODEL_EXECUTION_SCHEMA,
        "runtime_session_id": runtime_session_id,
        "invocation": int(row["invocation"]),
        "prompt_sha256": row["prompt_sha256"],
        "layer": int(row["layer"]),
        "vector_layer": int(row["vector_layer"]),
        "gain": float(row["gain"]),
        "control": str(row["control"]),
        "mode": str(row.get("mode") or "control"),
        "seed": int(row["seed"]),
        "positive_label": str(row["positive_label"]),
        "negative_label": str(row["negative_label"]),
    }


def derive_model_execution_id(runtime_session_id: str, row: dict[str, Any]) -> str:
    if not isinstance(runtime_session_id, str) or not runtime_session_id:
        raise ValueError("RUNTIME_SESSION_ID_REQUIRED")
    return canonical_sha(model_execution_material(runtime_session_id, row))
