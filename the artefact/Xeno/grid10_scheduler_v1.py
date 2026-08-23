#!/usr/bin/env python3
"""Deterministic XENO_GRID10 logical-cell scheduler baseline.

The scheduler consumes an already-admitted XenoIngressPacket and creates a bounded
10-cell logical plan. It owns no truth, model weights, canonical state, or effect authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from entry_fabric_v1 import XenoIngressPacket

MODE = "XENO_GRID10"
CELL_COUNT = 10


class Grid10SchedulingError(ValueError):
    pass


@dataclass(frozen=True)
class Grid10Cell:
    cell_index: int
    function: str
    active: bool
    task_id: str


@dataclass(frozen=True)
class Grid10Plan:
    schema: str
    plan_id: str
    mode: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    active_cells: int
    cells: tuple[Grid10Cell, ...]


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _function_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Grid10SchedulingError("FUNCTION_NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 96:
        raise Grid10SchedulingError("FUNCTION_NAME_TOO_LONG")
    return value


def schedule_grid10(
    packet: XenoIngressPacket,
    functions: Sequence[str],
    *,
    current_generation: int,
) -> Grid10Plan:
    if not isinstance(packet, XenoIngressPacket):
        raise Grid10SchedulingError("ADMITTED_INGRESS_PACKET_REQUIRED")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise Grid10SchedulingError("CURRENT_GENERATION_INVALID")
    if packet.entity_generation != current_generation:
        raise Grid10SchedulingError("STALE_ENTITY_GENERATION")
    if not isinstance(functions, (list, tuple)):
        raise Grid10SchedulingError("FUNCTION_SEQUENCE_REQUIRED")
    if len(functions) > CELL_COUNT:
        raise Grid10SchedulingError("GRID10_CELL_LIMIT_EXCEEDED")
    if len(functions) > packet.resource_budget.max_logical_cells:
        raise Grid10SchedulingError("INGRESS_LOGICAL_CELL_BUDGET_EXCEEDED")

    normalized = tuple(_function_name(value) for value in functions)
    cells: list[Grid10Cell] = []
    for index in range(CELL_COUNT):
        active = index < len(normalized)
        function = normalized[index] if active else "IDLE"
        task_payload = {
            "mode": MODE,
            "ingress_id": packet.ingress_id,
            "causal_id": packet.causal_id,
            "entity_generation": packet.entity_generation,
            "cell_index": index,
            "function": function,
            "active": active,
        }
        task_id = hashlib.sha256(_canonical(task_payload)).hexdigest()
        cells.append(
            Grid10Cell(
                cell_index=index,
                function=function,
                active=active,
                task_id=task_id,
            )
        )

    plan_payload = {
        "schema": "XENO_GRID10_PLAN/v1",
        "mode": MODE,
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "active_cells": len(normalized),
        "cells": [asdict(cell) for cell in cells],
    }
    plan_id = hashlib.sha256(_canonical(plan_payload)).hexdigest()
    return Grid10Plan(
        schema="XENO_GRID10_PLAN/v1",
        plan_id=plan_id,
        mode=MODE,
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        entity_generation=packet.entity_generation,
        active_cells=len(normalized),
        cells=tuple(cells),
    )


def plan_json(plan: Grid10Plan) -> str:
    body = asdict(plan)
    body["cells"] = [asdict(cell) for cell in plan.cells]
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
