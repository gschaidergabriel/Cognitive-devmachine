#!/usr/bin/env python3
"""Instrumented Global J-Space/GWT transition prototype for EntityOS/HCU.

The prototype is deterministic telemetry/control plumbing around the current Entry -> Route
-> GRID10 path. It does not inspect or claim model-hidden-state truth, does not persist a
second entity state, and cannot grant effects/capabilities. Its purpose is to emit exact,
machine-checkable transition traces suitable for causal controls and later training-data
compilation once a real local model/J-Lens observer supplies measured vectors/outcomes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        CODEC_SCHEMA,
        CONTROL_CONDITIONS,
        VectorControlPacket,
        validate_packet,
    )
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from jspace_vector_control_v1 import ABI_SCHEMA, CODEC_SCHEMA, CONTROL_CONDITIONS, VectorControlPacket, validate_packet
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision
    from xeno_entry_fabric_v1 import EntryPacket

TRACE_SCHEMA = "JSPACE_GWT_TRANSITION_TRACE/v1"
SELECTOR_SCHEMA = "JSPACE_GWT_SELECTOR/v1"
SCORE_DENOMINATOR = 100_000
DEFAULT_BROADCAST_THRESHOLD = 50_000
DEFAULT_MAX_SLOTS = 3
MAX_COMPETITORS = 32
EVIDENCE_CLASSES = frozenset({
    "MEASURED_INTERPRETABILITY",
    "DETERMINISTIC_CONTROL",
    "VERIFIED_OUTCOME",
    "SYNTHETIC_HARD_NEGATIVE",
})
CREDIT_LABELS = frozenset({"POSITIVE", "NEGATIVE", "NEUTRAL", "UNKNOWN"})


class JSpaceGWTError(ValueError):
    pass


@dataclass(frozen=True)
class GWTCompetitor:
    candidate_id: str
    role: str
    salience_bp: int
    novelty_bp: int
    contradiction_bp: int
    task_relevance_bp: int
    evidence_ref: str
    evidence_sha256: str


@dataclass(frozen=True)
class GWTCompetitionRecord:
    candidate_id: str
    role: str
    score: int
    selected: bool
    evidence_ref: str
    evidence_sha256: str


@dataclass(frozen=True)
class GWTSelection:
    schema: str
    max_slots: int
    broadcast_threshold: int
    competition_set: tuple[GWTCompetitionRecord, ...]
    winner_ids: tuple[str, ...]
    broadcast_gate: bool
    selection_sha256: str


@dataclass(frozen=True)
class JSpaceGWTTransitionTrace:
    schema_version: str
    trace_id: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    jspace_input_vector_ref: str
    jspace_input_codec_version: str
    jspace_vector_control_abi: str
    local_workspace_state_ref: str
    gwt_selector_schema: str
    gwt_selection_sha256: str
    gwt_competition_set: tuple[GWTCompetitionRecord, ...]
    gwt_winner_ids: tuple[str, ...]
    gwt_broadcast_gate: bool
    global_jspace_slice_ref: str
    hyperposition_branch_ids: tuple[str, ...]
    evidence_class: str
    resource_budget: tuple[tuple[str, int], ...]
    requested_action_class: str
    expected_structured_model_output: Mapping[str, Any]
    observed_downstream_outcome: Mapping[str, Any]
    falsifier_lesion_condition: str
    credit_label: str
    trace_sha256: str


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceGWTError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceGWTError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceGWTError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _nonnegative_safe_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceGWTError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceGWTError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _basis_points(value: Any, field: str) -> int:
    value = _nonnegative_safe_int(value, field)
    if value > 10_000:
        raise JSpaceGWTError(f"{field}:BASIS_POINTS_OUT_OF_RANGE")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceGWTError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _mapping(value: Any, field: str, *, max_bytes: int = 16_384) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceGWTError(f"{field}:MAPPING_REQUIRED")
    try:
        raw = canonicalize(dict(value))
    except CanonicalizationError as exc:
        raise JSpaceGWTError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    if len(raw) > max_bytes:
        raise JSpaceGWTError(f"{field}:CANONICAL_BYTES_TOO_LARGE")
    return dict(value)


def _competitor(value: GWTCompetitor) -> GWTCompetitor:
    if not isinstance(value, GWTCompetitor):
        raise JSpaceGWTError("GWT_COMPETITOR_REQUIRED")
    return GWTCompetitor(
        candidate_id=_text(value.candidate_id, "candidate_id"),
        role=_text(value.role, "candidate.role"),
        salience_bp=_basis_points(value.salience_bp, "candidate.salience_bp"),
        novelty_bp=_basis_points(value.novelty_bp, "candidate.novelty_bp"),
        contradiction_bp=_basis_points(value.contradiction_bp, "candidate.contradiction_bp"),
        task_relevance_bp=_basis_points(value.task_relevance_bp, "candidate.task_relevance_bp"),
        evidence_ref=_text(value.evidence_ref, "candidate.evidence_ref"),
        evidence_sha256=_sha256(value.evidence_sha256, "candidate.evidence_sha256"),
    )


def _competition_score(value: GWTCompetitor) -> int:
    # Fixed v1 weights: salience 30%, novelty 20%, contradiction 20%, task relevance 30%.
    return (
        3 * value.salience_bp
        + 2 * value.novelty_bp
        + 2 * value.contradiction_bp
        + 3 * value.task_relevance_bp
    )


def select_gwt(
    competitors: Sequence[GWTCompetitor],
    *,
    max_slots: int = DEFAULT_MAX_SLOTS,
    broadcast_threshold: int = DEFAULT_BROADCAST_THRESHOLD,
) -> GWTSelection:
    """Select a bounded workspace coalition with deterministic tie-breaking.

    There is no majority-vote truth rule: candidate count never changes a candidate's score.
    """
    if isinstance(competitors, (str, bytes, bytearray)) or not isinstance(competitors, Sequence):
        raise JSpaceGWTError("GWT_COMPETITOR_SEQUENCE_REQUIRED")
    if not 1 <= len(competitors) <= MAX_COMPETITORS:
        raise JSpaceGWTError("GWT_COMPETITOR_COUNT_OUT_OF_RANGE")
    if isinstance(max_slots, bool) or not isinstance(max_slots, int) or not 1 <= max_slots <= 8:
        raise JSpaceGWTError("GWT_MAX_SLOTS_OUT_OF_RANGE")
    if isinstance(broadcast_threshold, bool) or not isinstance(broadcast_threshold, int) or not 0 <= broadcast_threshold <= SCORE_DENOMINATOR:
        raise JSpaceGWTError("GWT_BROADCAST_THRESHOLD_OUT_OF_RANGE")

    normalized = tuple(_competitor(value) for value in competitors)
    candidate_ids = [value.candidate_id for value in normalized]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise JSpaceGWTError("GWT_DUPLICATE_CANDIDATE_ID_FORBIDDEN")
    ranked = sorted(
        ((-_competition_score(value), value.candidate_id, value) for value in normalized),
        key=lambda row: (row[0], row[1]),
    )
    winners = tuple(row[2].candidate_id for row in ranked[:min(max_slots, len(ranked))])
    winner_set = set(winners)
    records = tuple(
        GWTCompetitionRecord(
            candidate_id=row[2].candidate_id,
            role=row[2].role,
            score=-row[0],
            selected=row[2].candidate_id in winner_set,
            evidence_ref=row[2].evidence_ref,
            evidence_sha256=row[2].evidence_sha256,
        )
        for row in ranked
    )
    broadcast_gate = bool(records and records[0].score >= broadcast_threshold)
    material = {
        "schema": SELECTOR_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "max_slots": max_slots,
        "broadcast_threshold": broadcast_threshold,
        "competition_set": [asdict(record) for record in records],
        "winner_ids": list(winners),
        "broadcast_gate": broadcast_gate,
    }
    return GWTSelection(
        schema=SELECTOR_SCHEMA,
        max_slots=max_slots,
        broadcast_threshold=broadcast_threshold,
        competition_set=records,
        winner_ids=winners,
        broadcast_gate=broadcast_gate,
        selection_sha256=_canonical_sha256(material, "GWT_SELECTION"),
    )


def _bind_causal_path(
    packet: EntryPacket,
    decision: RouteDecision,
    plan: GridPlan,
    vector_packet: VectorControlPacket,
    *,
    current_generation: int,
    cell_id: str,
    role: str,
) -> None:
    if not isinstance(packet, EntryPacket):
        raise JSpaceGWTError("ENTRY_PACKET_REQUIRED")
    if not isinstance(decision, RouteDecision):
        raise JSpaceGWTError("ROUTE_DECISION_REQUIRED")
    if not isinstance(plan, GridPlan):
        raise JSpaceGWTError("GRID_PLAN_REQUIRED")
    validate_packet(vector_packet)
    current_generation = _nonnegative_safe_int(current_generation, "current_generation")
    if packet.entity_generation != current_generation or plan.entity_generation != current_generation or vector_packet.generation != current_generation:
        raise JSpaceGWTError("STALE_JSPACE_TRANSITION_GENERATION")
    if HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA or decision.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceGWTError("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if plan.schema != PLAN_SCHEMA or plan.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceGWTError("GRID_PLAN_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if plan.entry_binding_schema != ENTRY_BINDING_SCHEMA:
        raise JSpaceGWTError("GRID_PLAN_ENTRY_BINDING_SCHEMA_UNSUPPORTED")

    expected = {
        "decision.event_sha256": (decision.event_sha256, packet.event_sha256),
        "decision.entry_admission_sha256": (decision.entry_admission_sha256, packet.admission_sha256),
        "plan.entry_event_sha256": (plan.entry_event_sha256, packet.event_sha256),
        "plan.entry_admission_sha256": (plan.entry_admission_sha256, packet.admission_sha256),
        "plan.route_event_sha256": (plan.route_event_sha256, decision.event_sha256),
        "plan.route_decision_sha256": (plan.route_decision_sha256, decision.decision_sha256),
        "plan.router_policy_sha256": (plan.router_policy_sha256, decision.router_policy_sha256),
        "plan.engine_identity_sha256": (plan.engine_identity_sha256, decision.engine_identity_sha256),
    }
    for field, (observed, wanted) in expected.items():
        if observed != wanted:
            raise JSpaceGWTError(f"CAUSAL_PATH_IDENTITY_MISMATCH:{field}")

    cell_id = _text(cell_id, "cell_id")
    role = _text(role, "role")
    matches = [cell for cell in plan.cells if cell.cell_id == cell_id]
    if len(matches) != 1:
        raise JSpaceGWTError("GRID_CELL_ID_NOT_UNIQUE_OR_MISSING")
    cell = matches[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise JSpaceGWTError("JSPACE_TRACE_REQUIRES_MODEL_CELL")
    if cell.function != f"MODEL:{role}":
        raise JSpaceGWTError("JSPACE_ROLE_GRID_CELL_MISMATCH")
    if vector_packet.role != role:
        raise JSpaceGWTError("JSPACE_ROLE_VECTOR_PACKET_MISMATCH")


def _resource_budget(value: Mapping[str, Any], *, plan: GridPlan, cell_id: str) -> tuple[tuple[str, int], ...]:
    value = _mapping(value, "resource_budget", max_bytes=2048)
    required = {"max_model_calls", "max_tokens", "max_wall_ms"}
    if set(value) == required:
        raise JSpaceGWTError("RESOURCE_BUDGET_SCHEMA_MISMATCH")
    required = {"model_tokens", "wall_ms"}
    if set(value) != required:
        raise JSpaceGWTError("RESOURCE_BUDGET_SCHEMA_MISMATCH")
    model_tokens = _nonnegative_safe_int(value["model_tokens"], "resource_budget.model_tokens")
    wall_ms = _nonnegative_safe_int(value["wall_ms"], "resource_budget.wall_ms")
    cell = next(cell for cell in plan.cells if cell.cell_id == cell_id)
    if model_tokens > cell.model_token_budget:
        raise JSpaceGWTError("RESOURCE_BUDGET_MODEL_TOKENS_EXCEEDED")
    if wall_ms > plan.max_wall_ms:
        raise JSpaceGWTError("RESOURCE_BUDGET_WALL_MS_EXCEEDED")
    return (("model_tokens", model_tokens), ("wall_ms", wall_ms))


def make_transition_trace(
    *,
    trace_id: str,
    packet: EntryPacket,
    decision: RouteDecision,
    plan: GridPlan,
    vector_packet: VectorControlPacket,
    current_generation: int,
    cell_id: str,
    role: str,
    local_workspace_state_ref: str,
    competitors: Sequence[GWTCompetitor],
    global_jspace_slice_ref: str,
    hyperposition_branch_ids: Sequence[str],
    evidence_class: str,
    resource_budget: Mapping[str, Any],
    requested_action_class: str,
    expected_structured_model_output: Mapping[str, Any],
    observed_downstream_outcome: Mapping[str, Any],
    credit_label: str,
    max_slots: int = DEFAULT_MAX_SLOTS,
    broadcast_threshold: int = DEFAULT_BROADCAST_THRESHOLD,
) -> JSpaceGWTTransitionTrace:
    """Emit one immutable observable transition trace for later causal evaluation/training.

    Transition trace v1 intentionally fixes selector parameters to the declared v1 defaults.
    The trace schema does not persist alternative selector parameters, so accepting custom
    values here would create an unreconstructable selector digest after deserialization.
    """
    trace_id = _text(trace_id, "trace_id")
    role = _text(role, "role")
    cell_id = _text(cell_id, "cell_id")
    _bind_causal_path(
        packet,
        decision,
        plan,
        vector_packet,
        current_generation=current_generation,
        cell_id=cell_id,
        role=role,
    )
    if evidence_class not in EVIDENCE_CLASSES:
        raise JSpaceGWTError("evidence_class:UNSUPPORTED")
    if credit_label not in CREDIT_LABELS:
        raise JSpaceGWTError("credit_label:UNSUPPORTED")
    if isinstance(hyperposition_branch_ids, (str, bytes, bytearray)) or not isinstance(hyperposition_branch_ids, Sequence):
        raise JSpaceGWTError("HYPERPOSITION_BRANCH_SEQUENCE_REQUIRED")
    branches = tuple(_text(value, "hyperposition_branch_id") for value in hyperposition_branch_ids)
    if len(branches) != len(set(branches)):
        raise JSpaceGWTError("HYPERPOSITION_DUPLICATE_BRANCH_FORBIDDEN")
    if len(branches) > 32:
        raise JSpaceGWTError("HYPERPOSITION_BRANCH_COUNT_EXCEEDED")
    if max_slots != DEFAULT_MAX_SLOTS or broadcast_threshold != DEFAULT_BROADCAST_THRESHOLD:
        raise JSpaceGWTError("GWT_TRACE_V1_SELECTOR_PARAMETERS_FIXED")

    selection = select_gwt(
        competitors,
        max_slots=DEFAULT_MAX_SLOTS,
        broadcast_threshold=DEFAULT_BROADCAST_THRESHOLD,
    )
    budget = _resource_budget(resource_budget, plan=plan, cell_id=cell_id)
    expected_output = _mapping(expected_structured_model_output, "expected_structured_model_output")
    observed_outcome = _mapping(observed_downstream_outcome, "observed_downstream_outcome")
    material = {
        "schema_version": TRACE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "trace_id": trace_id,
        "generation": current_generation,
        "entry_event_sha256": _sha256(packet.event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(packet.admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(decision.decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(plan.plan_sha256, "grid_plan_sha256"),
        "cell_id": cell_id,
        "role": role,
        "jspace_basis_id": vector_packet.basis_id,
        "jspace_basis_sha256": vector_packet.basis_sha256,
        "jspace_input_vector_ref": f"sha256:{vector_packet.packet_sha256}",
        "jspace_input_codec_version": CODEC_SCHEMA,
        "jspace_vector_control_abi": ABI_SCHEMA,
        "local_workspace_state_ref": _text(local_workspace_state_ref, "local_workspace_state_ref"),
        "gwt_selector_schema": SELECTOR_SCHEMA,
        "gwt_selection_sha256": selection.selection_sha256,
        "gwt_competition_set": [asdict(record) for record in selection.competition_set],
        "gwt_winner_ids": list(selection.winner_ids),
        "gwt_broadcast_gate": selection.broadcast_gate,
        "global_jspace_slice_ref": _text(global_jspace_slice_ref, "global_jspace_slice_ref"),
        "hyperposition_branch_ids": list(branches),
        "evidence_class": evidence_class,
        "resource_budget": dict(budget),
        "requested_action_class": _text(requested_action_class, "requested_action_class"),
        "expected_structured_model_output": dict(expected_output),
        "observed_downstream_outcome": dict(observed_outcome),
        "falsifier_lesion_condition": vector_packet.control_condition,
        "credit_label": credit_label,
    }
    trace_sha256 = _canonical_sha256(material, "JSPACE_GWT_TRANSITION_TRACE")
    return JSpaceGWTTransitionTrace(
        schema_version=TRACE_SCHEMA,
        trace_id=trace_id,
        generation=current_generation,
        entry_event_sha256=material["entry_event_sha256"],
        entry_admission_sha256=material["entry_admission_sha256"],
        route_decision_sha256=material["route_decision_sha256"],
        grid_plan_sha256=material["grid_plan_sha256"],
        cell_id=cell_id,
        role=role,
        jspace_basis_id=vector_packet.basis_id,
        jspace_basis_sha256=vector_packet.basis_sha256,
        jspace_input_vector_ref=material["jspace_input_vector_ref"],
        jspace_input_codec_version=CODEC_SCHEMA,
        jspace_vector_control_abi=ABI_SCHEMA,
        local_workspace_state_ref=material["local_workspace_state_ref"],
        gwt_selector_schema=SELECTOR_SCHEMA,
        gwt_selection_sha256=selection.selection_sha256,
        gwt_competition_set=selection.competition_set,
        gwt_winner_ids=selection.winner_ids,
        gwt_broadcast_gate=selection.broadcast_gate,
        global_jspace_slice_ref=material["global_jspace_slice_ref"],
        hyperposition_branch_ids=branches,
        evidence_class=evidence_class,
        resource_budget=budget,
        requested_action_class=material["requested_action_class"],
        expected_structured_model_output=expected_output,
        observed_downstream_outcome=observed_outcome,
        falsifier_lesion_condition=vector_packet.control_condition,
        credit_label=credit_label,
        trace_sha256=trace_sha256,
    )


def trace_material(trace: JSpaceGWTTransitionTrace) -> dict[str, Any]:
    if not isinstance(trace, JSpaceGWTTransitionTrace):
        raise JSpaceGWTError("JSPACE_GWT_TRANSITION_TRACE_REQUIRED")
    material = asdict(trace)
    material.pop("trace_sha256", None)
    material["canonicalization_schema"] = CANONICALIZATION_SCHEMA
    material["gwt_competition_set"] = [asdict(value) for value in trace.gwt_competition_set]
    material["gwt_winner_ids"] = list(trace.gwt_winner_ids)
    material["hyperposition_branch_ids"] = list(trace.hyperposition_branch_ids)
    material["resource_budget"] = dict(trace.resource_budget)
    return material


def _canonical_trace_text(value: Any, field: str, *, max_len: int = 1024) -> str:
    normalized = _text(value, field, max_len=max_len)
    if value != normalized:
        raise JSpaceGWTError(f"{field}:NONCANONICAL_WHITESPACE")
    return normalized


def _validate_trace_competition(trace: JSpaceGWTTransitionTrace) -> None:
    records = trace.gwt_competition_set
    if not isinstance(records, tuple) or not 1 <= len(records) <= MAX_COMPETITORS:
        raise JSpaceGWTError("GWT_COMPETITION_SET_INVALID")
    seen: set[str] = set()
    selected_ids: list[str] = []
    previous_key: tuple[int, str] | None = None
    selection_closed = False
    for record in records:
        if not isinstance(record, GWTCompetitionRecord):
            raise JSpaceGWTError("GWT_COMPETITION_RECORD_REQUIRED")
        candidate_id = _canonical_trace_text(record.candidate_id, "gwt_record.candidate_id")
        _canonical_trace_text(record.role, "gwt_record.role")
        score = _nonnegative_safe_int(record.score, "gwt_record.score")
        if score > SCORE_DENOMINATOR:
            raise JSpaceGWTError("GWT_COMPETITION_SCORE_OUT_OF_RANGE")
        if not isinstance(record.selected, bool):
            raise JSpaceGWTError("GWT_COMPETITION_SELECTED_BOOL_REQUIRED")
        _canonical_trace_text(record.evidence_ref, "gwt_record.evidence_ref")
        _sha256(record.evidence_sha256, "gwt_record.evidence_sha256")
        if candidate_id in seen:
            raise JSpaceGWTError("GWT_DUPLICATE_CANDIDATE_ID_FORBIDDEN")
        seen.add(candidate_id)
        key = (-score, candidate_id)
        if previous_key is not None and key < previous_key:
            raise JSpaceGWTError("GWT_COMPETITION_ORDER_INVALID")
        previous_key = key
        if record.selected:
            if selection_closed:
                raise JSpaceGWTError("GWT_SELECTED_RECORDS_MUST_BE_PREFIX")
            selected_ids.append(candidate_id)
        else:
            selection_closed = True

    winners = trace.gwt_winner_ids
    if not isinstance(winners, tuple) or not 1 <= len(winners) <= 8:
        raise JSpaceGWTError("GWT_WINNER_IDS_INVALID")
    normalized_winners = tuple(_canonical_trace_text(value, "gwt_winner_id") for value in winners)
    if len(set(normalized_winners)) != len(normalized_winners):
        raise JSpaceGWTError("GWT_DUPLICATE_WINNER_ID_FORBIDDEN")
    if normalized_winners != tuple(selected_ids):
        raise JSpaceGWTError("GWT_WINNER_SELECTION_MISMATCH")
    if not isinstance(trace.gwt_broadcast_gate, bool):
        raise JSpaceGWTError("GWT_BROADCAST_GATE_BOOL_REQUIRED")


def _validate_trace_selector(trace: JSpaceGWTTransitionTrace) -> None:
    """Reconstruct the complete v1 selector preimage from persisted trace material.

    v1 has no fields for custom selector parameters, therefore DEFAULT_MAX_SLOTS and
    DEFAULT_BROADCAST_THRESHOLD are part of the trace contract. Any old self-consistent v1
    trace produced with custom selector parameters is intentionally rejected: its selector
    identity cannot be independently reconstructed from its persisted preimage.
    """
    _validate_trace_competition(trace)
    records = trace.gwt_competition_set
    expected_count = min(DEFAULT_MAX_SLOTS, len(records))
    selected_count = sum(1 for record in records if record.selected)
    if selected_count != expected_count:
        raise JSpaceGWTError("GWT_SELECTOR_MAX_SLOTS_MISMATCH")

    expected_winners = tuple(record.candidate_id for record in records[:expected_count])
    if trace.gwt_winner_ids != expected_winners:
        raise JSpaceGWTError("GWT_SELECTOR_WINNER_PREFIX_MISMATCH")

    expected_gate = records[0].score >= DEFAULT_BROADCAST_THRESHOLD
    if trace.gwt_broadcast_gate != expected_gate:
        raise JSpaceGWTError("GWT_BROADCAST_GATE_THRESHOLD_MISMATCH")

    material = {
        "schema": SELECTOR_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "max_slots": DEFAULT_MAX_SLOTS,
        "broadcast_threshold": DEFAULT_BROADCAST_THRESHOLD,
        "competition_set": [asdict(record) for record in records],
        "winner_ids": list(trace.gwt_winner_ids),
        "broadcast_gate": trace.gwt_broadcast_gate,
    }
    expected_selection_sha256 = _canonical_sha256(material, "GWT_SELECTION")
    observed_selection_sha256 = _sha256(trace.gwt_selection_sha256, "gwt_selection_sha256")
    if observed_selection_sha256 != expected_selection_sha256:
        raise JSpaceGWTError("GWT_SELECTION_DIGEST_MISMATCH")


def _validate_trace_resource_budget(value: Any) -> None:
    if not isinstance(value, tuple) or len(value) != 2:
        raise JSpaceGWTError("RESOURCE_BUDGET_CANONICAL_TUPLE_REQUIRED")
    expected_keys = ("model_tokens", "wall_ms")
    keys: list[str] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise JSpaceGWTError("RESOURCE_BUDGET_CANONICAL_PAIR_REQUIRED")
        key, amount = item
        key = _canonical_trace_text(key, "resource_budget.key", max_len=64)
        keys.append(key)
        _nonnegative_safe_int(amount, f"resource_budget.{key}")
    if tuple(keys) != expected_keys:
        raise JSpaceGWTError("RESOURCE_BUDGET_SCHEMA_MISMATCH")


def validate_transition_trace(trace: JSpaceGWTTransitionTrace) -> None:
    """Fail closed on both semantic shape and digest identity of a persisted/training trace.

    A matching hash proves identity only. It must not turn a caller-constructed invalid trace
    into admitted training evidence. This validator therefore rechecks every self-contained
    v1 invariant that can be established from the trace before accepting its digest.
    """
    if not isinstance(trace, JSpaceGWTTransitionTrace):
        raise JSpaceGWTError("JSPACE_GWT_TRANSITION_TRACE_REQUIRED")
    if trace.schema_version != TRACE_SCHEMA:
        raise JSpaceGWTError("JSPACE_TRACE_SCHEMA_UNSUPPORTED")
    _canonical_trace_text(trace.trace_id, "trace_id")
    _nonnegative_safe_int(trace.generation, "generation")
    _sha256(trace.entry_event_sha256, "entry_event_sha256")
    _sha256(trace.entry_admission_sha256, "entry_admission_sha256")
    _sha256(trace.route_decision_sha256, "route_decision_sha256")
    _sha256(trace.grid_plan_sha256, "grid_plan_sha256")
    _canonical_trace_text(trace.cell_id, "cell_id")
    _canonical_trace_text(trace.role, "role")
    _canonical_trace_text(trace.jspace_basis_id, "jspace_basis_id")
    _sha256(trace.jspace_basis_sha256, "jspace_basis_sha256")
    vector_ref = _canonical_trace_text(trace.jspace_input_vector_ref, "jspace_input_vector_ref")
    if not vector_ref.startswith("sha256:"):
        raise JSpaceGWTError("JSPACE_INPUT_VECTOR_REF_SHA256_REQUIRED")
    _sha256(vector_ref[7:], "jspace_input_vector_ref.digest")
    if trace.jspace_input_codec_version != CODEC_SCHEMA:
        raise JSpaceGWTError("JSPACE_INPUT_CODEC_VERSION_UNSUPPORTED")
    if trace.jspace_vector_control_abi != ABI_SCHEMA:
        raise JSpaceGWTError("JSPACE_VECTOR_CONTROL_ABI_UNSUPPORTED")
    _canonical_trace_text(trace.local_workspace_state_ref, "local_workspace_state_ref")
    if trace.gwt_selector_schema != SELECTOR_SCHEMA:
        raise JSpaceGWTError("GWT_SELECTOR_SCHEMA_UNSUPPORTED")
    _validate_trace_selector(trace)
    _canonical_trace_text(trace.global_jspace_slice_ref, "global_jspace_slice_ref")
    if not isinstance(trace.hyperposition_branch_ids, tuple) or len(trace.hyperposition_branch_ids) > 32:
        raise JSpaceGWTError("HYPERPOSITION_BRANCH_SEQUENCE_REQUIRED")
    branches = tuple(_canonical_trace_text(value, "hyperposition_branch_id") for value in trace.hyperposition_branch_ids)
    if len(branches) != len(set(branches)):
        raise JSpaceGWTError("HYPERPOSITION_DUPLICATE_BRANCH_FORBIDDEN")
    if trace.evidence_class not in EVIDENCE_CLASSES:
        raise JSpaceGWTError("evidence_class:UNSUPPORTED")
    _validate_trace_resource_budget(trace.resource_budget)
    _canonical_trace_text(trace.requested_action_class, "requested_action_class")
    _mapping(trace.expected_structured_model_output, "expected_structured_model_output")
    _mapping(trace.observed_downstream_outcome, "observed_downstream_outcome")
    if trace.falsifier_lesion_condition not in CONTROL_CONDITIONS:
        raise JSpaceGWTError("falsifier_lesion_condition:UNSUPPORTED")
    if trace.credit_label not in CREDIT_LABELS:
        raise JSpaceGWTError("credit_label:UNSUPPORTED")

    material = trace_material(trace)
    observed = _sha256(trace.trace_sha256, "trace_sha256")
    expected = _canonical_sha256(material, "JSPACE_GWT_TRANSITION_TRACE")
    if observed != expected:
        raise JSpaceGWTError("JSPACE_TRACE_DIGEST_MISMATCH")
