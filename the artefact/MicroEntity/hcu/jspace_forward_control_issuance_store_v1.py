#!/usr/bin/env python3
"""Pre-invocation forward-control issuance for recurrent EntityOS/HCU J-Space.

This module closes one temporal source-level gap without creating another state or effect
authority.  A validated predecessor ``TrainingTrace`` may issue exactly one control packet
toward a *future* executor invocation inside the caller-supplied canonical MiniUnifiedDB.
The issuance is rejected if that executor/invocation has already been admitted by the
existing ``HCU_MODEL_EXECUTION_ADMISSION_STORE/v1``.

The resulting causal order is deliberately narrow::

    validated predecessor TrainingTrace(t) / VectorControlPacket(t)
      -> canonical MiniUnifiedDB ForwardControlIssuance(t -> t+1)
      -> later ModelExecution invocation(t+1)

A later ``ModelInputControlBinding`` can be required to consume the exact packet identity
reserved by this issuance.  This proves pre-invocation packet existence/order plus exact
byte-delivery when composed with the existing binding/admission path.  It does NOT prove
hidden-state causal use, model benefit, truth, effects, runtime acceptance or training
benefit.

Boot/first invocation is intentionally outside this recurrent primitive: it must use an
explicit versioned null/no-predecessor-control condition rather than fabricating a prior
trace.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .jspace_training_trace_v1 import TrainingTrace, trace_dict, validate_training_trace
    from .model_input_control_binding_v1 import (
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from jspace_training_trace_v1 import TrainingTrace, trace_dict, validate_training_trace
    from model_input_control_binding_v1 import (
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )

STORE_SCHEMA = "HCU_JSPACE_FORWARD_CONTROL_ISSUANCE_STORE/v1"
ISSUANCE_SCHEMA = "HCU_JSPACE_FORWARD_CONTROL_ISSUANCE/v1"
TRIGGER_NAME = "hcu_jspace_forward_control_no_late_issue"
TABLE_NAME = "hcu_jspace_forward_control_issuances"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class JSpaceForwardControlIssuanceError(ValueError):
    pass


@dataclass(frozen=True)
class ForwardControlIssuance:
    schema: str
    canonicalization_schema: str
    predecessor_trace_id: str
    predecessor_trace_family_id: str
    predecessor_training_trace_sha256: str
    predecessor_prototype_trace_sha256: str
    predecessor_vector_control_packet_sha256: str
    predecessor_vector_control_packet_jcs_utf8: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    predecessor_grid_plan_sha256: str
    predecessor_cell_id: str
    controlled_role: str
    controlled_executor_id: str
    controlled_invocation_id: str
    issuance_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise JSpaceForwardControlIssuanceError(message)


def _canonical_text(value: Any, field: str, max_len: int = 8192) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    value = _canonical_text(value, field, 64)
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _generation(value: Any, field: str) -> int:
    _need(type(value) is int and 0 <= value <= MAX_SAFE_INTEGER, f"{field}:IJSON_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise JSpaceForwardControlIssuanceError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _generation(row[0], "entity_state.generation")


def _require_model_execution_store(db: sqlite3.Connection) -> None:
    """The recurrent path begins only after the canonical execution store exists."""
    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)",
        ("hcu_model_execution_invocations", "hcu_model_execution_observations"),
    ).fetchall()
    _need(
        {str(row[0]) for row in rows}
        == {"hcu_model_execution_invocations", "hcu_model_execution_observations"},
        "MODEL_EXECUTION_ADMISSION_STORE_REQUIRED_FOR_RECURRENT_CONTROL",
    )


def _material(issuance: ForwardControlIssuance) -> dict[str, Any]:
    data = asdict(issuance)
    data.pop("issuance_sha256", None)
    return data


def _issuance_sha256(material: dict[str, Any]) -> str:
    return hashlib.sha256(canonicalize(material)).hexdigest()


def _build_issuance(
    predecessor_trace: TrainingTrace,
    *,
    controlled_executor_id: str,
    controlled_invocation_id: str,
) -> ForwardControlIssuance:
    try:
        validate_training_trace(predecessor_trace)
        serialized_trace = trace_dict(predecessor_trace)
    except Exception as exc:
        raise JSpaceForwardControlIssuanceError(f"PREDECESSOR_TRAINING_TRACE_REJECTED:{exc}") from exc

    material = {
        "schema": ISSUANCE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "predecessor_trace_id": _canonical_text(predecessor_trace.trace_id, "predecessor_trace_id", 256),
        "predecessor_trace_family_id": _canonical_text(
            predecessor_trace.trace_family_id,
            "predecessor_trace_family_id",
            256,
        ),
        "predecessor_training_trace_sha256": _sha256(
            predecessor_trace.trace_sha256,
            "predecessor_training_trace_sha256",
        ),
        "predecessor_prototype_trace_sha256": _sha256(
            predecessor_trace.prototype_trace_sha256,
            "predecessor_prototype_trace_sha256",
        ),
        "predecessor_vector_control_packet_sha256": _sha256(
            predecessor_trace.vector_control_packet_sha256,
            "predecessor_vector_control_packet_sha256",
        ),
        "predecessor_vector_control_packet_jcs_utf8": _canonical_text(
            predecessor_trace.vector_control_packet_jcs_utf8,
            "predecessor_vector_control_packet_jcs_utf8",
            262144,
        ),
        "generation": _generation(predecessor_trace.generation, "generation"),
        "entry_event_sha256": _sha256(predecessor_trace.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(
            predecessor_trace.entry_admission_sha256,
            "entry_admission_sha256",
        ),
        "route_decision_sha256": _sha256(predecessor_trace.route_decision_sha256, "route_decision_sha256"),
        "predecessor_grid_plan_sha256": _sha256(
            predecessor_trace.grid_plan_sha256,
            "predecessor_grid_plan_sha256",
        ),
        "predecessor_cell_id": _canonical_text(predecessor_trace.cell_id, "predecessor_cell_id", 256),
        "controlled_role": _canonical_text(predecessor_trace.role, "controlled_role", 256),
        "controlled_executor_id": _canonical_text(controlled_executor_id, "controlled_executor_id", 256),
        "controlled_invocation_id": _canonical_text(controlled_invocation_id, "controlled_invocation_id", 256),
    }
    # Re-canonicalize the validated trace mapping now so a serialization failure cannot be
    # hidden behind an otherwise valid trace object. The issuance deliberately stores the
    # trace identity, not a second authoritative copy of the trace.
    canonicalize(serialized_trace)
    return ForwardControlIssuance(
        **material,
        issuance_sha256=_issuance_sha256(material),
    )


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    fk = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk is not None and int(fk[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    db.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
          issuance_sha256 TEXT PRIMARY KEY,
          issuance_jcs BLOB NOT NULL,
          predecessor_training_trace_sha256 TEXT NOT NULL,
          predecessor_vector_control_packet_sha256 TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          controlled_role TEXT NOT NULL,
          controlled_executor_id TEXT NOT NULL,
          controlled_invocation_id TEXT NOT NULL,
          UNIQUE(controlled_executor_id, controlled_invocation_id)
        )"""
    )
    db.execute(
        f"""CREATE TRIGGER IF NOT EXISTS {TRIGGER_NAME}
        BEFORE INSERT ON {TABLE_NAME}
        WHEN EXISTS(
          SELECT 1 FROM hcu_model_execution_invocations
          WHERE executor_id=NEW.controlled_executor_id
            AND invocation_id=NEW.controlled_invocation_id
        )
        BEGIN
          SELECT RAISE(ABORT, 'LATE_FORWARD_CONTROL_ISSUANCE');
        END"""
    )
    _verify_temporal_trigger(db)


