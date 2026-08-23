"""Xeno typed ingress boundary v1.

Deterministic and side-effect free: bind new data to causal/generation/provenance,
security and resource metadata before cognition. This layer owns neither truth nor effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Iterable

SCHEMA_ID = "XENO_INGRESS_PACKET/v1"
_MAX_ID_LEN = 256
_ALLOWED_PAYLOAD_PREFIXES = ("sha256:", "unifieddb:", "object:", "event:")
_SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class AdmissionError(ValueError):
    """Fail-closed ingress admission error."""


class IngressSource(str, Enum):
    HUMAN = "HUMAN"
    EXTERNAL_EVENT = "EXTERNAL_EVENT"
    TOOL_OUTCOME = "TOOL_OUTCOME"
    SENSOR_STREAM = "SENSOR_STREAM"
    DATABASE_CHANGE = "DATABASE_CHANGE"
    INTRINSIC_EVENT = "INTRINSIC_EVENT"


class Modality(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"
    VECTOR = "VECTOR"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    SENSOR = "SENSOR"
    STATE_DELTA = "STATE_DELTA"
    EVENT = "EVENT"


def _clean_atom(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise AdmissionError(f"{field} must be a string")
    value = value.strip()
    if not value or len(value) > _MAX_ID_LEN:
        raise AdmissionError(f"{field} must be non-empty and <= {_MAX_ID_LEN} chars")
    return value


def _clean_atoms(values: Iterable[str], field: str, *, required: bool = False) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, (tuple, list, set, frozenset)):
        raise AdmissionError(f"{field} must be a collection of strings")
    cleaned = tuple(sorted({_clean_atom(v, field) for v in values}))
    if required and not cleaned:
        raise AdmissionError(f"{field} must not be empty")
    if len(cleaned) > 64:
        raise AdmissionError(f"{field} has too many entries")
    return cleaned


def _strict_int(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdmissionError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise AdmissionError(f"{field} must be in [{minimum}, {maximum}]")
    return value


def _canonical_time(value: str, field: str) -> tuple[datetime, str]:
    text = _clean_atom(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdmissionError(f"{field} must be RFC3339/ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AdmissionError(f"{field} must carry timezone information")
    utc = parsed.astimezone(timezone.utc)
    canonical = utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return utc, canonical


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    max_logical_cells: int
    max_inference_calls: int
    max_tokens: int
    wall_ms: int
    memory_bytes: int = 0

    def normalized(self) -> "ResourceBudget":
        return ResourceBudget(
            max_logical_cells=_strict_int(self.max_logical_cells, "max_logical_cells", 1, 600),
            max_inference_calls=_strict_int(self.max_inference_calls, "max_inference_calls", 0, 600),
            max_tokens=_strict_int(self.max_tokens, "max_tokens", 0, 10_000_000),
            wall_ms=_strict_int(self.wall_ms, "wall_ms", 1, 3_600_000),
            memory_bytes=_strict_int(self.memory_bytes, "memory_bytes", 0, 10**15),
        )


@dataclass(frozen=True, slots=True)
class XenoIngressDraft:
    causal_id: str
    generation: int
    source: IngressSource
    provenance: tuple[str, ...]
    modality: Modality
    observed_at: str
    received_at: str
    isolation_domain: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    resource_budget: ResourceBudget
    payload_ref: str
    parent_or_stream_id: str | None = None


@dataclass(frozen=True, slots=True)
class XenoIngressPacket:
    schema_id: str
    ingress_id: str
    causal_id: str
    generation: int
    source: str
    provenance: tuple[str, ...]
    modality: str
    observed_at: str
    received_at: str
    isolation_domain: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    parent_or_stream_id: str | None
    resource_budget: ResourceBudget
    payload_ref: str

    def identity_material(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "source": self.source,
            "provenance": list(self.provenance),
            "modality": self.modality,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "isolation_domain": self.isolation_domain,
            "permissions": list(self.permissions),
            "capability_scope": list(self.capability_scope),
            "parent_or_stream_id": self.parent_or_stream_id,
            "resource_budget": {
                "max_logical_cells": self.resource_budget.max_logical_cells,
                "max_inference_calls": self.resource_budget.max_inference_calls,
                "max_tokens": self.resource_budget.max_tokens,
                "wall_ms": self.resource_budget.wall_ms,
                "memory_bytes": self.resource_budget.memory_bytes,
            },
            "payload_ref": self.payload_ref,
        }

    def receipt(self) -> dict[str, object]:
        return {**self.identity_material(), "ingress_id": self.ingress_id}


def admit_ingress(draft: XenoIngressDraft, *, current_generation: int) -> XenoIngressPacket:
    """Admit one typed ingress packet or fail closed."""
    if not isinstance(draft, XenoIngressDraft):
        raise AdmissionError("draft must be XenoIngressDraft")
    generation = _strict_int(draft.generation, "generation", 0, 2**63 - 1)
    current = _strict_int(current_generation, "current_generation", 0, 2**63 - 1)
    if generation != current:
        raise AdmissionError("stale or future generation")

    causal_id = _clean_atom(draft.causal_id, "causal_id")
    provenance = _clean_atoms(draft.provenance, "provenance", required=True)
    isolation_domain = _clean_atom(draft.isolation_domain, "isolation_domain")
    permissions = _clean_atoms(draft.permissions, "permissions", required=True)
    capability_scope = _clean_atoms(draft.capability_scope, "capability_scope")
    parent = None if draft.parent_or_stream_id is None else _clean_atom(draft.parent_or_stream_id, "parent_or_stream_id")

    observed, observed_text = _canonical_time(draft.observed_at, "observed_at")
    received, received_text = _canonical_time(draft.received_at, "received_at")
    if observed > received:
        raise AdmissionError("observed_at must not be after received_at")

    payload_ref = _clean_atom(draft.payload_ref, "payload_ref")
    if not payload_ref.startswith(_ALLOWED_PAYLOAD_PREFIXES):
        raise AdmissionError("payload_ref must be an opaque/digest-backed reference, not raw payload")
    if payload_ref.startswith("sha256:") and not _SHA256_REF_RE.fullmatch(payload_ref):
        raise AdmissionError("sha256 payload_ref must contain exactly 64 lowercase hex characters")

    try:
        source = IngressSource(draft.source).value
        modality = Modality(draft.modality).value
    except (TypeError, ValueError) as exc:
        raise AdmissionError("unknown source or modality") from exc

    if not isinstance(draft.resource_budget, ResourceBudget):
        raise AdmissionError("resource_budget must be ResourceBudget")
    budget = draft.resource_budget.normalized()
    material = {
        "schema_id": SCHEMA_ID,
        "causal_id": causal_id,
        "generation": generation,
        "source": source,
        "provenance": list(provenance),
        "modality": modality,
        "observed_at": observed_text,
        "received_at": received_text,
        "isolation_domain": isolation_domain,
        "permissions": list(permissions),
        "capability_scope": list(capability_scope),
        "parent_or_stream_id": parent,
        "resource_budget": {
            "max_logical_cells": budget.max_logical_cells,
            "max_inference_calls": budget.max_inference_calls,
            "max_tokens": budget.max_tokens,
            "wall_ms": budget.wall_ms,
            "memory_bytes": budget.memory_bytes,
        },
        "payload_ref": payload_ref,
    }
    ingress_id = f"xeno-ingress:{_digest(material)}"
    return XenoIngressPacket(
        schema_id=SCHEMA_ID,
        ingress_id=ingress_id,
        causal_id=causal_id,
        generation=generation,
        source=source,
        provenance=provenance,
        modality=modality,
        observed_at=observed_text,
        received_at=received_text,
        isolation_domain=isolation_domain,
        permissions=permissions,
        capability_scope=capability_scope,
        parent_or_stream_id=parent,
        resource_budget=budget,
        payload_ref=payload_ref,
    )


def verify_ingress_packet(packet: XenoIngressPacket, *, current_generation: int) -> XenoIngressPacket:
    """Re-admit packet material and require byte-semantic identity before downstream use.

    This prevents callers from bypassing Entry admission by directly constructing the
    frozen dataclass with a forged ingress_id, generation, budget or authority metadata.
    """
    if not isinstance(packet, XenoIngressPacket):
        raise AdmissionError("packet must be XenoIngressPacket")
    if packet.schema_id != SCHEMA_ID:
        raise AdmissionError("unsupported ingress schema")
    expected = admit_ingress(
        XenoIngressDraft(
            causal_id=packet.causal_id,
            generation=packet.generation,
            source=packet.source,
            provenance=packet.provenance,
            modality=packet.modality,
            observed_at=packet.observed_at,
            received_at=packet.received_at,
            isolation_domain=packet.isolation_domain,
            permissions=packet.permissions,
            capability_scope=packet.capability_scope,
            resource_budget=packet.resource_budget,
            payload_ref=packet.payload_ref,
            parent_or_stream_id=packet.parent_or_stream_id,
        ),
        current_generation=current_generation,
    )
    if packet != expected:
        raise AdmissionError("ingress packet identity/material mismatch")
    return packet
