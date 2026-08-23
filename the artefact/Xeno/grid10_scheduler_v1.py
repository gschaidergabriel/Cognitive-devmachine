"""Xeno deterministic 10-cell scheduler/control-plane baseline v1.

XPU-style allocator over verified typed Xeno ingress. It owns no truth, durable state
or effects. Logical cells are leases over shared workers/control functions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from entry_fabric_v1 import AdmissionError, XenoIngressPacket, verify_ingress_packet

SCHEMA_ID = "XENO_GRID_PLAN/v1"


class ScheduleError(ValueError):
    """Fail-closed schedule compilation error."""


class XenoMode(str, Enum):
    DIRECT = "DIRECT"
    XENO_GRID10 = "XENO_GRID10"
    XENO_COGSIM10 = "XENO_COGSIM10"
    XENO_WM_TEST = "XENO_WM_TEST"
    XENO_NESTED_SIM = "XENO_NESTED_SIM"


def _strict_int(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScheduleError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise ScheduleError(f"{field} must be in [{minimum},{maximum}]")
    return value


@dataclass(frozen=True, slots=True)
class FunctionRequest:
    name: str
    priority: int
    inference_required: bool = True
    estimated_tokens: int = 0
    authority_class: str = "CANDIDATE_COMPUTE"

    def normalized(self) -> "FunctionRequest":
        if not isinstance(self.name, str):
            raise ScheduleError("function name must be a string")
        name = self.name.strip()
        if not name or len(name) > 128:
            raise ScheduleError("function name must be non-empty and <= 128 chars")
        priority = _strict_int(self.priority, "priority", 0, 100)
        tokens = _strict_int(self.estimated_tokens, "estimated_tokens", 0, 10_000_000)
        if not isinstance(self.inference_required, bool):
            raise ScheduleError("inference_required must be boolean")
        if self.authority_class != "CANDIDATE_COMPUTE":
            raise ScheduleError("logical cells may carry candidate compute only")
        return FunctionRequest(name=name, priority=priority, inference_required=self.inference_required, estimated_tokens=tokens)


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    max_logical_cells: int = 10
    shared_workers: tuple[str, ...] = ("xcu:shared-worker-0",)

    def normalized(self) -> "SchedulerConfig":
        cells = _strict_int(self.max_logical_cells, "GRID10 max_logical_cells", 1, 10)
        if isinstance(self.shared_workers, (str, bytes)) or not isinstance(self.shared_workers, (tuple, list, set, frozenset)):
            raise ScheduleError("shared_workers must be a collection of worker ids")
        workers_set: set[str] = set()
        for worker in self.shared_workers:
            if not isinstance(worker, str):
                raise ScheduleError("worker id must be a string")
            worker = worker.strip()
            if not worker or len(worker) > 256:
                raise ScheduleError("worker id must be non-empty and <= 256 chars")
            workers_set.add(worker)
        workers = tuple(sorted(workers_set))
        if not workers:
            raise ScheduleError("at least one shared worker is required")
        if len(workers) > 10:
            raise ScheduleError("too many physical workers for GRID10 baseline")
        return SchedulerConfig(max_logical_cells=cells, shared_workers=workers)


@dataclass(frozen=True, slots=True)
class CellLease:
    cell_id: str
    function_name: str
    worker_id: str
    inference_required: bool
    estimated_tokens: int
    authority_class: str = "CANDIDATE_COMPUTE"


@dataclass(frozen=True, slots=True)
class GridPlan:
    schema_id: str
    plan_id: str
    ingress_id: str
    causal_id: str
    generation: int
    mode: str
    leases: tuple[CellLease, ...]
    total_estimated_tokens: int
    inference_lease_count: int

    def receipt(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id, "plan_id": self.plan_id, "ingress_id": self.ingress_id,
            "causal_id": self.causal_id, "generation": self.generation, "mode": self.mode,
            "total_estimated_tokens": self.total_estimated_tokens,
            "inference_lease_count": self.inference_lease_count,
            "leases": [
                {"cell_id": lease.cell_id, "function_name": lease.function_name, "worker_id": lease.worker_id,
                 "inference_required": lease.inference_required, "estimated_tokens": lease.estimated_tokens,
                 "authority_class": lease.authority_class}
                for lease in self.leases
            ],
        }


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compile_grid_plan(packet: XenoIngressPacket, functions: tuple[FunctionRequest, ...], *, mode: XenoMode,
                      current_generation: int, config: SchedulerConfig = SchedulerConfig()) -> GridPlan:
    """Compile a deterministic bounded plan only after Entry identity re-verification."""
    current = _strict_int(current_generation, "current_generation", 0, 2**63 - 1)
    try:
        verify_ingress_packet(packet, current_generation=current)
    except AdmissionError as exc:
        raise ScheduleError("unverified ingress packet") from exc
    try:
        selected_mode = XenoMode(mode).value
    except (TypeError, ValueError) as exc:
        raise ScheduleError("unsupported mode") from exc
    if isinstance(functions, (str, bytes)) or not isinstance(functions, (tuple, list)):
        raise ScheduleError("functions must be a sequence of FunctionRequest")
    if len(functions) > 256:
        raise ScheduleError("too many function requests")
    cfg = config.normalized()
    normalized = []
    for req in functions:
        if not isinstance(req, FunctionRequest):
            raise ScheduleError("each function must be FunctionRequest")
        normalized.append(req.normalized())
    if not normalized:
        raise ScheduleError("at least one function request is required")

    unique: dict[str, FunctionRequest] = {}
    for req in normalized:
        previous = unique.get(req.name)
        if previous is None or (req.priority, -req.estimated_tokens) > (previous.priority, -previous.estimated_tokens):
            unique[req.name] = req
    ordered = sorted(unique.values(), key=lambda item: (-item.priority, item.name))
    cell_limit = min(cfg.max_logical_cells, packet.resource_budget.max_logical_cells)
    inference_limit = packet.resource_budget.max_inference_calls
    token_limit = packet.resource_budget.max_tokens
    leases: list[CellLease] = []
    inference_used = 0
    tokens_used = 0
    worker_cursor = 0
    for req in ordered:
        if len(leases) >= cell_limit:
            break
        if tokens_used + req.estimated_tokens > token_limit:
            continue
        if req.inference_required:
            if inference_used >= inference_limit:
                continue
            worker_id = cfg.shared_workers[worker_cursor % len(cfg.shared_workers)]
            worker_cursor += 1
            inference_used += 1
        else:
            worker_id = "xpu:deterministic"
        ordinal = len(leases)
        cell_material = {
            "ingress_id": packet.ingress_id, "causal_id": packet.causal_id, "generation": packet.generation,
            "mode": selected_mode, "ordinal": ordinal, "function_name": req.name, "worker_id": worker_id,
            "inference_required": req.inference_required, "estimated_tokens": req.estimated_tokens,
            "authority_class": req.authority_class,
        }
        leases.append(CellLease(cell_id=f"xeno-cell:{_digest(cell_material)}", function_name=req.name,
                                worker_id=worker_id, inference_required=req.inference_required,
                                estimated_tokens=req.estimated_tokens))
        tokens_used += req.estimated_tokens
    if not leases:
        raise ScheduleError("budget admits no function lease")
    plan_material = {
        "schema_id": SCHEMA_ID, "ingress_id": packet.ingress_id, "causal_id": packet.causal_id,
        "generation": packet.generation, "mode": selected_mode,
        "leases": [
            {"cell_id": lease.cell_id, "function_name": lease.function_name, "worker_id": lease.worker_id,
             "inference_required": lease.inference_required, "estimated_tokens": lease.estimated_tokens,
             "authority_class": lease.authority_class}
            for lease in leases
        ],
        "total_estimated_tokens": tokens_used, "inference_lease_count": inference_used,
    }
    return GridPlan(schema_id=SCHEMA_ID, plan_id=f"xeno-plan:{_digest(plan_material)}", ingress_id=packet.ingress_id,
                    causal_id=packet.causal_id, generation=packet.generation, mode=selected_mode,
                    leases=tuple(leases), total_estimated_tokens=tokens_used, inference_lease_count=inference_used)
