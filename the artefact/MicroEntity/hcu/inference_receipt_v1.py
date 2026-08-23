#!/usr/bin/env python3
"""Deterministic downstream inference receipt producer for EntityOS/HCU.

This module does not invoke a model and grants no truth/effect authority. It consumes the
canonical HCU RouteDecision, then fail-closes unless the concrete Typed-Entry admission
still binds to that causal event, the route decision is independently bound to the live
entity generation, the exact engine artifact is still independently admitted, and the
runtime caller supplies a hash of the actual model-output bytes.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from reactive_event_router_v1 import (
    HASH_SERIALIZATION_SCHEMA,
    RouteDecision,
    assert_inference_echo,
)

SCHEMA = "HCU_INFERENCE_RECEIPT/v1"
STATUS = "CANDIDATE_ONLY"


class InferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceReceipt:
    schema: str
    status: str
    hash_serialization_schema: str
    entity_generation: int
    entry_admission_sha256: str
    event_sha256: str
    decision_sha256: str
    router_policy_sha256: str
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    model_lanes: tuple[str, ...]
    receipt_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise InferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise InferenceReceiptError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InferenceReceiptError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise InferenceReceiptError(f"{field}:TOO_LONG")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InferenceReceiptError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _generation(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
) -> int:
    current_generation = _nonnegative_int(current_generation, "current_generation")
    if not isinstance(admitted_route_generations, Mapping):
        raise InferenceReceiptError("ADMITTED_ROUTE_GENERATION_REGISTRY_REQUIRED")
    bound_generation = admitted_route_generations.get(decision.decision_sha256)
    if bound_generation is None:
        raise InferenceReceiptError("ROUTE_GENERATION_NOT_ADMITTED")
    bound_generation = _nonnegative_int(bound_generation, "admitted_route_generation")
    if bound_generation != current_generation:
        raise InferenceReceiptError("STALE_ROUTE_GENERATION")
    return bound_generation


def _output_size(value: Any) -> int:
    return _nonnegative_int(value, "output_size")


def make_inference_receipt(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    model_call_id: str,
    output_ref: str,
    output_sha256: str,
    output_size: int,
) -> InferenceReceipt:
    """Produce a candidate-only inference receipt from already-admitted route evidence.

    All three registries are authority/control-plane views, not values copied from the
    untrusted event: decision->generation, admission->causal-event and engine->artifact.
    For the current product path, inference without a concrete Typed Entry admission is
    intentionally rejected even though the router retains a legacy/internal script path.
    """
    if not isinstance(decision, RouteDecision):
        raise InferenceReceiptError("ROUTE_DECISION_REQUIRED")
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise InferenceReceiptError("MODEL_ACTIVATION_ROUTE_REQUIRED")
    if decision.hash_serialization_schema != HASH_SERIALIZATION_SCHEMA:
        raise InferenceReceiptError("ROUTE_SERIALIZATION_SCHEMA_UNSUPPORTED")

    generation = _generation(
        decision,
        current_generation=current_generation,
        admitted_route_generations=admitted_route_generations,
    )

    admission_sha256 = _sha256(entry_admission_sha256, "entry_admission_sha256")
    if decision.entry_admission_sha256 != admission_sha256:
        raise InferenceReceiptError("ROUTE_ENTRY_ADMISSION_IDENTITY_MISMATCH")
    if not isinstance(admitted_entry_bindings, Mapping):
        raise InferenceReceiptError("ADMITTED_ENTRY_BINDING_REGISTRY_REQUIRED")
    admitted_event_sha256 = admitted_entry_bindings.get(admission_sha256)
    if admitted_event_sha256 is None:
        raise InferenceReceiptError("ENTRY_ADMISSION_NOT_ADMITTED")
    admitted_event_sha256 = _sha256(admitted_event_sha256, "admitted_entry_event_sha256")
    if admitted_event_sha256 != decision.event_sha256:
        raise InferenceReceiptError("ENTRY_EVENT_ROUTE_IDENTITY_MISMATCH")

    engine_id = _text(decision.resolved_engine_identity, "resolved_engine_identity")
    engine_class = _text(decision.resolved_engine_class, "resolved_engine_class")
    engine_artifact_sha256 = _sha256(
        decision.resolved_engine_artifact_sha256,
        "resolved_engine_artifact_sha256",
    )
    engine_identity_sha256 = _sha256(decision.engine_identity_sha256, "engine_identity_sha256")
    if not isinstance(admitted_engine_artifacts, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    current_engine_artifact = admitted_engine_artifacts.get(engine_id)
    if current_engine_artifact is None:
        raise InferenceReceiptError("ENGINE_ARTIFACT_NOT_CURRENTLY_ADMITTED")
    current_engine_artifact = _sha256(current_engine_artifact, "admitted_engine_artifact_sha256")
    if current_engine_artifact != engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ARTIFACT_ADMISSION_MISMATCH")

    model_call_id = _text(model_call_id, "model_call_id")
    output_ref = _text(output_ref, "output_ref")
    output_sha256 = _sha256(output_sha256, "output_sha256")
    output_size = _output_size(output_size)

    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "hash_serialization_schema": decision.hash_serialization_schema,
        "entity_generation": generation,
        "entry_admission_sha256": admission_sha256,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "engine_identity_sha256": engine_identity_sha256,
        "resolved_engine_identity": engine_id,
        "resolved_engine_class": engine_class,
        "resolved_engine_artifact_sha256": engine_artifact_sha256,
        "model_call_id": model_call_id,
        "output_ref": output_ref,
        "output_sha256": output_sha256,
        "output_size": output_size,
        "model_lanes": tuple(decision.model_lanes),
    }
    receipt_sha256 = hashlib.sha256(_canonical(payload)).hexdigest()
    receipt = InferenceReceipt(**payload, receipt_sha256=receipt_sha256)

    # Reuse the canonical route echo assertion rather than inventing a second route
    # validation law. `asdict` contains a strict superset of the expected echo fields.
    assert_inference_echo(decision, asdict(receipt))
    return receipt


def receipt_json(receipt: InferenceReceipt) -> str:
    if not isinstance(receipt, InferenceReceipt):
        raise InferenceReceiptError("INFERENCE_RECEIPT_REQUIRED")
    return json.dumps(
        asdict(receipt),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
