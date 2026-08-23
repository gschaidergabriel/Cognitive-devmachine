#!/usr/bin/env python3
"""Read back canonical model-input control evidence as a serious J-Space training parent.

``HCU_MODEL_INPUT_CONTROL_ADMISSION_STORE/v1`` atomically admits an exact
``HCU_MODEL_INPUT_CONTROL_BINDING/v1`` behind one already-admitted ModelExecution
invocation in the caller-supplied canonical MiniUnifiedDB. This module is the read-side
bridge: it re-reads those canonical rows, revalidates their exact stored JCS bytes and
ModelExecution parent, revalidates the exact executor-consumed input bytes, and cross-binds
that evidence to already-admitted J-Space DatasetAdmission/InferenceBinding parents.

Parent semantics are delegated to the current single reusable InferenceReceipt and
Vector-Control parent guards. This module adds only the previously missing relation from
their admitted row to canonical model-input-control evidence. It creates no database,
performs no write, mints no truth/effect authority, and grants no runtime/model/training
credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .jspace_dataset_admission_gate_v1 import DatasetAdmission
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding
    from .jspace_inference_parent_admission_v1 import (
        JSpaceInferenceParentAdmissionError,
        require_admitted_inference_receipt_parent,
    )
    from .jspace_vector_control_parent_admission_v1 import (
        JSpaceVectorControlParentAdmissionError,
        require_admitted_vector_control_packet_parent,
    )
    from .jspace_vector_control_v1 import VectorControlPacket
    from .model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
    )
    from .model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA as MODEL_INPUT_ADMISSION_SCHEMA,
        SCHEMA as MODEL_INPUT_STORE_SCHEMA,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from jspace_dataset_admission_gate_v1 import DatasetAdmission
    from jspace_inference_binding_v1 import JSpaceInferenceBinding
    from jspace_inference_parent_admission_v1 import (
        JSpaceInferenceParentAdmissionError,
        require_admitted_inference_receipt_parent,
    )
    from jspace_vector_control_parent_admission_v1 import (
        JSpaceVectorControlParentAdmissionError,
        require_admitted_vector_control_packet_parent,
    )
    from jspace_vector_control_v1 import VectorControlPacket
    from model_execution_receipt_v1 import (
        ModelExecutionObservation,
        ModelExecutionReceiptError,
        model_execution_invocation_binding_key,
        model_execution_observation_record,
    )
    from model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA as MODEL_INPUT_ADMISSION_SCHEMA,
        SCHEMA as MODEL_INPUT_STORE_SCHEMA,
    )
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )

PARENT_SCHEMA = "ENTITYOS_HCU_JSPACE_MODEL_INPUT_TRAINING_PARENT/v1"


class ModelInputTrainingParentError(ValueError):
    pass


@dataclass(frozen=True)
class ModelInputTrainingParent:
    schema: str
    model_input_store_schema: str
    model_input_admission_schema: str
    model_input_admission_sha256: str
    model_input_binding_schema: str
    model_input_binding_sha256: str
    model_execution_observation_sha256: str
    training_trace_sha256: str
    inference_receipt_sha256: str
    vector_control_packet_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    vector_control_condition: str
    executor_id: str
    invocation_id: str
    input_sha256: str
    input_size: int


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ModelInputTrainingParentError(message)


def _same(left: Any, right: Any, field: str) -> Any:
    if left != right:
        raise ModelInputTrainingParentError(f"MODEL_INPUT_TRAINING_PARENT_MISMATCH:{field}")
    return left


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


def _canonical_object(raw: Any, field: str) -> dict[str, Any]:
    try:
        payload = bytes(raw)
        value = json.loads(payload.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelInputTrainingParentError(f"{field}:STORED_JCS_INVALID") from exc
    _need(isinstance(value, dict), f"{field}:STORED_OBJECT_REQUIRED")
    _need(canonicalize(value) == payload, f"{field}:STORED_JCS_MISMATCH")
    return value


def _model_input_admission_sha256(
    binding: ModelInputControlBinding,
    model_execution_observation_sha256: str,
) -> str:
    material = {
        "schema": MODEL_INPUT_ADMISSION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "binding_schema": BINDING_SCHEMA,
        "binding_sha256": binding.binding_sha256,
        "model_execution_observation_sha256": model_execution_observation_sha256,
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
    return hashlib.sha256(canonicalize(material)).hexdigest()


def _read_canonical_model_input_parent(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
    consumed_input_bytes: bytes,
) -> tuple[ModelInputControlBinding, str, str]:
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "CALLER_TRANSACTION_FORBIDDEN")
    fk = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk is not None and int(fk[0]) == 1, "FOREIGN_KEYS_REQUIRED")

    try:
        rows = db.execute(
            """SELECT
                 i.invocation_binding_key,
                 i.entity_generation,
                 i.model_execution_observation_sha256,
                 i.binding_sha256,
                 b.binding_jcs,
                 b.entity_generation,
                 b.executor_id,
                 b.invocation_id,
                 b.input_sha256,
                 b.input_size,
                 b.model_execution_observation_sha256,
                 o.observation_jcs,
                 o.entity_generation,
                 o.executor_id,
                 o.invocation_id
               FROM hcu_model_input_control_invocations AS i
               JOIN hcu_model_input_control_bindings AS b
                 ON b.binding_sha256=i.binding_sha256
               JOIN hcu_model_execution_observations AS o
                 ON o.observation_sha256=i.model_execution_observation_sha256
               WHERE i.executor_id=? AND i.invocation_id=?""",
            (executor_id, invocation_id),
        ).fetchall()
    except sqlite3.Error as exc:
        raise ModelInputTrainingParentError(
            "MODEL_INPUT_CONTROL_CANONICAL_ADMISSION_STORE_REQUIRED"
        ) from exc

    _need(len(rows) == 1, "EXACTLY_ONE_CANONICAL_MODEL_INPUT_CONTROL_PARENT_REQUIRED")
    (
        invocation_binding_key,
        invocation_generation,
        invocation_observation_sha256,
        invocation_binding_sha256,
        binding_jcs,
        binding_generation,
        binding_executor_id,
        binding_invocation_id,
        binding_input_sha256,
        binding_input_size,
        binding_observation_sha256,
        observation_jcs,
        observation_generation,
        observation_executor_id,
        observation_invocation_id,
    ) = rows[0]

    binding_record = _canonical_object(binding_jcs, "MODEL_INPUT_CONTROL_BINDING")
    try:
        binding = ModelInputControlBinding(**binding_record)
        validate_model_input_control_binding(binding, consumed_input_bytes)
    except (TypeError, ModelInputControlBindingError) as exc:
        raise ModelInputTrainingParentError(
            f"MODEL_INPUT_CONTROL_BINDING_REVALIDATION_FAILED:{exc}"
        ) from exc

    observed_binding_sha256 = _sha256(binding.binding_sha256, "binding.binding_sha256")
    _same(str(invocation_binding_sha256), observed_binding_sha256, "invocation.binding_sha256")
    _same(str(binding_executor_id), binding.executor_id, "binding.executor_id")
    _same(str(binding_invocation_id), binding.invocation_id, "binding.invocation_id")
    _same(binding_generation, binding.generation, "binding.generation")
    _same(str(binding_input_sha256), binding.input_sha256, "binding.input_sha256")
    _same(binding_input_size, binding.input_size, "binding.input_size")

    observation_sha256 = _sha256(
        str(invocation_observation_sha256),
        "invocation.model_execution_observation_sha256",
    )
    _same(
        str(binding_observation_sha256),
        observation_sha256,
        "binding.model_execution_observation_sha256",
    )
    observation_record = _canonical_object(observation_jcs, "MODEL_EXECUTION_OBSERVATION")
    _need(
        hashlib.sha256(canonicalize(observation_record)).hexdigest() == observation_sha256,
        "MODEL_EXECUTION_OBSERVATION_DIGEST_MISMATCH",
    )
    try:
        observation = ModelExecutionObservation(**observation_record)
        normalized_observation = model_execution_observation_record(observation)
    except (TypeError, ModelExecutionReceiptError) as exc:
        raise ModelInputTrainingParentError(
            "MODEL_EXECUTION_OBSERVATION_SEMANTIC_REVALIDATION_FAILED"
        ) from exc
    _need(
        normalized_observation == observation_record,
        "MODEL_EXECUTION_OBSERVATION_NORMALIZATION_MISMATCH",
    )
    _same(observation_generation, observation.entity_generation, "observation.generation")
    _same(str(observation_executor_id), observation.executor_id, "observation.executor_id")
    _same(str(observation_invocation_id), observation.invocation_id, "observation.invocation_id")
    _same(invocation_generation, observation.entity_generation, "invocation.generation")
    _same(executor_id, observation.executor_id, "requested.executor_id")
    _same(invocation_id, observation.invocation_id, "requested.invocation_id")
    _same(
        str(invocation_binding_key),
        model_execution_invocation_binding_key(observation),
        "invocation.binding_key",
    )

    for field, left, right in (
        ("generation", binding.generation, observation.entity_generation),
        ("grid_plan_sha256", binding.grid_plan_sha256, observation.grid_plan_sha256),
        ("cell_id", binding.cell_id, observation.output_producing_cell_id),
        ("role", binding.role, observation.role),
        ("input_sha256", binding.input_sha256, observation.input_sha256),
        ("input_size", binding.input_size, observation.input_size),
    ):
        _same(left, right, f"model_execution.{field}")

    admission_sha256 = _model_input_admission_sha256(binding, observation_sha256)
    return binding, observation_sha256, admission_sha256


def require_admitted_model_input_training_parent(
    db: sqlite3.Connection,
    admission: DatasetAdmission,
    inference_binding: JSpaceInferenceBinding,
    consumed_input_bytes: bytes,
    *,
    admitted_inference_receipts: Mapping[str, Any],
    admitted_vector_control_packets: Mapping[str, VectorControlPacket],
) -> ModelInputTrainingParent:
    """Require one admitted J-Space row to inherit one canonical executor-input parent.

    This guard assumes the serious-training caller also runs its canonical row-level
    TrainingTrace/DatasetAdmission/InferenceBinding closure. Here we only delegate the two
    external parent admissions and add the missing canonical ModelInputControl relation.
    """
    try:
        require_admitted_inference_receipt_parent(
            inference_binding,
            admitted_inference_receipts,
        )
    except JSpaceInferenceParentAdmissionError as exc:
        raise ModelInputTrainingParentError(
            f"INFERENCE_PARENT_ADMISSION_REJECTED:{exc}"
        ) from exc

    try:
        require_admitted_vector_control_packet_parent(
            admission,
            admitted_vector_control_packets,
        )
    except JSpaceVectorControlParentAdmissionError as exc:
        raise ModelInputTrainingParentError(
            f"VECTOR_CONTROL_PARENT_ADMISSION_REJECTED:{exc}"
        ) from exc

    binding, observation_sha256, model_input_admission_sha256 = (
        _read_canonical_model_input_parent(
            db,
            executor_id=inference_binding.model_execution_executor_id,
            invocation_id=inference_binding.model_execution_invocation_id,
            consumed_input_bytes=consumed_input_bytes,
        )
    )

    # Unique new relation: canonical model-input evidence -> admitted DatasetAdmission row.
    for field in (
        "generation",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "cell_id",
        "role",
        "jspace_basis_id",
        "jspace_basis_sha256",
        "vector_control_packet_sha256",
        "vector_control_condition",
    ):
        _same(getattr(admission, field), getattr(binding, field), f"admission.{field}")

    # Unique new relation: canonical model-input evidence -> admitted ModelExecution/Inference row.
    for field, left, right in (
        (
            "inference.executor_id",
            inference_binding.model_execution_executor_id,
            binding.executor_id,
        ),
        (
            "inference.invocation_id",
            inference_binding.model_execution_invocation_id,
            binding.invocation_id,
        ),
        ("inference.input_sha256", inference_binding.input_sha256, binding.input_sha256),
        ("inference.input_size", inference_binding.input_size, binding.input_size),
        (
            "inference.model_execution_observation_sha256",
            inference_binding.model_execution_observation_sha256,
            observation_sha256,
        ),
    ):
        _same(left, right, field)

    return ModelInputTrainingParent(
        schema=PARENT_SCHEMA,
        model_input_store_schema=MODEL_INPUT_STORE_SCHEMA,
        model_input_admission_schema=MODEL_INPUT_ADMISSION_SCHEMA,
        model_input_admission_sha256=model_input_admission_sha256,
        model_input_binding_schema=BINDING_SCHEMA,
        model_input_binding_sha256=binding.binding_sha256,
        model_execution_observation_sha256=observation_sha256,
        training_trace_sha256=admission.training_trace_sha256,
        inference_receipt_sha256=inference_binding.inference_receipt_sha256,
        vector_control_packet_sha256=admission.vector_control_packet_sha256,
        generation=admission.generation,
        entry_event_sha256=admission.entry_event_sha256,
        entry_admission_sha256=admission.entry_admission_sha256,
        route_decision_sha256=admission.route_decision_sha256,
        grid_plan_sha256=admission.grid_plan_sha256,
        cell_id=admission.cell_id,
        role=admission.role,
        jspace_basis_id=admission.jspace_basis_id,
        jspace_basis_sha256=admission.jspace_basis_sha256,
        vector_control_condition=admission.vector_control_condition,
        executor_id=binding.executor_id,
        invocation_id=binding.invocation_id,
        input_sha256=binding.input_sha256,
        input_size=binding.input_size,
    )


__all__ = [
    "PARENT_SCHEMA",
    "ModelInputTrainingParent",
    "ModelInputTrainingParentError",
    "require_admitted_model_input_training_parent",
]
