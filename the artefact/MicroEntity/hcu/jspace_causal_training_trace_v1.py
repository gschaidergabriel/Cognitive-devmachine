from __future__ import annotations

"""Read-only causal binder for EntityOS/HCU J-Space training traces.

This module mints no truth, route, compute, effect, loader, or training authority. It only
cross-binds already-produced Typed Entry, HCU RouteDecision, GRID10 plan, candidate
InferenceReceipt, and Global J-Space/GWT step into one machine-checkable causal trace.
"""

import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from .global_jspace_gwt_v1 import JSpaceStep, TRACE_SCHEMA as JSPACE_TRACE_SCHEMA
    from .grid10_scheduler_v1 import GridPlan, PLAN_SCHEMA
    from .inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_SCHEMA
    from .reactive_event_router_v1 import RouteDecision
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from global_jspace_gwt_v1 import JSpaceStep, TRACE_SCHEMA as JSPACE_TRACE_SCHEMA
    from grid10_scheduler_v1 import GridPlan, PLAN_SCHEMA
    from inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_SCHEMA
    from reactive_event_router_v1 import RouteDecision
    from xeno_entry_fabric_v1 import EntryPacket


TRACE_SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_TRAINING_TRACE/v1"
AUTHORITY = "CANDIDATE_TRAINING_EVIDENCE_ONLY_NOT_TRUTH_EFFECT_ROUTE_OR_COMPUTE"
CREDIT_LABELS = frozenset(
    {
        "NO_RUNTIME_CREDIT",
        "VERIFIED_TASK_OUTCOME",
        "NEGATIVE_VERIFIED_OUTCOME",
        "ABSTAINED",
    }
)


class CausalTrainingTraceError(ValueError):
    pass


def _text(value: Any, field: str, *, max_bytes: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CausalTrainingTraceError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value.encode("utf-8", "strict")) > max_bytes:
        raise CausalTrainingTraceError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_bytes=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise CausalTrainingTraceError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _json_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CausalTrainingTraceError(f"{field}:MAPPING_REQUIRED")
    material = dict(value)
    try:
        canonicalize(material)
    except CanonicalizationError as exc:
        raise CausalTrainingTraceError(f"{field}:CANONICAL_JSON_REQUIRED:{exc}") from exc
    return material


def _trace_digest(value: Mapping[str, Any]) -> str:
    try:
        return hashlib.sha256(canonicalize(dict(value))).hexdigest()
    except CanonicalizationError as exc:
        raise CausalTrainingTraceError(f"TRACE_CANONICALIZATION_FAILED:{exc}") from exc


def _verify_jspace_step(step: JSpaceStep) -> None:
    if not isinstance(step, JSpaceStep):
        raise CausalTrainingTraceError("JSPACE_STEP_REQUIRED")
    if step.trace.get("schema") != JSPACE_TRACE_SCHEMA:
        raise CausalTrainingTraceError("JSPACE_TRACE_SCHEMA_MISMATCH")
    observed = _sha256(step.trace_sha256, "jspace.trace_sha256")
    if _trace_digest(step.trace) != observed:
        raise CausalTrainingTraceError("JSPACE_TRACE_DIGEST_MISMATCH")
    if step.trace.get("generation") != step.generation:
        raise CausalTrainingTraceError("JSPACE_TRACE_GENERATION_MISMATCH")
    if step.trace.get("basis_id") != step.basis_id:
        raise CausalTrainingTraceError("JSPACE_TRACE_BASIS_ID_MISMATCH")
    if step.trace.get("basis_sha256") != step.basis_sha256:
        raise CausalTrainingTraceError("JSPACE_TRACE_BASIS_SHA256_MISMATCH")
    if step.trace.get("winner_cell_id") != step.winner_cell_id:
        raise CausalTrainingTraceError("JSPACE_TRACE_WINNER_CELL_MISMATCH")
    if step.trace.get("winner_role") != step.winner_role:
        raise CausalTrainingTraceError("JSPACE_TRACE_WINNER_ROLE_MISMATCH")


