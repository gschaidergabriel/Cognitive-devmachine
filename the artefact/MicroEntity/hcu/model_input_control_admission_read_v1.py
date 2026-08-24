#!/usr/bin/env python3
"""Read-only semantic guard for an already-admitted HCU model-input-control binding.

This module is a derived verifier over the existing canonical MiniUnifiedDB tables owned by
``HCU_MODEL_INPUT_CONTROL_ADMISSION_STORE/v1``. It never creates tables, inserts rows, updates
rows, commits evidence, or opens a competing state authority. Its purpose is to let downstream
J-Space/training code prove that a claimed ModelInputControlAdmission already existed before
validation rather than accidentally minting it by calling the admission path.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import sqlite3

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .grid10_scheduler_v1 import GridPlan
    from .model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA,
        ModelInputControlAdmission,
        ModelInputControlAdmissionStoreError,
        _canonical_binding_bytes,
        _cross_bind_grid_plan,
        _cross_bind_parent,
        _current_generation,
        _read_model_execution_parent,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA,
        ModelInputControlAdmission,
        ModelInputControlAdmissionStoreError,
        _canonical_binding_bytes,
        _cross_bind_grid_plan,
        _cross_bind_parent,
        _current_generation,
        _read_model_execution_parent,
    )
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )


class ModelInputControlAdmissionReadError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ModelInputControlAdmissionReadError(message)


def require_existing_model_input_control_admission(
    db: sqlite3.Connection,
    binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    grid_plan: GridPlan,
    *,
    current_generation: int,
) -> ModelInputControlAdmission:
    """Return the deterministic admission record only if all canonical rows already exist.

    The function is intentionally read-only. Missing control-admission rows are rejection,
    never an invitation to call INSERT from inside a validator.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    _need(type(current_generation) is int and current_generation >= 0, "CURRENT_GENERATION_INVALID")
    _need(isinstance(binding, ModelInputControlBinding), "MODEL_INPUT_CONTROL_BINDING_REQUIRED")

    try:
        live_generation = _current_generation(db)
        _need(live_generation == current_generation, "STALE_MODEL_INPUT_CONTROL_READ_GENERATION")
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

        try:
            row = db.execute(
                "SELECT binding_jcs,entity_generation,executor_id,invocation_id,input_sha256,input_size,model_execution_observation_sha256 "
                "FROM hcu_model_input_control_bindings WHERE binding_sha256=?",
                (binding.binding_sha256,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ModelInputControlAdmissionReadError(
                "MODEL_INPUT_CONTROL_ADMISSION_STORE_REQUIRED"
            ) from exc
        _need(row is not None, "MODEL_INPUT_CONTROL_BINDING_NOT_ADMITTED")
        stored_binding = (bytes(row[0]), *row[1:])
        expected_binding = (
            binding_jcs,
            binding.generation,
            binding.executor_id,
            binding.invocation_id,
            binding.input_sha256,
            binding.input_size,
            observation_sha256,
        )
        _need(stored_binding == expected_binding, "MODEL_INPUT_CONTROL_BINDING_STORED_DIVERGENCE")

        try:
            invocation_row = db.execute(
                "SELECT executor_id,invocation_id,entity_generation,model_execution_observation_sha256,binding_sha256 "
                "FROM hcu_model_input_control_invocations WHERE invocation_binding_key=?",
                (invocation_key,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ModelInputControlAdmissionReadError(
                "MODEL_INPUT_CONTROL_ADMISSION_STORE_REQUIRED"
            ) from exc
        _need(invocation_row is not None, "MODEL_INPUT_CONTROL_INVOCATION_NOT_ADMITTED")
        invocation_expected = (
            binding.executor_id,
            binding.invocation_id,
            binding.generation,
            observation_sha256,
            binding.binding_sha256,
        )
        _need(tuple(invocation_row) == invocation_expected, "MODEL_INPUT_CONTROL_INVOCATION_STORED_DIVERGENCE")

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
        admission = ModelInputControlAdmission(**material, admission_sha256=admission_sha256)

        # A final field-set round trip makes accidental dataclass drift fail here instead of
        # silently changing the downstream closure identity.
        _need(set(asdict(admission)) == set(material) | {"admission_sha256"}, "MODEL_INPUT_CONTROL_ADMISSION_FIELD_SET_MISMATCH")
        return admission
    except (
        ModelInputControlAdmissionReadError,
        ModelInputControlAdmissionStoreError,
        ModelInputControlBindingError,
        sqlite3.Error,
    ):
        raise
    except Exception as exc:
        raise ModelInputControlAdmissionReadError(
            f"MODEL_INPUT_CONTROL_READ_REVALIDATION_FAILED:{exc}"
        ) from exc
