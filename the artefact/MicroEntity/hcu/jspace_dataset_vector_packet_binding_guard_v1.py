#!/usr/bin/env python3
"""Fail-closed helper for DatasetAdmission -> J-Space Vector Control packet evidence.

This module is deliberately *not* a second dataset/state/truth authority. It verifies that
a packet identity already cross-bound by the canonical DatasetAdmission path is backed by
caller-owned admitted packet evidence and by the single canonical JSPACE_VECTOR_CONTROL_ABI/v1
validator. It mints no fact, effect, runtime, model, training, or provider-execution credit.
"""
from __future__ import annotations

from typing import Any, Mapping

try:
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )
except ImportError:
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )


class JSpaceDatasetVectorPacketBindingError(ValueError):
    pass


def _text(value: Any, field: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceDatasetVectorPacketBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceDatasetVectorPacketBindingError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceDatasetVectorPacketBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceDatasetVectorPacketBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9_007_199_254_740_991:
        raise JSpaceDatasetVectorPacketBindingError("generation:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _coerce_packet(value: Any) -> VectorControlPacket:
    if isinstance(value, VectorControlPacket):
        return value
    if not isinstance(value, Mapping):
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_REGISTRY_VALUE_INVALID")
    material = dict(value)
    if isinstance(material.get("q8_values"), list):
        material["q8_values"] = tuple(material["q8_values"])
    try:
        return VectorControlPacket(**material)
    except (TypeError, ValueError) as exc:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_REGISTRY_VALUE_INVALID") from exc


def verify_admitted_vector_packet_binding(
    admitted_vector_control_packets: Mapping[str, Any],
    *,
    expected_packet_sha256: str,
    expected_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    expected_control_condition: str,
) -> VectorControlPacket:
    """Verify one externally admitted packet against the exact dataset causal family.

    The registry is caller-owned evidence. Presence in the registry is necessary but not
    sufficient: the canonical vector-control validator must accept the exact packet bytes,
    and packet identity/generation/basis/role/control condition must all match the dataset
    family. Agreement among trace labels alone is never admission evidence.
    """
    if not isinstance(admitted_vector_control_packets, Mapping):
        raise JSpaceDatasetVectorPacketBindingError("ADMITTED_VECTOR_CONTROL_PACKETS:MAPPING_REQUIRED")

    expected_packet_sha256 = _sha256(expected_packet_sha256, "expected_packet_sha256")
    expected_generation = _generation(expected_generation)
    expected_basis_id = _text(expected_basis_id, "expected_basis_id")
    expected_basis_sha256 = _sha256(expected_basis_sha256, "expected_basis_sha256")
    expected_role = _text(expected_role, "expected_role")
    expected_control_condition = _text(expected_control_condition, "expected_control_condition", max_len=64)

    admitted = admitted_vector_control_packets.get(expected_packet_sha256)
    if admitted is None:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_NOT_ADMITTED")
    packet = _coerce_packet(admitted)

    try:
        validate_packet(packet)
    except JSpaceVectorControlError as exc:
        raise JSpaceDatasetVectorPacketBindingError(f"VECTOR_CONTROL_PACKET_INVALID:{exc}") from exc

    if packet.abi_schema != ABI_SCHEMA:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_ABI_MISMATCH")
    if packet.packet_sha256 != expected_packet_sha256:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH")
    if packet.generation != expected_generation:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_GENERATION_MISMATCH")
    if packet.basis_id != expected_basis_id:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != expected_basis_sha256:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH")
    if packet.role != expected_role:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_ROLE_MISMATCH")
    if packet.control_condition != expected_control_condition:
        raise JSpaceDatasetVectorPacketBindingError("VECTOR_CONTROL_PACKET_CONDITION_MISMATCH")
    return packet
