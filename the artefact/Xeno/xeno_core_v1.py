from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence

INGRESS_SCHEMA = "XENO_INGRESS_PACKET/v1"
GRID_PLAN_SCHEMA = "XENO_GRID_PLAN/v1"
COMPUTE_PACKET_SCHEMA = "XENO_COMPUTE_PACKET/v1"

SOURCE_CLASSES = frozenset({
    "HUMAN_PROMPT",
    "EXTERNAL_EVENT",
    "TOOL_OUTCOME",
    "SENSOR_STREAM",
    "DATABASE_CHANGE",
    "INTRINSIC_EVENT",
})
MODALITIES = frozenset({"TEXT", "JSON", "SCALAR", "BINARY_REF", "IMAGE_REF", "AUDIO_REF", "EVENT"})
GRID10_MODES = frozenset({"XENO_GRID10", "XENO_COGSIM10", "XENO_WM_TEST", "XENO_NESTED_SIM"})

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,255}$")
_CAP_RE = re.compile(r"^[a-z][a-z0-9_.:-]{0,127}$")
_SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class XenoAdmissionError(ValueError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value)).hexdigest()


def _strict_int(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise XenoAdmissionError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise XenoAdmissionError(f"{name} outside admitted range")
    return value


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise XenoAdmissionError(f"{name} is not a canonical identifier")
    return value


def _sorted_unique_strings(value: Any, name: str, *, pattern: re.Pattern[str] | None = None, max_items: int = 64) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise XenoAdmissionError(f"{name} must be a list")
    if len(value) > max_items:
        raise XenoAdmissionError(f"{name} exceeds item limit")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise XenoAdmissionError(f"{name} contains a non-string/empty item")
        if pattern is not None and not pattern.fullmatch(item):
            raise XenoAdmissionError(f"{name} contains a non-canonical item")
        out.append(item)
    return tuple(sorted(set(out)))


@dataclass(frozen=True)
class ResourceBudget:
    logical_cells_max: int
    active_decodes_max: int
    token_budget_total: int
    wall_time_ms: int
    payload_bytes_max: int

    @classmethod
    def admit(cls, raw: Any) -> "ResourceBudget":
        if not isinstance(raw, Mapping):
            raise XenoAdmissionError("resource_budget must be an object")
        expected = {
            "logical_cells_max",
            "active_decodes_max",
            "token_budget_total",
            "wall_time_ms",
            "payload_bytes_max",
        }
        if set(raw) != expected:
            raise XenoAdmissionError("resource_budget keys must match schema exactly")
        logical = _strict_int(raw["logical_cells_max"], "logical_cells_max", 1, 600)
        active = _strict_int(raw["active_decodes_max"], "active_decodes_max", 1, 600)
        if active > logical:
            raise XenoAdmissionError("active_decodes_max cannot exceed logical_cells_max")
        return cls(
            logical_cells_max=logical,
            active_decodes_max=active,
            token_budget_total=_strict_int(raw["token_budget_total"], "token_budget_total", 1, 100_000_000),
            wall_time_ms=_strict_int(raw["wall_time_ms"], "wall_time_ms", 1, 86_400_000),
            payload_bytes_max=_strict_int(raw["payload_bytes_max"], "payload_bytes_max", 1, 1_000_000_000),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "logical_cells_max": self.logical_cells_max,
            "active_decodes_max": self.active_decodes_max,
            "token_budget_total": self.token_budget_total,
            "wall_time_ms": self.wall_time_ms,
            "payload_bytes_max": self.payload_bytes_max,
        }


@dataclass(frozen=True)
class XenoIngressPacket:
    ingress_id: str
    source_event_key: str
    causal_id: str
    generation: int
    source_class: str
    source: str
    source_event_id: str
    provenance: tuple[str, ...]
    modality: str
    observed_at: int
    received_at: int
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    parent_or_stream_id: str | None
    resource_budget: ResourceBudget
    payload_ref: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": INGRESS_SCHEMA,
            "ingress_id": self.ingress_id,
            "source_event_key": self.source_event_key,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "source_class": self.source_class,
            "source": self.source,
            "source_event_id": self.source_event_id,
            "provenance": list(self.provenance),
            "modality": self.modality,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "permissions": list(self.permissions),
            "capability_scope": list(self.capability_scope),
            "parent_or_stream_id": self.parent_or_stream_id,
            "resource_budget": self.resource_budget.to_dict(),
            "payload_ref": self.payload_ref,
        }


_INGRESS_INPUT_KEYS = {
    "causal_id",
    "generation",
    "source_class",
    "source",
    "source_event_id",
    "provenance",
    "modality",
    "observed_at",
    "received_at",
    "permissions",
    "capability_scope",
    "parent_or_stream_id",
    "resource_budget",
    "payload_ref",
}


