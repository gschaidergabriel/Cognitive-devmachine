#!/usr/bin/env python3
"""Canonical pre-invocation predecessor admission for EntityOS/HCU J-Space control.

This module closes one narrow causal-ordering gap without executing a model or claiming
hidden-state causality.  A validated ``ModelInputControlBinding`` already proves that one
exact canonical ``JSPACE_VECTOR_CONTROL_ABI/v1`` packet occurs exactly once in the exact
bytes prepared for one executor invocation.  This store additionally proves, inside the
caller-supplied canonical MiniUnifiedDB transaction, that the control/input binding was
admitted while the same executor/invocation identity had *not yet* been admitted as a model
execution.

The resulting receipt is therefore a deterministic predecessor edge:

    exact J-Space control packet
      -> exact prepared model-input bytes
      -> canonical pre-invocation admission
      -> [later actual model execution may occur]

It does NOT prove that a model consumed hidden-state vectors, that the control altered the
output, that a later execution succeeded, or that any output is true.  It creates no second
database, effect path, product identity, model-runtime credit, or training credit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )

SCHEMA = "HCU_JSPACE_PREINVOCATION_CONTROL_ADMISSION_STORE/v1"
ADMISSION_SCHEMA = "HCU_JSPACE_PREINVOCATION_CONTROL_ADMISSION/v1"
INVOCATION_KEY_SCHEMA = "HCU_JSPACE_PREINVOCATION_CONTROL_INVOCATION_KEY/v1"


class JSpacePreInvocationControlAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class JSpacePreInvocationControlAdmission:
    schema: str
    canonicalization_schema: str
    binding_schema: str
    binding_sha256: str
    generation: int
    executor_id: str
    invocation_id: str
    invocation_key: str
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    vector_control_packet_sha256: str
    vector_control_condition: str
    input_sha256: str
    input_size: int
    model_execution_absent_at_admission: bool
    admission_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise JSpacePreInvocationControlAdmissionError(message)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _generation(value: Any, field: str) -> int:
    _need(type(value) is int and value >= 0, f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    _need(value <= 9_007_199_254_740_991, f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _input_size(value: Any, field: str) -> int:
    _need(type(value) is int and value > 0, f"{field}:POSITIVE_INTEGER_REQUIRED")
    return value


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise JSpacePreInvocationControlAdmissionError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _generation(row[0], "entity_state.generation")


def _invocation_key(executor_id: str, invocation_id: str) -> str:
    material = {
        "schema": INVOCATION_KEY_SCHEMA,
        "executor_id": _text(executor_id, "executor_id", 256),
        "invocation_id": _text(invocation_id, "invocation_id", 256),
    }
    return hashlib.sha256(canonicalize(material)).hexdigest()


def _model_execution_already_admitted(db: sqlite3.Connection, *, executor_id: str, invocation_id: str) -> bool:
    table = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='hcu_model_execution_invocations'"
    ).fetchone()
    if table is None:
        return False
    rows = db.execute(
        "SELECT 1 FROM hcu_model_execution_invocations WHERE executor_id=? AND invocation_id=? LIMIT 2",
        (executor_id, invocation_id),
    ).fetchall()
    _need(len(rows) <= 1, "MODEL_EXECUTION_INVOCATION_IDENTITY_NOT_UNIQUE")
    return bool(rows)


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    fk = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk is not None and int(fk[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_jspace_preinvocation_control_admissions(
          invocation_key TEXT PRIMARY KEY,
          admission_sha256 TEXT NOT NULL UNIQUE,
          admission_jcs BLOB NOT NULL,
          binding_sha256 TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL,
          grid_plan_sha256 TEXT NOT NULL,
          vector_control_packet_sha256 TEXT NOT NULL,
          input_sha256 TEXT NOT NULL,
          input_size INTEGER NOT NULL,
          UNIQUE(executor_id, invocation_id)
        )"""
    )


