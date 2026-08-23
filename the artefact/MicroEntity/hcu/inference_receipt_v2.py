#!/usr/bin/env python3
"""JCS-bound downstream inference receipt for the EntityOS/HCU retained path.

This is deterministic evidence plumbing only. It consumes a RouteDecision plus a
control-plane-admitted VerifiedEngineLoad and emits no model call, truth, capability,
state, or effect authority. Historical inference/lease schemas are not rehashed here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from engine_load_lease_v1 import (
    ACTUAL_LOADER_EVIDENCE_SOURCE,
    VERIFIED_LOAD_SCHEMA,
    LoaderConsumedArtifact,
    VerifiedEngineLoad,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
from reactive_event_router_v1 import HASH_SERIALIZATION_SCHEMA, RouteDecision, assert_inference_echo

SCHEMA = "HCU_INFERENCE_RECEIPT/v2"
STATUS = "CANDIDATE_ONLY"


class InferenceReceiptV2Error(ValueError):
    pass


@dataclass(frozen=True)
class InferenceReceiptV2:
    schema: str
    status: str
    canonicalization_schema: str
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
    engine_admission_receipt_sha256: str
    engine_load_lease_sha256: str
    engine_load_consumption_receipt_sha256: str
    engine_load_loader_binding_sha256: str
    engine_load_loader_id: str
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    model_lanes: tuple[str, ...]
    receipt_sha256: str


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise InferenceReceiptV2Error(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InferenceReceiptV2Error(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise InferenceReceiptV2Error(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise InferenceReceiptV2Error(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise InferenceReceiptV2Error(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InferenceReceiptV2Error(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _artifact_material(value: LoaderConsumedArtifact, field: str) -> dict[str, Any]:
    if not isinstance(value, LoaderConsumedArtifact):
        raise InferenceReceiptV2Error(f"{field}:LOADER_CONSUMED_ARTIFACT_REQUIRED")
    if value.evidence_source != ACTUAL_LOADER_EVIDENCE_SOURCE:
        raise InferenceReceiptV2Error(f"{field}:ACTUAL_LOADER_READ_EVIDENCE_REQUIRED")
    file_count = _generation(value.file_count, f"{field}.file_count")
    byte_count = _generation(value.byte_count, f"{field}.byte_count")
    return {
        "kind": _text(value.kind, f"{field}.kind"),
        "sha256": _sha256(value.sha256, f"{field}.sha256"),
        "file_count": file_count,
        "byte_count": byte_count,
        "evidence_source": ACTUAL_LOADER_EVIDENCE_SOURCE,
    }


def _verify_load(
    receipt_sha256: str,
    admitted_verified_engine_loads: Mapping[str, Any],
    *,
    current_generation: int,
    decision: RouteDecision,
    admitted_engine_artifacts: Mapping[str, Any],
    admitted_engine_admission_receipts: Mapping[str, Any],
) -> VerifiedEngineLoad:
    receipt_sha256 = _sha256(receipt_sha256, "verified_engine_load_receipt_sha256")
    if not isinstance(admitted_verified_engine_loads, Mapping):
        raise InferenceReceiptV2Error("ADMITTED_VERIFIED_ENGINE_LOAD_REGISTRY_REQUIRED")
    load = admitted_verified_engine_loads.get(receipt_sha256)
    if not isinstance(load, VerifiedEngineLoad):
        raise InferenceReceiptV2Error("VERIFIED_ENGINE_LOAD_NOT_ADMITTED")
    if load.schema != VERIFIED_LOAD_SCHEMA or load.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptV2Error("VERIFIED_ENGINE_LOAD_SCHEMA_UNSUPPORTED")
    if _generation(load.entity_generation, "verified_engine_load.entity_generation") != current_generation:
        raise InferenceReceiptV2Error("STALE_VERIFIED_ENGINE_LOAD_GENERATION")

    engine_id = _text(decision.resolved_engine_identity, "resolved_engine_identity")
    engine_class = _text(decision.resolved_engine_class, "resolved_engine_class")
    engine_artifact = _sha256(decision.resolved_engine_artifact_sha256, "resolved_engine_artifact_sha256")
    if load.engine_identity != engine_id or load.engine_class != engine_class:
        raise InferenceReceiptV2Error("VERIFIED_ENGINE_LOAD_IDENTITY_OR_CLASS_MISMATCH")
    if _sha256(load.engine_artifact_sha256, "verified_engine_load.engine_artifact_sha256") != engine_artifact:
        raise InferenceReceiptV2Error("VERIFIED_ENGINE_LOAD_ARTIFACT_MISMATCH")

    if not isinstance(admitted_engine_artifacts, Mapping):
        raise InferenceReceiptV2Error("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    if _sha256(admitted_engine_artifacts.get(engine_id), "admitted_engine_artifact_sha256") != engine_artifact:
        raise InferenceReceiptV2Error("ENGINE_ARTIFACT_ADMISSION_MISMATCH")
    admission_receipt = _sha256(load.engine_admission_receipt_sha256, "engine_admission_receipt_sha256")
    if not isinstance(admitted_engine_admission_receipts, Mapping) or admission_receipt not in admitted_engine_admission_receipts:
        raise InferenceReceiptV2Error("ENGINE_ADMISSION_RECEIPT_NOT_ADMITTED")

    material = {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": current_generation,
        "loader_id": _text(load.loader_id, "verified_engine_load.loader_id"),
        "loader_binding_sha256": _sha256(load.loader_binding_sha256, "verified_engine_load.loader_binding_sha256"),
        "engine_admission_receipt_sha256": admission_receipt,
        "engine_load_lease_sha256": _sha256(load.engine_load_lease_sha256, "verified_engine_load.engine_load_lease_sha256"),
        "engine_identity": engine_id,
        "engine_class": engine_class,
        "engine_artifact_sha256": engine_artifact,
        "checkpoint": _artifact_material(load.checkpoint, "checkpoint"),
        "tokenizer": _artifact_material(load.tokenizer, "tokenizer"),
        "runtime": _artifact_material(load.runtime, "runtime"),
        "build": _artifact_material(load.build, "build"),
    }
    recomputed = _canonical_sha256(material, "VERIFIED_ENGINE_LOAD")
    observed = _sha256(load.consumption_receipt_sha256, "verified_engine_load.consumption_receipt_sha256")
    if observed != receipt_sha256 or recomputed != receipt_sha256:
        raise InferenceReceiptV2Error("VERIFIED_ENGINE_LOAD_RECEIPT_DIGEST_MISMATCH")
    return load


def make_inference_receipt_v2(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    verified_engine_load_receipt_sha256: str,
    admitted_verified_engine_loads: Mapping[str, Any],
    admitted_engine_admission_receipts: Mapping[str, Any],
    model_call_id: str,
    output_ref: str,
    output_sha256: str,
    output_size: int,
) -> InferenceReceiptV2:
    if not isinstance(decision, RouteDecision) or decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise InferenceReceiptV2Error("MODEL_ACTIVATION_ROUTE_REQUIRED")
    if HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA or decision.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptV2Error("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    current_generation = _generation(current_generation, "current_generation")
    if not isinstance(admitted_route_generations, Mapping) or admitted_route_generations.get(decision.decision_sha256) != current_generation:
        raise InferenceReceiptV2Error("ROUTE_GENERATION_NOT_CURRENTLY_ADMITTED")

    admission_sha256 = _sha256(entry_admission_sha256, "entry_admission_sha256")
    if decision.entry_admission_sha256 != admission_sha256:
        raise InferenceReceiptV2Error("ROUTE_ENTRY_ADMISSION_IDENTITY_MISMATCH")
    if not isinstance(admitted_entry_bindings, Mapping):
        raise InferenceReceiptV2Error("ADMITTED_ENTRY_BINDING_REGISTRY_REQUIRED")
    if _sha256(admitted_entry_bindings.get(admission_sha256), "admitted_entry_event_sha256") != decision.event_sha256:
        raise InferenceReceiptV2Error("ENTRY_EVENT_ROUTE_IDENTITY_MISMATCH")

    load = _verify_load(
        verified_engine_load_receipt_sha256,
        admitted_verified_engine_loads,
        current_generation=current_generation,
        decision=decision,
        admitted_engine_artifacts=admitted_engine_artifacts,
        admitted_engine_admission_receipts=admitted_engine_admission_receipts,
    )
    engine_identity_sha256 = _sha256(decision.engine_identity_sha256, "engine_identity_sha256")
    output_size = _generation(output_size, "output_size")
    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "hash_serialization_schema": decision.hash_serialization_schema,
        "entity_generation": current_generation,
        "entry_admission_sha256": admission_sha256,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "engine_identity_sha256": engine_identity_sha256,
        "resolved_engine_identity": _text(decision.resolved_engine_identity, "resolved_engine_identity"),
        "resolved_engine_class": _text(decision.resolved_engine_class, "resolved_engine_class"),
        "resolved_engine_artifact_sha256": _sha256(decision.resolved_engine_artifact_sha256, "resolved_engine_artifact_sha256"),
        "engine_admission_receipt_sha256": _sha256(load.engine_admission_receipt_sha256, "engine_admission_receipt_sha256"),
        "engine_load_lease_sha256": _sha256(load.engine_load_lease_sha256, "engine_load_lease_sha256"),
        "engine_load_consumption_receipt_sha256": _sha256(load.consumption_receipt_sha256, "engine_load_consumption_receipt_sha256"),
        "engine_load_loader_binding_sha256": _sha256(load.loader_binding_sha256, "engine_load_loader_binding_sha256"),
        "engine_load_loader_id": _text(load.loader_id, "engine_load_loader_id"),
        "model_call_id": _text(model_call_id, "model_call_id"),
        "output_ref": _text(output_ref, "output_ref"),
        "output_sha256": _sha256(output_sha256, "output_sha256"),
        "output_size": output_size,
        "model_lanes": tuple(decision.model_lanes),
    }
    receipt = InferenceReceiptV2(**payload, receipt_sha256=_canonical_sha256(payload, "INFERENCE_RECEIPT_V2"))
    assert_inference_echo(decision, asdict(receipt))
    return receipt


def receipt_json(receipt: InferenceReceiptV2) -> str:
    if not isinstance(receipt, InferenceReceiptV2):
        raise InferenceReceiptV2Error("INFERENCE_RECEIPT_V2_REQUIRED")
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