def bind_causal_training_trace(
    entry: EntryPacket,
    route: RouteDecision,
    grid_plan: GridPlan,
    inference: InferenceReceipt,
    jspace: JSpaceStep,
    *,
    local_workspace_state_ref: str,
    jspace_input_vector_ref: str,
    requested_action_class: str,
    expected_structured_model_output: Mapping[str, Any],
    observed_downstream_outcome: Mapping[str, Any],
    falsifier_or_lesion_condition: str,
    evidence_class: str,
    credit_label: str = "NO_RUNTIME_CREDIT",
) -> dict[str, Any]:
    """Cross-bind one causal training trace without creating upstream authority."""
    if not isinstance(entry, EntryPacket):
        raise CausalTrainingTraceError("ENTRY_PACKET_REQUIRED")
    if not isinstance(route, RouteDecision):
        raise CausalTrainingTraceError("ROUTE_DECISION_REQUIRED")
    if not isinstance(grid_plan, GridPlan):
        raise CausalTrainingTraceError("GRID_PLAN_REQUIRED")
    if not isinstance(inference, InferenceReceipt):
        raise CausalTrainingTraceError("INFERENCE_RECEIPT_REQUIRED")
    _verify_jspace_step(jspace)

    if grid_plan.schema != PLAN_SCHEMA:
        raise CausalTrainingTraceError("GRID_PLAN_SCHEMA_MISMATCH")
    if inference.schema != INFERENCE_SCHEMA:
        raise CausalTrainingTraceError("INFERENCE_SCHEMA_MISMATCH")

    generations = {entry.entity_generation, grid_plan.entity_generation, inference.entity_generation, jspace.generation}
    if len(generations) != 1:
        raise CausalTrainingTraceError("CAUSAL_GENERATION_MISMATCH")

    entry_event = _sha256(entry.event_sha256, "entry.event_sha256")
    entry_admission = _sha256(entry.admission_sha256, "entry.admission_sha256")
    route_event = _sha256(route.event_sha256, "route.event_sha256")
    route_decision = _sha256(route.decision_sha256, "route.decision_sha256")
    grid_sha = _sha256(grid_plan.plan_sha256, "grid_plan.plan_sha256")
    inference_sha = _sha256(inference.receipt_sha256, "inference.receipt_sha256")

    if route_event != entry_event:
        raise CausalTrainingTraceError("ROUTE_ENTRY_EVENT_MISMATCH")
    if route.entry_admission_sha256 != entry_admission:
        raise CausalTrainingTraceError("ROUTE_ENTRY_ADMISSION_MISMATCH")
    if grid_plan.entry_event_sha256 != entry_event:
        raise CausalTrainingTraceError("GRID_ENTRY_EVENT_MISMATCH")
    if grid_plan.entry_admission_sha256 != entry_admission:
        raise CausalTrainingTraceError("GRID_ENTRY_ADMISSION_MISMATCH")
    if grid_plan.route_event_sha256 != route_event:
        raise CausalTrainingTraceError("GRID_ROUTE_EVENT_MISMATCH")
    if grid_plan.route_decision_sha256 != route_decision:
        raise CausalTrainingTraceError("GRID_ROUTE_DECISION_MISMATCH")
    if inference.event_sha256 != entry_event:
        raise CausalTrainingTraceError("INFERENCE_ENTRY_EVENT_MISMATCH")
    if inference.entry_admission_sha256 != entry_admission:
        raise CausalTrainingTraceError("INFERENCE_ENTRY_ADMISSION_MISMATCH")
    if inference.decision_sha256 != route_decision:
        raise CausalTrainingTraceError("INFERENCE_ROUTE_DECISION_MISMATCH")

    if grid_plan.engine_identity_sha256 != route.engine_identity_sha256:
        raise CausalTrainingTraceError("GRID_ROUTE_ENGINE_IDENTITY_MISMATCH")
    if inference.engine_identity_sha256 != route.engine_identity_sha256:
        raise CausalTrainingTraceError("INFERENCE_ROUTE_ENGINE_IDENTITY_MISMATCH")
    if grid_plan.resolved_engine_identity != inference.resolved_engine_identity:
        raise CausalTrainingTraceError("GRID_INFERENCE_ENGINE_ID_MISMATCH")
    if grid_plan.resolved_engine_artifact_sha256 != inference.resolved_engine_artifact_sha256:
        raise CausalTrainingTraceError("GRID_INFERENCE_ENGINE_ARTIFACT_MISMATCH")

    grid_cell_ids = [cell.cell_id for cell in grid_plan.cells]
    if len(grid_cell_ids) != len(set(grid_cell_ids)):
        raise CausalTrainingTraceError("GRID_CELL_ID_DUPLICATE")
    if jspace.winner_cell_id not in set(grid_cell_ids):
        raise CausalTrainingTraceError("JSPACE_WINNER_NOT_IN_GRID_PLAN")

    competition = jspace.trace.get("contributions")
    if not isinstance(competition, list) or not competition:
        raise CausalTrainingTraceError("JSPACE_COMPETITION_SET_REQUIRED")
    competition_ids = [row.get("cell_id") for row in competition if isinstance(row, Mapping)]
    if len(competition_ids) != len(competition) or len(competition_ids) != len(set(competition_ids)):
        raise CausalTrainingTraceError("JSPACE_COMPETITION_SET_INVALID")
    if any(cell_id not in set(grid_cell_ids) for cell_id in competition_ids):
        raise CausalTrainingTraceError("JSPACE_COMPETITION_CELL_NOT_IN_GRID_PLAN")

    credit_label = _text(credit_label, "credit_label")
    if credit_label not in CREDIT_LABELS:
        raise CausalTrainingTraceError("CREDIT_LABEL_UNSUPPORTED")

    workspace_ref = _text(local_workspace_state_ref, "local_workspace_state_ref")
    input_vector_ref = _text(jspace_input_vector_ref, "jspace_input_vector_ref")
    action_class = _text(requested_action_class, "requested_action_class")
    falsifier = _text(falsifier_or_lesion_condition, "falsifier_or_lesion_condition")
    evidence_class = _text(evidence_class, "evidence_class")
    expected_output = _json_object(expected_structured_model_output, "expected_structured_model_output")
    downstream_outcome = _json_object(observed_downstream_outcome, "observed_downstream_outcome")

    material = {
        "schema": TRACE_SCHEMA,
        "generation": entry.entity_generation,
        "entry_event_sha256": entry_event,
        "entry_admission_sha256": entry_admission,
        "route_decision_sha256": route_decision,
        "grid_plan_sha256": grid_sha,
        "inference_receipt_sha256": inference_sha,
        "cell_id": jspace.winner_cell_id,
        "cell_role": jspace.winner_role,
        "jspace_basis_id": jspace.basis_id,
        "jspace_basis_sha256": _sha256(jspace.basis_sha256, "jspace.basis_sha256"),
        "jspace_input_vector_ref": input_vector_ref,
        "local_workspace_state_ref": workspace_ref,
        "gwt_competition_set": competition_ids,
        "gwt_broadcast_gate_q": jspace.winner_gate_q,
        "global_jspace_slice_ref": f"sha256:{_sha256(jspace.control_packet_sha256, 'jspace.control_packet_sha256')}",
        "hyperposition_branch_ids": list(jspace.hyperposition_cells),
        "provenance_ref": entry.provenance_ref,
        "provenance_sha256": _sha256(entry.provenance_sha256, "entry.provenance_sha256"),
        "evidence_class": evidence_class,
        "resource_budget": dict(entry.budget),
        "requested_action_class": action_class,
        "expected_structured_model_output": expected_output,
        "observed_downstream_outcome": downstream_outcome,
        "falsifier_or_lesion_condition": falsifier,
        "credit_label": credit_label,
        "jspace_trace_sha256": _sha256(jspace.trace_sha256, "jspace.trace_sha256"),
        "authority": AUTHORITY,
    }
    trace_id = _trace_digest(material)
    return {**material, "trace_id": trace_id}
