#!/usr/bin/env python3
"""Generation-fenced physical HCU engine-load lease and consumption receipt.

This is downstream evidence plumbing only. It does not grant engine admission, truth,
capabilities, routing authority, durable state authority, or effects. A VerifiedEngineAdmission
proves pre-load artifact identity; this module separately binds that admission to evidence
reported from the actual loader read path. Source-level construction alone grants zero runtime
credit until the real loader is instrumented to emit the consumed-byte evidence used here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
from engine_admission_v1 import ArtifactDigest, VerifiedEngineAdmission

LEASE_SCHEMA = "HCU_ENGINE_LOAD_LEASE/v1"
CONSUMPTION_SCHEMA = "HCU_ENGINE_LOAD_CONSUMPTION/v1"
VERIFIED_LOAD_SCHEMA = "HCU_VERIFIED_ENGINE_LOAD/v1"
ACTUAL_LOADER_EVIDENCE_SOURCE = "ACTUAL_LOADER_READ_PATH"


class EngineLoadLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class LoaderConsumedArtifact:
    kind: str
    sha256: str
    file_count: int
    byte_count: int
    evidence_source: str = ACTUAL_LOADER_EVIDENCE_SOURCE


@dataclass(frozen=True)
class LoaderConsumption:
    schema: str
    entity_generation: int
    loader_id: str
    loader_binding_sha256: str
    engine_identity: str
    engine_artifact_sha256: str
    checkpoint: LoaderConsumedArtifact
    tokenizer: LoaderConsumedArtifact
    runtime: LoaderConsumedArtifact
    build: LoaderConsumedArtifact


@dataclass(frozen=True)
class EngineLoadLease:
    schema: str
    canonicalization_schema: str
    entity_generation: int
    loader_id: str
    loader_binding_sha256: str
    engine_admission_receipt_sha256: str
    engine_identity: str
    engine_class: str
    engine_artifact_sha256: str
    checkpoint: ArtifactDigest
    tokenizer: ArtifactDigest
    runtime: ArtifactDigest
    build: ArtifactDigest
    lease_sha256: str


@dataclass(frozen=True)
class VerifiedEngineLoad:
    schema: str
    canonicalization_schema: str
    entity_generation: int
    loader_id: str
    loader_binding_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_lease_sha256: str
    engine_identity: str
    engine_class: str
    engine_artifact_sha256: str
    checkpoint: LoaderConsumedArtifact
    tokenizer: LoaderConsumedArtifact
    runtime: LoaderConsumedArtifact
    build: LoaderConsumedArtifact
    consumption_receipt_sha256: str

    def inference_echo(self) -> dict[str, Any]:
        """Fields the downstream inference receipt must echo exactly."""
        return {
            "engine_load_canonicalization_schema": self.canonicalization_schema,
            "engine_load_loader_binding_sha256": self.loader_binding_sha256,
            "engine_admission_receipt_sha256": self.engine_admission_receipt_sha256,
            "engine_load_lease_sha256": self.engine_load_lease_sha256,
            "engine_load_consumption_receipt_sha256": self.consumption_receipt_sha256,
            "engine_load_loader_id": self.loader_id,
        }


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EngineLoadLeaseError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise EngineLoadLeaseError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise EngineLoadLeaseError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EngineLoadLeaseError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EngineLoadLeaseError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _artifact_material(value: ArtifactDigest) -> dict[str, Any]:
    if not isinstance(value, ArtifactDigest):
        raise EngineLoadLeaseError("ARTIFACT_DIGEST_TYPE_REQUIRED")
    return {
        "kind": _text(value.kind, "artifact.kind"),
        "sha256": _sha256(value.sha256, "artifact.sha256"),
        "file_count": _count(value.file_count, "artifact.file_count"),
        "byte_count": _count(value.byte_count, "artifact.byte_count"),
    }


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        payload = canonicalize(value)
    except CanonicalizationError as exc:
        raise EngineLoadLeaseError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(payload).hexdigest()


def _verified_admission(value: Any, *, current_generation: int) -> VerifiedEngineAdmission:
    if not isinstance(value, VerifiedEngineAdmission):
        raise EngineLoadLeaseError("VERIFIED_ENGINE_ADMISSION_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    admission_generation = _generation(value.entity_generation, "engine_admission.entity_generation")
    if admission_generation != current_generation:
        raise EngineLoadLeaseError("STALE_ENTITY_GENERATION")
    _sha256(value.receipt_sha256, "engine_admission.receipt_sha256")
    _sha256(value.engine_artifact_sha256, "engine_admission.engine_artifact_sha256")
    _text(value.admission.engine_identity, "engine_admission.engine_identity")
    _text(value.admission.engine_class, "engine_admission.engine_class")
    if value.admission.engine_artifact_sha256 != value.engine_artifact_sha256:
        raise EngineLoadLeaseError("ENGINE_ADMISSION_ARTIFACT_IDENTITY_MISMATCH")
    for artifact in (value.checkpoint, value.tokenizer, value.runtime, value.build):
        _artifact_material(artifact)
    return value


def issue_engine_load_lease(
    verified_admission: VerifiedEngineAdmission,
    *,
    loader_id: str,
    loader_binding_sha256: str,
    current_generation: int,
) -> EngineLoadLease:
    """Issue an intent lease over already-verified pre-load artifact identities.

    The lease is not proof that loading happened. It only defines exactly which admission,
    generation, loader and bytes a later actual-loader consumption receipt must match.
    """
    verified = _verified_admission(verified_admission, current_generation=current_generation)
    loader_id = _text(loader_id, "loader_id")
    loader_binding_sha256 = _sha256(loader_binding_sha256, "loader_binding_sha256")
    material = {
        "schema": LEASE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": verified.entity_generation,
        "loader_id": loader_id,
        "loader_binding_sha256": loader_binding_sha256,
        "engine_admission_receipt_sha256": verified.receipt_sha256,
        "engine_identity": verified.admission.engine_identity,
        "engine_class": verified.admission.engine_class,
        "engine_artifact_sha256": verified.engine_artifact_sha256,
        "checkpoint": _artifact_material(verified.checkpoint),
        "tokenizer": _artifact_material(verified.tokenizer),
        "runtime": _artifact_material(verified.runtime),
        "build": _artifact_material(verified.build),
    }
    lease_sha256 = _canonical_sha256(material, "ENGINE_LOAD_LEASE")
    return EngineLoadLease(
        schema=LEASE_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entity_generation=verified.entity_generation,
        loader_id=loader_id,
        loader_binding_sha256=loader_binding_sha256,
        engine_admission_receipt_sha256=verified.receipt_sha256,
        engine_identity=verified.admission.engine_identity,
        engine_class=verified.admission.engine_class,
        engine_artifact_sha256=verified.engine_artifact_sha256,
        checkpoint=verified.checkpoint,
        tokenizer=verified.tokenizer,
        runtime=verified.runtime,
        build=verified.build,
        lease_sha256=lease_sha256,
    )


def _consumed_artifact(
    actual: LoaderConsumedArtifact,
    expected: ArtifactDigest,
    field: str,
) -> LoaderConsumedArtifact:
    if not isinstance(actual, LoaderConsumedArtifact):
        raise EngineLoadLeaseError(f"{field}:LOADER_CONSUMED_ARTIFACT_REQUIRED")
    if actual.evidence_source != ACTUAL_LOADER_EVIDENCE_SOURCE:
        raise EngineLoadLeaseError(f"{field}:ACTUAL_LOADER_READ_EVIDENCE_REQUIRED")
    expected_material = _artifact_material(expected)
    actual_material = {
        "kind": _text(actual.kind, f"{field}.kind"),
        "sha256": _sha256(actual.sha256, f"{field}.sha256"),
        "file_count": _count(actual.file_count, f"{field}.file_count"),
        "byte_count": _count(actual.byte_count, f"{field}.byte_count"),
    }
    if actual_material != expected_material:
        raise EngineLoadLeaseError(f"{field}:CONSUMED_BYTES_MISMATCH")
    return actual


def verify_loader_consumption(
    lease: EngineLoadLease,
    verified_admission: VerifiedEngineAdmission,
    consumption: LoaderConsumption,
    *,
    current_generation: int,
) -> VerifiedEngineLoad:
    """Bind actual-loader consumption evidence to one admitted physical engine lease.

    Runtime credit remains zero unless the real loader is the producer of `consumption`.
    A caller-constructed or post-hoc filesystem rehash is not equivalent evidence and must
    not be represented as loader attestation.
    """
    if not isinstance(lease, EngineLoadLease):
        raise EngineLoadLeaseError("ENGINE_LOAD_LEASE_REQUIRED")
    verified = _verified_admission(verified_admission, current_generation=current_generation)
    current_generation = _generation(current_generation, "current_generation")
    if lease.schema != LEASE_SCHEMA or lease.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise EngineLoadLeaseError("ENGINE_LOAD_LEASE_SCHEMA_UNSUPPORTED")
    if lease.entity_generation != current_generation:
        raise EngineLoadLeaseError("STALE_ENGINE_LOAD_LEASE")
    if lease.engine_admission_receipt_sha256 != verified.receipt_sha256:
        raise EngineLoadLeaseError("ENGINE_ADMISSION_RECEIPT_MISMATCH")
    if lease.engine_artifact_sha256 != verified.engine_artifact_sha256:
        raise EngineLoadLeaseError("ENGINE_ARTIFACT_MISMATCH")
    if lease.engine_identity != verified.admission.engine_identity or lease.engine_class != verified.admission.engine_class:
        raise EngineLoadLeaseError("ENGINE_IDENTITY_OR_CLASS_MISMATCH")

    expected_lease = issue_engine_load_lease(
        verified,
        loader_id=lease.loader_id,
        loader_binding_sha256=lease.loader_binding_sha256,
        current_generation=current_generation,
    )
    if expected_lease != lease:
        raise EngineLoadLeaseError("ENGINE_LOAD_LEASE_IDENTITY_MISMATCH")

    if not isinstance(consumption, LoaderConsumption):
        raise EngineLoadLeaseError("LOADER_CONSUMPTION_REQUIRED")
    if consumption.schema != CONSUMPTION_SCHEMA:
        raise EngineLoadLeaseError("LOADER_CONSUMPTION_SCHEMA_UNSUPPORTED")
    if _generation(consumption.entity_generation, "consumption.entity_generation") != current_generation:
        raise EngineLoadLeaseError("STALE_LOADER_CONSUMPTION")
    loader_id = _text(consumption.loader_id, "consumption.loader_id")
    if loader_id != lease.loader_id:
        raise EngineLoadLeaseError("LOADER_ID_MISMATCH")
    loader_binding_sha256 = _sha256(consumption.loader_binding_sha256, "consumption.loader_binding_sha256")
    if loader_binding_sha256 != lease.loader_binding_sha256:
        raise EngineLoadLeaseError("LOADER_BINDING_MISMATCH")
    if _text(consumption.engine_identity, "consumption.engine_identity") != lease.engine_identity:
        raise EngineLoadLeaseError("CONSUMPTION_ENGINE_IDENTITY_MISMATCH")
    if _sha256(consumption.engine_artifact_sha256, "consumption.engine_artifact_sha256") != lease.engine_artifact_sha256:
        raise EngineLoadLeaseError("CONSUMPTION_ENGINE_ARTIFACT_MISMATCH")

    checkpoint = _consumed_artifact(consumption.checkpoint, verified.checkpoint, "checkpoint")
    tokenizer = _consumed_artifact(consumption.tokenizer, verified.tokenizer, "tokenizer")
    runtime = _consumed_artifact(consumption.runtime, verified.runtime, "runtime")
    build = _consumed_artifact(consumption.build, verified.build, "build")

    material = {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": current_generation,
        "loader_id": loader_id,
        "loader_binding_sha256": loader_binding_sha256,
        "engine_admission_receipt_sha256": verified.receipt_sha256,
        "engine_load_lease_sha256": lease.lease_sha256,
        "engine_identity": lease.engine_identity,
        "engine_class": lease.engine_class,
        "engine_artifact_sha256": lease.engine_artifact_sha256,
        "checkpoint": {
            **_artifact_material(verified.checkpoint),
            "evidence_source": checkpoint.evidence_source,
        },
        "tokenizer": {
            **_artifact_material(verified.tokenizer),
            "evidence_source": tokenizer.evidence_source,
        },
        "runtime": {
            **_artifact_material(verified.runtime),
            "evidence_source": runtime.evidence_source,
        },
        "build": {
            **_artifact_material(verified.build),
            "evidence_source": build.evidence_source,
        },
    }
    receipt_sha256 = _canonical_sha256(material, "ENGINE_LOAD_CONSUMPTION")
    return VerifiedEngineLoad(
        schema=VERIFIED_LOAD_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entity_generation=current_generation,
        loader_id=loader_id,
        loader_binding_sha256=loader_binding_sha256,
        engine_admission_receipt_sha256=verified.receipt_sha256,
        engine_load_lease_sha256=lease.lease_sha256,
        engine_identity=lease.engine_identity,
        engine_class=lease.engine_class,
        engine_artifact_sha256=lease.engine_artifact_sha256,
        checkpoint=checkpoint,
        tokenizer=tokenizer,
        runtime=runtime,
        build=build,
        consumption_receipt_sha256=receipt_sha256,
    )
