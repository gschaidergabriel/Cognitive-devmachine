#!/usr/bin/env python3
"""Deterministic downstream inference receipt producer for EntityOS/HCU.

This module invokes no model and grants no truth/effect authority. It consumes a canonical
HCU RouteDecision and fails closed unless: the concrete Typed-Entry admission is bound to
the same JCS causal event; the route is bound to the live generation; a verified JCS engine
admission receipt binds the exact engine bundle; and a generation-fenced physical-load lease
binds loader-consumed component identities to that same engine admission.

The load lease remains evidence consumed here, not runtime truth minted here. Until an
admitted real loader produces its evidence from the bytes actually consumed, this path has
zero HCU runtime credit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

from engine_admission_v1 import (
    ENGINE_ADMISSION_RECEIPT_SCHEMA,
    LOCK_SCHEMA as ENGINE_ARTIFACT_LOCK_SCHEMA,
    EngineArtifactLock,
    derive_engine_artifact_sha256,
)
from physical_engine_lease_v1 import SCHEMA as ENGINE_LOAD_LEASE_SCHEMA
from reactive_event_router_v1 import (
    ENTRY_BINDING_SCHEMA,
    HASH_SERIALIZATION_SCHEMA,
    ReactiveRoutingError,
    RouteDecision,
    assert_inference_echo,
    resolve_admitted_entry_binding,
)

SCHEMA = "HCU_INFERENCE_RECEIPT/v2"
STATUS = "CANDIDATE_ONLY"


class InferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceReceipt:
    schema: str
    status: str
    hash_serialization_schema: str
    entry_binding_schema: str
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
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    model_lanes: tuple[str, ...]
    receipt_sha256: str


def _canonical(value: Any) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise InferenceReceiptError(f"CANONICALIZATION_FAILED:{exc}") from exc


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


def _artifact_receipt_part(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise InferenceReceiptError(f"{field}:MAPPING_REQUIRED")
    required = {"kind", "sha256", "file_count", "byte_count"}
    if set(value) != required:
        raise InferenceReceiptError(f"{field}:SCHEMA_MISMATCH")
    return {
        "kind": _text(value.get("kind"), f"{field}.kind"),
        "sha256": _sha256(value.get("sha256"), f"{field}.sha256"),
        "file_count": _nonnegative_int(value.get("file_count"), f"{field}.file_count"),
        "byte_count": _nonnegative_int(value.get("byte_count"), f"{field}.byte_count"),
    }


def _verify_engine_admission_receipt(
    *,
    engine_admission_receipt_sha256: str,
    admitted_engine_admission_receipts: Mapping[str, Any],
    generation: int,
    expected_engine_identity: str,
    expected_engine_class: str,
    expected_engine_artifact_sha256: str,
) -> tuple[str, dict[str, str], str]:
    receipt_sha256 = _sha256(engine_admission_receipt_sha256, "engine_admission_receipt_sha256")
    if not isinstance(admitted_engine_admission_receipts, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_ADMISSION_RECEIPT_REGISTRY_REQUIRED")
    receipt = admitted_engine_admission_receipts.get(receipt_sha256)
    if not isinstance(receipt, Mapping):
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_NOT_ADMITTED")
    required = {
        "schema",
        "hash_serialization_schema",
        "entity_generation",
        "provider_alias",
        "engine_identity",
        "engine_class",
        "checkpoint",
        "tokenizer",
        "runtime",
        "build",
        "engine_artifact_sha256",
        "receipt_sha256",
    }
    if set(receipt) != required:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_SCHEMA_MISMATCH")
    if receipt.get("schema") != ENGINE_ADMISSION_RECEIPT_SCHEMA:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.get("hash_serialization_schema") != HASH_SERIALIZATION_SCHEMA:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    receipt_generation = _nonnegative_int(receipt.get("entity_generation"), "engine_admission_receipt.entity_generation")
    if receipt_generation != generation:
        raise InferenceReceiptError("STALE_ENGINE_ADMISSION_RECEIPT_GENERATION")

    provider_alias = _text(receipt.get("provider_alias"), "engine_admission_receipt.provider_alias").lower()
    engine_identity = _text(receipt.get("engine_identity"), "engine_admission_receipt.engine_identity").lower()
    engine_class = _text(receipt.get("engine_class"), "engine_admission_receipt.engine_class").upper()
    artifact_sha256 = _sha256(receipt.get("engine_artifact_sha256"), "engine_admission_receipt.engine_artifact_sha256")
    if engine_identity != expected_engine_identity:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_IDENTITY_MISMATCH")
    if engine_class != expected_engine_class:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_CLASS_MISMATCH")
    if artifact_sha256 != expected_engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_ARTIFACT_MISMATCH")

    checkpoint = _artifact_receipt_part(receipt.get("checkpoint"), "engine_admission_receipt.checkpoint")
    tokenizer = _artifact_receipt_part(receipt.get("tokenizer"), "engine_admission_receipt.tokenizer")
    runtime = _artifact_receipt_part(receipt.get("runtime"), "engine_admission_receipt.runtime")
    build = _artifact_receipt_part(receipt.get("build"), "engine_admission_receipt.build")
    lock = EngineArtifactLock(
        schema=ENGINE_ARTIFACT_LOCK_SCHEMA,
        provider_alias=provider_alias,
        engine_identity=engine_identity,
        engine_class=engine_class,
        checkpoint_sha256=checkpoint["sha256"],
        tokenizer_sha256=tokenizer["sha256"],
        runtime_sha256=runtime["sha256"],
        build_sha256=build["sha256"],
        engine_artifact_sha256=artifact_sha256,
    )
    if derive_engine_artifact_sha256(lock) != artifact_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_BUNDLE_DIGEST_MISMATCH")

    material = {
        "schema": ENGINE_ADMISSION_RECEIPT_SCHEMA,
        "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
        "entity_generation": receipt_generation,
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "checkpoint": checkpoint,
        "tokenizer": tokenizer,
        "runtime": runtime,
        "build": build,
        "engine_artifact_sha256": artifact_sha256,
    }
    observed_receipt_sha256 = _sha256(receipt.get("receipt_sha256"), "engine_admission_receipt.receipt_sha256")
    recomputed_receipt_sha256 = hashlib.sha256(_canonical(material)).hexdigest()
    if observed_receipt_sha256 != receipt_sha256 or recomputed_receipt_sha256 != receipt_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_DIGEST_MISMATCH")
    return receipt_sha256, {
        "checkpoint_sha256": checkpoint["sha256"],
        "tokenizer_sha256": tokenizer["sha256"],
        "runtime_sha256": runtime["sha256"],
        "build_sha256": build["sha256"],
    }, provider_alias


def _verify_engine_load_lease(
    *,
    engine_load_lease_sha256: str,
    admitted_engine_load_leases: Mapping[str, Any],
    generation: int,
    expected_provider_alias: str,
    expected_engine_identity: str,
    expected_engine_class: str,
    expected_engine_artifact_sha256: str,
    expected_engine_admission_receipt_sha256: str,
    expected_artifact_digests: Mapping[str, str],
) -> str:
    lease_sha256 = _sha256(engine_load_lease_sha256, "engine_load_lease_sha256")
    if not isinstance(admitted_engine_load_leases, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_LOAD_LEASE_REGISTRY_REQUIRED")
    lease = admitted_engine_load_leases.get(lease_sha256)
    if not isinstance(lease, Mapping):
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_NOT_ADMITTED")
    required = {
        "schema",
        "canonicalization_schema",
        "entity_generation",
        "engine_admission_receipt_sha256",
        "provider_alias",
        "engine_identity",
        "engine_class",
        "engine_artifact_sha256",
        "consumed_checkpoint_sha256",
        "consumed_tokenizer_sha256",
        "consumed_runtime_sha256",
        "consumed_build_sha256",
        "loader_instance_id",
        "loader_runtime_sha256",
        "artifact_boundary_receipt_sha256",
        "lease_id",
        "lease_sha256",
    }
    if set(lease) != required:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_SCHEMA_MISMATCH")
    if lease.get("schema") != ENGINE_LOAD_LEASE_SCHEMA:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_SCHEMA_UNSUPPORTED")
    if lease.get("canonicalization_schema") != HASH_SERIALIZATION_SCHEMA:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    lease_generation = _nonnegative_int(lease.get("entity_generation"), "engine_load_lease.entity_generation")
    if lease_generation != generation:
        raise InferenceReceiptError("STALE_ENGINE_LOAD_LEASE_GENERATION")

    provider_alias = _text(lease.get("provider_alias"), "engine_load_lease.provider_alias").lower()
    engine_identity = _text(lease.get("engine_identity"), "engine_load_lease.engine_identity").lower()
    engine_class = _text(lease.get("engine_class"), "engine_load_lease.engine_class").upper()
    engine_artifact_sha256 = _sha256(lease.get("engine_artifact_sha256"), "engine_load_lease.engine_artifact_sha256")
    engine_admission_sha256 = _sha256(
        lease.get("engine_admission_receipt_sha256"),
        "engine_load_lease.engine_admission_receipt_sha256",
    )
    if provider_alias != expected_provider_alias:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_PROVIDER_MISMATCH")
    if engine_identity != expected_engine_identity:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_IDENTITY_MISMATCH")
    if engine_class != expected_engine_class:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_CLASS_MISMATCH")
    if engine_artifact_sha256 != expected_engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_ARTIFACT_MISMATCH")
    if engine_admission_sha256 != expected_engine_admission_receipt_sha256:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_ADMISSION_RECEIPT_MISMATCH")

    consumed = {
        "checkpoint_sha256": _sha256(lease.get("consumed_checkpoint_sha256"), "engine_load_lease.consumed_checkpoint_sha256"),
        "tokenizer_sha256": _sha256(lease.get("consumed_tokenizer_sha256"), "engine_load_lease.consumed_tokenizer_sha256"),
        "runtime_sha256": _sha256(lease.get("consumed_runtime_sha256"), "engine_load_lease.consumed_runtime_sha256"),
        "build_sha256": _sha256(lease.get("consumed_build_sha256"), "engine_load_lease.consumed_build_sha256"),
    }
    for field in sorted(consumed):
        expected = _sha256(expected_artifact_digests.get(field), f"expected_artifact_digests.{field}")
        if consumed[field] != expected:
            raise InferenceReceiptError(f"ENGINE_LOAD_LEASE_CONSUMED_BYTES_MISMATCH:{field}")

    material = {
        "schema": ENGINE_LOAD_LEASE_SCHEMA,
        "canonicalization_schema": HASH_SERIALIZATION_SCHEMA,
        "entity_generation": lease_generation,
        "engine_admission_receipt_sha256": engine_admission_sha256,
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "engine_artifact_sha256": engine_artifact_sha256,
        "consumed_checkpoint_sha256": consumed["checkpoint_sha256"],
        "consumed_tokenizer_sha256": consumed["tokenizer_sha256"],
        "consumed_runtime_sha256": consumed["runtime_sha256"],
        "consumed_build_sha256": consumed["build_sha256"],
        "loader_instance_id": _text(lease.get("loader_instance_id"), "engine_load_lease.loader_instance_id"),
        "loader_runtime_sha256": _sha256(lease.get("loader_runtime_sha256"), "engine_load_lease.loader_runtime_sha256"),
        "artifact_boundary_receipt_sha256": _sha256(
            lease.get("artifact_boundary_receipt_sha256"),
            "engine_load_lease.artifact_boundary_receipt_sha256",
        ),
        "lease_id": _text(lease.get("lease_id"), "engine_load_lease.lease_id"),
    }
    observed_lease_sha256 = _sha256(lease.get("lease_sha256"), "engine_load_lease.lease_sha256")
    recomputed_lease_sha256 = hashlib.sha256(_canonical(material)).hexdigest()
    if observed_lease_sha256 != lease_sha256 or recomputed_lease_sha256 != lease_sha256:
        raise InferenceReceiptError("ENGINE_LOAD_LEASE_DIGEST_MISMATCH")
    return lease_sha256


def make_inference_receipt(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    engine_admission_receipt_sha256: str,
    admitted_engine_admission_receipts: Mapping[str, Any],
    engine_load_lease_sha256: str,
    admitted_engine_load_leases: Mapping[str, Any],
    model_call_id: str,
    output_ref: str,
    output_sha256: str,
    output_size: int,
) -> InferenceReceipt:
    """Produce a candidate-only inference receipt from admitted route and loader evidence."""
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
    try:
        admitted_event_sha256 = resolve_admitted_entry_binding(admitted_entry_bindings, admission_sha256)
    except ReactiveRoutingError as exc:
        raise InferenceReceiptError(str(exc)) from exc
    if admitted_event_sha256 != decision.event_sha256:
        raise InferenceReceiptError("ENTRY_EVENT_ROUTE_IDENTITY_MISMATCH")

    engine_id = _text(decision.resolved_engine_identity, "resolved_engine_identity")
    engine_class = _text(decision.resolved_engine_class, "resolved_engine_class")
    engine_artifact_sha256 = _sha256(decision.resolved_engine_artifact_sha256, "resolved_engine_artifact_sha256")
    engine_identity_sha256 = _sha256(decision.engine_identity_sha256, "engine_identity_sha256")
    if not isinstance(admitted_engine_artifacts, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    current_engine_artifact = admitted_engine_artifacts.get(engine_id)
    if current_engine_artifact is None:
        raise InferenceReceiptError("ENGINE_ARTIFACT_NOT_CURRENTLY_ADMITTED")
    current_engine_artifact = _sha256(current_engine_artifact, "admitted_engine_artifact_sha256")
    if current_engine_artifact != engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ARTIFACT_ADMISSION_MISMATCH")

    verified_engine_admission_receipt_sha256, admitted_artifact_digests, provider_alias = _verify_engine_admission_receipt(
        engine_admission_receipt_sha256=engine_admission_receipt_sha256,
        admitted_engine_admission_receipts=admitted_engine_admission_receipts,
        generation=generation,
        expected_engine_identity=engine_id,
        expected_engine_class=engine_class,
        expected_engine_artifact_sha256=engine_artifact_sha256,
    )
    verified_engine_load_lease_sha256 = _verify_engine_load_lease(
        engine_load_lease_sha256=engine_load_lease_sha256,
        admitted_engine_load_leases=admitted_engine_load_leases,
        generation=generation,
        expected_provider_alias=provider_alias,
        expected_engine_identity=engine_id,
        expected_engine_class=engine_class,
        expected_engine_artifact_sha256=engine_artifact_sha256,
        expected_engine_admission_receipt_sha256=verified_engine_admission_receipt_sha256,
        expected_artifact_digests=admitted_artifact_digests,
    )

    model_call_id = _text(model_call_id, "model_call_id")
    output_ref = _text(output_ref, "output_ref")
    output_sha256 = _sha256(output_sha256, "output_sha256")
    output_size = _output_size(output_size)

    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "hash_serialization_schema": decision.hash_serialization_schema,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "entity_generation": generation,
        "entry_admission_sha256": admission_sha256,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "engine_identity_sha256": engine_identity_sha256,
        "resolved_engine_identity": engine_id,
        "resolved_engine_class": engine_class,
        "resolved_engine_artifact_sha256": engine_artifact_sha256,
        "engine_admission_receipt_sha256": verified_engine_admission_receipt_sha256,
        "engine_load_lease_sha256": verified_engine_load_lease_sha256,
        "model_call_id": model_call_id,
        "output_ref": output_ref,
        "output_sha256": output_sha256,
        "output_size": output_size,
        "model_lanes": tuple(decision.model_lanes),
    }
    receipt_sha256 = hashlib.sha256(_canonical(payload)).hexdigest()
    receipt = InferenceReceipt(**payload, receipt_sha256=receipt_sha256)
    assert_inference_echo(decision, asdict(receipt))
    return receipt


def receipt_json(receipt: InferenceReceipt) -> str:
    if not isinstance(receipt, InferenceReceipt):
        raise InferenceReceiptError("INFERENCE_RECEIPT_REQUIRED")
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
