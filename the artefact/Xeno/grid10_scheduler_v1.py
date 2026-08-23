#!/usr/bin/env python3
"""Deterministic GRID10 logical-cell scheduler baseline for EntityOS/HCU.

The scheduler consumes an admitted Entry packet and creates a bounded 10-cell logical
plan. It carries both replay-stable event identity and concrete admission identity.
Logical cells are not claims of resident model copies or simultaneous decode streams.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from entry_fabric_v1 import XenoIngressPacket

MODE = "GRID10"
COMPAT_MODE = "XENO_GRID10"
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
    semantic_plan_sha256: str
    mode: str
    event_sha256: str
    admission_sha256: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    active_cells: int
    physical_decode_concurrency_claimed: int | None
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
    semantic_plan_payload = {
        "schema": "ENTITYOS_HCU_GRID10_SEMANTIC_PLAN/v1",
        "mode": MODE,
        "event_sha256": packet.event_sha256,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "functions": list(normalized),
        "logical_capacity": CELL_COUNT,
    }
    semantic_plan_sha256 = hashlib.sha256(_canonical(semantic_plan_payload)).hexdigest()

    cells: list[Grid10Cell] = []
    for index in range(CELL_COUNT):
        active = index < len(normalized)
        function = normalized[index] if active else "IDLE"
        task_payload = {
            "schema": "ENTITYOS_HCU_GRID10_TASK/v1",
            "semantic_plan_sha256": semantic_plan_sha256,
            "event_sha256": packet.event_sha256,
            "admission_sha256": packet.admission_sha256,
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
        "schema": "ENTITYOS_HCU_GRID10_PLAN/v1",
        "semantic_plan_sha256": semantic_plan_sha256,
        "mode": MODE,
        "event_sha256": packet.event_sha256,
        "admission_sha256": packet.admission_sha256,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "active_cells": len(normalized),
        "physical_decode_concurrency_claimed": None,
        "cells": [asdict(cell) for cell in cells],
    }
    plan_id = hashlib.sha256(_canonical(plan_payload)).hexdigest()
    return Grid10Plan(
        schema="ENTITYOS_HCU_GRID10_PLAN/v1",
        plan_id=plan_id,
        semantic_plan_sha256=semantic_plan_sha256,
        mode=MODE,
        event_sha256=packet.event_sha256,
        admission_sha256=packet.admission_sha256,
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        entity_generation=packet.entity_generation,
        active_cells=len(normalized),
        physical_decode_concurrency_claimed=None,
        cells=tuple(cells),
    )


def plan_json(plan: Grid10Plan) -> str:
    body = asdict(plan)
    body["cells"] = [asdict(cell) for cell in plan.cells]
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
