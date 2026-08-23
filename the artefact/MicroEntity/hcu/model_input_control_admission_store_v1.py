#!/usr/bin/env python3
"""Atomically admit J-Space model-input control evidence inside canonical MiniUnifiedDB.

``model_input_control_binding_v1`` proves a byte-level fact about one exact executor input,
but its executor/invocation and causal-parent labels are parameters. This store closes that
trust split by requiring the same invocation to have already been admitted by
``HCU_MODEL_EXECUTION_ADMISSION_STORE/v1`` in the caller-supplied canonical MiniUnifiedDB
and by revalidating the exact scheduler-owned GRID plan named by that execution.

The transaction revalidates the exact consumed input bytes, reads back and semantically
revalidates the canonical ModelExecutionObservation, cross-binds generation/GRID
cell/role/input identity plus Entry event/admission and route-decision identities, and then
persists one immutable control binding per executor invocation. Divergent replay rolls back.
No new database, truth authority, effect path, model execution, or runtime/training credit is
created here.
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
    from .model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_observation_record,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
    from model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_observation_record,
    )
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )

SCHEMA = "HCU_MODEL_INPUT_CONTROL_ADMISSION_STORE/v1"
ADMISSION_SCHEMA = "HCU_MODEL_INPUT_CONTROL_ADMISSION/v1"


class ModelInputControlAdmissionStoreError(ValueError):
    pass


@dataclass(frozen=True)
class ModelInputControlAdmission:
    schema: str
    canonicalization_schema: str
    binding_schema: str
    binding_sha256: str
    model_execution_observation_sha256: str
    generation: int
    executor_id: str
    invocation_id: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    vector_control_packet_sha256: str
    input_sha256: str
    input_size: int
    admission_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ModelInputControlAdmissionStoreError(message)


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


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise ModelInputControlAdmissionStoreError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def _install_schema(db: sqlite3.Connection) -> None:
    _need(db.in_transaction, "ACTIVE_TRANSACTION_REQUIRED")
    fk_row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk_row is not None and int(fk_row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_model_input_control_bindings(
          binding_sha256 TEXT PRIMARY KEY,
          binding_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL,
          input_sha256 TEXT NOT NULL,
          input_size INTEGER NOT NULL,
          model_execution_observation_sha256 TEXT NOT NULL,
          FOREIGN KEY(model_execution_observation_sha256)
            REFERENCES hcu_model_execution_observations(observation_sha256)
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS hcu_model_input_control_invocations(
          invocation_binding_key TEXT PRIMARY KEY,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          model_execution_observation_sha256 TEXT NOT NULL,
          binding_sha256 TEXT NOT NULL,
          FOREIGN KEY(model_execution_observation_sha256)
            REFERENCES hcu_model_execution_observations(observation_sha256),
          FOREIGN KEY(binding_sha256)
            REFERENCES hcu_model_input_control_bindings(binding_sha256)
        )"""
    )


def _canonical_binding_bytes(binding: ModelInputControlBinding) -> bytes:
    data = asdict(binding)
    observed = _sha256(data.get("binding_sha256"), "binding.binding_sha256")
    material = dict(data)
    material.pop("binding_sha256")
    expected = hashlib.sha256(canonicalize(material)).hexdigest()
    _need(observed == expected, "MODEL_INPUT_CONTROL_BINDING_DIGEST_MISMATCH")
    return canonicalize(data)


