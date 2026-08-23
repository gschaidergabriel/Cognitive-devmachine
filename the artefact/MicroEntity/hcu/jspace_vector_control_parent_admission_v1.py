#!/usr/bin/env python3
"""Compatibility adapter for the canonical DatasetAdmission Vector-Control parent gate.

The canonical exact-packet preimage/generation/basis/role/control-condition semantics live in
``jspace_dataset_admission_gate_v1``. This module intentionally does not maintain a second
copy of those checks. It preserves the established parent-admission API/error surface for
callers such as the compositional serious-training parent closure while delegating validation
to the single DatasetAdmission implementation.

This adapter mints no truth, model/runtime credit, reward, capability or effect authority.
"""
from __future__ import annotations

from typing import Any, Mapping

try:
    from .jspace_dataset_admission_gate_v1 import (
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        _verify_vector_control_packet_binding,
    )
    from .jspace_vector_control_v1 import VectorControlPacket
except ImportError:
    from jspace_dataset_admission_gate_v1 import (
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        _verify_vector_control_packet_binding,
    )
    from jspace_vector_control_v1 import VectorControlPacket

GUARD_SCHEMA = "ENTITYOS_HCU_JSPACE_VECTOR_CONTROL_PARENT_ADMISSION/v1"


class JSpaceVectorControlParentAdmissionError(ValueError):
    pass


_ERROR_COMPATIBILITY = {
    "VECTOR_CONTROL_PACKET_NOT_ADMITTED": "VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED",
    "VECTOR_CONTROL_PACKET_PREIMAGE_TYPE_INVALID": "VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED",
    "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH": "VECTOR_CONTROL_PACKET_PARENT_IDENTITY_MISMATCH",
    "VECTOR_CONTROL_PACKET_GENERATION_MISMATCH": "VECTOR_CONTROL_PACKET_GENERATION_MISMATCH",
    "VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH": "VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH",
    "VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH": "VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH",
    "VECTOR_CONTROL_PACKET_ROLE_MISMATCH": "VECTOR_CONTROL_PACKET_ROLE_MISMATCH",
    "VECTOR_CONTROL_PACKET_CONDITION_MISMATCH": "VECTOR_CONTROL_PACKET_CONDITION_MISMATCH",
}


def _compatibility_error(exc: JSpaceDatasetAdmissionError) -> str:
    message = str(exc)
    if message.startswith("VECTOR_CONTROL_PACKET_REJECTED:"):
        return "VECTOR_CONTROL_PACKET_PARENT_REJECTED:" + message.split(":", 1)[1]
    return _ERROR_COMPATIBILITY.get(message, f"DATASET_ADMISSION_VECTOR_PARENT_REJECTED:{message}")


def require_admitted_vector_control_packet_parent(
    admission: DatasetAdmission,
    admitted_vector_control_packets: Mapping[str, VectorControlPacket],
) -> VectorControlPacket:
    """Delegate exact Vector-Control parent admission to the canonical DatasetAdmission gate."""
    if not isinstance(admission, DatasetAdmission):
        raise JSpaceVectorControlParentAdmissionError("DATASET_ADMISSION_REQUIRED")

    try:
        _verify_vector_control_packet_binding(
            admitted_vector_control_packets,
            packet_sha256=admission.vector_control_packet_sha256,
            generation=admission.generation,
            basis_id=admission.jspace_basis_id,
            basis_sha256=admission.jspace_basis_sha256,
            role=admission.role,
            control_condition=admission.vector_control_condition,
        )
    except JSpaceDatasetAdmissionError as exc:
        raise JSpaceVectorControlParentAdmissionError(_compatibility_error(exc)) from exc

    packet = admitted_vector_control_packets.get(admission.vector_control_packet_sha256)
    if not isinstance(packet, VectorControlPacket):
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED")
    return packet


__all__ = [
    "GUARD_SCHEMA",
    "JSpaceVectorControlParentAdmissionError",
    "require_admitted_vector_control_packet_parent",
]
