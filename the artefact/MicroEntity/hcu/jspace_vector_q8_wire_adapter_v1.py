#!/usr/bin/env python3
"""Explicit namespace adapter for the retained HCU donor q8 J-Space wire codec.

Canonical main already uses ``JSPACE_VECTOR_CONTROL_ABI/v1`` for the Trigger-1
model-specific intervention/derivation source descriptor.  The retained donor q8 codec
historically used the same identifier for materially different wire bytes.  This module
keeps those historical bytes reproducible while giving any future promoted q8 wire packet
a distinct, non-colliding ABI identity.

This is a migration/compatibility adapter only.  It is not a second canonicalizer, truth
store, effect path, model authority, or J-Space scientific promotion.  All hashing is
delegated to the donor codec's existing RFC8785/JCS implementation and all semantic q8,
generation, basis, role, and control-condition fences remain delegated to the legacy codec.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Sequence

try:
    from . import jspace_vector_control_v1 as legacy
except ImportError:
    import jspace_vector_control_v1 as legacy


SCHEMA = "ENTITYOS_HCU_JSPACE_VECTOR_Q8_WIRE_ADAPTER/v1"
Q8_WIRE_ABI_SCHEMA = "JSPACE_VECTOR_Q8_WIRE_ABI/v1"
LEGACY_COLLIDING_DONOR_ABI_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
MIGRATION_POLICY = "LEGACY_DONOR_BYTES_REPRODUCIBLE_NEW_PROMOTION_BYTES_USE_DISTINCT_Q8_WIRE_ABI"


class JSpaceQ8WireAdapterError(ValueError):
    pass


def _require_namespace_invariant() -> None:
    if legacy.ABI_SCHEMA != LEGACY_COLLIDING_DONOR_ABI_SCHEMA:
        raise JSpaceQ8WireAdapterError("LEGACY_DONOR_ABI_UNEXPECTED")
    if Q8_WIRE_ABI_SCHEMA == CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA:
        raise JSpaceQ8WireAdapterError("Q8_WIRE_ABI_COLLIDES_WITH_CANONICAL_TRIGGER1_DESCRIPTOR")


def _rehash(packet: legacy.VectorControlPacket) -> legacy.VectorControlPacket:
    unsigned = replace(packet, packet_sha256="0" * 64)
    digest = legacy._canonical_sha256(legacy._packet_material(unsigned), "VECTOR_CONTROL_PACKET")
    return replace(unsigned, packet_sha256=digest)


def _legacy_form(packet: legacy.VectorControlPacket) -> legacy.VectorControlPacket:
    """Map one admitted q8-wire packet back to the exact legacy semantic packet."""
    _require_namespace_invariant()
    if not isinstance(packet, legacy.VectorControlPacket):
        raise JSpaceQ8WireAdapterError("VECTOR_CONTROL_PACKET_REQUIRED")
    if packet.abi_schema != Q8_WIRE_ABI_SCHEMA:
        raise JSpaceQ8WireAdapterError("Q8_WIRE_ABI_SCHEMA_REQUIRED")

    # Verify the new wire digest before changing any bytes.  The existing donor JCS
    # canonicalizer is the sole hash/serialization authority used by this adapter.
    observed = legacy._sha256(packet.packet_sha256, "packet_sha256")
    expected = legacy._canonical_sha256(legacy._packet_material(packet), "VECTOR_CONTROL_PACKET")
    if observed != expected:
        raise JSpaceQ8WireAdapterError("Q8_WIRE_PACKET_DIGEST_MISMATCH")

    migrated = replace(packet, abi_schema=LEGACY_COLLIDING_DONOR_ABI_SCHEMA)
    migrated = _rehash(migrated)
    legacy.validate_packet(migrated)
    return migrated


def migrate_legacy_packet(packet: legacy.VectorControlPacket) -> legacy.VectorControlPacket:
    """Re-namespace one valid historical donor q8 packet without changing q8 semantics."""
    _require_namespace_invariant()
    legacy.validate_packet(packet)
    if packet.abi_schema != LEGACY_COLLIDING_DONOR_ABI_SCHEMA:
        raise JSpaceQ8WireAdapterError("LEGACY_DONOR_ABI_SCHEMA_REQUIRED")
    migrated = replace(packet, abi_schema=Q8_WIRE_ABI_SCHEMA)
    migrated = _rehash(migrated)
    validate_q8_wire_packet(migrated)
    return migrated


def validate_q8_wire_packet(packet: legacy.VectorControlPacket) -> None:
    _legacy_form(packet)


def encode_q8_wire(
    values: Sequence[Any],
    *,
    basis_id: str,
    basis_sha256: str,
    generation: int,
    role: str,
    control_condition: str = "BASELINE",
) -> legacy.VectorControlPacket:
    historical = legacy.encode_vector(
        values,
        basis_id=basis_id,
        basis_sha256=basis_sha256,
        generation=generation,
        role=role,
        control_condition=control_condition,
    )
    return migrate_legacy_packet(historical)


def decode_q8_wire(
    packet: legacy.VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    expected_control_condition: str | None = None,
) -> tuple[float, ...]:
    historical = _legacy_form(packet)
    return legacy.decode_vector(
        historical,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
        expected_control_condition=expected_control_condition,
    )


__all__ = [
    "SCHEMA",
    "Q8_WIRE_ABI_SCHEMA",
    "LEGACY_COLLIDING_DONOR_ABI_SCHEMA",
    "CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA",
    "MIGRATION_POLICY",
    "JSpaceQ8WireAdapterError",
    "migrate_legacy_packet",
    "validate_q8_wire_packet",
    "encode_q8_wire",
    "decode_q8_wire",
]
