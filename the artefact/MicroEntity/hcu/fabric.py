#!/usr/bin/env python3
"""Typed Hyperposition Computational Unit packet fabric.

This module carries candidate/simulated computation only. It intentionally exposes no canonical
MiniUnifiedDB write primitive and no real-effect execution primitive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping
import hashlib
import json


class PacketClass(str, Enum):
    CANDIDATE_OBSERVATION = "CANDIDATE_OBSERVATION"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    CANDIDATE_GOAL = "CANDIDATE_GOAL"
    CANDIDATE_PLAN = "CANDIDATE_PLAN"
    CANDIDATE_CRITIQUE = "CANDIDATE_CRITIQUE"
    SIMULATED_STATE = "SIMULATED_STATE"
    ZERO_TWIN_PREDICTION = "ZERO_TWIN_PREDICTION"


FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "canonical_fact",
        "canonical_write",
        "direct_effect",
        "effect_executed",
        "truth_authority",
    }
)


@dataclass(frozen=True)
class HCUPacket:
    packet_class: PacketClass
    cycle_id: str
    causal_id: str
    entity_generation: int
    producer_cell_id: str
    payload: Mapping[str, Any]
    parent_packet_ids: tuple[str, ...] = ()
    confidence: float | None = None
    simulated: bool = False

    def validate(self) -> None:
        if not self.cycle_id or not self.causal_id or not self.producer_cell_id:
            raise ValueError("identity fields must be non-empty")
        if self.entity_generation < 0:
            raise ValueError("entity_generation must be >= 0")
        if self.packet_class is PacketClass.SIMULATED_STATE and not self.simulated:
            raise ValueError("SIMULATED_STATE must set simulated=true")
        if self.simulated and self.packet_class is not PacketClass.SIMULATED_STATE:
            raise ValueError("simulated=true is reserved for SIMULATED_STATE packets")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0,1]")
        overlap = FORBIDDEN_AUTHORITY_FIELDS.intersection(self.payload)
        if overlap:
            raise ValueError(f"forbidden authority fields: {sorted(overlap)}")

    def packet_id(self) -> str:
        self.validate()
        canonical = json.dumps(
            {
                "packet_class": self.packet_class.value,
                "cycle_id": self.cycle_id,
                "causal_id": self.causal_id,
                "entity_generation": self.entity_generation,
                "producer_cell_id": self.producer_cell_id,
                "payload": self.payload,
                "parent_packet_ids": self.parent_packet_ids,
                "confidence": self.confidence,
                "simulated": self.simulated,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def generation_matches(packet: HCUPacket, current_generation: int) -> bool:
    packet.validate()
    return packet.entity_generation == current_generation