def admit_ingress(raw: Mapping[str, Any], *, current_generation: int, allowed_capabilities: Iterable[str]) -> XenoIngressPacket:
    if not isinstance(raw, Mapping):
        raise XenoAdmissionError("ingress must be an object")
    if set(raw) != _INGRESS_INPUT_KEYS:
        missing = sorted(_INGRESS_INPUT_KEYS - set(raw))
        extra = sorted(set(raw) - _INGRESS_INPUT_KEYS)
        raise XenoAdmissionError(f"ingress schema mismatch missing={missing} extra={extra}")

    generation = _strict_int(raw["generation"], "generation", 0, 2**63 - 1)
    expected_generation = _strict_int(current_generation, "current_generation", 0, 2**63 - 1)
    if generation != expected_generation:
        raise XenoAdmissionError("stale/future generation rejected")

    source_class = raw["source_class"]
    if source_class not in SOURCE_CLASSES:
        raise XenoAdmissionError("unknown source_class")
    modality = raw["modality"]
    if modality not in MODALITIES:
        raise XenoAdmissionError("unknown modality")

    observed_at = _strict_int(raw["observed_at"], "observed_at", 0, 2**63 - 1)
    received_at = _strict_int(raw["received_at"], "received_at", 0, 2**63 - 1)
    if received_at < observed_at:
        raise XenoAdmissionError("received_at cannot precede observed_at")

    payload_ref = raw["payload_ref"]
    if not isinstance(payload_ref, str) or not _SHA256_REF_RE.fullmatch(payload_ref):
        raise XenoAdmissionError("payload_ref must be lowercase sha256:<64hex>")

    allowed = frozenset(allowed_capabilities)
    if any(not isinstance(x, str) or not _CAP_RE.fullmatch(x) for x in allowed):
        raise XenoAdmissionError("allowed_capabilities contains invalid capability")
    capabilities = _sorted_unique_strings(raw["capability_scope"], "capability_scope", pattern=_CAP_RE)
    if not set(capabilities).issubset(allowed):
        raise XenoAdmissionError("capability_scope exceeds admitted capabilities")

    parent = raw["parent_or_stream_id"]
    if parent is not None:
        parent = _id(parent, "parent_or_stream_id")

    budget = ResourceBudget.admit(raw["resource_budget"])
    source = _id(raw["source"], "source")
    source_event_id = _id(raw["source_event_id"], "source_event_id")
    source_event_key = _digest({"source": source, "source_event_id": source_event_id})
    body = {
        "schema": INGRESS_SCHEMA,
        "source_event_key": source_event_key,
        "causal_id": _id(raw["causal_id"], "causal_id"),
        "generation": generation,
        "source_class": source_class,
        "source": source,
        "source_event_id": source_event_id,
        "provenance": list(_sorted_unique_strings(raw["provenance"], "provenance", max_items=32)),
        "modality": modality,
        "observed_at": observed_at,
        "received_at": received_at,
        "permissions": list(_sorted_unique_strings(raw["permissions"], "permissions", pattern=_CAP_RE)),
        "capability_scope": list(capabilities),
        "parent_or_stream_id": parent,
        "resource_budget": budget.to_dict(),
        "payload_ref": payload_ref,
    }
    ingress_id = _digest(body)
    return XenoIngressPacket(
        ingress_id=ingress_id,
        source_event_key=source_event_key,
        causal_id=body["causal_id"],
        generation=generation,
        source_class=source_class,
        source=body["source"],
        source_event_id=body["source_event_id"],
        provenance=tuple(body["provenance"]),
        modality=modality,
        observed_at=observed_at,
        received_at=received_at,
        permissions=tuple(body["permissions"]),
        capability_scope=capabilities,
        parent_or_stream_id=parent,
        resource_budget=budget,
        payload_ref=payload_ref,
    )


@dataclass(frozen=True)
class XenoGridCell:
    cell_id: str
    function: str
    token_budget: int

    def to_dict(self) -> dict[str, Any]:
        return {"cell_id": self.cell_id, "function": self.function, "token_budget": self.token_budget}


@dataclass(frozen=True)
class XenoGridPlan:
    plan_id: str
    ingress_id: str
    source_event_key: str
    causal_id: str
    generation: int
    mode: str
    logical_cell_count: int
    active_decode_limit: int
    cells: tuple[XenoGridCell, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": GRID_PLAN_SCHEMA,
            "plan_id": self.plan_id,
            "ingress_id": self.ingress_id,
            "source_event_key": self.source_event_key,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "mode": self.mode,
            "logical_cell_count": self.logical_cell_count,
            "active_decode_limit": self.active_decode_limit,
            "cells": [c.to_dict() for c in self.cells],
        }


