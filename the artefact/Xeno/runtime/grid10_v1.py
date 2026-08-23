#!/usr/bin/env python3
"""Deterministic GRID10 control/interconnect baseline for Xeno.

GRID10 schedules logical function cells over shared physical compute. It never claims
that logical cells are resident model copies or simultaneous decode streams.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

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


class Grid10SchedulingError(ValueError):
    pass


@dataclass(frozen=True)
class LogicalCell:
    slot: int
    function: str
    model_required: bool


@dataclass(frozen=True)
class WorkPacket:
    schema: str
    work_packet_id: str
    entry_packet_id: str
    causal_id: str
    entity_generation: int
    schedule_id: str
    slot: int
    function: str


@dataclass(frozen=True)
class Grid10Schedule:
    schema: str
    policy_version: str
    schedule_id: str
    mode: str
    entry_packet_id: str
    causal_id: str
    entity_generation: int
    logical_capacity: int
    active_cells: tuple[LogicalCell, ...]
    physical_decode_concurrency_claimed: int | None
    work_packets: tuple[WorkPacket, ...]


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _model_required(function: str) -> bool:
    return function in {
        "hypothesis",
        "counterhypothesis",
        "critic",
        "simulate",
        "jspace_probe",
        "world_project",
        "summarize",
    }


def _normalize_functions(functions: Iterable[str]) -> tuple[str, ...]:
    if isinstance(functions, (str, bytes)):
        raise Grid10SchedulingError("FUNCTIONS_ITERABLE_REQUIRED")
    normalized: list[str] = []
    for function in functions:
        if not isinstance(function, str) or function not in FUNCTIONS:
            raise Grid10SchedulingError("FUNCTION_UNSUPPORTED")
        if function not in normalized:
            normalized.append(function)
    return tuple(normalized)


def schedule_grid10(
    entry: EntryPacket,
    *,
    mode: str,
    requested_functions: Iterable[str],
    current_generation: int,
) -> Grid10Schedule:
    if not isinstance(entry, EntryPacket):
        raise Grid10SchedulingError("ENTRY_PACKET_REQUIRED")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise Grid10SchedulingError("CURRENT_GENERATION_INVALID")
    if entry.entity_generation != current_generation:
        raise Grid10SchedulingError("STALE_ENTITY_GENERATION")
    if mode not in MODES:
        raise Grid10SchedulingError("MODE_UNSUPPORTED")

    functions = _normalize_functions(requested_functions)
    allowed_cells = min(GRID_SIZE, entry.budget.max_cells)
    if len(functions) > allowed_cells:
        raise Grid10SchedulingError("CELL_BUDGET_EXCEEDED")

    cells = tuple(
        LogicalCell(slot=slot, function=function, model_required=_model_required(function))
        for slot, function in enumerate(functions)
    )
    model_calls = sum(1 for cell in cells if cell.model_required)
    if model_calls > entry.budget.max_model_calls:
        raise Grid10SchedulingError("MODEL_CALL_BUDGET_EXCEEDED")

    schedule_identity = {
        "schema": SCHEDULE_SCHEMA,
        "policy_version": SCHEDULER_POLICY,
        "mode": mode,
        "entry_packet_id": entry.packet_id,
        "causal_id": entry.causal_id,
        "entity_generation": entry.entity_generation,
        "logical_capacity": GRID_SIZE,
        "active_cells": [
            {"slot": cell.slot, "function": cell.function, "model_required": cell.model_required}
            for cell in cells
        ],
        "physical_decode_concurrency_claimed": None,
    }
    schedule_id = hashlib.sha256(_canonical(schedule_identity)).hexdigest()

    work_packets = []
    for cell in cells:
        identity = {
            "schema": WORK_PACKET_SCHEMA,
            "entry_packet_id": entry.packet_id,
            "causal_id": entry.causal_id,
            "entity_generation": entry.entity_generation,
            "schedule_id": schedule_id,
            "slot": cell.slot,
            "function": cell.function,
        }
        work_packets.append(
            WorkPacket(
                schema=WORK_PACKET_SCHEMA,
                work_packet_id=hashlib.sha256(_canonical(identity)).hexdigest(),
                entry_packet_id=entry.packet_id,
                causal_id=entry.causal_id,
                entity_generation=entry.entity_generation,
                schedule_id=schedule_id,
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
        causal_id=entry.causal_id,
        entity_generation=entry.entity_generation,
        logical_capacity=GRID_SIZE,
        active_cells=cells,
        physical_decode_concurrency_claimed=None,
        work_packets=tuple(work_packets),
    )
