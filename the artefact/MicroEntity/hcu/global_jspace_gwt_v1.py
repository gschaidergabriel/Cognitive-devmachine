from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        VectorControlPacket,
        decode_vector,
        encode_vector,
        packet_bytes,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        VectorControlPacket,
        decode_vector,
        encode_vector,
        packet_bytes,
    )

TRACE_SCHEMA = "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v3"
TRACE_CANONICALIZATION_SCHEMA = CANONICALIZATION_SCHEMA
MAX_DIM = 4096
MAX_JCS_SAFE_INTEGER = 9_007_199_254_740_991
HYPERPOSITION_MARGIN_Q = 750  # 0.075 on 0..10000 gate scale


class JSpaceError(ValueError):
    pass


def _unit(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JSpaceError(f"{field}:NUMBER_REQUIRED")
    value = float(value)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise JSpaceError(f"{field}:UNIT_INTERVAL_REQUIRED")
    return value


def _text(value: str, field: str, max_bytes: int = 255) -> str:
    if not isinstance(value, str) or not value:
        raise JSpaceError(f"{field}:NONEMPTY_STRING_REQUIRED")
    raw = value.encode("utf-8", "strict")
    if len(raw) > max_bytes:
        raise JSpaceError(f"{field}:TOO_LONG")
    return value


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise JSpaceError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceError("GENERATION_NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_JCS_SAFE_INTEGER:
        raise JSpaceError("GENERATION_JCS_SAFE_INTEGER_REQUIRED")
    return value


def _q_unit(value: float) -> int:
    return int(math.floor(_unit(value, "unit") * 10000.0 + 0.5))


def _q_signed(value: float) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JSpaceError("VECTOR_NUMBER_REQUIRED")
    value = float(value)
    if not math.isfinite(value):
        raise JSpaceError("VECTOR_FINITE_REQUIRED")
    clipped = max(-1.0, min(1.0, value))
    scaled = clipped * 127.0
    if scaled >= 0:
        q = math.floor(scaled + 0.5)
    else:
        q = math.ceil(scaled - 0.5)
    return int(max(-127, min(127, q)))


@dataclass(frozen=True)
class CellContribution:
    cell_id: str
    role: str
    vector: tuple[float, ...]
    novelty: float
    contradiction: float
    uncertainty: float
    goal_pressure: float
    effect_pressure: float
    evidence_quality: float = 1.0

    def validated(self, dim: int) -> "CellContribution":
        _text(self.cell_id, "cell_id")
        _text(self.role, "role")
        if len(self.vector) != dim:
            raise JSpaceError("VECTOR_DIMENSION_MISMATCH")
        if dim < 1 or dim > MAX_DIM:
            raise JSpaceError("VECTOR_DIMENSION_UNSUPPORTED")
        for value in self.vector:
            _q_signed(value)
        for field in (
            "novelty",
            "contradiction",
            "uncertainty",
            "goal_pressure",
            "effect_pressure",
            "evidence_quality",
        ):
            _unit(getattr(self, field), field)
        return self

    def gate_q(self) -> int:
        # Activation/broadcast scheduler signal only; never truth/confidence authority.
        weighted = (
            0.24 * self.novelty
            + 0.24 * self.contradiction
            + 0.18 * self.uncertainty
            + 0.12 * self.goal_pressure
            + 0.12 * self.effect_pressure
            + 0.10 * self.evidence_quality
        )
        return int(math.floor(max(0.0, min(1.0, weighted)) * 10000.0 + 0.5))


@dataclass(frozen=True)
class JSpaceStep:
    generation: int
    basis_id: str
    basis_sha256: str
    winner_cell_id: str
    winner_role: str
    global_vector: tuple[float, ...]
    winner_gate_q: int
    hyperposition_cells: tuple[str, ...]
    control_condition: str
    control_packet: VectorControlPacket
    control_packet_text: str
    control_packet_sha256: str
    trace_sha256: str
    trace: dict

    def __post_init__(self) -> None:
        """Fail closed if top-level fields split from the digest-bound observable trace.

        `JSpaceStep` is frozen, but its trace payload is a dict. Downstream training code must
        never be able to relabel a valid trace by constructing/replacing top-level fields while
        retaining the old trace digest. The producer remains the sole J-Space authority; this
        constructor only binds its two representations to the same evidence identity.
        """
        _generation(self.generation)
        _text(self.basis_id, "basis_id")
        _sha256(self.basis_sha256, "basis_sha256")
        _text(self.winner_cell_id, "winner_cell_id")
        _text(self.winner_role, "winner_role")
        _text(self.control_condition, "control_condition")
        observed_trace_sha = _sha256(self.trace_sha256, "trace_sha256")
        if not isinstance(self.trace, dict):
            raise JSpaceError("TRACE_MAPPING_REQUIRED")
        if self.trace.get("schema") != TRACE_SCHEMA:
            raise JSpaceError("TRACE_SCHEMA_MISMATCH")
        if self.trace.get("canonicalization_schema") != TRACE_CANONICALIZATION_SCHEMA:
            raise JSpaceError("TRACE_CANONICALIZATION_SCHEMA_MISMATCH")

        expected_trace_fields = {
            "generation": self.generation,
            "basis_id": self.basis_id,
            "basis_sha256": self.basis_sha256,
            "dimension": len(self.global_vector),
            "winner_cell_id": self.winner_cell_id,
            "winner_role": self.winner_role,
            "winner_gate_q": self.winner_gate_q,
            "hyperposition_cells": list(self.hyperposition_cells),
            "broadcast_contributor_cells": list(self.hyperposition_cells),
            "global_vector_q127": [_q_signed(v) for v in self.global_vector],
            "control_condition": self.control_condition,
            "control_packet_schema": ABI_SCHEMA,
        }
        for field, expected in expected_trace_fields.items():
            if self.trace.get(field) != expected:
                raise JSpaceError(f"TRACE_STEP_BINDING_MISMATCH:{field}")
        if self.winner_cell_id not in self.hyperposition_cells:
            raise JSpaceError("TRACE_WINNER_NOT_IN_BROADCAST_COALITION")

        if not isinstance(self.control_packet, VectorControlPacket):
            raise JSpaceError("CONTROL_PACKET_REQUIRED")
        decode_vector(
            self.control_packet,
            current_generation=self.generation,
            expected_basis_id=self.basis_id,
            expected_basis_sha256=self.basis_sha256,
            expected_role=self.winner_role,
            expected_control_condition=self.control_condition,
        )
        packet_wire = packet_bytes(self.control_packet)
        packet_text = packet_wire.decode("utf-8", "strict")
        packet_wire_sha = hashlib.sha256(packet_wire).hexdigest()
        if self.control_packet_text != packet_text:
            raise JSpaceError("CONTROL_PACKET_TEXT_MISMATCH")
        if self.control_packet_sha256 != packet_wire_sha:
            raise JSpaceError("CONTROL_PACKET_WIRE_SHA256_MISMATCH")
        if self.trace.get("control_packet_text") != packet_text:
            raise JSpaceError("TRACE_STEP_BINDING_MISMATCH:control_packet_text")
        if self.trace.get("control_packet_identity_sha256") != self.control_packet.packet_sha256:
            raise JSpaceError("TRACE_STEP_BINDING_MISMATCH:control_packet_identity_sha256")
        for field in ("control_packet_sha256", "control_packet_wire_sha256"):
            if self.trace.get(field) != packet_wire_sha:
                raise JSpaceError(f"TRACE_STEP_BINDING_MISMATCH:{field}")

        if hashlib.sha256(_trace_bytes(self.trace)).hexdigest() != observed_trace_sha:
            raise JSpaceError("TRACE_DIGEST_MISMATCH")


def _trace_bytes(value: dict) -> bytes:
    # Prototype evidence identity only, never canonical durable-state authority.
    # Reuse the one selected HCU JCS canonicalizer; no local serializer authority.
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceError(f"TRACE_CANONICALIZATION_FAILED:{exc}") from exc


def _global_vector(validated: Sequence[CellContribution], dim: int) -> tuple[float, ...]:
    # Sort before summation so caller input ordering cannot alter packet identity through
    # floating addition order. This is source determinism, not a truth/confidence rule.
    ordered = sorted(validated, key=lambda c: c.cell_id)
    weights = [1 + c.gate_q() for c in ordered]
    total_weight = sum(weights)
    return tuple(
        sum(w * c.vector[i] for w, c in zip(weights, ordered)) / total_weight
        for i in range(dim)
    )


def step(
    contributions: Sequence[CellContribution],
    *,
    generation: int,
    basis_id: str,
    basis_sha256: str,
    control_condition: str = "BASELINE",
) -> JSpaceStep:
    generation = _generation(generation)
    basis_id = _text(basis_id, "basis_id")
    basis_sha256 = _sha256(basis_sha256, "basis_sha256")
    if not contributions:
        raise JSpaceError("CONTRIBUTION_REQUIRED")
    dim = len(contributions[0].vector)
    validated = [c.validated(dim) for c in contributions]
    ids = [c.cell_id for c in validated]
    if len(ids) != len(set(ids)):
        raise JSpaceError("CELL_ID_DUPLICATE")

    ranked = sorted(validated, key=lambda c: (-c.gate_q(), c.cell_id))
    winner = ranked[0]
    winner_gate_q = winner.gate_q()
    coalition = tuple(c for c in ranked if winner_gate_q - c.gate_q() <= HYPERPOSITION_MARGIN_Q)
    hyper = tuple(c.cell_id for c in coalition)
    # Broadcast only the selected GWT/Hyperposition coalition. Cells outside the admitted
    # selection margin remain observable in the trace but cannot silently reverse a packet
    # labelled with the winner's role.
    global_vector = _global_vector(coalition, dim)

    # One role-relevant Global J-Space return packet using the sole selected Vector Control ABI.
    packet = encode_vector(
        global_vector,
        basis_id=basis_id,
        basis_sha256=basis_sha256,
        generation=generation,
        role=winner.role,
        control_condition=control_condition,
    )
    # Re-validate the packet through the same ABI consumer boundary before trace production.
    decode_vector(
        packet,
        current_generation=generation,
        expected_basis_id=basis_id,
        expected_basis_sha256=basis_sha256,
        expected_role=winner.role,
        expected_control_condition=control_condition,
    )
    packet_wire = packet_bytes(packet)
    packet_text = packet_wire.decode("utf-8", "strict")
    packet_sha256 = hashlib.sha256(packet_wire).hexdigest()

    trace = {
        "schema": TRACE_SCHEMA,
        "canonicalization_schema": TRACE_CANONICALIZATION_SCHEMA,
        "generation": generation,
        "basis_id": basis_id,
        "basis_sha256": basis_sha256,
        "dimension": dim,
        "winner_cell_id": winner.cell_id,
        "winner_role": winner.role,
        "winner_gate_q": winner_gate_q,
        "hyperposition_cells": list(hyper),
        "broadcast_contributor_cells": list(hyper),
        "global_vector_q127": [_q_signed(v) for v in global_vector],
        "control_condition": packet.control_condition,
        "control_packet_schema": ABI_SCHEMA,
        "control_packet_text": packet_text,
        "control_packet_identity_sha256": packet.packet_sha256,
        "control_packet_sha256": packet_sha256,
        "control_packet_wire_sha256": packet_sha256,
        "contributions": [
            {
                "cell_id": c.cell_id,
                "role": c.role,
                "gate_q": c.gate_q(),
                "vector_q127": [_q_signed(v) for v in c.vector],
                "novelty_q": _q_unit(c.novelty),
                "contradiction_q": _q_unit(c.contradiction),
                "uncertainty_q": _q_unit(c.uncertainty),
                "goal_pressure_q": _q_unit(c.goal_pressure),
                "effect_pressure_q": _q_unit(c.effect_pressure),
                "evidence_quality_q": _q_unit(c.evidence_quality),
            }
            for c in sorted(validated, key=lambda x: x.cell_id)
        ],
        "authority": "CANDIDATE_MEASUREMENT_ONLY_NOT_TRUTH_OR_EFFECT",
    }
    trace_sha = hashlib.sha256(_trace_bytes(trace)).hexdigest()
    return JSpaceStep(
        generation=generation,
        basis_id=basis_id,
        basis_sha256=basis_sha256,
        winner_cell_id=winner.cell_id,
        winner_role=winner.role,
        global_vector=global_vector,
        winner_gate_q=winner_gate_q,
        hyperposition_cells=hyper,
        control_condition=packet.control_condition,
        control_packet=packet,
        control_packet_text=packet_text,
        control_packet_sha256=packet_sha256,
        trace_sha256=trace_sha,
        trace=trace,
    )


def lesion(
    contributions: Sequence[CellContribution],
    *,
    lesion_cell_id: str,
    generation: int,
    basis_id: str,
    basis_sha256: str,
) -> JSpaceStep:
    remaining = [c for c in contributions if c.cell_id != lesion_cell_id]
    if len(remaining) == len(contributions):
        raise JSpaceError("LESION_CELL_UNKNOWN")
    if not remaining:
        raise JSpaceError("LESION_REMOVED_ALL_CELLS")
    return step(
        remaining,
        generation=generation,
        basis_id=basis_id,
        basis_sha256=basis_sha256,
        control_condition="LESION",
    )
