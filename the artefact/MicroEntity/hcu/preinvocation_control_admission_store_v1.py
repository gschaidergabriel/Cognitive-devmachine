#!/usr/bin/env python3
"""Pre-invocation predecessor-control admission for EntityOS/HCU J-Space.

This module closes a narrow source-level ordering gap without creating a second truth,
state, effect, executor, or J-Space authority.

It admits one already-produced, inference-bound J-Space TrainingTrace control packet as
the predecessor of one *distinct* future model invocation, and it does so in the caller's
existing canonical MiniUnifiedDB before any ModelExecution admission for that controlled
executor/invocation may exist.

Positive preparation therefore proves only:

    canonically admitted predecessor ModelExecution
      -> admitted exact HCU_INFERENCE_RECEIPT/v4 parent
      -> prior JSpaceInferenceBinding / TrainingTrace packet
      -> exact ModelInputControlBinding bytes for a distinct invocation
      -> committed pre-invocation preparation row
      -> no ModelExecution admission for that invocation existed at commit time.

The predecessor ModelExecution check, inference-parent admission check, and controlled-
invocation absence check execute before any preparation-table write; the two MiniUnifiedDB
checks execute under the same ``BEGIN IMMEDIATE`` writer transaction as the preparation
write. A self-consistent J-Space binding therefore cannot manufacture either a predecessor
ModelExecution parent or an inference-receipt parent that was not admitted by the existing
single parent-evidence guard.

It does NOT prove that a physical model call had not already happened outside the admitted
executor path, does NOT prove hidden-state use or counterfactual influence, and grants no
runtime/model/training credit. Real executor integration must call this preparation before
the physical model invocation and later close it through the existing canonical
ModelExecution + ModelInputControl admission path.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding as validate_jspace_inference_binding,
    )
    from .jspace_inference_parent_admission_v1 import (
        JSpaceInferenceParentAdmissionError,
        require_admitted_inference_receipt_parent,
    )
    from .jspace_training_trace_v1 import (
        TrainingTrace,
        JSpaceTrainingTraceError,
        validate_training_trace,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA as CONTROL_BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
    from .preinvocation_canonical_predecessor_guard_v1 import (
        PreInvocationCanonicalPredecessorError,
        require_canonical_predecessor_execution,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding as validate_jspace_inference_binding,
    )
    from jspace_inference_parent_admission_v1 import (
        JSpaceInferenceParentAdmissionError,
        require_admitted_inference_receipt_parent,
    )
    from jspace_training_trace_v1 import (
        TrainingTrace,
        JSpaceTrainingTraceError,
        validate_training_trace,
    )
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA as CONTROL_BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
    from preinvocation_canonical_predecessor_guard_v1 import (
        PreInvocationCanonicalPredecessorError,
        require_canonical_predecessor_execution,
    )

STORE_SCHEMA = "HCU_PREINVOCATION_CONTROL_ADMISSION_STORE/v1"
PREPARATION_SCHEMA = "HCU_PREINVOCATION_CONTROL_PREPARATION/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class PreInvocationControlAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class PreInvocationControlPreparation:
    schema: str
    canonicalization_schema: str
    generation: int
    predecessor_jspace_binding_sha256: str
    predecessor_training_trace_sha256: str
    predecessor_prototype_trace_sha256: str
    predecessor_model_executor_id: str
    predecessor_model_invocation_id: str
    predecessor_vector_control_packet_sha256: str
    predecessor_vector_control_condition: str
    predecessor_jspace_basis_id: str
    predecessor_jspace_basis_sha256: str
    controlled_entry_event_sha256: str
    controlled_entry_admission_sha256: str
    controlled_route_decision_sha256: str
    controlled_grid_plan_sha256: str
    controlled_cell_id: str
    controlled_role: str
    controlled_executor_id: str
    controlled_invocation_id: str
    controlled_input_sha256: str
    controlled_input_size: int
    model_input_control_binding_schema: str
    model_input_control_binding_sha256: str
    preparation_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PreInvocationControlAdmissionError(message)


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    _need(
        len(normalized) == 64
        and normalized.lower() == normalized
        and all(ch in "0123456789abcdef" for ch in normalized)
        and normalized not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return normalized


def _safe_int(value: Any, field: str) -> int:
    _need(
        not isinstance(value, bool)
        and isinstance(value, int)
        and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise PreInvocationControlAdmissionError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    return _safe_int(row[0], "entity_state.generation")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonicalize(value)).hexdigest()


def _material(preparation: PreInvocationControlPreparation) -> dict[str, Any]:
    data = asdict(preparation)
    data.pop("preparation_sha256", None)
    return data


def _invocation_key(executor_id: str, invocation_id: str) -> str:
    return _canonical_sha256(
        {
            "executor_id": _text(executor_id, "executor_id", 256),
            "invocation_id": _text(invocation_id, "invocation_id", 256),
        }
    )


def _table_exists(db: sqlite3.Connection, table: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _controlled_execution_already_admitted(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> bool:
    if not _table_exists(db, "hcu_model_execution_invocations"):
        return False
    rows = db.execute(
        "SELECT 1 FROM hcu_model_execution_invocations "
        "WHERE executor_id=? AND invocation_id=? LIMIT 2",
        (executor_id, invocation_id),
    ).fetchall()
    _need(len(rows) <= 1, "MODEL_EXECUTION_INVOCATION_AMBIGUOUS")
    return bool(rows)


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    fk_row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk_row is not None and int(fk_row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_preinvocation_control_preparations(
          preparation_sha256 TEXT PRIMARY KEY,
          preparation_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          controlled_executor_id TEXT NOT NULL,
          controlled_invocation_id TEXT NOT NULL,
          predecessor_training_trace_sha256 TEXT NOT NULL,
          predecessor_jspace_binding_sha256 TEXT NOT NULL,
          model_input_control_binding_sha256 TEXT NOT NULL
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_preinvocation_control_invocations(
          invocation_binding_key TEXT PRIMARY KEY,
          controlled_executor_id TEXT NOT NULL,
          controlled_invocation_id TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          preparation_sha256 TEXT NOT NULL,
          FOREIGN KEY(preparation_sha256)
            REFERENCES hcu_preinvocation_control_preparations(preparation_sha256)
        )"""
    )


