#!/usr/bin/env python3
"""Deterministic downstream HCU inference receipt producer.

This module does not perform inference and cannot mint canonical truth or effect
authority. It converts an already-admitted model RouteDecision plus the actual candidate
result into one immutable causal receipt whose identity is derived from the route's
admitted event/policy/engine tuple and the canonical candidate-result digest.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from reactive_event_router_v1 import RouteDecision, ReactiveRoutingError, assert_inference_echo

SCHEMA = "HCU_INFERENCE_RECEIPT/v1"


class InferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceReceipt:
    schema: str
    event_sha256: str
    router_policy_sha256: str
    decision_sha256: str
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    candidate_result_sha256: str
    receipt_sha256: str


def _canonical(value: Any, field: str) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InferenceReceiptError(f"{field}:CANONICALIZATION_FAILED") from exc


def _sha256_canonical(value: Any, field: str) -> str:
    return hashlib.sha256(_canonical(value, field)).hexdigest()


def _require_model_route(decision: RouteDecision) -> None:
    if not isinstance(decision, RouteDecision):
        raise InferenceReceiptError("ROUTE_DECISION_REQUIRED")
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise InferenceReceiptError("MODEL_ROUTE_REQUIRED_FOR_INFERENCE_RECEIPT")
    required = {
        "event_sha256": decision.event_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
    }
    if any(value is None for value in required.values()):
        raise InferenceReceiptError("MODEL_ROUTE_IDENTITY_INCOMPLETE")


def _body_from_decision(decision: RouteDecision, candidate_result_sha256: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "event_sha256": decision.event_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
        "candidate_result_sha256": candidate_result_sha256,
    }


def build_inference_receipt(decision: RouteDecision, candidate_result: Any) -> InferenceReceipt:
    """Produce one deterministic receipt from the admitted route and actual candidate result.

    The caller cannot supply event/route/engine echo fields independently: those values are
    derived from ``decision``. This closes the gap where a downstream component could emit
    an arbitrary self-consistent echo unrelated to the admitted route.
    """
    _require_model_route(decision)
    candidate_result_sha256 = _sha256_canonical(candidate_result, "CANDIDATE_RESULT")
    body = _body_from_decision(decision, candidate_result_sha256)
    receipt_sha256 = _sha256_canonical(body, "INFERENCE_RECEIPT")
    receipt = InferenceReceipt(**body, receipt_sha256=receipt_sha256)

    # Reuse the router-owned identity assertion as a construction invariant.
    try:
        assert_inference_echo(decision, asdict(receipt))
    except ReactiveRoutingError as exc:
        raise InferenceReceiptError("ROUTE_ECHO_CONSTRUCTION_FAILED") from exc
    return receipt


def validate_inference_receipt(
    decision: RouteDecision,
    receipt: InferenceReceipt | Mapping[str, Any],
    *,
    candidate_result: Any | None = None,
) -> None:
    """Fail closed on route-echo drift, receipt mutation, or candidate-result mismatch.

    Passing ``candidate_result`` additionally proves that the receipt's candidate digest
    matches the supplied result. Runtime integration must call this with the actual model
    result before that result is admitted into later HCU/EntityOS processing.
    """
    _require_model_route(decision)
    if isinstance(receipt, InferenceReceipt):
        observed = asdict(receipt)
    elif isinstance(receipt, Mapping):
        observed = dict(receipt)
    else:
        raise InferenceReceiptError("INFERENCE_RECEIPT_MAPPING_REQUIRED")

    if observed.get("schema") != SCHEMA:
        raise InferenceReceiptError("INFERENCE_RECEIPT_SCHEMA_UNSUPPORTED")

    try:
        assert_inference_echo(decision, observed)
    except ReactiveRoutingError as exc:
        raise InferenceReceiptError("INFERENCE_RECEIPT_ROUTE_ECHO_MISMATCH") from exc

    candidate_result_sha256 = observed.get("candidate_result_sha256")
    if not isinstance(candidate_result_sha256, str) or len(candidate_result_sha256) != 64:
        raise InferenceReceiptError("CANDIDATE_RESULT_SHA256_INVALID")
    if candidate_result_sha256.lower() != candidate_result_sha256 or any(
        ch not in "0123456789abcdef" for ch in candidate_result_sha256
    ):
        raise InferenceReceiptError("CANDIDATE_RESULT_SHA256_INVALID")

    body = _body_from_decision(decision, candidate_result_sha256)
    expected_receipt_sha256 = _sha256_canonical(body, "INFERENCE_RECEIPT")
    if observed.get("receipt_sha256") != expected_receipt_sha256:
        raise InferenceReceiptError("INFERENCE_RECEIPT_DIGEST_MISMATCH")

    if candidate_result is not None:
        actual_result_sha256 = _sha256_canonical(candidate_result, "CANDIDATE_RESULT")
        if actual_result_sha256 != candidate_result_sha256:
            raise InferenceReceiptError("CANDIDATE_RESULT_DIGEST_MISMATCH")


def receipt_json(receipt: InferenceReceipt) -> str:
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
