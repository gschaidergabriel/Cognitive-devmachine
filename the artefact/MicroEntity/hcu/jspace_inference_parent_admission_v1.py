#!/usr/bin/env python3
"""Single fail-closed parent-evidence guard for EntityOS/HCU J-Space bindings.

A ``JSpaceInferenceBinding`` is a deterministic child envelope. Its self-consistent digest
proves the binding bytes, not that the referenced ``HCU_INFERENCE_RECEIPT/v4`` was admitted.
This guard is the one reusable authority for that parent admission: it requires the exact
parent receipt from an external registry, revalidates its canonical identity and schema,
and cross-binds every execution-critical field mirrored into the binding.

This module mints no truth, runtime credit, model credit, reward, capability or effect
authority. Downstream training-data orchestration must delegate parent-receipt admission here
rather than maintaining a second copy of the same semantics.
"""
from __future__ import annotations

from dataclasses import asdict, fields
import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA

GUARD_SCHEMA = "ENTITYOS_HCU_JSPACE_INFERENCE_PARENT_ADMISSION/v1"


class JSpaceInferenceParentAdmissionError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceInferenceParentAdmissionError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceInferenceParentAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceInferenceParentAdmissionError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceInferenceParentAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceInferenceParentAdmissionError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _normalize_receipt(value: Any) -> dict[str, Any]:
    if isinstance(value, InferenceReceipt):
        receipt = asdict(value)
    elif isinstance(value, Mapping):
        receipt = dict(value)
    else:
        raise JSpaceInferenceParentAdmissionError("ADMITTED_INFERENCE_RECEIPT_VALUE_INVALID")
    expected_fields = {field.name for field in fields(InferenceReceipt)}
    if set(receipt) != expected_fields:
        raise JSpaceInferenceParentAdmissionError("ADMITTED_INFERENCE_RECEIPT_FIELD_SET_MISMATCH")
    return receipt


def _canonical_receipt_sha256(receipt: Mapping[str, Any]) -> str:
    material = dict(receipt)
    observed = _sha256(material.pop("receipt_sha256", None), "inference_receipt.receipt_sha256")
    try:
        expected = hashlib.sha256(canonicalize(material)).hexdigest()
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_CANONICALIZATION_FAILED") from exc
    if observed != expected:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_DIGEST_MISMATCH")
    return observed


_MIRRORED_FIELDS = {
    "entity_generation": "generation",
    "entry_admission_sha256": "entry_admission_sha256",
    "event_sha256": "entry_event_sha256",
    "decision_sha256": "route_decision_sha256",
    "grid_plan_sha256": "grid_plan_sha256",
    "engine_identity_sha256": "engine_identity_sha256",
    "resolved_engine_identity": "resolved_engine_identity",
    "resolved_engine_class": "resolved_engine_class",
    "resolved_engine_artifact_sha256": "resolved_engine_artifact_sha256",
    "engine_admission_receipt_sha256": "engine_admission_receipt_sha256",
    "engine_load_loader_binding_sha256": "engine_load_loader_binding_sha256",
    "engine_load_lease_sha256": "engine_load_lease_sha256",
    "engine_load_consumption_receipt_sha256": "engine_load_consumption_receipt_sha256",
    "engine_load_loader_id": "engine_load_loader_id",
    "model_execution_receipt_sha256": "model_execution_receipt_sha256",
    "model_execution_observation_sha256": "model_execution_observation_sha256",
    "model_execution_executor_id": "model_execution_executor_id",
    "model_execution_invocation_id": "model_execution_invocation_id",
    "output_producing_cell_id": "output_producing_cell_id",
    "model_execution_role": "model_execution_role",
    "input_sha256": "input_sha256",
    "input_size": "input_size",
    "model_call_id": "model_call_id",
    "output_ref": "output_ref",
    "output_sha256": "output_sha256",
    "output_size": "output_size",
}


def require_admitted_inference_receipt_parent(
    binding: JSpaceInferenceBinding,
    admitted_inference_receipts: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Require exact admitted parent evidence for a self-authenticating J-Space binding."""
    try:
        validate_binding(binding)
    except JSpaceInferenceBindingError as exc:
        raise JSpaceInferenceParentAdmissionError(f"JSPACE_INFERENCE_BINDING_REJECTED:{exc}") from exc

    registry = _mapping(admitted_inference_receipts, "admitted_inference_receipts")
    parent_sha = _sha256(binding.inference_receipt_sha256, "binding.inference_receipt_sha256")
    raw_receipt = registry.get(parent_sha)
    if raw_receipt is None:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_PARENT_NOT_ADMITTED")
    receipt = _normalize_receipt(raw_receipt)

    if receipt.get("schema") != INFERENCE_RECEIPT_SCHEMA or receipt.get("schema") != binding.inference_receipt_schema:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.get("status") != INFERENCE_RECEIPT_STATUS:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_STATUS_UNSUPPORTED")
    for field in (
        "hash_serialization_schema",
        "engine_load_canonicalization_schema",
        "model_execution_canonicalization_schema",
    ):
        if receipt.get(field) != CANONICALIZATION_SCHEMA or receipt.get(field) != binding.canonicalization_schema:
            raise JSpaceInferenceParentAdmissionError(
                f"INFERENCE_RECEIPT_CANONICALIZATION_SCHEMA_MISMATCH:{field}"
            )
    if receipt.get("entry_binding_schema") != ENTRY_BINDING_SCHEMA:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH")
    if _canonical_receipt_sha256(receipt) != parent_sha:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_PARENT_IDENTITY_MISMATCH")

    for receipt_field, binding_field in _MIRRORED_FIELDS.items():
        if receipt.get(receipt_field) != getattr(binding, binding_field):
            raise JSpaceInferenceParentAdmissionError(
                f"INFERENCE_RECEIPT_PARENT_BINDING_MISMATCH:{receipt_field}"
            )

    model_lanes = receipt.get("model_lanes")
    if isinstance(model_lanes, (str, bytes, bytearray)) or not isinstance(model_lanes, (list, tuple)):
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_MODEL_LANES_INVALID")
    normalized_lanes = tuple(_text(value, "inference_receipt.model_lane", max_len=256) for value in model_lanes)
    if binding.role not in normalized_lanes:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_ROLE_NOT_IN_MODEL_LANES")

    return receipt


__all__ = [
    "GUARD_SCHEMA",
    "JSpaceInferenceParentAdmissionError",
    "require_admitted_inference_receipt_parent",
]
