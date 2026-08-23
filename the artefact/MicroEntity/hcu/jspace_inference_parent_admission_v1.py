#!/usr/bin/env python3
"""Fail-closed parent-evidence guard for EntityOS/HCU J-Space inference bindings.

A ``JSpaceInferenceBinding`` is a deterministic child envelope. Its self-consistent digest
proves the binding bytes, not that the referenced ``HCU_INFERENCE_RECEIPT/v4`` was admitted.
This guard requires the exact parent receipt from an external admitted registry, revalidates
its canonical digest, and cross-binds every execution-critical field mirrored into the
binding before downstream training-data orchestration may trust that ancestry.

This module mints no truth, runtime credit, model credit, reward, capability or effect
authority. It is a reusable admission primitive intended to be fused into the single
canonical training-data orchestration path.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA, STATUS as INFERENCE_RECEIPT_STATUS
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA, STATUS as INFERENCE_RECEIPT_STATUS
    from jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA

GUARD_SCHEMA = "ENTITYOS_HCU_JSPACE_INFERENCE_PARENT_ADMISSION/v1"


class JSpaceInferenceParentAdmissionError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceInferenceParentAdmissionError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceInferenceParentAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceInferenceParentAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceInferenceParentAdmissionError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


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


def require_admitted_inference_receipt_parent(
    binding: JSpaceInferenceBinding,
    admitted_inference_receipts: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Require exact admitted parent evidence for a self-authenticating J-Space binding."""
    try:
        validate_binding(binding)
    except JSpaceInferenceBindingError as exc:
        raise JSpaceInferenceParentAdmissionError(f"JSPACE_INFERENCE_BINDING_REJECTED:{exc}") from exc

    registry = _mapping(admitted_inference_receipts, "admitted_inference_receipts")
    parent_sha = _sha256(binding.inference_receipt_sha256, "binding.inference_receipt_sha256")
    receipt = registry.get(parent_sha)
    if not isinstance(receipt, Mapping):
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_PARENT_NOT_ADMITTED")
    receipt = dict(receipt)

    if receipt.get("schema") != INFERENCE_RECEIPT_SCHEMA or receipt.get("status") != INFERENCE_RECEIPT_STATUS:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_SCHEMA_OR_STATUS_UNSUPPORTED")
    if receipt.get("hash_serialization_schema") != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_CANONICALIZATION_SCHEMA_MISMATCH")
    if receipt.get("entry_binding_schema") != ENTRY_BINDING_SCHEMA:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH")
    if _canonical_receipt_sha256(receipt) != parent_sha:
        raise JSpaceInferenceParentAdmissionError("INFERENCE_RECEIPT_PARENT_IDENTITY_MISMATCH")

    mirrored = {
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
    for receipt_field, binding_field in mirrored.items():
        if receipt.get(receipt_field) != getattr(binding, binding_field):
            raise JSpaceInferenceParentAdmissionError(
                f"INFERENCE_RECEIPT_PARENT_BINDING_MISMATCH:{receipt_field}"
            )

    return receipt


__all__ = [
    "GUARD_SCHEMA",
    "JSpaceInferenceParentAdmissionError",
    "require_admitted_inference_receipt_parent",
]
