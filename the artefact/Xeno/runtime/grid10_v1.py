#!/usr/bin/env python3
"""Deterministic 10-cell Xeno scheduler/interconnect baseline.

GRID10 is a logical scheduling profile, not a claim of ten simultaneous model decoders.
The scheduler consumes only an already-admitted EntryPacket, emits typed work packets,
and has no canonical-state or real-effect authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from entry_fabric_v1 import EntryPacket

SCHEDULE_SCHEMA = "XENO_GRID10_SCHEDULE/v1"
WORK_PACKET_SCHEMA = "XENO_WORK_PACKET/v1"
SCHEDULER_POLICY = "XENO_GRID10_POLICY/v1"
GRID_SIZE = 10
MODES = frozenset({"XENO_GRID10", "XENO_COGSIM10", "XENO_WM_TEST"})
FUNCTIONS = frozenset({
    "retrieve",
    "provenance",
    "hypothesis",
    "counterhypothesis",
    "critic",
    "simulate",
    "calibrate",
    "jspace_probe",
    "summarize",
    "world_project",
})
MODEL_FUNCTIONS = frozenset({
    "hypothesis",
    "counterhypothesis",
    "critic",
    "simulate",
    "jspace_probe",
    "summarize",
    "world_project",
})


class Grid10Error(ValueError):
    pass


@dataclass(frozen=True)
class LogicalCell:
    slot: int
    function: str


@dataclass(frozen=True)
class WorkPacket:
    schema: str
    work_packet_id: str
    schedule_id: str
    entry_packet_id: str
    entity_generation: int
    causal_id: str
    slot: int
    function: str


@dataclass(frozen=True)
class Grid10Schedule:
    schema: str
    policy_version: str
    schedule_id: str
    mode: str
    entry_packet_id: str
    entity_generation: int
    causal_id: str
    logical_capacity: int
    active_cells: tuple[LogicalCell, ...]
    work_packets: tuple[WorkPacket, ...]
    model_call_budget: int
    physical_decode_concurrency_claimed: int | None


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Grid10Error(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _functions(functions: Iterable[str]) -> tuple[str, ...]:
    if isinstance(functions, (str, bytes)):
        raise Grid10Error("functions:ITERABLE_REQUIRED")
    result: list[str] = []
    for function in functions:
        if not isinstance(function, str) or function not in FUNCTIONS:
            raise Grid10Error("functions:UNSUPPORTED_FUNCTION")
        if function in result:
            raise Grid10Error("functions:DUPLICATE_FUNCTION")
        result.append(function)
    if not result:
        raise Grid10Error("functions:AT_LEAST_ONE_REQUIRED")
    return tuple(result)


def build_grid10_schedule(
    entry: EntryPacket,
    *,
    current_generation: int,
    mode: str = "XENO_GRID10",
    functions: Iterable[str] = ("retrieve", "provenance", "hypothesis", "counterhypothesis", "critic"),
) -> Grid10Schedule:
    if not isinstance(entry, EntryPacket):
        raise Grid10Error("ENTRY_PACKET_REQUIRED")
    current_generation = _nonnegative_int(current_generation, "current_generation")
    if entry.entity_generation != current_generation:
        raise Grid10Error("STALE_ENTITY_GENERATION")
    if mode not in MODES:
        raise Grid10Error("MODE_UNSUPPORTED")

    selected = _functions(functions)
    if len(selected) > GRID_SIZE or len(selected) > entry.budget.max_cells:
        raise Grid10Error("CELL_BUDGET_EXCEEDED")

    required_model_calls = sum(function in MODEL_FUNCTIONS for function in selected)
    if required_model_calls > entry.budget.max_model_calls:
        raise Grid10Error("MODEL_CALL_BUDGET_EXCEEDED")

    cells = tuple(LogicalCell(slot=slot, function=function) for slot, function in enumerate(selected))
    schedule_identity = {
        "schema": SCHEDULE_SCHEMA,
        "policy_version": SCHEDULER_POLICY,
        "mode": mode,
        "entry_packet_id": entry.packet_id,
        "entity_generation": entry.entity_generation,
        "causal_id": entry.causal_id,
        "logical_capacity": GRID_SIZE,
        "active_cells": [asdict(cell) for cell in cells],
        "model_call_budget": entry.budget.max_model_calls,
    }
    schedule_id = hashlib.sha256(_canonical(schedule_identity)).hexdigest()

    work_packets: list[WorkPacket] = []
    for cell in cells:
        work_identity = {
            "schema": WORK_PACKET_SCHEMA,
            "schedule_id": schedule_id,
            "entry_packet_id": entry.packet_id,
            "entity_generation": entry.entity_generation,
            "causal_id": entry.causal_id,
            "slot": cell.slot,
            "function": cell.function,
        }
        work_packet_id = hashlib.sha256(_canonical(work_identity)).hexdigest()
        work_packets.append(
            WorkPacket(
                schema=WORK_PACKET_SCHEMA,
                work_packet_id=work_packet_id,
                schedule_id=schedule_id,
                entry_packet_id=entry.packet_id,
                entity_generation=entry.entity_generation,
                causal_id=entry.causal_id,
                slot=cell.slot,
                function=cell.function,
            )
        )

    return Grid10Schedule(
        schema=SCHEDULE_SCHEMA,
        policy_version=SCHEDULER_POLICY,
        schedule_id=schedule_id,
        mode=mode,
        entry_packet_id=entry.packet_id,
        entity_generation=entry.entity_generation,
        causal_id=entry.causal_id,
        logical_capacity=GRID_SIZE,
        active_cells=cells,
        work_packets=tuple(work_packets),
        model_call_budget=entry.budget.max_model_calls,
        physical_decode_concurrency_claimed=None,
    )
