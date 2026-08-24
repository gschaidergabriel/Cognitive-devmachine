#!/usr/bin/env python3
"""Canonical predecessor guard for EntityOS/HCU pre-invocation control.

A valid ``JSpaceInferenceBinding`` is a self-authenticating child envelope.  Its digest does
not prove that the referenced predecessor model invocation was actually admitted by the
canonical MiniUnifiedDB model-execution store.  The selected pre-invocation control path
therefore needs an independent source check before it may treat that binding/TrainingTrace
as a real predecessor of a future controlled invocation.

This module is deliberately read-only.  It creates no table, state authority, effect path,
model executor, J-Space authority, or runtime credit.  It reuses the existing
``HCU_MODEL_EXECUTION_ADMISSION_STORE/v1`` tables and the sole
``HCU_MODEL_EXECUTION_OBSERVATION/v1`` normalizer to require that:

* the exact observation digest referenced by the J-Space binding exists canonically;
* its canonical bytes re-hash to that digest;
* all execution-critical fields mirrored by the J-Space binding match the admitted
  observation exactly;
* the canonical invocation key maps uniquely to that exact observation; and
* live entity generation equals the binding/current generation.

For temporal credit this guard is intended to run while the caller already holds the same
``BEGIN IMMEDIATE`` MiniUnifiedDB writer transaction used by pre-invocation preparation.
A positive result proves canonical predecessor ModelExecution admission only.  It does not
prove the J-Space interpretation, hidden-state causal use, training benefit, truth, effects,
or whole EntityOS/HCU runtime acceptance.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import canonicalize
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from .model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
        model_execution_observation_sha256,
    )
except ImportError:
    from entry_canonicalization_v1 import canonicalize
    from jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
        model_execution_observation_sha256,
    )


SCHEMA = "HCU_PREINVOCATION_CANONICAL_PREDECESSOR_GUARD/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class PreInvocationCanonicalPredecessorError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PreInvocationCanonicalPredecessorError(message)


def _generation(value: Any, field: str) -> int:
    _need(
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _sha256(value: Any, field: str) -> str:
    _need(isinstance(value, str), f"{field}:STRING_REQUIRED")
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _table_exists(db: sqlite3.Connection, table: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _live_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise PreInvocationCanonicalPredecessorError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _generation(row[0], "entity_state.generation")


def _decode_observation(raw: bytes) -> ModelExecutionObservation:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreInvocationCanonicalPredecessorError(
            "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_STORED_BYTES_INVALID"
        ) from exc
    _need(
        isinstance(value, dict),
        "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_STORED_OBJECT_REQUIRED",
    )
    _need(
        canonicalize(value) == raw,
        "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_STORED_JCS_MISMATCH",
    )
    try:
        observation = ModelExecutionObservation(**value)
        normalized = model_execution_observation_record(observation)
    except (TypeError, ModelExecutionReceiptError) as exc:
        raise PreInvocationCanonicalPredecessorError(
            f"PREDECESSOR_MODEL_EXECUTION_OBSERVATION_REJECTED:{exc}"
        ) from exc
    _need(
        canonicalize(normalized) == raw,
        "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_NORMALIZATION_MISMATCH",
    )
    return observation


def require_canonical_predecessor_execution(
    db: sqlite3.Connection,
    predecessor_jspace_binding: JSpaceInferenceBinding,
    *,
    current_generation: int,
) -> str:
    """Require exact canonical ModelExecution backing for a predecessor J-Space binding.

    The function performs no writes.  Call it inside the pre-invocation store's locked
    transaction when the result is used to establish predecessor-before-controlled ordering.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    _need(
        isinstance(predecessor_jspace_binding, JSpaceInferenceBinding),
        "PREDECESSOR_JSPACE_BINDING_REQUIRED",
    )
    try:
        validate_binding(predecessor_jspace_binding)
    except JSpaceInferenceBindingError as exc:
        raise PreInvocationCanonicalPredecessorError(
            f"PREDECESSOR_JSPACE_BINDING_REJECTED:{exc}"
        ) from exc

    _need(
        predecessor_jspace_binding.generation == current_generation,
        "PREDECESSOR_JSPACE_GENERATION_MISMATCH",
    )
    _need(
        _live_generation(db) == current_generation,
        "STALE_PREDECESSOR_MODEL_EXECUTION_GENERATION",
    )
    _need(
        _table_exists(db, "hcu_model_execution_observations")
        and _table_exists(db, "hcu_model_execution_invocations"),
        "PREDECESSOR_MODEL_EXECUTION_STORE_REQUIRED",
    )

    expected_observation_sha256 = _sha256(
        predecessor_jspace_binding.model_execution_observation_sha256,
        "predecessor_jspace_binding.model_execution_observation_sha256",
    )
    rows = db.execute(
        "SELECT observation_jcs,entity_generation,executor_id,invocation_id "
        "FROM hcu_model_execution_observations WHERE observation_sha256=?",
        (expected_observation_sha256,),
    ).fetchall()
    _need(
        len(rows) == 1,
        "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_NOT_UNIQUELY_ADMITTED",
    )
    raw, row_generation, row_executor_id, row_invocation_id = rows[0]
    observation = _decode_observation(bytes(raw))
    try:
        observed_observation_sha256 = model_execution_observation_sha256(observation)
    except ModelExecutionReceiptError as exc:
        raise PreInvocationCanonicalPredecessorError(
            f"PREDECESSOR_MODEL_EXECUTION_OBSERVATION_REJECTED:{exc}"
        ) from exc
    _need(
        observed_observation_sha256 == expected_observation_sha256,
        "PREDECESSOR_MODEL_EXECUTION_OBSERVATION_DIGEST_MISMATCH",
    )
    _need(
        (
            _generation(row_generation, "model_execution.entity_generation"),
            str(row_executor_id),
            str(row_invocation_id),
        )
        == (
            current_generation,
            predecessor_jspace_binding.model_execution_executor_id,
            predecessor_jspace_binding.model_execution_invocation_id,
        ),
        "PREDECESSOR_MODEL_EXECUTION_ROW_IDENTITY_MISMATCH",
    )

    mirrored = {
        "entity_generation": predecessor_jspace_binding.generation,
        "executor_id": predecessor_jspace_binding.model_execution_executor_id,
        "invocation_id": predecessor_jspace_binding.model_execution_invocation_id,
        "engine_load_consumption_receipt_sha256": predecessor_jspace_binding.engine_load_consumption_receipt_sha256,
        "grid_plan_sha256": predecessor_jspace_binding.grid_plan_sha256,
        "output_producing_cell_id": predecessor_jspace_binding.output_producing_cell_id,
        "role": predecessor_jspace_binding.model_execution_role,
        "input_sha256": predecessor_jspace_binding.input_sha256,
        "input_size": predecessor_jspace_binding.input_size,
        "output_ref": predecessor_jspace_binding.output_ref,
        "output_sha256": predecessor_jspace_binding.output_sha256,
        "output_size": predecessor_jspace_binding.output_size,
    }
    observation_record = model_execution_observation_record(observation)
    for field, expected in mirrored.items():
        _need(
            observation_record.get(field) == expected,
            f"PREDECESSOR_MODEL_EXECUTION_BINDING_MISMATCH:{field}",
        )

    invocation_key = model_execution_invocation_binding_key(observation)
    invocation_rows = db.execute(
        "SELECT invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256 "
        "FROM hcu_model_execution_invocations WHERE executor_id=? AND invocation_id=?",
        (
            predecessor_jspace_binding.model_execution_executor_id,
            predecessor_jspace_binding.model_execution_invocation_id,
        ),
    ).fetchall()
    _need(
        len(invocation_rows) == 1,
        "PREDECESSOR_MODEL_EXECUTION_INVOCATION_NOT_UNIQUELY_ADMITTED",
    )
    _need(
        tuple(invocation_rows[0])
        == (
            invocation_key,
            predecessor_jspace_binding.model_execution_executor_id,
            predecessor_jspace_binding.model_execution_invocation_id,
            current_generation,
            expected_observation_sha256,
        ),
        "PREDECESSOR_MODEL_EXECUTION_INVOCATION_IDENTITY_MISMATCH",
    )
    return expected_observation_sha256


__all__ = [
    "SCHEMA",
    "PreInvocationCanonicalPredecessorError",
    "require_canonical_predecessor_execution",
]
