#!/usr/bin/env python3
"""Independent model-execution evidence for the EntityOS/HCU inference path.

This module is causal evidence plumbing only. It does not execute a model, mint truth,
grant capabilities, or create a second inference authority. Source-level construction
alone grants zero model/runtime credit.

A ModelExecutionObservation becomes admissible only when:
- it is explicitly marked as emitted by the actual model-executor I/O path;
- it is bound to the current generation, exact verified engine-load consumption receipt,
  exact scheduler-owned GRID plan and exact MODEL cell/role;
- the exact normalized observation already exists in an externally admitted observation
  registry;
- the exact executor/invocation identity is externally bound to that same observation
  digest, preventing one invocation identity from being admitted with different bytes.

The external registries are the trust split: a caller cannot obtain model-execution credit
merely by setting ``evidence_source=ACTUAL_MODEL_EXECUTOR_IO_PATH``, inventing an invocation
label, or admitting two different observations under the same executor invocation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .engine_load_lease_v1 import VERIFIED_LOAD_SCHEMA, VerifiedEngineLoad
    from .grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from engine_load_lease_v1 import VERIFIED_LOAD_SCHEMA, VerifiedEngineLoad
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity

OBSERVATION_SCHEMA = "HCU_MODEL_EXECUTION_OBSERVATION/v1"
VERIFIED_EXECUTION_SCHEMA = "HCU_VERIFIED_MODEL_EXECUTION/v1"
INVOCATION_BINDING_SCHEMA = "HCU_MODEL_EXECUTION_INVOCATION_BINDING/v1"
ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE = "ACTUAL_MODEL_EXECUTOR_IO_PATH"


class ModelExecutionReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class ModelExecutionObservation:
    schema: str
    evidence_source: str
    entity_generation: int
    executor_id: str
    invocation_id: str
    engine_load_consumption_receipt_sha256: str
    grid_plan_sha256: str
    output_producing_cell_id: str
    role: str
    input_sha256: str
    input_size: int
    output_ref: str
    output_sha256: str
    output_size: int


@dataclass(frozen=True)
class VerifiedModelExecution:
    schema: str
    canonicalization_schema: str
    observation_schema: str
    entity_generation: int
    executor_id: str
    invocation_id: str
    engine_load_consumption_receipt_sha256: str
    engine_identity: str
    engine_class: str
    engine_artifact_sha256: str
    grid_plan_sha256: str
    output_producing_cell_id: str
    role: str
    input_sha256: str
    input_size: int
    output_ref: str
    output_sha256: str
    output_size: int
    observation_sha256: str
    receipt_sha256: str

    def inference_echo(self) -> dict[str, Any]:
        """Fields a downstream canonical inference receipt must consume exactly."""
        return {
            "model_execution_canonicalization_schema": self.canonicalization_schema,
            "model_execution_receipt_sha256": self.receipt_sha256,
            "model_execution_observation_sha256": self.observation_sha256,
            "model_execution_executor_id": self.executor_id,
            "model_execution_invocation_id": self.invocation_id,
            "grid_plan_sha256": self.grid_plan_sha256,
            "output_producing_cell_id": self.output_producing_cell_id,
            "model_execution_role": self.role,
            "input_sha256": self.input_sha256,
            "input_size": self.input_size,
            "output_ref": self.output_ref,
            "output_sha256": self.output_sha256,
            "output_size": self.output_size,
        }


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelExecutionReceiptError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise ModelExecutionReceiptError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ModelExecutionReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise ModelExecutionReceiptError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ModelExecutionReceiptError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise ModelExecutionReceiptError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ModelExecutionReceiptError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise ModelExecutionReceiptError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def model_execution_observation_record(observation: ModelExecutionObservation) -> dict[str, Any]:
    if not isinstance(observation, ModelExecutionObservation):
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OBSERVATION_REQUIRED")
    if observation.schema != OBSERVATION_SCHEMA:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OBSERVATION_SCHEMA_UNSUPPORTED")
    if observation.evidence_source != ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE:
        raise ModelExecutionReceiptError("ACTUAL_MODEL_EXECUTOR_IO_EVIDENCE_REQUIRED")
    return {
        "schema": OBSERVATION_SCHEMA,
        "evidence_source": ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
        "entity_generation": _generation(observation.entity_generation, "observation.entity_generation"),
        "executor_id": _text(observation.executor_id, "observation.executor_id"),
        "invocation_id": _text(observation.invocation_id, "observation.invocation_id"),
        "engine_load_consumption_receipt_sha256": _sha256(
            observation.engine_load_consumption_receipt_sha256,
            "observation.engine_load_consumption_receipt_sha256",
        ),
        "grid_plan_sha256": _sha256(observation.grid_plan_sha256, "observation.grid_plan_sha256"),
        "output_producing_cell_id": _text(
            observation.output_producing_cell_id,
            "observation.output_producing_cell_id",
            256,
        ),
        "role": _text(observation.role, "observation.role", 256),
        "input_sha256": _sha256(observation.input_sha256, "observation.input_sha256"),
        "input_size": _nonnegative_int(observation.input_size, "observation.input_size"),
        "output_ref": _text(observation.output_ref, "observation.output_ref"),
        "output_sha256": _sha256(observation.output_sha256, "observation.output_sha256"),
        "output_size": _nonnegative_int(observation.output_size, "observation.output_size"),
    }


def model_execution_observation_sha256(observation: ModelExecutionObservation) -> str:
    return _canonical_sha256(
        model_execution_observation_record(observation),
        "MODEL_EXECUTION_OBSERVATION",
    )


def _invocation_binding_key(record: Mapping[str, Any]) -> str:
    return _canonical_sha256(
        {
            "schema": INVOCATION_BINDING_SCHEMA,
            "executor_id": _text(record.get("executor_id"), "record.executor_id"),
            "invocation_id": _text(record.get("invocation_id"), "record.invocation_id"),
        },
        "MODEL_EXECUTION_INVOCATION_BINDING",
    )


def model_execution_invocation_binding_key(observation: ModelExecutionObservation) -> str:
    """Stable external-registry key for one executor-scoped invocation identity."""
    return _invocation_binding_key(model_execution_observation_record(observation))


def verify_model_execution(
    grid_plan: GridPlan,
    verified_engine_load: VerifiedEngineLoad,
    observation: ModelExecutionObservation,
    *,
    admitted_model_execution_observations: Mapping[str, Any],
    admitted_model_execution_invocations: Mapping[str, Any],
    current_generation: int,
) -> VerifiedModelExecution:
    """Bind externally admitted actual executor I/O evidence to GRID10 and the loaded engine."""
    current_generation = _generation(current_generation, "current_generation")
    try:
        validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise ModelExecutionReceiptError(f"GRID10_PLAN_REJECTED:{exc}") from exc

    if not isinstance(verified_engine_load, VerifiedEngineLoad):
        raise ModelExecutionReceiptError("VERIFIED_ENGINE_LOAD_REQUIRED")
    if verified_engine_load.schema != VERIFIED_LOAD_SCHEMA:
        raise ModelExecutionReceiptError("VERIFIED_ENGINE_LOAD_SCHEMA_UNSUPPORTED")
    if verified_engine_load.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise ModelExecutionReceiptError("VERIFIED_ENGINE_LOAD_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    record = model_execution_observation_record(observation)
    generation = record["entity_generation"]
    if generation != current_generation:
        raise ModelExecutionReceiptError("STALE_MODEL_EXECUTION_OBSERVATION_GENERATION")
    if grid_plan.entity_generation != generation:
        raise ModelExecutionReceiptError("GRID10_MODEL_EXECUTION_GENERATION_MISMATCH")
    if verified_engine_load.entity_generation != generation:
        raise ModelExecutionReceiptError("ENGINE_LOAD_MODEL_EXECUTION_GENERATION_MISMATCH")

    load_receipt_sha256 = _sha256(
        verified_engine_load.consumption_receipt_sha256,
        "verified_engine_load.consumption_receipt_sha256",
    )
    if record["engine_load_consumption_receipt_sha256"] != load_receipt_sha256:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_ENGINE_LOAD_RECEIPT_MISMATCH")

    if grid_plan.plan_sha256 != record["grid_plan_sha256"]:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_GRID10_PLAN_MISMATCH")
    if grid_plan.resolved_engine_identity != verified_engine_load.engine_identity:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_ENGINE_IDENTITY_MISMATCH")
    if grid_plan.resolved_engine_class != verified_engine_load.engine_class:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_ENGINE_CLASS_MISMATCH")
    if grid_plan.resolved_engine_artifact_sha256 != verified_engine_load.engine_artifact_sha256:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_ENGINE_ARTIFACT_MISMATCH")

    matching_cells = [
        cell
        for cell in grid_plan.cells
        if cell.cell_id == record["output_producing_cell_id"]
    ]
    if len(matching_cells) != 1:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OUTPUT_CELL_NOT_UNIQUE_IN_GRID10_PLAN")
    cell = matching_cells[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OUTPUT_CELL_NOT_MODEL")
    if cell.function != f"MODEL:{record['role']}":
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OUTPUT_CELL_ROLE_MISMATCH")

    observation_sha256 = _canonical_sha256(record, "MODEL_EXECUTION_OBSERVATION")
    if not isinstance(admitted_model_execution_observations, Mapping):
        raise ModelExecutionReceiptError("ADMITTED_MODEL_EXECUTION_OBSERVATION_REGISTRY_REQUIRED")
    admitted = admitted_model_execution_observations.get(observation_sha256)
    if not isinstance(admitted, Mapping):
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OBSERVATION_NOT_ADMITTED")
    if dict(admitted) != record:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_OBSERVATION_REGISTRY_MISMATCH")

    if not isinstance(admitted_model_execution_invocations, Mapping):
        raise ModelExecutionReceiptError("ADMITTED_MODEL_EXECUTION_INVOCATION_REGISTRY_REQUIRED")
    invocation_key = _invocation_binding_key(record)
    admitted_observation_sha256 = admitted_model_execution_invocations.get(invocation_key)
    if admitted_observation_sha256 is None:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_INVOCATION_NOT_ADMITTED")
    if _sha256(
        admitted_observation_sha256,
        "admitted_model_execution_invocations.observation_sha256",
    ) != observation_sha256:
        raise ModelExecutionReceiptError("MODEL_EXECUTION_INVOCATION_OBSERVATION_MISMATCH")

    material = {
        "schema": VERIFIED_EXECUTION_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "observation_schema": OBSERVATION_SCHEMA,
        "entity_generation": generation,
        "executor_id": record["executor_id"],
        "invocation_id": record["invocation_id"],
        "engine_load_consumption_receipt_sha256": load_receipt_sha256,
        "engine_identity": _text(verified_engine_load.engine_identity, "verified_engine_load.engine_identity"),
        "engine_class": _text(verified_engine_load.engine_class, "verified_engine_load.engine_class"),
        "engine_artifact_sha256": _sha256(
            verified_engine_load.engine_artifact_sha256,
            "verified_engine_load.engine_artifact_sha256",
        ),
        "grid_plan_sha256": grid_plan.plan_sha256,
        "output_producing_cell_id": record["output_producing_cell_id"],
        "role": record["role"],
        "input_sha256": record["input_sha256"],
        "input_size": record["input_size"],
        "output_ref": record["output_ref"],
        "output_sha256": record["output_sha256"],
        "output_size": record["output_size"],
        "observation_sha256": observation_sha256,
    }
    receipt_sha256 = _canonical_sha256(material, "VERIFIED_MODEL_EXECUTION")
    return VerifiedModelExecution(**material, receipt_sha256=receipt_sha256)


def validate_verified_model_execution(value: VerifiedModelExecution) -> None:
    if not isinstance(value, VerifiedModelExecution):
        raise ModelExecutionReceiptError("VERIFIED_MODEL_EXECUTION_REQUIRED")
    material = asdict(value)
    observed = _sha256(material.pop("receipt_sha256", None), "verified_model_execution.receipt_sha256")
    if material.get("schema") != VERIFIED_EXECUTION_SCHEMA:
        raise ModelExecutionReceiptError("VERIFIED_MODEL_EXECUTION_SCHEMA_UNSUPPORTED")
    if material.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise ModelExecutionReceiptError("VERIFIED_MODEL_EXECUTION_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if material.get("observation_schema") != OBSERVATION_SCHEMA:
        raise ModelExecutionReceiptError("VERIFIED_MODEL_EXECUTION_OBSERVATION_SCHEMA_UNSUPPORTED")
    expected = _canonical_sha256(material, "VERIFIED_MODEL_EXECUTION")
    if observed != expected:
        raise ModelExecutionReceiptError("VERIFIED_MODEL_EXECUTION_DIGEST_MISMATCH")
