#!/usr/bin/env python3
"""Generation-fenced physical engine-load lease for EntityOS/HCU.

Deterministic control-plane plumbing only. This module does not load a model and does not
by itself prove that a loader consumed bytes. It binds separately supplied loader-consumed
checkpoint/tokenizer/runtime/build identities to one already verified EngineAdmission
receipt and the live entity generation. Pre-load hashes alone receive no runtime credit.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .engine_admission_v1 import VerifiedEngineAdmission
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from engine_admission_v1 import VerifiedEngineAdmission

SCHEMA = "HCU_PHYSICAL_ENGINE_LOAD_LEASE/v2"


class PhysicalEngineLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class PhysicalEngineLease:
    schema: str
    canonicalization_schema: str
    entity_generation: int
    engine_admission_receipt_sha256: str
    provider_alias: str
    engine_identity: str
    engine_class: str
    engine_artifact_sha256: str
    consumed_checkpoint_sha256: str
    consumed_tokenizer_sha256: str
    consumed_runtime_sha256: str
    consumed_build_sha256: str
    loader_instance_id: str
    loader_runtime_sha256: str
    artifact_boundary_receipt_sha256: str
    lease_id: str
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
    if (
        len(value) != 64
        or value.lower() != value
        or any(ch not in "0123456789abcdef" for ch in value)
        or value in {"0" * 64, "f" * 64}
    ):
        raise PhysicalEngineLeaseError(f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PhysicalEngineLeaseError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: dict[str, Any], field: str) -> str:
    try:
        encoded = canonicalize(value)
    except CanonicalizationError as exc:
        raise PhysicalEngineLeaseError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _verified_admission(
    verified: VerifiedEngineAdmission,
    *,
    current_generation: int,
) -> tuple[str, str, str, str, str, str, str, str, str]:
    if not isinstance(verified, VerifiedEngineAdmission):
        raise PhysicalEngineLeaseError("VERIFIED_ENGINE_ADMISSION_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    if verified.entity_generation != current_generation:
        raise PhysicalEngineLeaseError("STALE_VERIFIED_ENGINE_ADMISSION")

    provider_alias = _text(verified.admission.provider_alias, "provider_alias").lower()
    engine_identity = _text(verified.admission.engine_identity, "engine_identity").lower()
    engine_class = _text(verified.admission.engine_class, "engine_class").upper()
    engine_artifact_sha256 = _sha256(verified.engine_artifact_sha256, "engine_artifact_sha256")
    if _sha256(verified.admission.engine_artifact_sha256, "engine_admission.engine_artifact_sha256") != engine_artifact_sha256:
        raise PhysicalEngineLeaseError("ENGINE_ADMISSION_BUNDLE_IDENTITY_MISMATCH")

    checkpoint_sha256 = _sha256(verified.checkpoint.sha256, "verified_checkpoint_sha256")
    tokenizer_sha256 = _sha256(verified.tokenizer.sha256, "verified_tokenizer_sha256")
    runtime_sha256 = _sha256(verified.runtime.sha256, "verified_runtime_sha256")
    build_sha256 = _sha256(verified.build.sha256, "verified_build_sha256")
    receipt_sha256 = _sha256(verified.receipt_sha256, "engine_admission_receipt_sha256")
    return (
        provider_alias,
        engine_identity,
        engine_class,
        engine_artifact_sha256,
        checkpoint_sha256,
        tokenizer_sha256,
        runtime_sha256,
        build_sha256,
        receipt_sha256,
    )


def issue_physical_engine_lease(
    verified_engine_admission: VerifiedEngineAdmission,
    *,
    current_generation: int,
    loader_generation: int,
    loader_consumed_checkpoint_sha256: str,
    loader_consumed_tokenizer_sha256: str,
    loader_consumed_runtime_sha256: str,
    loader_consumed_build_sha256: str,
    loader_instance_id: str,
    loader_runtime_sha256: str,
    lease_id: str,
    artifact_boundary_receipt_sha256: str,
) -> PhysicalEngineLease:
    """Bind loader-consumed component identities to one verified engine bundle.

    The caller remains responsible for obtaining the consumed digests from an admitted
    loader/boundary. Supplying matching strings here is not runtime attestation by itself.
    """
    current_generation = _generation(current_generation, "current_generation")
    loader_generation = _generation(loader_generation, "loader_generation")
    if loader_generation != current_generation:
        raise PhysicalEngineLeaseError("STALE_LOADER_GENERATION")

    (
        provider_alias,
        engine_identity,
        engine_class,
        engine_artifact_sha256,
        checkpoint_sha256,
        tokenizer_sha256,
        runtime_sha256,
        build_sha256,
        engine_admission_receipt_sha256,
    ) = _verified_admission(
        verified_engine_admission,
        current_generation=current_generation,
    )

    consumed_checkpoint = _sha256(loader_consumed_checkpoint_sha256, "loader_consumed_checkpoint_sha256")
    consumed_tokenizer = _sha256(loader_consumed_tokenizer_sha256, "loader_consumed_tokenizer_sha256")
    consumed_runtime = _sha256(loader_consumed_runtime_sha256, "loader_consumed_runtime_sha256")
    consumed_build = _sha256(loader_consumed_build_sha256, "loader_consumed_build_sha256")
    if consumed_checkpoint != checkpoint_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_CHECKPOINT_MISMATCH")
    if consumed_tokenizer != tokenizer_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_TOKENIZER_MISMATCH")
    if consumed_runtime != runtime_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_RUNTIME_MISMATCH")
    if consumed_build != build_sha256:
        raise PhysicalEngineLeaseError("LOADER_CONSUMED_BUILD_MISMATCH")

    payload = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": current_generation,
        "engine_admission_receipt_sha256": engine_admission_receipt_sha256,
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "engine_artifact_sha256": engine_artifact_sha256,
        "consumed_checkpoint_sha256": consumed_checkpoint,
        "consumed_tokenizer_sha256": consumed_tokenizer,
        "consumed_runtime_sha256": consumed_runtime,
        "consumed_build_sha256": consumed_build,
        "loader_instance_id": _text(loader_instance_id, "loader_instance_id"),
        "loader_runtime_sha256": _sha256(loader_runtime_sha256, "loader_runtime_sha256"),
        "artifact_boundary_receipt_sha256": _sha256(
            artifact_boundary_receipt_sha256,
            "artifact_boundary_receipt_sha256",
        ),
        "lease_id": _text(lease_id, "lease_id"),
    }
    return PhysicalEngineLease(
        **payload,
        lease_sha256=_canonical_sha256(payload, "PHYSICAL_ENGINE_LOAD_LEASE"),
    )


def assert_physical_engine_lease_current(
    lease: PhysicalEngineLease,
    *,
    current_generation: int,
    verified_engine_admission: VerifiedEngineAdmission,
) -> None:
    """Re-check the lease against the current verified engine bundle before inference."""
    if not isinstance(lease, PhysicalEngineLease):
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    if lease.schema != SCHEMA or lease.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_SCHEMA_UNSUPPORTED")
    if lease.entity_generation != current_generation:
        raise PhysicalEngineLeaseError("STALE_PHYSICAL_ENGINE_LEASE")

    (
        provider_alias,
        engine_identity,
        engine_class,
        engine_artifact_sha256,
        checkpoint_sha256,
        tokenizer_sha256,
        runtime_sha256,
        build_sha256,
        engine_admission_receipt_sha256,
    ) = _verified_admission(
        verified_engine_admission,
        current_generation=current_generation,
    )
    expected = {
        "provider_alias": provider_alias,
        "engine_identity": engine_identity,
        "engine_class": engine_class,
        "engine_artifact_sha256": engine_artifact_sha256,
        "engine_admission_receipt_sha256": engine_admission_receipt_sha256,
        "consumed_checkpoint_sha256": checkpoint_sha256,
        "consumed_tokenizer_sha256": tokenizer_sha256,
        "consumed_runtime_sha256": runtime_sha256,
        "consumed_build_sha256": build_sha256,
    }
    for field, value in expected.items():
        if getattr(lease, field) != value:
            raise PhysicalEngineLeaseError(f"PHYSICAL_ENGINE_LEASE_{field.upper()}_REVOKED")

    payload = asdict(lease)
    observed_sha256 = payload.pop("lease_sha256")
    if _canonical_sha256(payload, "PHYSICAL_ENGINE_LOAD_LEASE") != observed_sha256:
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_DIGEST_MISMATCH")


def inference_lease_echo(lease: PhysicalEngineLease) -> dict[str, str | int]:
    if not isinstance(lease, PhysicalEngineLease):
        raise PhysicalEngineLeaseError("PHYSICAL_ENGINE_LEASE_REQUIRED")
    return {
        "engine_load_lease_sha256": lease.lease_sha256,
        "engine_load_lease_generation": lease.entity_generation,
        "engine_admission_receipt_sha256": lease.engine_admission_receipt_sha256,
        "loader_instance_id": lease.loader_instance_id,
        "loader_runtime_sha256": lease.loader_runtime_sha256,
        "artifact_boundary_receipt_sha256": lease.artifact_boundary_receipt_sha256,
        "consumed_checkpoint_sha256": lease.consumed_checkpoint_sha256,
        "consumed_tokenizer_sha256": lease.consumed_tokenizer_sha256,
        "consumed_runtime_sha256": lease.consumed_runtime_sha256,
        "consumed_build_sha256": lease.consumed_build_sha256,
    }
