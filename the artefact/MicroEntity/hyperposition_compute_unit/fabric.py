#!/usr/bin/env python3
"""Typed HCU fabric primitives.

The fabric transports candidate/simulated computation only. Canonical state writes and real
effects are intentionally absent from this module.
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
            # Other candidate classes may describe a simulation but the packet authority itself
            # remains candidate-only. Use SIMULATED_STATE for state predictions.
            raise ValueError("simulated=true is reserved for SIMULATED_STATE packets")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0,1]")

        forbidden = {
            "canonical_fact",
            "canonical_write",
            "direct_effect",
            "effect_executed",
            "truth_authority",
        }
        overlap = forbidden.intersection(self.payload)
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


@dataclass(frozen=True)
class CellSpec:
    cell_id: str
    role: str
    mode: str
    priority: int
    max_parallel_instances: int
    output_classes: tuple[PacketClass, ...]

    def validate(self) -> None:
        if self.mode not in {
            "SHARED_BASE_08B_CELL",
            "FULL_RESIDENT_08B_CELL",
            "COLD_SLOT_08B_CELL",
            "IO_ONLY",
        }:
            raise ValueError("unsupported cell mode")
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        if self.max_parallel_instances < 1:
            raise ValueError("max_parallel_instances must be >= 1")
        if not self.output_classes:
            raise ValueError("cell must declare at least one candidate output class")


def generation_matches(packet: HCUPacket, current_generation: int) -> bool:
    packet.validate()
    return packet.entity_generation == current_generation