def _validate_sources(
    predecessor_trace: TrainingTrace,
    predecessor_jspace_binding: JSpaceInferenceBinding,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    controlled_grid_plan: GridPlan,
    *,
    current_generation: int,
) -> None:
    try:
        validate_training_trace(predecessor_trace)
    except (JSpaceTrainingTraceError, ValueError, TypeError) as exc:
        raise PreInvocationControlAdmissionError(f"PREDECESSOR_TRAINING_TRACE_REJECTED:{exc}") from exc
    try:
        validate_jspace_inference_binding(predecessor_jspace_binding)
    except (JSpaceInferenceBindingError, ValueError, TypeError) as exc:
        raise PreInvocationControlAdmissionError(f"PREDECESSOR_JSPACE_BINDING_REJECTED:{exc}") from exc
    try:
        validate_model_input_control_binding(input_binding, consumed_input_bytes)
    except (ModelInputControlBindingError, ValueError, TypeError) as exc:
        raise PreInvocationControlAdmissionError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc
    try:
        observed_plan = validate_grid_plan_identity(controlled_grid_plan)
    except (GridScheduleError, ValueError, TypeError) as exc:
        raise PreInvocationControlAdmissionError(f"CONTROLLED_GRID_PLAN_REJECTED:{exc}") from exc
    _need(observed_plan == controlled_grid_plan.plan_sha256, "CONTROLLED_GRID_PLAN_IDENTITY_MISMATCH")

    generation = _safe_int(current_generation, "current_generation")
    _need(predecessor_trace.generation == generation, "PREDECESSOR_TRACE_GENERATION_MISMATCH")
    _need(predecessor_jspace_binding.generation == generation, "PREDECESSOR_JSPACE_GENERATION_MISMATCH")
    _need(input_binding.generation == generation, "CONTROLLED_INPUT_GENERATION_MISMATCH")
    _need(controlled_grid_plan.entity_generation == generation, "CONTROLLED_GRID_GENERATION_MISMATCH")

    _need(
        predecessor_jspace_binding.training_trace_sha256 == predecessor_trace.trace_sha256,
        "PREDECESSOR_JSPACE_TRACE_IDENTITY_MISMATCH",
    )
    _need(
        predecessor_jspace_binding.prototype_trace_sha256 == predecessor_trace.prototype_trace_sha256,
        "PREDECESSOR_PROTOTYPE_TRACE_IDENTITY_MISMATCH",
    )
    _need(
        predecessor_jspace_binding.vector_control_packet_sha256
        == predecessor_trace.vector_control_packet_sha256,
        "PREDECESSOR_JSPACE_PACKET_IDENTITY_MISMATCH",
    )

    for left, right, code in (
        (
            predecessor_trace.vector_control_packet_sha256,
            input_binding.vector_control_packet_sha256,
            "PREDECESSOR_CONTROL_PACKET_IDENTITY_MISMATCH",
        ),
        (
            predecessor_trace.vector_control_packet_jcs_utf8,
            input_binding.vector_control_packet_jcs_utf8,
            "PREDECESSOR_CONTROL_PACKET_WIRE_MISMATCH",
        ),
        (
            predecessor_trace.vector_control_condition,
            input_binding.vector_control_condition,
            "PREDECESSOR_CONTROL_CONDITION_MISMATCH",
        ),
        (
            predecessor_trace.jspace_basis_id,
            input_binding.jspace_basis_id,
            "PREDECESSOR_CONTROL_BASIS_ID_MISMATCH",
        ),
        (
            predecessor_trace.jspace_basis_sha256,
            input_binding.jspace_basis_sha256,
            "PREDECESSOR_CONTROL_BASIS_SHA256_MISMATCH",
        ),
        (
            predecessor_trace.role,
            input_binding.role,
            "PREDECESSOR_CONTROL_ROLE_MISMATCH",
        ),
    ):
        _need(left == right, code)

    _need(
        not (
            predecessor_jspace_binding.model_execution_executor_id == input_binding.executor_id
            and predecessor_jspace_binding.model_execution_invocation_id == input_binding.invocation_id
        ),
        "SAME_INVOCATION_POSTHOC_CONTROL_FORBIDDEN",
    )

    for left, right, code in (
        (input_binding.grid_plan_sha256, controlled_grid_plan.plan_sha256, "CONTROLLED_GRID_PLAN_MISMATCH"),
        (input_binding.entry_event_sha256, controlled_grid_plan.entry_event_sha256, "CONTROLLED_ENTRY_EVENT_MISMATCH"),
        (
            input_binding.entry_admission_sha256,
            controlled_grid_plan.entry_admission_sha256,
            "CONTROLLED_ENTRY_ADMISSION_MISMATCH",
        ),
        (
            input_binding.route_decision_sha256,
            controlled_grid_plan.route_decision_sha256,
            "CONTROLLED_ROUTE_DECISION_MISMATCH",
        ),
    ):
        _need(left == right, code)

    matching_cells = [cell for cell in controlled_grid_plan.cells if cell.cell_id == input_binding.cell_id]
    _need(len(matching_cells) == 1, "CONTROLLED_GRID_CELL_NOT_UNIQUE")
    _need(
        matching_cells[0].execution_class is ExecutionClass.MODEL,
        "CONTROLLED_GRID_CELL_NOT_MODEL_EXECUTION",
    )
    _need(matching_cells[0].function == f"MODEL:{input_binding.role}", "CONTROLLED_GRID_CELL_ROLE_MISMATCH")


