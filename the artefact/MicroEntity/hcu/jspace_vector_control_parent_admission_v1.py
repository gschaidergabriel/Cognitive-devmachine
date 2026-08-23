#!/usr/bin/env python3
"""Fail-closed parent-evidence guard for J-Space Vector Control packets.

``DatasetAdmission`` cross-binds the packet digest claimed by transition/prototype/training
layers. Equal digest strings alone do not prove that an actual canonical
``JSPACE_VECTOR_CONTROL_ABI/v1`` packet exists behind that identity. This guard requires the
exact packet from an external admitted registry, revalidates its RFC8785/JCS-bound identity,
and cross-binds generation, basis, role and control condition before serious training-data
orchestration may trust that parent.

This module mints no truth, model/runtime credit, reward, capability or effect authority.
"""
from __future__ import annotations

from typing import Any, Mapping

try:
    from .jspace_dataset_admission_gate_v1 import DatasetAdmission
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )
except ImportError:
    from jspace_dataset_admission_gate_v1 import DatasetAdmission
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )

GUARD_SCHEMA = "ENTITYOS_HCU_JSPACE_VECTOR_CONTROL_PARENT_ADMISSION/v1"


class JSpaceVectorControlParentAdmissionError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceVectorControlParentAdmissionError(f"{field}:MAPPING_REQUIRED")
    return value


def require_admitted_vector_control_packet_parent(
    admission: DatasetAdmission,
    admitted_vector_control_packets: Mapping[str, VectorControlPacket],
) -> VectorControlPacket:
    """Require and cross-bind the exact canonical Vector Control parent packet."""
    if not isinstance(admission, DatasetAdmission):
        raise JSpaceVectorControlParentAdmissionError("DATASET_ADMISSION_REQUIRED")

    registry = _mapping(admitted_vector_control_packets, "admitted_vector_control_packets")
    packet_sha = admission.vector_control_packet_sha256
    packet = registry.get(packet_sha)
    if not isinstance(packet, VectorControlPacket):
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_PARENT_NOT_ADMITTED")

    try:
        validate_packet(packet)
    except JSpaceVectorControlError as exc:
        raise JSpaceVectorControlParentAdmissionError(
            f"VECTOR_CONTROL_PACKET_PARENT_REJECTED:{exc}"
        ) from exc

    if packet.abi_schema != ABI_SCHEMA:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_ABI_MISMATCH")
    if packet.packet_sha256 != packet_sha:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_PARENT_IDENTITY_MISMATCH")
    if packet.generation != admission.generation:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_GENERATION_MISMATCH")
    if packet.basis_id != admission.jspace_basis_id:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != admission.jspace_basis_sha256:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH")
    if packet.role != admission.role:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_ROLE_MISMATCH")
    if packet.control_condition != admission.vector_control_condition:
        raise JSpaceVectorControlParentAdmissionError("VECTOR_CONTROL_PACKET_CONDITION_MISMATCH")
    return packet


__all__ = [
    "GUARD_SCHEMA",
    "JSpaceVectorControlParentAdmissionError",
    "require_admitted_vector_control_packet_parent",
]