def _read_model_execution_parent(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
) -> tuple[str, dict[str, Any], str]:
    """Read and revalidate one already-admitted model invocation and observation."""
    try:
        rows = db.execute(
            "SELECT invocation_binding_key,entity_generation,observation_sha256 "
            "FROM hcu_model_execution_invocations WHERE executor_id=? AND invocation_id=?",
            (executor_id, invocation_id),
        ).fetchall()
    except sqlite3.Error as exc:
        raise ModelInputControlAdmissionStoreError("MODEL_EXECUTION_ADMISSION_STORE_REQUIRED") from exc
    _need(len(rows) == 1, "EXACTLY_ONE_ADMITTED_MODEL_EXECUTION_INVOCATION_REQUIRED")
    invocation_key, generation, observation_sha256 = rows[0]
    observation_sha256 = _sha256(str(observation_sha256), "model_execution.observation_sha256")

    row = db.execute(
        "SELECT observation_jcs,entity_generation,executor_id,invocation_id "
        "FROM hcu_model_execution_observations WHERE observation_sha256=?",
        (observation_sha256,),
    ).fetchone()
    _need(row is not None, "MODEL_EXECUTION_OBSERVATION_ADMISSION_LOST")
    raw = bytes(row[0])
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelInputControlAdmissionStoreError("MODEL_EXECUTION_OBSERVATION_STORED_BYTES_INVALID") from exc
    _need(isinstance(record, dict), "MODEL_EXECUTION_OBSERVATION_STORED_OBJECT_REQUIRED")
    _need(canonicalize(record) == raw, "MODEL_EXECUTION_OBSERVATION_STORED_JCS_MISMATCH")
    _need(hashlib.sha256(raw).hexdigest() == observation_sha256, "MODEL_EXECUTION_OBSERVATION_DIGEST_MISMATCH")

    try:
        normalized = model_execution_observation_record(ModelExecutionObservation(**record))
    except (TypeError, ModelExecutionReceiptError) as exc:
        raise ModelInputControlAdmissionStoreError("MODEL_EXECUTION_OBSERVATION_SEMANTIC_REVALIDATION_FAILED") from exc
    _need(normalized == record, "MODEL_EXECUTION_OBSERVATION_NORMALIZATION_MISMATCH")
    _need(generation == row[1] == record["entity_generation"], "MODEL_EXECUTION_PARENT_GENERATION_MISMATCH")
    _need(executor_id == row[2] == record["executor_id"], "MODEL_EXECUTION_PARENT_EXECUTOR_MISMATCH")
    _need(invocation_id == row[3] == record["invocation_id"], "MODEL_EXECUTION_PARENT_INVOCATION_MISMATCH")
    return str(invocation_key), record, observation_sha256


def _cross_bind_parent(
    binding: ModelInputControlBinding,
    observation: dict[str, Any],
    observation_sha256: str,
) -> None:
    checks = {
        "entity_generation": (binding.generation, observation.get("entity_generation")),
        "executor_id": (binding.executor_id, observation.get("executor_id")),
        "invocation_id": (binding.invocation_id, observation.get("invocation_id")),
        "grid_plan_sha256": (binding.grid_plan_sha256, observation.get("grid_plan_sha256")),
        "output_producing_cell_id": (binding.cell_id, observation.get("output_producing_cell_id")),
        "role": (binding.role, observation.get("role")),
        "input_sha256": (binding.input_sha256, observation.get("input_sha256")),
        "input_size": (binding.input_size, observation.get("input_size")),
    }
    for field, (left, right) in checks.items():
        _need(left == right, f"MODEL_INPUT_CONTROL_PARENT_MISMATCH:{field}")
    _sha256(observation_sha256, "model_execution_observation_sha256")


def _cross_bind_grid_plan(
    binding: ModelInputControlBinding,
    grid_plan: GridPlan,
    observation: dict[str, Any],
) -> None:
    """Bind caller-visible causal labels to the exact scheduler-owned plan identity."""
    _need(isinstance(grid_plan, GridPlan), "GRID_PLAN_REQUIRED")
    try:
        observed_plan_sha256 = validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise ModelInputControlAdmissionStoreError("GRID_PLAN_SEMANTIC_REVALIDATION_FAILED") from exc

    _need(observed_plan_sha256 == grid_plan.plan_sha256, "GRID_PLAN_IDENTITY_REVALIDATION_MISMATCH")
    checks = {
        "grid_plan_sha256": (
            binding.grid_plan_sha256,
            grid_plan.plan_sha256,
            observation.get("grid_plan_sha256"),
        ),
        "generation": (
            binding.generation,
            grid_plan.entity_generation,
            observation.get("entity_generation"),
        ),
        "entry_event_sha256": (
            binding.entry_event_sha256,
            grid_plan.entry_event_sha256,
            grid_plan.entry_event_sha256,
        ),
        "entry_admission_sha256": (
            binding.entry_admission_sha256,
            grid_plan.entry_admission_sha256,
            grid_plan.entry_admission_sha256,
        ),
        "route_decision_sha256": (
            binding.route_decision_sha256,
            grid_plan.route_decision_sha256,
            grid_plan.route_decision_sha256,
        ),
    }
    for field, values in checks.items():
        _need(len(set(values)) == 1, f"MODEL_INPUT_CONTROL_GRID_PARENT_MISMATCH:{field}")

    matching_cells = [cell for cell in grid_plan.cells if cell.cell_id == binding.cell_id]
    _need(len(matching_cells) == 1, "MODEL_INPUT_CONTROL_GRID_CELL_NOT_UNIQUE")
    cell = matching_cells[0]
    _need(cell.execution_class is ExecutionClass.MODEL, "MODEL_INPUT_CONTROL_GRID_CELL_NOT_MODEL")
    _need(cell.function == f"MODEL:{binding.role}", "MODEL_INPUT_CONTROL_GRID_CELL_ROLE_MISMATCH")


