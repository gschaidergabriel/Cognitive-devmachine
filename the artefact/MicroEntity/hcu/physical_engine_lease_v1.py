#!/usr/bin/env python3
"""Generation-fenced physical engine lease for EntityOS/HCU.

Deterministic control-plane plumbing only. This module does not load a model or prove
that a loader consumed bytes. It binds separately supplied loader-consumption evidence
to the already-admitted EngineAdmission and current artifact registries. Pre-load hashes
alone receive no runtime credit.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .reactive_event_router_v1 import EngineAdmission
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from reactive_event_router_v1 import EngineAdmission

SCHEMA = "HCU_PHYSICAL_ENGINE_LEASE/v1"
ADMISSION_BINDING_SCHEMA = "HCU_ENGINE_ADMISSION_BINDING/v1"


class PhysicalEngineLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class PhysicalEngineLease:
    schema: str
    canonicalization_schema: str
    entity_generation: int
    lease_id: str
    loader_instance_id: str
    artifact_boundary_receipt_sha256: str
    provider_alias: str
    engine_identity: str
    engine_class: str
    admitted_checkpoint_sha256: str
    admitted_tokenizer_sha256: str
    admitted_runtime_build_sha256: str
    loader_consumed_checkpoint_sha256: str
    loader_consumed_tokenizer_sha256: str
    loader_consumed_runtime_build_sha256: str
    engine_admission_binding_sha256: str
    lease_sha256: str


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PhysicalEngineLeaseError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise PhysicalEngineLeaseError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise PhysicalEngineLeaseError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value) or value in {"0" * 64, "f" * 64}:
        raise PhysicalEngineLeaseError(f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PhysicalEngineLeaseError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Mapping[str, Any], field: str) -> str:
    try:
        encoded = canonicalize(value)
    except CanonicalizationError as exc:
        raise PhysicalEngineLeaseError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _admitted_aux_digest(admitted_aux_artifacts: Mapping[str, Any], engine_identity: str, key: str) -> str:
    if not isinstance(admitted_aux_artifacts, Mapping):
        raise PhysicalEngineLeaseError("ADMITTED_AUX_ARTIFACT_REGISTRY_REQUIRED")
    record = admitted_aux_artifacts.get(engine_identity)
    if not isinstance(record, Mapping):
        raise PhysicalEngineLeaseError("ENGINE_AUX_ARTIFACT_RECORD_NOT_ADMITTED")
    if key not in record:
        raise PhysicalEngineLeaseError(f"ENGINE_AUX_ARTIFACT_{key.upper()}_NOT_ADMITTED")
    return _sha256(record[key], f"admitted_{key}")


def issue_physical_engine_lease(
    engine_admission: EngineAdmission,
    *,
    current_generation: int,
    loader_generation: int,
    admitted_engine_artifacts: Mapping[str, Any],
    admitted_aux_artifacts: Mapping[str, Any],
    loader_consumed_checkpoint_sha256: str,
    loader_consumed_tokenizer_sha256: str,
    loader_consumed_runtime_build_sha256: str,
    loader_instance_id: str,
    lease_id: str,
    artifact_boundary_receipt_sha256: str,
) -> PhysicalEngineLease:
    """Bind real-loader evidence to one current control-plane EngineAdmission."""
    if not isinstance(engine_admission, EngineAdmission):
        raise PhysicalEngineLeaseError("ENGINE_ADMISSION_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    loader_generation = _generation(loader_generation, "loader_generation")
    if loader_generation != current_generation:
        raise PhysicalEngineLeaseError("STALE_LOADER_GENERATION")

    provider_alias = _text(engine_admission.provider_alias, "provider_alias").lower()
    engine_identity = _text(engine_admission.engine_identity, "engine_identity").lower()
    engine_class = _text(engine_admission.engine_class, "engine_class").upper()
    admitted_checkpoint_sha256 = _sha256(engine_admission.engine_artifact_sha256, "engine_admission_artifact_sha256")

    if not isinstance(admitted_engine_artifacts, Mapping):
        raise PhysicalEngineLeaseError("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    registry_checkpoint = admitted_engine_artifacts.get(engine_identity)
    if registry_checkpoint is None:
        raise PhysicalEngineLeaseError("ENGINE_CHECKPOINT_NOT_ADMITTED")
    registry_checkpoint = _sha256(registry_checkpoint, "admitted_checkpoint_sha256")
    if registry_checkpoint != admitted_checkpoint_sha256:
        raise PhysicalEngineLeaseError("ENGINE_ADMISSION_CHECKPOINT_REGISTRY_MISMATCH")

    admitted_tokenizer_sha256 = _admitted_aux_digest(admitted_aux_artifacts, engine_identity, "tokenizer_sha256")
    admitted_runtime_build_sha256 = _admitted_aux_digest(admitted_aux_artifacts, engine_identity, "runtime_build_sha256")
    consumed_checkpoint = _sha256(loader_consumed_checkpoint_sha256, "loader_consumed_checkpoint_sha256")
    consumed_tokenizer = _sha256(loader_consumed_tokenizer_sha256, "loader_consumed_tokenizer_sha256")
    consumed_runtime = _sha256(loader_consumed_runtime_build_sha256, "loader_consumed_runtime_build_sha256")
    if consumed_checkpoint != admitted_checkpoint_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_CHECKPOINT_MISMATCH")
    if consumed_tokenizer != admitted_tokenizer_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_TOKENIZER_MISMATCH")
    if consumed_runtime != admitted_runtime_build_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_RUNTIME_BUILD_MISMATCH")

    loader_instance_id = _text(loader_instance_id, "loader_instance_id")
    lease_id = _text(lease_id, "lease_id")
    boundary_receipt = _sha256(artifact_boundary_receipt_sha256, "artifact_boundary_receipt_sha256")

    admission_binding_payload = {
        "schema": ADMISSION_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": current_generation,
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "admitted_checkpoint_sha256": admitted_checkpoint_sha256,
        "admitted_tokenizer_sha256": admitted_tokenizer_sha256,
        "admitted_runtime_build_sha256": admitted_runtime_build_sha256,
    }
    admission_binding_sha256 = _canonical_sha256(admission_binding_payload, "ENGINE_ADMISSION_BINDING")
    payload = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": current_generation,
        "lease_id": lease_id,
        "loader_instance_id": loader_instance_id,
        "artifact_boundary_receipt_sha256": boundary_receipt,
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "admitted_checkpoint_sha256": admitted_checkpoint_sha256,
        "admitted_tokenizer_sha256": admitted_tokenizer_sha256,
        "admitted_runtime_build_sha256": admitted_runtime_build_sha256,
        "loader_consumed_checkpoint_sha256": consumed_checkpoint,
        "loader_consumed_tokenizer_sha256": consumed_tokenizer,
        "loader_consumed_runtime_build_sha256": consumed_runtime,
        "engine_admission_binding_sha256": admission_binding_sha256,
    }
    return PhysicalEngineLease(**payload, lease_sha256=_canonical_sha256(payload, "PHYSICAL_ENGINE_LEASE"))


def assert_physical_engine_lease_current(
    lease: PhysicalEngineLease,
    *,
    current_generation: int,
    admitted_engine_artifacts: Mapping[str, Any],
    admitted_aux_artifacts: Mapping[str, Any],
) -> None:
    """Re-check the lease immediately before inference/receipt production."""
    if not isinstance(lease, PhysicalEngineLease):
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    if lease.entity_generation != current_generation:
        raise PhysicalEngineLeaseError("STALE_PHYSICAL_ENGINE_LEASE")
    if not isinstance(admitted_engine_artifacts, Mapping):
        raise PhysicalEngineLeaseError("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    checkpoint = admitted_engine_artifacts.get(lease.engine_identity)
    if checkpoint is None:
        raise PhysicalEngineLeaseError("ENGINE_CHECKPOINT_NOT_CURRENTLY_ADMITTED")
    if _sha256(checkpoint, "current_admitted_checkpoint_sha256") != lease.admitted_checkpoint_sha256:
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_CHECKPOINT_REVOKED")
    if _admitted_aux_digest(admitted_aux_artifacts, lease.engine_identity, "tokenizer_sha256") != lease.admitted_tokenizer_sha256:
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_TOKENIZER_REVOKED")
    if _admitted_aux_digest(admitted_aux_artifacts, lease.engine_identity, "runtime_build_sha256") != lease.admitted_runtime_build_sha256:
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_RUNTIME_BUILD_REVOKED")


def inference_lease_echo(lease: PhysicalEngineLease) -> dict[str, str | int]:
    if not isinstance(lease, PhysicalEngineLease):
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_REQUIRED")
    return {
        "physical_engine_lease_sha256": lease.lease_sha256,
        "physical_engine_lease_generation": lease.entity_generation,
        "loader_instance_id": lease.loader_instance_id,
        "artifact_boundary_receipt_sha256": lease.artifact_boundary_receipt_sha256,
        "loader_consumed_checkpoint_sha256": lease.loader_consumed_checkpoint_sha256,
        "loader_consumed_tokenizer_sha256": lease.loader_consumed_tokenizer_sha256,
        "loader_consumed_runtime_build_sha256": lease.loader_consumed_runtime_build_sha256,
    }
