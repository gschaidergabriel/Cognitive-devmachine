"""Xeno deterministic 10-cell scheduler/control-plane baseline v1.

This is an XPU-style allocator over typed Xeno ingress. It owns no truth, no durable
state and no effects. Logical cells are leases over shared workers or deterministic
control functions; plan identity is causally bound to the admitted ingress identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from entry_fabric_v1 import XenoIngressPacket

SCHEMA_ID = "XENO_GRID_PLAN/v1"
_MAX_GENERATION = 2**63 - 1


class ScheduleError(ValueError):
    """Fail-closed schedule compilation error."""


class XenoMode(str, Enum):
    DIRECT = "DIRECT"
    XENO_GRID10 = "XENO_GRID10"
    XENO_COGSIM10 = "XENO_COGSIM10"
    XENO_WM_TEST = "XENO_WM_TEST"
    XENO_NESTED_SIM = "XENO_NESTED_SIM"


def _strict_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScheduleError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise ScheduleError(f"{field} must be in [{minimum},{maximum}]")
    return value


def _strict_text(value: object, field: str, *, max_len: int) -> str:
    if not isinstance(value, str):
        raise ScheduleError(f"{field} must be a string")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > max_len:
        raise ScheduleError(f"{field} must be non-empty and <= {max_len} chars")
    return cleaned


@dataclass(frozen=True, slots=True)
class FunctionRequest:
    name: str
    priority: int
    inference_required: bool = True
    estimated_tokens: int = 0
    authority_class: str = "CANDIDATE_COMPUTE"

    def normalized(self) -> "FunctionRequest":
        name = _strict_text(self.name, "function name", max_len=128)
        priority = _strict_int(self.priority, "priority", minimum=0, maximum=100)
        tokens = _strict_int(
            self.estimated_tokens, "estimated_tokens", minimum=0, maximum=10_000_000
        )
        if not isinstance(self.inference_required, bool):
            raise ScheduleError("inference_required must be boolean")
        if self.authority_class != "CANDIDATE_COMPUTE":
            raise ScheduleError("logical cells may carry candidate compute only")
        return FunctionRequest(
            name=name,
            priority=priority,
            inference_required=self.inference_required,
            estimated_tokens=tokens,
            authority_class="CANDIDATE_COMPUTE",
        )


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    max_logical_cells: int = 10
    shared_workers: tuple[str, ...] = ("xcu:shared-worker-0",)

    def normalized(self) -> "SchedulerConfig":
        cells = _strict_int(
            self.max_logical_cells,
            "GRID10 scheduler max_logical_cells",
            minimum=1,
            maximum=10,
        )
        if not isinstance(self.shared_workers, tuple):
            raise ScheduleError("shared_workers must be a tuple of strings")
        workers_list: list[str] = []
        for worker in self.shared_workers:
            workers_list.append(_strict_text(worker, "shared worker", max_len=256))
        workers = tuple(sorted(set(workers_list)))
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
            "schema_id": self.schema_id,
            "plan_id": self.plan_id,
            "ingress_id": self.ingress_id,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "mode": self.mode,
            "total_estimated_tokens": self.total_estimated_tokens,
            "inference_lease_count": self.inference_lease_count,
            "leases": [
                {
                    "cell_id": lease.cell_id,
                    "function_name": lease.function_name,
                    "worker_id": lease.worker_id,
                    "inference_required": lease.inference_required,
                    "estimated_tokens": lease.estimated_tokens,
                    "authority_class": lease.authority_class,
                }
                for lease in self.leases
            ],
        }


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compile_grid_plan(
    packet: XenoIngressPacket,
    functions: tuple[FunctionRequest, ...],
    *,
    mode: XenoMode,
    current_generation: int,
    config: SchedulerConfig = SchedulerConfig(),
) -> GridPlan:
    """Compile a deterministic bounded plan over shared workers.

    Plan identity commits to ingress identity + causal identity + generation + mode +
    selected leases. Two different admitted events cannot alias to the same route plan
    simply because they select the same functions.
    """
    if not isinstance(packet, XenoIngressPacket):
        raise ScheduleError("packet must be an admitted XenoIngressPacket")
    packet_generation = _strict_int(
        packet.generation, "packet generation", minimum=0, maximum=_MAX_GENERATION
    )
    live_generation = _strict_int(
        current_generation, "current_generation", minimum=0, maximum=_MAX_GENERATION
    )
    if packet_generation != live_generation:
        raise ScheduleError("packet generation is stale or future")
    try:
        selected_mode = XenoMode(mode).value
    except ValueError as exc:
        raise ScheduleError("unsupported mode") from exc

    cfg = config.normalized()
    if not isinstance(functions, tuple):
        raise ScheduleError("functions must be a tuple of FunctionRequest values")
    normalized_items: list[FunctionRequest] = []
    for req in functions:
        if not isinstance(req, FunctionRequest):
            raise ScheduleError("functions must contain FunctionRequest values only")
        normalized_items.append(req.normalized())
    normalized = tuple(normalized_items)
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
            "ingress_id": packet.ingress_id,
            "causal_id": packet.causal_id,
            "generation": packet.generation,
            "mode": selected_mode,
            "ordinal": ordinal,
            "function_name": req.name,
            "worker_id": worker_id,
            "inference_required": req.inference_required,
            "estimated_tokens": req.estimated_tokens,
            "authority_class": req.authority_class,
        }
        cell_id = f"xeno-cell:{_digest(cell_material)}"
        leases.append(
            CellLease(
                cell_id=cell_id,
                function_name=req.name,
                worker_id=worker_id,
                inference_required=req.inference_required,
                estimated_tokens=req.estimated_tokens,
            )
        )
        tokens_used += req.estimated_tokens

    if not leases:
        raise ScheduleError("budget admits no function lease")

    plan_material = {
        "schema_id": SCHEMA_ID,
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "generation": packet.generation,
        "mode": selected_mode,
        "leases": [
            {
                "cell_id": lease.cell_id,
                "function_name": lease.function_name,
                "worker_id": lease.worker_id,
                "inference_required": lease.inference_required,
                "estimated_tokens": lease.estimated_tokens,
                "authority_class": lease.authority_class,
            }
            for lease in leases
        ],
        "total_estimated_tokens": tokens_used,
        "inference_lease_count": inference_used,
    }
    return GridPlan(
        schema_id=SCHEMA_ID,
        plan_id=f"xeno-plan:{_digest(plan_material)}",
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        generation=packet.generation,
        mode=selected_mode,
        leases=tuple(leases),
        total_estimated_tokens=tokens_used,
        inference_lease_count=inference_used,
    )