def admit_model_input_control_binding(
    db: sqlite3.Connection,
    binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    grid_plan: GridPlan,
    *,
    current_generation: int,
) -> ModelInputControlAdmission:
    """Atomically bind one control packet to one admitted invocation and exact GRID parent."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _need(type(current_generation) is int and current_generation >= 0, "CURRENT_GENERATION_INVALID")
    _need(isinstance(binding, ModelInputControlBinding), "MODEL_INPUT_CONTROL_BINDING_REQUIRED")

    try:
        db.execute("BEGIN IMMEDIATE")
        live_generation = _current_generation(db)
        _need(live_generation == current_generation, "STALE_MODEL_INPUT_CONTROL_ADMISSION_GENERATION")
        _need(binding.generation == current_generation, "MODEL_INPUT_CONTROL_BINDING_GENERATION_MISMATCH")

        validate_model_input_control_binding(binding, consumed_input_bytes)
        binding_jcs = _canonical_binding_bytes(binding)
        invocation_key, observation, observation_sha256 = _read_model_execution_parent(
            db,
            executor_id=binding.executor_id,
            invocation_id=binding.invocation_id,
        )
        _cross_bind_parent(binding, observation, observation_sha256)
        _cross_bind_grid_plan(binding, grid_plan, observation)
        _install_schema(db)

        row = db.execute(
            "SELECT binding_jcs,entity_generation,executor_id,invocation_id,input_sha256,input_size,model_execution_observation_sha256 "
            "FROM hcu_model_input_control_bindings WHERE binding_sha256=?",
            (binding.binding_sha256,),
        ).fetchone()
        expected = (
            binding_jcs,
            binding.generation,
            binding.executor_id,
            binding.invocation_id,
            binding.input_sha256,
            binding.input_size,
            observation_sha256,
        )
        if row is None:
            db.execute(
                "INSERT INTO hcu_model_input_control_bindings "
                "(binding_sha256,binding_jcs,entity_generation,executor_id,invocation_id,input_sha256,input_size,model_execution_observation_sha256) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (binding.binding_sha256, *expected),
            )
        else:
            stored = (bytes(row[0]), *row[1:])
            _need(stored == expected, "MODEL_INPUT_CONTROL_BINDING_REPLAY_DIVERGENCE")

        invocation_row = db.execute(
            "SELECT executor_id,invocation_id,entity_generation,model_execution_observation_sha256,binding_sha256 "
            "FROM hcu_model_input_control_invocations WHERE invocation_binding_key=?",
            (invocation_key,),
        ).fetchone()
        invocation_expected = (
            binding.executor_id,
            binding.invocation_id,
            binding.generation,
            observation_sha256,
            binding.binding_sha256,
        )
        if invocation_row is None:
            db.execute(
                "INSERT INTO hcu_model_input_control_invocations "
                "(invocation_binding_key,executor_id,invocation_id,entity_generation,model_execution_observation_sha256,binding_sha256) "
                "VALUES(?,?,?,?,?,?)",
                (invocation_key, *invocation_expected),
            )
        else:
            _need(tuple(invocation_row) == invocation_expected, "MODEL_INPUT_CONTROL_INVOCATION_REPLAY_DIVERGENCE")

        material = {
            "schema": ADMISSION_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "binding_schema": BINDING_SCHEMA,
            "binding_sha256": binding.binding_sha256,
            "model_execution_observation_sha256": observation_sha256,
            "generation": binding.generation,
            "executor_id": binding.executor_id,
            "invocation_id": binding.invocation_id,
            "grid_plan_sha256": binding.grid_plan_sha256,
            "cell_id": binding.cell_id,
            "role": binding.role,
            "vector_control_packet_sha256": binding.vector_control_packet_sha256,
            "input_sha256": binding.input_sha256,
            "input_size": binding.input_size,
        }
        admission_sha256 = hashlib.sha256(canonicalize(material)).hexdigest()
        db.commit()
        return ModelInputControlAdmission(**material, admission_sha256=admission_sha256)
    except (
        ModelInputControlAdmissionStoreError,
        ModelInputControlBindingError,
        ModelExecutionReceiptError,
        sqlite3.Error,
    ):
        if db.in_transaction:
            db.rollback()
        raise
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise
