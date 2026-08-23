#!/usr/bin/env python3
"""Single causal admission binding for serious EntityOS/HCU J-Space training evidence.

This module does not create another truth, memory, inference, or effect authority. It joins
three already-selected evidence objects and fails closed unless they describe the same
observable transition:

  JSPACE_GWT_TRANSITION_TRACE/v1
      -> ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1
      -> ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v1.

The result is a bounded training-evidence receipt. It is not model reward by itself and does
not authorize the owner-approved Together job.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_gwt_prototype_v1 import (
        JSpaceGWTTransitionTrace,
        TRACE_SCHEMA as TRANSITION_TRACE_SCHEMA,
        validate_transition_trace,
    )
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        validate_binding as validate_inference_binding,
    )
    from .jspace_training_trace_v1 import (
        TRACE_SCHEMA as TRAINING_TRACE_SCHEMA,
        TrainingTrace,
        validate_training_trace,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_gwt_prototype_v1 import (
        JSpaceGWTTransitionTrace,
        TRACE_SCHEMA as TRANSITION_TRACE_SCHEMA,
        validate_transition_trace,
    )
    from jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        validate_binding as validate_inference_binding,
    )
    from jspace_training_trace_v1 import (
        TRACE_SCHEMA as TRAINING_TRACE_SCHEMA,
        TrainingTrace,
        validate_training_trace,
    )

SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_TRAINING_BINDING/v1"


class JSpaceCausalTrainingBindingError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceCausalTrainingBinding:
    schema: str
    canonicalization_schema: str
    transition_trace_schema: str
    transition_trace_sha256: str
    training_trace_schema: str
    training_trace_sha256: str
    trace_family_id: str
    inference_binding_schema: str
    inference_binding_sha256: str
    inference_receipt_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    vector_control_packet_sha256: str
    vector_control_condition: str
    engine_identity_sha256: str
    engine_load_consumption_receipt_sha256: str
    model_call_id: str
    output_sha256: str
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceCausalTrainingBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceCausalTrainingBindingError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceCausalTrainingBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceCausalTrainingBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceCausalTrainingBindingError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceCausalTrainingBindingError("generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceCausalTrainingBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _require_equal(field: str, *values: Any) -> Any:
    if not values or any(value != values[0] for value in values[1:]):
        raise JSpaceCausalTrainingBindingError(f"CAUSAL_BINDING_MISMATCH:{field}")
    return values[0]


def bind_causal_training_evidence(
    transition_trace: JSpaceGWTTransitionTrace,
    training_trace: TrainingTrace,
    inference_binding: JSpaceInferenceBinding,
) -> JSpaceCausalTrainingBinding:
    """Join exact causal-transition, training, and real-inference evidence into one receipt."""
    try:
        validate_transition_trace(transition_trace)
    except Exception as exc:
        raise JSpaceCausalTrainingBindingError(f"TRANSITION_TRACE_REJECTED:{exc}") from exc
    try:
        validate_training_trace(training_trace)
    except Exception as exc:
        raise JSpaceCausalTrainingBindingError(f"TRAINING_TRACE_REJECTED:{exc}") from exc
    try:
        validate_inference_binding(inference_binding)
    except Exception as exc:
        raise JSpaceCausalTrainingBindingError(f"INFERENCE_BINDING_REJECTED:{exc}") from exc

    generation = _require_equal(
        "generation",
        transition_trace.generation,
        training_trace.generation,
        inference_binding.generation,
    )
    entry_event = _require_equal(
        "entry_event_sha256",
        transition_trace.entry_event_sha256,
        training_trace.entry_event_sha256,
        inference_binding.entry_event_sha256,
    )
    entry_admission = _require_equal(
        "entry_admission_sha256",
        transition_trace.entry_admission_sha256,
        training_trace.entry_admission_sha256,
        inference_binding.entry_admission_sha256,
    )
    route = _require_equal(
        "route_decision_sha256",
        transition_trace.route_decision_sha256,
        training_trace.route_decision_sha256,
        inference_binding.route_decision_sha256,
    )
    grid = _require_equal(
        "grid_plan_sha256",
        transition_trace.grid_plan_sha256,
        training_trace.grid_plan_sha256,
        inference_binding.grid_plan_sha256,
    )
    cell_id = _require_equal(
        "cell_id",
        transition_trace.cell_id,
        training_trace.cell_id,
        inference_binding.cell_id,
    )
    role = _require_equal(
        "role",
        transition_trace.role,
        training_trace.role,
        inference_binding.role,
    )
    basis_id = _require_equal(
        "jspace_basis_id",
        transition_trace.jspace_basis_id,
        training_trace.jspace_basis_id,
    )
    basis_sha = _require_equal(
        "jspace_basis_sha256",
        transition_trace.jspace_basis_sha256,
        training_trace.jspace_basis_sha256,
    )
    control_condition = _require_equal(
        "vector_control_condition",
        transition_trace.falsifier_lesion_condition,
        training_trace.vector_control_condition,
    )

    training_sha = _sha256(training_trace.trace_sha256, "training_trace.trace_sha256")
    if inference_binding.training_trace_sha256 != training_sha:
        raise JSpaceCausalTrainingBindingError("CAUSAL_BINDING_MISMATCH:training_trace_sha256")
    if inference_binding.prototype_trace_sha256 != training_trace.prototype_trace_sha256:
        raise JSpaceCausalTrainingBindingError("CAUSAL_BINDING_MISMATCH:prototype_trace_sha256")

    packet_sha = _sha256(training_trace.vector_control_packet_sha256, "training_trace.vector_control_packet_sha256")
    if transition_trace.jspace_input_vector_ref != f"sha256:{packet_sha}":
        raise JSpaceCausalTrainingBindingError("CAUSAL_BINDING_MISMATCH:transition_vector_packet_ref")
    if inference_binding.vector_control_packet_sha256 != packet_sha:
        raise JSpaceCausalTrainingBindingError("CAUSAL_BINDING_MISMATCH:inference_vector_control_packet_sha256")

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "transition_trace_schema": TRANSITION_TRACE_SCHEMA,
        "transition_trace_sha256": _sha256(transition_trace.trace_sha256, "transition_trace.trace_sha256"),
        "training_trace_schema": TRAINING_TRACE_SCHEMA,
        "training_trace_sha256": training_sha,
        "trace_family_id": _text(training_trace.trace_family_id, "training_trace.trace_family_id", 256),
        "inference_binding_schema": INFERENCE_BINDING_SCHEMA,
        "inference_binding_sha256": _sha256(inference_binding.binding_sha256, "inference_binding.binding_sha256"),
        "inference_receipt_sha256": _sha256(inference_binding.inference_receipt_sha256, "inference_binding.inference_receipt_sha256"),
        "generation": _generation(generation),
        "entry_event_sha256": _sha256(entry_event, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(entry_admission, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(route, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid, "grid_plan_sha256"),
        "cell_id": _text(cell_id, "cell_id", 256),
        "role": _text(role, "role", 256),
        "jspace_basis_id": _text(basis_id, "jspace_basis_id", 256),
        "jspace_basis_sha256": _sha256(basis_sha, "jspace_basis_sha256"),
        "vector_control_packet_sha256": packet_sha,
        "vector_control_condition": _text(control_condition, "vector_control_condition", 64),
        "engine_identity_sha256": _sha256(inference_binding.engine_identity_sha256, "inference_binding.engine_identity_sha256"),
        "engine_load_consumption_receipt_sha256": _sha256(
            inference_binding.engine_load_consumption_receipt_sha256,
            "inference_binding.engine_load_consumption_receipt_sha256",
        ),
        "model_call_id": _text(inference_binding.model_call_id, "inference_binding.model_call_id"),
        "output_sha256": _sha256(inference_binding.output_sha256, "inference_binding.output_sha256"),
    }
    return JSpaceCausalTrainingBinding(
        **material,
        binding_sha256=_canonical_sha256(material, "JSPACE_CAUSAL_TRAINING_BINDING"),
    )


def validate_binding(binding: JSpaceCausalTrainingBinding) -> None:
    if not isinstance(binding, JSpaceCausalTrainingBinding):
        raise JSpaceCausalTrainingBindingError("JSPACE_CAUSAL_TRAINING_BINDING_REQUIRED")
    if binding.schema != SCHEMA or binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceCausalTrainingBindingError("JSPACE_CAUSAL_TRAINING_BINDING_SCHEMA_UNSUPPORTED")
    if binding.transition_trace_schema != TRANSITION_TRACE_SCHEMA:
        raise JSpaceCausalTrainingBindingError("TRANSITION_TRACE_SCHEMA_UNSUPPORTED")
    if binding.training_trace_schema != TRAINING_TRACE_SCHEMA:
        raise JSpaceCausalTrainingBindingError("TRAINING_TRACE_SCHEMA_UNSUPPORTED")
    if binding.inference_binding_schema != INFERENCE_BINDING_SCHEMA:
        raise JSpaceCausalTrainingBindingError("INFERENCE_BINDING_SCHEMA_UNSUPPORTED")
    material = asdict(binding)
    observed = _sha256(material.pop("binding_sha256", None), "binding.binding_sha256")
    expected = _canonical_sha256(material, "JSPACE_CAUSAL_TRAINING_BINDING")
    if observed != expected:
        raise JSpaceCausalTrainingBindingError("JSPACE_CAUSAL_TRAINING_BINDING_DIGEST_MISMATCH")


def binding_dict(binding: JSpaceCausalTrainingBinding) -> dict[str, Any]:
    validate_binding(binding)
    return asdict(binding)
