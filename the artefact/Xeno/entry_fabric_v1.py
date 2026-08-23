"""Xeno typed ingress boundary v1.

Source candidate only. This module is deliberately deterministic and side-effect free:
it binds new data to causal/generation/provenance/budget metadata before cognition,
without granting truth or effect authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Iterable

SCHEMA_ID = "XENO_INGRESS_PACKET/v1"
_MAX_ID_LEN = 256
_ALLOWED_PAYLOAD_PREFIXES = ("sha256:", "unifieddb:", "object:", "event:")


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
    cleaned = tuple(sorted({_clean_atom(v, field) for v in values}))
    if required and not cleaned:
        raise AdmissionError(f"{field} must not be empty")
    if len(cleaned) > 64:
        raise AdmissionError(f"{field} has too many entries")
    return cleaned


def _parse_time(value: str, field: str) -> datetime:
    text = _clean_atom(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdmissionError(f"{field} must be RFC3339/ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AdmissionError(f"{field} must carry timezone information")
    return parsed


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


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
        if not 1 <= int(self.max_logical_cells) <= 600:
            raise AdmissionError("max_logical_cells must be in [1, 600]")
        if not 0 <= int(self.max_inference_calls) <= 600:
            raise AdmissionError("max_inference_calls must be in [0, 600]")
        if not 0 <= int(self.max_tokens) <= 10_000_000:
            raise AdmissionError("max_tokens must be in [0, 10000000]")
        if not 1 <= int(self.wall_ms) <= 3_600_000:
            raise AdmissionError("wall_ms must be in [1, 3600000]")
        if not 0 <= int(self.memory_bytes) <= 10**15:
            raise AdmissionError("memory_bytes is out of range")
        return ResourceBudget(
            max_logical_cells=int(self.max_logical_cells),
            max_inference_calls=int(self.max_inference_calls),
            max_tokens=int(self.max_tokens),
            wall_ms=int(self.wall_ms),
            memory_bytes=int(self.memory_bytes),
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
    """Admit one typed ingress packet or fail closed.

    The ingress digest commits to the complete admitted event identity. Replaying the
    exact same admitted event is deterministic; materially different events cannot
    alias merely because downstream routing later chooses the same functions.
    """
    generation = int(draft.generation)
    if generation != int(current_generation):
        raise AdmissionError("stale or future generation")
    if generation < 0:
        raise AdmissionError("generation must be non-negative")

    causal_id = _clean_atom(draft.causal_id, "causal_id")
    provenance = _clean_atoms(draft.provenance, "provenance", required=True)
    permissions = _clean_atoms(draft.permissions, "permissions", required=True)
    capability_scope = _clean_atoms(draft.capability_scope, "capability_scope")
    parent = None if draft.parent_or_stream_id is None else _clean_atom(draft.parent_or_stream_id, "parent_or_stream_id")

    observed = _parse_time(draft.observed_at, "observed_at")
    received = _parse_time(draft.received_at, "received_at")
    if observed > received:
        raise AdmissionError("observed_at must not be after received_at")

    payload_ref = _clean_atom(draft.payload_ref, "payload_ref")
    if not payload_ref.startswith(_ALLOWED_PAYLOAD_PREFIXES):
        raise AdmissionError("payload_ref must be an opaque/digest-backed reference, not raw payload")

    try:
        source = IngressSource(draft.source).value
        modality = Modality(draft.modality).value
    except ValueError as exc:
        raise AdmissionError("unknown source or modality") from exc

    budget = draft.resource_budget.normalized()
    material = {
        "schema_id": SCHEMA_ID,
        "causal_id": causal_id,
        "generation": generation,
        "source": source,
        "provenance": list(provenance),
        "modality": modality,
        "observed_at": draft.observed_at,
        "received_at": draft.received_at,
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
        observed_at=draft.observed_at,
        received_at=draft.received_at,
        permissions=permissions,
        capability_scope=capability_scope,
        parent_or_stream_id=parent,
        resource_budget=budget,
        payload_ref=payload_ref,
    )
