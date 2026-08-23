#!/usr/bin/env python3
"""Single compositional parent-evidence closure for serious EntityOS/HCU J-Space training.

DatasetAdmission, JSpaceInferenceBinding, the admitted HCU_INFERENCE_RECEIPT/v4 parent, and
the admitted JSPACE_VECTOR_CONTROL_ABI/v1 packet are individually useful evidence surfaces.
Serious training readiness additionally needs them to describe one exact causal row rather
than several independently valid but cross-spliced parents.

This module deliberately delegates parent verification to the existing reusable inference-
receipt and Vector-Control parent guards, then cross-binds the child DatasetAdmission and
JSpaceInferenceBinding identities that both parents feed. It does not implement a second
receipt validator, packet validator, truth store, reward authority, runtime authority, or
effect path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:
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
except ImportError:
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

CLOSURE_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_PARENT_CLOSURE/v1"


class JSpaceTrainingParentClosureError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceTrainingParentClosure:
    schema: str
    training_trace_sha256: str
    prototype_trace_sha256: str
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


def _same(left: Any, right: Any, field: str) -> Any:
    if left != right:
        raise JSpaceTrainingParentClosureError(f"PARENT_CLOSURE_BINDING_MISMATCH:{field}")
    return left


def require_admitted_training_parent_closure(
    admission: DatasetAdmission,
    binding: JSpaceInferenceBinding,
    *,
    admitted_inference_receipts: Mapping[str, Any],
    admitted_vector_control_packets: Mapping[str, VectorControlPacket],
) -> JSpaceTrainingParentClosure:
    """Require both admitted parents and prove their child envelopes describe one causal row."""
    if not isinstance(admission, DatasetAdmission):
        raise JSpaceTrainingParentClosureError("DATASET_ADMISSION_REQUIRED")
    if not isinstance(binding, JSpaceInferenceBinding):
        raise JSpaceTrainingParentClosureError("JSPACE_INFERENCE_BINDING_REQUIRED")

    try:
        require_admitted_inference_receipt_parent(binding, admitted_inference_receipts)
    except JSpaceInferenceParentAdmissionError as exc:
        raise JSpaceTrainingParentClosureError(
            f"INFERENCE_PARENT_ADMISSION_REJECTED:{exc}"
        ) from exc

    try:
        require_admitted_vector_control_packet_parent(
            admission,
            admitted_vector_control_packets,
        )
    except JSpaceVectorControlParentAdmissionError as exc:
        raise JSpaceTrainingParentClosureError(
            f"VECTOR_CONTROL_PARENT_ADMISSION_REJECTED:{exc}"
        ) from exc

    training_trace_sha256 = _same(
        admission.training_trace_sha256,
        binding.training_trace_sha256,
        "training_trace_sha256",
    )
    prototype_trace_sha256 = _same(
        admission.prototype_trace_sha256,
        binding.prototype_trace_sha256,
        "prototype_trace_sha256",
    )
    generation = _same(admission.generation, binding.generation, "generation")
    entry_event_sha256 = _same(
        admission.entry_event_sha256,
        binding.entry_event_sha256,
        "entry_event_sha256",
    )
    entry_admission_sha256 = _same(
        admission.entry_admission_sha256,
        binding.entry_admission_sha256,
        "entry_admission_sha256",
    )
    route_decision_sha256 = _same(
        admission.route_decision_sha256,
        binding.route_decision_sha256,
        "route_decision_sha256",
    )
    grid_plan_sha256 = _same(
        admission.grid_plan_sha256,
        binding.grid_plan_sha256,
        "grid_plan_sha256",
    )
    cell_id = _same(admission.cell_id, binding.cell_id, "cell_id")
    role = _same(admission.role, binding.role, "role")
    vector_control_packet_sha256 = _same(
        admission.vector_control_packet_sha256,
        binding.vector_control_packet_sha256,
        "vector_control_packet_sha256",
    )

    return JSpaceTrainingParentClosure(
        schema=CLOSURE_SCHEMA,
        training_trace_sha256=training_trace_sha256,
        prototype_trace_sha256=prototype_trace_sha256,
        inference_receipt_sha256=binding.inference_receipt_sha256,
        vector_control_packet_sha256=vector_control_packet_sha256,
        generation=generation,
        entry_event_sha256=entry_event_sha256,
        entry_admission_sha256=entry_admission_sha256,
        route_decision_sha256=route_decision_sha256,
        grid_plan_sha256=grid_plan_sha256,
        cell_id=cell_id,
        role=role,
        jspace_basis_id=admission.jspace_basis_id,
        jspace_basis_sha256=admission.jspace_basis_sha256,
        vector_control_condition=admission.vector_control_condition,
    )


__all__ = [
    "CLOSURE_SCHEMA",
    "JSpaceTrainingParentClosure",
    "JSpaceTrainingParentClosureError",
    "require_admitted_training_parent_closure",
]