def prepare_preinvocation_control(
    db: sqlite3.Connection,
    predecessor_trace: TrainingTrace,
    predecessor_jspace_binding: JSpaceInferenceBinding,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    controlled_grid_plan: GridPlan,
    *,
    admitted_inference_receipts: Mapping[str, Any],
    current_generation: int,
) -> PreInvocationControlPreparation:
    """Commit predecessor control evidence before controlled ModelExecution admission exists.

    The canonical predecessor ModelExecution, exact admitted inference parent, and
    controlled-invocation absence are checked before the preparation is written. The caller
    must still invoke this on the real executor path before the physical model call to earn
    later temporal-control credit. This function itself proves database/admission ordering
    only.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _validate_sources(
        predecessor_trace,
        predecessor_jspace_binding,
        input_binding,
        consumed_input_bytes,
        controlled_grid_plan,
        current_generation=current_generation,
    )

    material = {
        "schema": PREPARATION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _safe_int(current_generation, "generation"),
        "predecessor_jspace_binding_sha256": _sha256(
            predecessor_jspace_binding.binding_sha256,
            "predecessor_jspace_binding_sha256",
        ),
        "predecessor_training_trace_sha256": _sha256(
            predecessor_trace.trace_sha256,
            "predecessor_training_trace_sha256",
        ),
        "predecessor_prototype_trace_sha256": _sha256(
            predecessor_trace.prototype_trace_sha256,
            "predecessor_prototype_trace_sha256",
        ),
        "predecessor_model_executor_id": _text(
            predecessor_jspace_binding.model_execution_executor_id,
            "predecessor_model_executor_id",
            256,
        ),
        "predecessor_model_invocation_id": _text(
            predecessor_jspace_binding.model_execution_invocation_id,
            "predecessor_model_invocation_id",
            256,
        ),
        "predecessor_vector_control_packet_sha256": _sha256(
            predecessor_trace.vector_control_packet_sha256,
            "predecessor_vector_control_packet_sha256",
        ),
        "predecessor_vector_control_condition": _text(
            predecessor_trace.vector_control_condition,
            "predecessor_vector_control_condition",
            64,
        ),
        "predecessor_jspace_basis_id": _text(
            predecessor_trace.jspace_basis_id,
            "predecessor_jspace_basis_id",
            256,
        ),
        "predecessor_jspace_basis_sha256": _sha256(
            predecessor_trace.jspace_basis_sha256,
            "predecessor_jspace_basis_sha256",
        ),
        "controlled_entry_event_sha256": _sha256(input_binding.entry_event_sha256, "controlled_entry_event_sha256"),
        "controlled_entry_admission_sha256": _sha256(
            input_binding.entry_admission_sha256,
            "controlled_entry_admission_sha256",
        ),
        "controlled_route_decision_sha256": _sha256(
            input_binding.route_decision_sha256,
            "controlled_route_decision_sha256",
        ),
        "controlled_grid_plan_sha256": _sha256(input_binding.grid_plan_sha256, "controlled_grid_plan_sha256"),
        "controlled_cell_id": _text(input_binding.cell_id, "controlled_cell_id", 256),
        "controlled_role": _text(input_binding.role, "controlled_role", 256),
        "controlled_executor_id": _text(input_binding.executor_id, "controlled_executor_id", 256),
        "controlled_invocation_id": _text(input_binding.invocation_id, "controlled_invocation_id", 256),
        "controlled_input_sha256": _sha256(input_binding.input_sha256, "controlled_input_sha256"),
        "controlled_input_size": _safe_int(input_binding.input_size, "controlled_input_size"),
        "model_input_control_binding_schema": CONTROL_BINDING_SCHEMA,
        "model_input_control_binding_sha256": _sha256(
            input_binding.binding_sha256,
            "model_input_control_binding_sha256",
        ),
    }
    preparation = PreInvocationControlPreparation(
        **material,
        preparation_sha256=_canonical_sha256(material),
    )
    preparation_bytes = canonicalize(asdict(preparation))
    invocation_key = _invocation_key(preparation.controlled_executor_id, preparation.controlled_invocation_id)

    try:
        db.execute("BEGIN IMMEDIATE")
        live_generation = _current_generation(db)
        _need(live_generation == current_generation, "STALE_PREINVOCATION_CONTROL_GENERATION")
        try:
            predecessor_observation_sha256 = require_canonical_predecessor_execution(
                db,
                predecessor_jspace_binding,
                current_generation=current_generation,
            )
        except PreInvocationCanonicalPredecessorError as exc:
            raise PreInvocationControlAdmissionError(
                f"PREDECESSOR_CANONICAL_EXECUTION_REJECTED:{exc}"
            ) from exc
        _need(
            predecessor_observation_sha256
            == predecessor_jspace_binding.model_execution_observation_sha256,
            "PREDECESSOR_CANONICAL_EXECUTION_OBSERVATION_MISMATCH",
        )
        try:
            require_admitted_inference_receipt_parent(
                predecessor_jspace_binding,
                admitted_inference_receipts,
            )
        except JSpaceInferenceParentAdmissionError as exc:
            raise PreInvocationControlAdmissionError(
                f"PREDECESSOR_INFERENCE_PARENT_REJECTED:{exc}"
            ) from exc
        _need(
            not _controlled_execution_already_admitted(
                db,
                executor_id=preparation.controlled_executor_id,
                invocation_id=preparation.controlled_invocation_id,
            ),
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_POSTHOC_PREPARATION_FORBIDDEN",
        )
        _install_schema(db)

        existing = db.execute(
            "SELECT preparation_jcs,entity_generation,controlled_executor_id,"
            "controlled_invocation_id,predecessor_training_trace_sha256,"
            "predecessor_jspace_binding_sha256,model_input_control_binding_sha256 "
            "FROM hcu_preinvocation_control_preparations WHERE preparation_sha256=?",
            (preparation.preparation_sha256,),
        ).fetchone()
        expected = (
            preparation_bytes,
            preparation.generation,
            preparation.controlled_executor_id,
            preparation.controlled_invocation_id,
            preparation.predecessor_training_trace_sha256,
            preparation.predecessor_jspace_binding_sha256,
            preparation.model_input_control_binding_sha256,
        )
        if existing is None:
            db.execute(
                "INSERT INTO hcu_preinvocation_control_preparations "
                "(preparation_sha256,preparation_jcs,entity_generation,controlled_executor_id,"
                "controlled_invocation_id,predecessor_training_trace_sha256,"
                "predecessor_jspace_binding_sha256,model_input_control_binding_sha256) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (preparation.preparation_sha256, *expected),
            )
        else:
            stored = (bytes(existing[0]), *existing[1:])
            _need(stored == expected, "PREINVOCATION_PREPARATION_DIGEST_COLLISION_OR_DIVERGENCE")

        invocation_row = db.execute(
            "SELECT controlled_executor_id,controlled_invocation_id,entity_generation,preparation_sha256 "
            "FROM hcu_preinvocation_control_invocations WHERE invocation_binding_key=?",
            (invocation_key,),
        ).fetchone()
        invocation_expected = (
            preparation.controlled_executor_id,
            preparation.controlled_invocation_id,
            preparation.generation,
            preparation.preparation_sha256,
        )
        if invocation_row is None:
            db.execute(
                "INSERT INTO hcu_preinvocation_control_invocations "
                "(invocation_binding_key,controlled_executor_id,controlled_invocation_id,"
                "entity_generation,preparation_sha256) VALUES(?,?,?,?,?)",
                (invocation_key, *invocation_expected),
            )
        else:
            _need(
                tuple(invocation_row) == invocation_expected,
                "PREINVOCATION_CONTROL_INVOCATION_REPLAY_DIVERGENCE",
            )
        db.commit()
        return preparation
    except (PreInvocationControlAdmissionError, sqlite3.Error):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise


def read_preinvocation_control_preparation(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> PreInvocationControlPreparation:
    """Read/revalidate one committed preparation by the controlled invocation identity."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _need(_table_exists(db, "hcu_preinvocation_control_invocations"), "PREINVOCATION_CONTROL_STORE_REQUIRED")
    key = _invocation_key(executor_id, invocation_id)
    row = db.execute(
        "SELECT preparation_sha256 FROM hcu_preinvocation_control_invocations "
        "WHERE invocation_binding_key=?",
        (key,),
    ).fetchone()
    _need(row is not None, "PREINVOCATION_CONTROL_PREPARATION_NOT_ADMITTED")
    preparation_sha256 = _sha256(str(row[0]), "preparation_sha256")
    record_row = db.execute(
        "SELECT preparation_jcs FROM hcu_preinvocation_control_preparations "
        "WHERE preparation_sha256=?",
        (preparation_sha256,),
    ).fetchone()
    _need(record_row is not None, "PREINVOCATION_CONTROL_PREPARATION_ROW_LOST")
    raw = bytes(record_row[0])
    try:
        record = json.loads(raw.decode("utf-8"))
        preparation = PreInvocationControlPreparation(**record)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise PreInvocationControlAdmissionError("PREINVOCATION_CONTROL_PREPARATION_STORED_BYTES_INVALID") from exc
    _need(canonicalize(record) == raw, "PREINVOCATION_CONTROL_PREPARATION_STORED_JCS_MISMATCH")
    observed = _sha256(preparation.preparation_sha256, "preparation.preparation_sha256")
    expected = _canonical_sha256(_material(preparation))
    _need(observed == expected, "PREINVOCATION_CONTROL_PREPARATION_DIGEST_MISMATCH")
    _need(preparation.controlled_executor_id == executor_id, "PREINVOCATION_CONTROL_EXECUTOR_MISMATCH")
    _need(preparation.controlled_invocation_id == invocation_id, "PREINVOCATION_CONTROL_INVOCATION_MISMATCH")
    return preparation


__all__ = [
    "STORE_SCHEMA",
    "PREPARATION_SCHEMA",
    "PreInvocationControlAdmissionError",
    "PreInvocationControlPreparation",
    "prepare_preinvocation_control",
    "read_preinvocation_control_preparation",
]