def build_grid10_plan(packet: XenoIngressPacket, functions: Sequence[str], *, physical_worker_slots: int, mode: str = "XENO_GRID10") -> XenoGridPlan:
    if mode not in GRID10_MODES:
        raise XenoAdmissionError("mode not admitted by GRID10 planner")
    if packet.resource_budget.logical_cells_max < 10:
        raise XenoAdmissionError("ingress budget does not admit GRID10")
    worker_slots = _strict_int(physical_worker_slots, "physical_worker_slots", 1, 10_000)
    if not isinstance(functions, Sequence) or isinstance(functions, (str, bytes)) or not 1 <= len(functions) <= 10:
        raise XenoAdmissionError("functions must contain 1..10 function identifiers")
    canonical_functions = tuple(_id(x, "function") for x in functions)

    if packet.resource_budget.token_budget_total < 10:
        raise XenoAdmissionError("GRID10 requires at least one token of budget per logical cell")
    active_decode_limit = min(10, packet.resource_budget.active_decodes_max, worker_slots)
    token_budget_per_cell = packet.resource_budget.token_budget_total // 10
    cells = tuple(
        XenoGridCell(cell_id=f"cell-{i:02d}", function=canonical_functions[i % len(canonical_functions)], token_budget=token_budget_per_cell)
        for i in range(10)
    )
    body = {
        "schema": GRID_PLAN_SCHEMA,
        "ingress_id": packet.ingress_id,
        "source_event_key": packet.source_event_key,
        "causal_id": packet.causal_id,
        "generation": packet.generation,
        "mode": mode,
        "logical_cell_count": 10,
        "active_decode_limit": active_decode_limit,
        "cells": [c.to_dict() for c in cells],
    }
    plan_id = _digest(body)
    return XenoGridPlan(plan_id, packet.ingress_id, packet.source_event_key, packet.causal_id, packet.generation, mode, 10, active_decode_limit, cells)


@dataclass(frozen=True)
class XenoComputePacket:
    packet_id: str
    plan_id: str
    ingress_id: str
    source_event_key: str
    causal_id: str
    generation: int
    mode: str
    producer_cell: str
    parent_packet_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    counterevidence_refs: tuple[str, ...]
    confidence_class: str
    payload_ref: str
    authority_class: str = "CANDIDATE_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": COMPUTE_PACKET_SCHEMA,
            "packet_id": self.packet_id,
            "plan_id": self.plan_id,
            "ingress_id": self.ingress_id,
            "source_event_key": self.source_event_key,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "mode": self.mode,
            "producer_cell": self.producer_cell,
            "parent_packet_ids": list(self.parent_packet_ids),
            "evidence_refs": list(self.evidence_refs),
            "counterevidence_refs": list(self.counterevidence_refs),
            "confidence_class": self.confidence_class,
            "payload_ref": self.payload_ref,
            "authority_class": self.authority_class,
        }


def make_compute_packet(
    plan: XenoGridPlan,
    *,
    producer_cell: str,
    payload_ref: str,
    parent_packet_ids: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
    counterevidence_refs: Sequence[str] = (),
    confidence_class: str = "UNVERIFIED",
) -> XenoComputePacket:
    admitted_cells = {cell.cell_id for cell in plan.cells}
    if producer_cell not in admitted_cells:
        raise XenoAdmissionError("producer_cell is not in plan")
    if not _SHA256_REF_RE.fullmatch(payload_ref):
        raise XenoAdmissionError("compute payload_ref must be lowercase sha256:<64hex>")
    parents = _sorted_unique_strings(parent_packet_ids, "parent_packet_ids", max_items=64)
    evidence = _sorted_unique_strings(evidence_refs, "evidence_refs", max_items=128)
    counter = _sorted_unique_strings(counterevidence_refs, "counterevidence_refs", max_items=128)
    confidence = _id(confidence_class, "confidence_class")
    body = {
        "schema": COMPUTE_PACKET_SCHEMA,
        "plan_id": plan.plan_id,
        "ingress_id": plan.ingress_id,
        "source_event_key": plan.source_event_key,
        "causal_id": plan.causal_id,
        "generation": plan.generation,
        "mode": plan.mode,
        "producer_cell": producer_cell,
        "parent_packet_ids": list(parents),
        "evidence_refs": list(evidence),
        "counterevidence_refs": list(counter),
        "confidence_class": confidence,
        "payload_ref": payload_ref,
        "authority_class": "CANDIDATE_ONLY",
    }
    packet_id = _digest(body)
    return XenoComputePacket(
        packet_id=packet_id,
        plan_id=plan.plan_id,
        ingress_id=plan.ingress_id,
        source_event_key=plan.source_event_key,
        causal_id=plan.causal_id,
        generation=plan.generation,
        mode=plan.mode,
        producer_cell=producer_cell,
        parent_packet_ids=parents,
        evidence_refs=evidence,
        counterevidence_refs=counter,
        confidence_class=confidence,
        payload_ref=payload_ref,
    )