def _cross_bind_grid_plan(binding: ModelInputControlBinding, grid_plan: GridPlan) -> None:
    _need(isinstance(grid_plan, GridPlan), "GRID_PLAN_REQUIRED")
    try:
        observed = validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise JSpacePreInvocationControlAdmissionError("GRID_PLAN_SEMANTIC_REVALIDATION_FAILED") from exc
    _need(observed == grid_plan.plan_sha256 == binding.grid_plan_sha256, "PREINVOCATION_GRID_PLAN_IDENTITY_MISMATCH")
    checks = {
        "generation": (binding.generation, grid_plan.entity_generation),
        "entry_event_sha256": (binding.entry_event_sha256, grid_plan.entry_event_sha256),
        "entry_admission_sha256": (binding.entry_admission_sha256, grid_plan.entry_admission_sha256),
        "route_decision_sha256": (binding.route_decision_sha256, grid_plan.route_decision_sha256),
    }
    for field, values in checks.items():
        _need(values[0] == values[1], f"PREINVOCATION_GRID_PARENT_MISMATCH:{field}")

    cells = [cell for cell in grid_plan.cells if cell.cell_id == binding.cell_id]
    _need(len(cells) == 1, "PREINVOCATION_GRID_CELL_NOT_UNIQUE")
    cell = cells[0]
    _need(cell.execution_class is ExecutionClass.MODEL, "PREINVOCATION_GRID_CELL_NOT_MODEL")
    _need(cell.function == f"MODEL:{binding.role}", "PREINVOCATION_GRID_CELL_ROLE_MISMATCH")


def _material(binding: ModelInputControlBinding, invocation_key: str) -> dict[str, Any]:
    return {
        "schema": ADMISSION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "binding_schema": BINDING_SCHEMA,
        "binding_sha256": _sha256(binding.binding_sha256, "binding.binding_sha256"),
        "generation": _generation(binding.generation, "binding.generation"),
        "executor_id": _text(binding.executor_id, "binding.executor_id", 256),
        "invocation_id": _text(binding.invocation_id, "binding.invocation_id", 256),
        "invocation_key": _sha256(invocation_key, "invocation_key"),
        "entry_event_sha256": _sha256(binding.entry_event_sha256, "binding.entry_event_sha256"),
        "entry_admission_sha256": _sha256(binding.entry_admission_sha256, "binding.entry_admission_sha256"),
        "route_decision_sha256": _sha256(binding.route_decision_sha256, "binding.route_decision_sha256"),
        "grid_plan_sha256": _sha256(binding.grid_plan_sha256, "binding.grid_plan_sha256"),
        "cell_id": _text(binding.cell_id, "binding.cell_id", 256),
        "role": _text(binding.role, "binding.role", 256),
        "vector_control_packet_sha256": _sha256(
            binding.vector_control_packet_sha256,
            "binding.vector_control_packet_sha256",
        ),
        "vector_control_condition": _text(
            binding.vector_control_condition,
            "binding.vector_control_condition",
            64,
        ),
        "input_sha256": _sha256(binding.input_sha256, "binding.input_sha256"),
        "input_size": _input_size(binding.input_size, "binding.input_size"),
        "model_execution_absent_at_admission": True,
    }


def _read_exact_admission(db: sqlite3.Connection, invocation_key: str) -> JSpacePreInvocationControlAdmission:
    row = db.execute(
        "SELECT admission_sha256,admission_jcs FROM hcu_jspace_preinvocation_control_admissions "
        "WHERE invocation_key=?",
        (invocation_key,),
    ).fetchone()
    _need(row is not None, "PREINVOCATION_ADMISSION_LOST")
    observed_sha = _sha256(str(row[0]), "stored.admission_sha256")
    raw = bytes(row[1])
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JSpacePreInvocationControlAdmissionError("PREINVOCATION_ADMISSION_STORED_BYTES_INVALID") from exc
    _need(isinstance(record, dict), "PREINVOCATION_ADMISSION_STORED_OBJECT_REQUIRED")
    _need(canonicalize(record) == raw, "PREINVOCATION_ADMISSION_STORED_JCS_MISMATCH")
    _need(hashlib.sha256(raw).hexdigest() == observed_sha, "PREINVOCATION_ADMISSION_DIGEST_MISMATCH")
    _need(record.get("model_execution_absent_at_admission") is True, "PREINVOCATION_ABSENCE_WITNESS_LOST")
    return JSpacePreInvocationControlAdmission(**record, admission_sha256=observed_sha)