def _verify_temporal_trigger(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
        (TRIGGER_NAME,),
    ).fetchone()
    _need(row is not None and isinstance(row[0], str), "FORWARD_CONTROL_TEMPORAL_TRIGGER_REQUIRED")
    sql = " ".join(str(row[0]).upper().split())
    for token in (
        "BEFORE INSERT",
        TABLE_NAME.upper(),
        "HCU_MODEL_EXECUTION_INVOCATIONS",
        "EXECUTOR_ID=NEW.CONTROLLED_EXECUTOR_ID",
        "INVOCATION_ID=NEW.CONTROLLED_INVOCATION_ID",
        "LATE_FORWARD_CONTROL_ISSUANCE",
    ):
        _need(token in sql, "FORWARD_CONTROL_TEMPORAL_TRIGGER_SEMANTICS_MISMATCH")


def _execution_already_admitted(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> bool:
    row = db.execute(
        "SELECT 1 FROM hcu_model_execution_invocations WHERE executor_id=? AND invocation_id=? LIMIT 1",
        (executor_id, invocation_id),
    ).fetchone()
    return row is not None


def _decode_stored_issuance(raw: bytes) -> ForwardControlIssuance:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JSpaceForwardControlIssuanceError("FORWARD_CONTROL_STORED_BYTES_INVALID") from exc
    _need(isinstance(data, dict), "FORWARD_CONTROL_STORED_OBJECT_REQUIRED")
    _need(canonicalize(data) == raw, "FORWARD_CONTROL_STORED_JCS_MISMATCH")
    try:
        issuance = ForwardControlIssuance(**data)
    except TypeError as exc:
        raise JSpaceForwardControlIssuanceError("FORWARD_CONTROL_STORED_SCHEMA_MISMATCH") from exc
    validate_forward_control_issuance(issuance)
    return issuance


def issue_forward_control(
    db: sqlite3.Connection,
    predecessor_trace: TrainingTrace,
    *,
    controlled_executor_id: str,
    controlled_invocation_id: str,
    current_generation: int,
) -> ForwardControlIssuance:
    """Atomically reserve a predecessor control packet for a not-yet-admitted invocation."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    current_generation = _generation(current_generation, "current_generation")
    issuance = _build_issuance(
        predecessor_trace,
        controlled_executor_id=controlled_executor_id,
        controlled_invocation_id=controlled_invocation_id,
    )
    _need(issuance.generation == current_generation, "PREDECESSOR_TRACE_GENERATION_MISMATCH")

    try:
        db.execute("BEGIN IMMEDIATE")
        _need(_current_generation(db) == current_generation, "STALE_FORWARD_CONTROL_ISSUANCE_GENERATION")
        _require_model_execution_store(db)
        _install_schema(db)

        existing = db.execute(
            f"SELECT issuance_jcs FROM {TABLE_NAME} WHERE controlled_executor_id=? AND controlled_invocation_id=?",
            (issuance.controlled_executor_id, issuance.controlled_invocation_id),
        ).fetchone()
        if existing is not None:
            stored = _decode_stored_issuance(bytes(existing[0]))
            _need(stored == issuance, "FORWARD_CONTROL_INVOCATION_REPLAY_DIVERGENCE")
            db.commit()
            return stored

        _need(
            not _execution_already_admitted(
                db,
                executor_id=issuance.controlled_executor_id,
                invocation_id=issuance.controlled_invocation_id,
            ),
            "CONTROLLED_INVOCATION_ALREADY_ADMITTED",
        )
        issuance_jcs = canonicalize(asdict(issuance))
        db.execute(
            f"INSERT INTO {TABLE_NAME} "
            "(issuance_sha256,issuance_jcs,predecessor_training_trace_sha256,"
            "predecessor_vector_control_packet_sha256,entity_generation,controlled_role,"
            "controlled_executor_id,controlled_invocation_id) VALUES(?,?,?,?,?,?,?,?)",
            (
                issuance.issuance_sha256,
                issuance_jcs,
                issuance.predecessor_training_trace_sha256,
                issuance.predecessor_vector_control_packet_sha256,
                issuance.generation,
                issuance.controlled_role,
                issuance.controlled_executor_id,
                issuance.controlled_invocation_id,
            ),
        )
        db.commit()
        return issuance
    except (JSpaceForwardControlIssuanceError, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise


def validate_forward_control_issuance(issuance: ForwardControlIssuance) -> None:
    if not isinstance(issuance, ForwardControlIssuance):
        raise JSpaceForwardControlIssuanceError("FORWARD_CONTROL_ISSUANCE_REQUIRED")
    _need(issuance.schema == ISSUANCE_SCHEMA, "FORWARD_CONTROL_ISSUANCE_SCHEMA_UNSUPPORTED")
    _need(
        issuance.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "FORWARD_CONTROL_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _generation(issuance.generation, "issuance.generation")
    for field in (
        "predecessor_training_trace_sha256",
        "predecessor_prototype_trace_sha256",
        "predecessor_vector_control_packet_sha256",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "predecessor_grid_plan_sha256",
    ):
        _sha256(getattr(issuance, field), f"issuance.{field}")
    for field, max_len in (
        ("predecessor_trace_id", 256),
        ("predecessor_trace_family_id", 256),
        ("predecessor_vector_control_packet_jcs_utf8", 262144),
        ("predecessor_cell_id", 256),
        ("controlled_role", 256),
        ("controlled_executor_id", 256),
        ("controlled_invocation_id", 256),
    ):
        _canonical_text(getattr(issuance, field), f"issuance.{field}", max_len)
    observed = _sha256(issuance.issuance_sha256, "issuance.issuance_sha256")
    _need(observed == _issuance_sha256(_material(issuance)), "FORWARD_CONTROL_ISSUANCE_DIGEST_MISMATCH")


def require_forward_control_for_model_input(
    db: sqlite3.Connection,
    binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> ForwardControlIssuance:
    """Require that exact model-input control was issued before its invocation was admitted.

    This function does not admit the model execution or control binding. It composes with the
    existing stores by proving that the exact packet/executor/invocation/generation/role now
    present in ``ModelInputControlBinding`` was reserved in canonical MiniUnifiedDB while the
    controlled invocation was still absent.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    try:
        validate_model_input_control_binding(binding, consumed_input_bytes)
    except ModelInputControlBindingError as exc:
        raise JSpaceForwardControlIssuanceError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc

    _require_model_execution_store(db)
    row = db.execute(
        f"SELECT issuance_jcs FROM {TABLE_NAME} WHERE controlled_executor_id=? AND controlled_invocation_id=?",
        (binding.executor_id, binding.invocation_id),
    ).fetchone()
    _need(row is not None, "FORWARD_CONTROL_ISSUANCE_NOT_ADMITTED")
    _verify_temporal_trigger(db)
    issuance = _decode_stored_issuance(bytes(row[0]))
    checks = {
        "generation": (issuance.generation, binding.generation),
        "controlled_role": (issuance.controlled_role, binding.role),
        "controlled_executor_id": (issuance.controlled_executor_id, binding.executor_id),
        "controlled_invocation_id": (issuance.controlled_invocation_id, binding.invocation_id),
        "vector_control_packet_sha256": (
            issuance.predecessor_vector_control_packet_sha256,
            binding.vector_control_packet_sha256,
        ),
        "vector_control_packet_jcs_utf8": (
            issuance.predecessor_vector_control_packet_jcs_utf8,
            binding.vector_control_packet_jcs_utf8,
        ),
    }
    for field, values in checks.items():
        _need(values[0] == values[1], f"FORWARD_CONTROL_MODEL_INPUT_MISMATCH:{field}")
    return issuance
