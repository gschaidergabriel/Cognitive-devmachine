from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import json
import math
import struct
from typing import Sequence

ABI_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
TRACE_SCHEMA = "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v1"
MAGIC = b"JCTL1\x00"
MAX_DIM = 4096
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


def _decode_q_signed(value: int) -> float:
    return float(value) / 127.0


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
class VectorControlPacket:
    basis_id: str
    role: str
    generation: int
    vector: tuple[float, ...]
    gate_q: int

    def encode_bytes(self) -> bytes:
        basis = _text(self.basis_id, "basis_id").encode("utf-8")
        role = _text(self.role, "role").encode("utf-8")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise JSpaceError("GENERATION_NONNEGATIVE_INTEGER_REQUIRED")
        if self.generation > (2**64 - 1):
            raise JSpaceError("GENERATION_TOO_LARGE")
        if not self.vector or len(self.vector) > MAX_DIM:
            raise JSpaceError("VECTOR_DIMENSION_UNSUPPORTED")
        if isinstance(self.gate_q, bool) or not isinstance(self.gate_q, int) or not 0 <= self.gate_q <= 10000:
            raise JSpaceError("GATE_Q_RANGE")
        qvec = bytes(((_q_signed(v) + 256) % 256 for v in self.vector))
        return (
            MAGIC
            + bytes([len(basis)])
            + basis
            + bytes([len(role)])
            + role
            + struct.pack(">QHH", self.generation, len(self.vector), self.gate_q)
            + qvec
        )

    def encode_text(self) -> str:
        encoded = base64.urlsafe_b64encode(self.encode_bytes()).decode("ascii").rstrip("=")
        return "jctl1:" + encoded

    @classmethod
    def decode_text(
        cls,
        text: str,
        *,
        expected_basis_id: str | None = None,
        expected_role: str | None = None,
        expected_generation: int | None = None,
    ) -> "VectorControlPacket":
        if not isinstance(text, str) or not text.startswith("jctl1:"):
            raise JSpaceError("JCTL_TEXT_PREFIX")
        payload = text[6:]
        padding = "=" * ((4 - len(payload) % 4) % 4)
        try:
            raw = base64.urlsafe_b64decode(payload + padding)
        except Exception as exc:
            raise JSpaceError("JCTL_BASE64_INVALID") from exc
        if not raw.startswith(MAGIC):
            raise JSpaceError("JCTL_MAGIC")
        offset = len(MAGIC)
        if offset >= len(raw):
            raise JSpaceError("JCTL_TRUNCATED")
        basis_len = raw[offset]
        offset += 1
        basis = raw[offset:offset + basis_len].decode("utf-8", "strict")
        offset += basis_len
        if offset >= len(raw):
            raise JSpaceError("JCTL_TRUNCATED")
        role_len = raw[offset]
        offset += 1
        role = raw[offset:offset + role_len].decode("utf-8", "strict")
        offset += role_len
        if len(raw) < offset + 12:
            raise JSpaceError("JCTL_TRUNCATED")
        generation, dim, gate_q = struct.unpack(">QHH", raw[offset:offset + 12])
        offset += 12
        if dim < 1 or dim > MAX_DIM or len(raw) != offset + dim:
            raise JSpaceError("JCTL_DIM_OR_LENGTH")
        qvec = tuple(struct.unpack("b", bytes([b]))[0] for b in raw[offset:])
        vector = tuple(_decode_q_signed(v) for v in qvec)
        packet = cls(basis, role, generation, vector, gate_q)
        if expected_basis_id is not None and basis != expected_basis_id:
            raise JSpaceError("JCTL_BASIS_MISMATCH")
        if expected_role is not None and role != expected_role:
            raise JSpaceError("JCTL_ROLE_MISMATCH")
        if expected_generation is not None and generation != expected_generation:
            raise JSpaceError("JCTL_GENERATION_MISMATCH")
        return packet


@dataclass(frozen=True)
class JSpaceStep:
    generation: int
    basis_id: str
    winner_cell_id: str
    winner_role: str
    global_vector: tuple[float, ...]
    winner_gate_q: int
    hyperposition_cells: tuple[str, ...]
    control_packet_text: str
    trace_sha256: str
    trace: dict


def _trace_bytes(value: dict) -> bytes:
    # Prototype evidence identity only, not canonical durable-state authority.
    # All model-relevant floats are quantized to bounded integers in the trace.
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def step(
    contributions: Sequence[CellContribution],
    *,
    generation: int,
    basis_id: str,
) -> JSpaceStep:
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise JSpaceError("GENERATION_NONNEGATIVE_INTEGER_REQUIRED")
    _text(basis_id, "basis_id")
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
    hyper = tuple(c.cell_id for c in ranked if winner_gate_q - c.gate_q() <= HYPERPOSITION_MARGIN_Q)

    weights = [1 + c.gate_q() for c in validated]
    total_weight = sum(weights)
    global_vector = tuple(
        sum(w * c.vector[i] for w, c in zip(weights, validated)) / total_weight
        for i in range(dim)
    )

    # Role-relevant Global J-Space return packet to the GWT winner.
    packet = VectorControlPacket(
        basis_id=basis_id,
        role=winner.role,
        generation=generation,
        vector=global_vector,
        gate_q=winner_gate_q,
    )
    packet_text = packet.encode_text()

    trace = {
        "schema": TRACE_SCHEMA,
        "generation": generation,
        "basis_id": basis_id,
        "dimension": dim,
        "winner_cell_id": winner.cell_id,
        "winner_role": winner.role,
        "winner_gate_q": winner_gate_q,
        "hyperposition_cells": list(hyper),
        "global_vector_q127": [_q_signed(v) for v in global_vector],
        "control_packet_schema": ABI_SCHEMA,
        "control_packet_text": packet_text,
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
        winner_cell_id=winner.cell_id,
        winner_role=winner.role,
        global_vector=global_vector,
        winner_gate_q=winner_gate_q,
        hyperposition_cells=hyper,
        control_packet_text=packet_text,
        trace_sha256=trace_sha,
        trace=trace,
    )


def lesion(
    contributions: Sequence[CellContribution],
    *,
    lesion_cell_id: str,
    generation: int,
    basis_id: str,
) -> JSpaceStep:
    remaining = [c for c in contributions if c.cell_id != lesion_cell_id]
    if len(remaining) == len(contributions):
        raise JSpaceError("LESION_CELL_UNKNOWN")
    if not remaining:
        raise JSpaceError("LESION_REMOVED_ALL_CELLS")
    return step(remaining, generation=generation, basis_id=basis_id)