def admit_preinvocation_control(
    db: sqlite3.Connection,
    binding: ModelInputControlBinding,
    prepared_input_bytes: bytes,
    grid_plan: GridPlan,
    *,
    current_generation: int,
) -> JSpacePreInvocationControlAdmission:
    """Admit control/input evidence only while model execution is still absent.

    This function must be called after the final model-input bytes are fixed and validated but
    before the real executor invocation is admitted.  The exact same executor/invocation label
    may then be used by the canonical model-execution admission path after this transaction
    commits.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    current_generation = _generation(current_generation, "current_generation")
    _need(isinstance(binding, ModelInputControlBinding), "MODEL_INPUT_CONTROL_BINDING_REQUIRED")

    try:
        db.execute("BEGIN IMMEDIATE")
        _need(_current_generation(db) == current_generation, "STALE_PREINVOCATION_CONTROL_GENERATION")
        _need(binding.generation == current_generation, "PREINVOCATION_BINDING_GENERATION_MISMATCH")
        validate_model_input_control_binding(binding, prepared_input_bytes)
        _cross_bind_grid_plan(binding, grid_plan)

        _need(
            not _model_execution_already_admitted(
                db,
                executor_id=binding.executor_id,
                invocation_id=binding.invocation_id,
            ),
            "MODEL_EXECUTION_ALREADY_ADMITTED_BEFORE_CONTROL",
        )

        _install_schema(db)
        invocation_key = _invocation_key(binding.executor_id, binding.invocation_id)
        material = _material(binding, invocation_key)
        raw = canonicalize(material)
        admission_sha = hashlib.sha256(raw).hexdigest()

        row = db.execute(
            "SELECT admission_sha256,admission_jcs,binding_sha256,entity_generation,executor_id,invocation_id,"
            "grid_plan_sha256,vector_control_packet_sha256,input_sha256,input_size "
            "FROM hcu_jspace_preinvocation_control_admissions WHERE invocation_key=?",
            (invocation_key,),
        ).fetchone()
        expected = (
            admission_sha,
            raw,
            binding.binding_sha256,
            binding.generation,
            binding.executor_id,
            binding.invocation_id,
            binding.grid_plan_sha256,
            binding.vector_control_packet_sha256,
            binding.input_sha256,
            binding.input_size,
        )
        if row is None:
            db.execute(
                "INSERT INTO hcu_jspace_preinvocation_control_admissions "
                "(invocation_key,admission_sha256,admission_jcs,binding_sha256,entity_generation,executor_id,invocation_id,"
                "grid_plan_sha256,vector_control_packet_sha256,input_sha256,input_size) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (invocation_key, *expected),
            )
        else:
            stored = (str(row[0]), bytes(row[1]), *row[2:])
            _need(stored == expected, "PREINVOCATION_CONTROL_REPLAY_DIVERGENCE")

        admitted = _read_exact_admission(db, invocation_key)
        _need(admitted.admission_sha256 == admission_sha, "PREINVOCATION_ADMISSION_POSTWRITE_MISMATCH")
        db.commit()
        return admitted
    except (
        JSpacePreInvocationControlAdmissionError,
        ModelInputControlBindingError,
        GridScheduleError,
        sqlite3.Error,
    ):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise
