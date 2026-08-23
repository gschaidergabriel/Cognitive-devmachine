from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import Mapping, Sequence

from jspace_vector_control_v1 import encode_control

TRACE_SCHEMA = "ENTITYOS_HCU_JSPACE_GWT_TRACE/v1"
PROTOTYPE_SCHEMA = "ENTITYOS_HCU_JSPACE_GWT_PROTOTYPE/v1"
_CODEC = "JSPACE_VECTOR_CONTROL_ABI/v1"


class JSpaceGWTError(ValueError):
    pass


def _cj(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _sha(obj: object) -> str:
    return hashlib.sha256(_cj(obj).encode("utf-8")).hexdigest()


def _hex64(name: str, value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise JSpaceGWTError(f"{name} must be lowercase sha256 hex")
    return value


def _token(name: str, value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128 or any(c.isspace() for c in value):
        raise JSpaceGWTError(f"invalid {name}")
    return value


def _d01(name: str, value: object) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise JSpaceGWTError(f"invalid {name}") from exc
    if not d.is_finite() or d < 0 or d > 1:
        raise JSpaceGWTError(f"{name} must be finite in [0,1]")
    return d


@dataclass(frozen=True)
class CellSignal:
    cell_id: str
    role: str
    vector: tuple[object, ...]
    salience: object
    novelty: object
    contradiction: object
    utility: object
    resource_cost: object
    local_workspace_state_ref: str
    expected_structured_model_output: Mapping[str, object]


def _score(cell: CellSignal) -> Decimal:
    # Fixed v1 coefficients; routing evidence only, never truth confidence.
    s = _d01("salience", cell.salience)
    n = _d01("novelty", cell.novelty)
    c = _d01("contradiction", cell.contradiction)
    u = _d01("utility", cell.utility)
    r = _d01("resource_cost", cell.resource_cost)
    with localcontext() as ctx:
        ctx.prec = 60
        return Decimal("0.30") * s + Decimal("0.20") * n + Decimal("0.25") * c + Decimal("0.35") * u - Decimal("0.20") * r


def _score_text(score: Decimal) -> str:
    with localcontext() as ctx:
        ctx.prec = 60
        s = format(score.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _mean_vector(cells: Sequence[CellSignal]) -> tuple[Decimal, ...]:
    if not cells:
        return ()
    dims = len(cells[0].vector)
    if dims == 0 or any(len(c.vector) != dims for c in cells):
        raise JSpaceGWTError("selected vectors must have one non-zero shared dimension")
    with localcontext() as ctx:
        ctx.prec = 80
        out = []
        for idx in range(dims):
            vals = [Decimal(str(c.vector[idx])) for c in cells]
            if any(not v.is_finite() for v in vals):
                raise JSpaceGWTError("non-finite vector coordinate")
            out.append(sum(vals, Decimal(0)) / Decimal(len(vals)))
    return tuple(out)


def run_transition(
    *,
    generation: int,
    basis_id: str,
    entry_event_sha256: str,
    entry_admission_sha256: str,
    route_decision_sha256: str,
    grid_plan_sha256: str,
    cells: Sequence[CellSignal],
    coalition_size: int,
    hyperposition_branch_ids: Sequence[str],
    resource_budget: int,
    requested_action_class: str,
    lesion_condition: str = "NONE",
) -> dict[str, object]:
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise JSpaceGWTError("generation must be a non-negative integer")
    basis_id = _token("basis_id", basis_id)
    for name, value in (
        ("entry_event_sha256", entry_event_sha256),
        ("entry_admission_sha256", entry_admission_sha256),
        ("route_decision_sha256", route_decision_sha256),
        ("grid_plan_sha256", grid_plan_sha256),
    ):
        _hex64(name, value)
    requested_action_class = _token("requested_action_class", requested_action_class)
    lesion_condition = _token("lesion_condition", lesion_condition)
    if not cells or len(cells) > 128:
        raise JSpaceGWTError("cell count out of bounds")
    if not isinstance(coalition_size, int) or coalition_size < 1 or coalition_size > len(cells):
        raise JSpaceGWTError("invalid coalition_size")
    if not isinstance(resource_budget, int) or resource_budget < 0:
        raise JSpaceGWTError("resource_budget must be non-negative")
    ids = [_token("cell_id", c.cell_id) for c in cells]
    if len(set(ids)) != len(ids):
        raise JSpaceGWTError("duplicate cell_id")
    [_token("role", c.role) for c in cells]
    for c in cells:
        _hex64("local_workspace_state_ref", c.local_workspace_state_ref)
        if not isinstance(c.expected_structured_model_output, Mapping):
            raise JSpaceGWTError("expected_structured_model_output must be a mapping")
    branches = [_token("hyperposition_branch_id", x) for x in hyperposition_branch_ids]
    if len(set(branches)) != len(branches):
        raise JSpaceGWTError("duplicate hyperposition branch")

    ranked = sorted(((c, _score(c)) for c in cells), key=lambda item: (-item[1], item[0].cell_id))
    selected: list[CellSignal] = []
    spent = 0
    if lesion_condition != "EMPTY_BROADCAST":
        for c, _ in ranked:
            cost = max(1, int((_d01("resource_cost", c.resource_cost) * Decimal(100)).to_integral_value()))
            if spent + cost <= resource_budget and len(selected) < coalition_size:
                selected.append(c)
                spent += cost
    selected_ids = {c.cell_id for c in selected}

    competition = [
        {
            "cell_id": c.cell_id,
            "role": c.role,
            "score": _score_text(score),
            "broadcast": c.cell_id in selected_ids,
        }
        for c, score in ranked
    ]
    competition_sha256 = _sha(competition)

    global_vector = _mean_vector(selected)
    global_packet = None
    global_jspace_slice_ref = None
    if global_vector:
        gv = list(global_vector)
        if lesion_condition == "SHUFFLED_SLICE":
            gv = list(reversed(gv))
        global_packet = encode_control(
            gv,
            basis_id=basis_id,
            role="global",
            generation=generation,
            gates={"broadcast": 1},
            workspace=[f"gwt:{competition_sha256[:16]}"],
        )
        global_jspace_slice_ref = hashlib.sha256(global_packet.encode("utf-8")).hexdigest()

    traces: list[dict[str, object]] = []
    for c, _score_value in ranked:
        gate = c.cell_id in selected_ids
        packet = encode_control(
            c.vector,
            basis_id=basis_id,
            role=c.role,
            generation=generation,
            gates={"broadcast": int(gate)},
            workspace=[f"local:{c.local_workspace_state_ref[:16]}"],
        )
        packet_ref = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        trace_core = {
            "schema_version": TRACE_SCHEMA,
            "generation": generation,
            "entry_event_sha256": entry_event_sha256,
            "entry_admission_sha256": entry_admission_sha256,
            "route_decision_sha256": route_decision_sha256,
            "grid_plan_sha256": grid_plan_sha256,
            "cell_id": c.cell_id,
            "role": c.role,
            "jspace_basis_id": basis_id,
            "jspace_input_vector_ref": packet_ref,
            "jspace_input_codec_version": _CODEC,
            "local_workspace_state_ref": c.local_workspace_state_ref,
            "gwt_competition_set": competition,
            "gwt_competition_sha256": competition_sha256,
            "gwt_broadcast_gate": gate,
            "global_jspace_slice_ref": global_jspace_slice_ref,
            "hyperposition_branch_ids": branches,
            "provenance_evidence_class": "PROTOTYPE_OBSERVED_TRANSITION",
            "resource_budget": resource_budget,
            "requested_action_class": requested_action_class,
            "expected_structured_model_output": dict(c.expected_structured_model_output),
            "observed_downstream_outcome": "PROTOTYPE_TRACE_ONLY_PENDING_MODEL_EFFECT_OUTCOME",
            "falsifier_lesion_condition": lesion_condition,
            "credit_label": "SELECTED_CANDIDATE" if gate else "NOT_SELECTED_CANDIDATE",
        }
        trace = dict(trace_core)
        trace["trace_id"] = _sha(trace_core)
        traces.append(trace)

    transition_core = {
        "schema_version": PROTOTYPE_SCHEMA,
        "generation": generation,
        "basis_id": basis_id,
        "competition_sha256": competition_sha256,
        "selected_cell_ids": [c.cell_id for c in selected],
        "global_jspace_slice_ref": global_jspace_slice_ref,
        "lesion_condition": lesion_condition,
        "resource_budget": resource_budget,
        "spent_budget": spent,
        "trace_ids": [t["trace_id"] for t in traces],
    }
    return {
        **transition_core,
        "transition_id": _sha(transition_core),
        "global_jspace_packet": global_packet,
        "traces": traces,
    }


def matched_budget_lesion_rescue(**kwargs: object) -> dict[str, object]:
    baseline = run_transition(**kwargs, lesion_condition="NONE")
    lesion = run_transition(**kwargs, lesion_condition="EMPTY_BROADCAST")
    rescue = run_transition(**kwargs, lesion_condition="NONE")
    return {
        "schema_version": "ENTITYOS_HCU_JSPACE_GWT_LESION_RESCUE/v1",
        "baseline_transition_id": baseline["transition_id"],
        "lesion_transition_id": lesion["transition_id"],
        "rescue_transition_id": rescue["transition_id"],
        "baseline_selected": baseline["selected_cell_ids"],
        "lesion_selected": lesion["selected_cell_ids"],
        "rescue_selected": rescue["selected_cell_ids"],
        "baseline_slice": baseline["global_jspace_slice_ref"],
        "lesion_slice": lesion["global_jspace_slice_ref"],
        "rescue_slice": rescue["global_jspace_slice_ref"],
        "matched_resource_budget": baseline["resource_budget"] == lesion["resource_budget"] == rescue["resource_budget"],
        "lesion_changed_broadcast": baseline["selected_cell_ids"] != lesion["selected_cell_ids"],
        "rescue_exact": baseline["transition_id"] == rescue["transition_id"],
    }
