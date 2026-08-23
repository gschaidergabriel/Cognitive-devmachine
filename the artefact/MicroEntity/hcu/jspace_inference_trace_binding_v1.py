#!/usr/bin/env python3
"""Bind observable Global J-Space/GWT steps to the exact HCU causal inference spine.

This is integration/evidence plumbing only. It creates no second state, truth, reward,
engine, effect, or J-Space authority. It rejects free-floating hash labels: a training
observation is emitted only when Entry, RouteDecision, GRID10 plan, prototype vector
control, and HCU_INFERENCE_RECEIPT/v3 mutually bind to the same generation and identities.

An inference receipt proves a candidate output was causally bound to the admitted
loader/inference path; it does NOT prove task success. Therefore this bridge always emits
UNKNOWN credit. A separately verified downstream outcome must perform later crediting.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .global_jspace_gwt_v1 import JSpaceStep
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from .inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from .jspace_training_trace_v1 import TrainingTrace, build_training_trace
    from .jspace_vector_control_v1 import VectorControlPacket
    from .reactive_event_router_v1 import RouteDecision
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from global_jspace_gwt_v1 import JSpaceStep
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from jspace_training_trace_v1 import TrainingTrace, build_training_trace
    from jspace_vector_control_v1 import VectorControlPacket
    from reactive_event_router_v1 import RouteDecision
    from xeno_entry_fabric_v1 import EntryPacket


BINDING_SCHEMA = "ENTITYOS_HCU_JSPACE_INFERENCE_TRACE_BINDING/v1"


class JSpaceInferenceBindingError(ValueError):
    pass


def _canonical(value: Any, field: str) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceInferenceBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise JSpaceInferenceBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceInferenceBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceInferenceBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _plan_material(plan: GridPlan) -> dict[str, Any]:
    return {
        "schema": plan.schema,
        "canonicalization_schema": plan.canonicalization_schema,
        "entry_binding_schema": plan.entry_binding_schema,
        "ingress_id": plan.ingress_id,
        "causal_id": plan.causal_id,
        "entity_generation": plan.entity_generation,
        "entry_event_sha256": plan.entry_event_sha256,
        "entry_admission_sha256": plan.entry_admission_sha256,
        "route_event_sha256": plan.route_event_sha256,
        "route_decision_sha256": plan.route_decision_sha256,
        "router_policy_sha256": plan.router_policy_sha256,
        "engine_identity_sha256": plan.engine_identity_sha256,
        "resolved_engine_identity": plan.resolved_engine_identity,
        "resolved_engine_class": plan.resolved_engine_class,
        "resolved_engine_artifact_sha256": plan.resolved_engine_artifact_sha256,
        "capacity_receipt_sha256": plan.capacity_receipt_sha256,
        "runtime_profile_id": plan.runtime_profile_id,
        "mode": plan.mode.value,
        "logical_cell_count": plan.logical_cell_count,
        "model_call_count": plan.model_call_count,
        "physical_decoder_limit": plan.physical_decoder_limit,
        "max_wall_ms": plan.max_wall_ms,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "function": cell.function,
                "execution_class": cell.execution_class.value,
                "model_token_budget": cell.model_token_budget,
                "physical_decoder_lane": cell.physical_decoder_lane,
            }
            for cell in plan.cells
        ],
    }


def _verify_plan(plan: GridPlan) -> None:
    if not isinstance(plan, GridPlan):
        raise JSpaceInferenceBindingError("GRID_PLAN_REQUIRED")
    if plan.schema != PLAN_SCHEMA or plan.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("GRID_PLAN_SCHEMA_OR_CANONICALIZATION_MISMATCH")
    observed = _sha256(plan.plan_sha256, "grid_plan.plan_sha256")
    expected = hashlib.sha256(_canonical(_plan_material(plan), "GRID_PLAN")).hexdigest()
    if observed != expected:
        raise JSpaceInferenceBindingError("GRID_PLAN_DIGEST_MISMATCH")


def _verify_inference_receipt(
    receipt: InferenceReceipt,
    admitted_inference_receipts: Mapping[str, Mapping[str, Any]],
) -> None:
    if not isinstance(receipt, InferenceReceipt):
        raise JSpaceInferenceBindingError("INFERENCE_RECEIPT_REQUIRED")
    if receipt.schema != INFERENCE_RECEIPT_SCHEMA or receipt.status != INFERENCE_RECEIPT_STATUS:
        raise JSpaceInferenceBindingError("INFERENCE_RECEIPT_SCHEMA_OR_STATUS_MISMATCH")
    if receipt.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("INFERENCE_RECEIPT_CANONICALIZATION_MISMATCH")
    material = asdict(receipt)
    observed = _sha256(material.pop("receipt_sha256"), "inference_receipt.receipt_sha256")
    expected = hashlib.sha256(_canonical(material, "INFERENCE_RECEIPT")).hexdigest()
    if observed != expected:
        raise JSpaceInferenceBindingError("INFERENCE_RECEIPT_DIGEST_MISMATCH")
    if not isinstance(admitted_inference_receipts, Mapping):
        raise JSpaceInferenceBindingError("ADMITTED_INFERENCE_RECEIPT_REGISTRY_REQUIRED")
    admitted = admitted_inference_receipts.get(observed)
    if not isinstance(admitted, Mapping) or dict(admitted) != asdict(receipt):
        raise JSpaceInferenceBindingError("INFERENCE_RECEIPT_NOT_EXACTLY_ADMITTED")


def _assert_causal_spine(
    prototype_step: JSpaceStep,
    entry_packet: EntryPacket,
    decision: RouteDecision,
    plan: GridPlan,
    receipt: InferenceReceipt,
) -> Any:
    if not isinstance(prototype_step, JSpaceStep):
        raise JSpaceInferenceBindingError("JSPACE_STEP_REQUIRED")
    if not isinstance(entry_packet, EntryPacket):
        raise JSpaceInferenceBindingError("ENTRY_PACKET_REQUIRED")
    if not isinstance(decision, RouteDecision):
        raise JSpaceInferenceBindingError("ROUTE_DECISION_REQUIRED")

    generation = prototype_step.generation
    if (
        entry_packet.entity_generation != generation
        or plan.entity_generation != generation
        or receipt.entity_generation != generation
    ):
        raise JSpaceInferenceBindingError("CAUSAL_GENERATION_MISMATCH")

    expected = {
        "route.event_sha256": (decision.event_sha256, entry_packet.event_sha256),
        "route.entry_admission_sha256": (decision.entry_admission_sha256, entry_packet.admission_sha256),
        "plan.entry_event_sha256": (plan.entry_event_sha256, entry_packet.event_sha256),
        "plan.entry_admission_sha256": (plan.entry_admission_sha256, entry_packet.admission_sha256),
        "plan.route_event_sha256": (plan.route_event_sha256, decision.event_sha256),
        "plan.route_decision_sha256": (plan.route_decision_sha256, decision.decision_sha256),
        "plan.router_policy_sha256": (plan.router_policy_sha256, decision.router_policy_sha256),
        "plan.engine_identity_sha256": (plan.engine_identity_sha256, decision.engine_identity_sha256),
        "plan.resolved_engine_identity": (plan.resolved_engine_identity, decision.resolved_engine_identity),
        "plan.resolved_engine_class": (plan.resolved_engine_class, decision.resolved_engine_class),
        "plan.resolved_engine_artifact_sha256": (
            plan.resolved_engine_artifact_sha256,
            decision.resolved_engine_artifact_sha256,
        ),
        "receipt.entry_admission_sha256": (receipt.entry_admission_sha256, entry_packet.admission_sha256),
        "receipt.event_sha256": (receipt.event_sha256, entry_packet.event_sha256),
        "receipt.decision_sha256": (receipt.decision_sha256, decision.decision_sha256),
        "receipt.router_policy_sha256": (receipt.router_policy_sha256, decision.router_policy_sha256),
        "receipt.engine_identity_sha256": (receipt.engine_identity_sha256, decision.engine_identity_sha256),
        "receipt.resolved_engine_identity": (receipt.resolved_engine_identity, decision.resolved_engine_identity),
        "receipt.resolved_engine_class": (receipt.resolved_engine_class, decision.resolved_engine_class),
        "receipt.resolved_engine_artifact_sha256": (
            receipt.resolved_engine_artifact_sha256,
            decision.resolved_engine_artifact_sha256,
        ),
        "receipt.model_lanes": (tuple(receipt.model_lanes), tuple(decision.model_lanes)),
    }
    for field, (observed, wanted) in expected.items():
        if observed != wanted:
            raise JSpaceInferenceBindingError(f"CAUSAL_IDENTITY_MISMATCH:{field}")

    cells = [cell for cell in plan.cells if cell.cell_id == prototype_step.winner_cell_id]
    if len(cells) != 1:
        raise JSpaceInferenceBindingError("JSPACE_WINNER_GRID_CELL_NOT_UNIQUE")
    cell = cells[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise JSpaceInferenceBindingError("JSPACE_WINNER_NOT_MODEL_CELL")
    if cell.function != f"MODEL:{prototype_step.winner_role}":
        raise JSpaceInferenceBindingError("JSPACE_WINNER_ROLE_GRID_MISMATCH")
    if prototype_step.control_packet.role != prototype_step.winner_role:
        raise JSpaceInferenceBindingError("JSPACE_VECTOR_ROLE_MISMATCH")
    if prototype_step.control_packet.generation != generation:
        raise JSpaceInferenceBindingError("JSPACE_VECTOR_GENERATION_MISMATCH")
    return cell


def bind_inference_observation_trace(
    prototype_step: JSpaceStep,
    vector_control_packet: VectorControlPacket,
    *,
    entry_packet: EntryPacket,
    decision: RouteDecision,
    grid_plan: GridPlan,
    inference_receipt: InferenceReceipt,
    admitted_inference_receipts: Mapping[str, Mapping[str, Any]],
    trace_id: str,
    trace_family_id: str,
    jspace_input_vector_ref: str,
    local_workspace_state_ref: str,
    global_jspace_slice_ref: str,
    expected_structured_model_output: str,
) -> TrainingTrace:
    """Create an UNKNOWN-credit trace only after exact causal-path cross-binding.

    The resulting receipt is useful as real execution telemetry once its supplied
    InferenceReceipt itself came from an admitted runtime path. It is deliberately not
    labelled POSITIVE/NEGATIVE; semantic task credit requires a separate verified outcome.
    """
    _verify_plan(grid_plan)
    _verify_inference_receipt(inference_receipt, admitted_inference_receipts)
    cell = _assert_causal_spine(
        prototype_step,
        entry_packet,
        decision,
        grid_plan,
        inference_receipt,
    )

    observed_output = {
        "binding_schema": BINDING_SCHEMA,
        "inference_receipt_sha256": inference_receipt.receipt_sha256,
        "model_call_id": inference_receipt.model_call_id,
        "output_ref": inference_receipt.output_ref,
        "output_sha256": inference_receipt.output_sha256,
        "output_size": inference_receipt.output_size,
    }
    observed_output_text = _canonical(observed_output, "OBSERVED_INFERENCE_OUTPUT").decode("utf-8", "strict")

    return build_training_trace(
        prototype_step,
        vector_control_packet,
        trace_id=trace_id,
        trace_family_id=trace_family_id,
        entry_event_sha256=entry_packet.event_sha256,
        entry_admission_sha256=entry_packet.admission_sha256,
        route_decision_sha256=decision.decision_sha256,
        grid_plan_sha256=grid_plan.plan_sha256,
        jspace_input_vector_ref=jspace_input_vector_ref,
        local_workspace_state_ref=local_workspace_state_ref,
        global_jspace_slice_ref=global_jspace_slice_ref,
        hyperposition_branch_ids=prototype_step.hyperposition_cells,
        provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
        resource_budget={
            "max_model_calls": grid_plan.model_call_count,
            "max_tokens": cell.model_token_budget,
            "max_wall_ms": grid_plan.max_wall_ms,
        },
        requested_action_class="CANDIDATE_INFERENCE",
        expected_structured_model_output=expected_structured_model_output,
        observed_downstream_outcome=observed_output_text,
        falsifier_lesion_condition=prototype_step.control_condition,
        credit_label="UNKNOWN",
        outcome_receipt_sha256=inference_receipt.receipt_sha256,
    )
