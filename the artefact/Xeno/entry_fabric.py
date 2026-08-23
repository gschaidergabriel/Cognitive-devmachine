#!/usr/bin/env python3
"""Typed Xeno ingress admission.

The Entry Fabric binds identity, provenance, generation, permissions and compute budget
*before* cognition. Payload semantics never grant authority. Admitted packets own an
immutable byte copy of the payload so caller mutation cannot change an already-bound
causal object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence
import hashlib
import json
import math


class IngressKind(str, Enum):
    HUMAN_PROMPT = "HUMAN_PROMPT"
    TOOL_OUTCOME = "TOOL_OUTCOME"
    EXTERNAL_EVENT = "EXTERNAL_EVENT"
    SENSOR_SAMPLE = "SENSOR_SAMPLE"
    DATABASE_CHANGE = "DATABASE_CHANGE"
    INTRINSIC_EVENT = "INTRINSIC_EVENT"


class Modality(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"
    BINARY = "BINARY"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    TIMESERIES = "TIMESERIES"
    STATE_DELTA = "STATE_DELTA"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResourceBudget:
    max_compute_tokens: int
    max_context_tokens: int
    max_wall_ms: int
    max_payload_bytes: int = 1_048_576
    max_logical_cells: int = 10
    max_physical_decoders: int = 1

    def validate(self) -> None:
        integer_fields = {
            "max_compute_tokens": self.max_compute_tokens,
            "max_context_tokens": self.max_context_tokens,
            "max_wall_ms": self.max_wall_ms,
            "max_payload_bytes": self.max_payload_bytes,
            "max_logical_cells": self.max_logical_cells,
            "max_physical_decoders": self.max_physical_decoders,
        }
        for name, value in integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be > 0")
        if self.max_logical_cells > 10:
            raise ValueError("GRID10 admission cannot exceed 10 logical cells")
        if self.max_physical_decoders > self.max_logical_cells:
            raise ValueError("physical decoder budget cannot exceed logical cell budget")

    def as_dict(self) -> dict[str, int]:
        self.validate()
        return {
            "max_compute_tokens": self.max_compute_tokens,
            "max_context_tokens": self.max_context_tokens,
            "max_wall_ms": self.max_wall_ms,
            "max_payload_bytes": self.max_payload_bytes,
            "max_logical_cells": self.max_logical_cells,
            "max_physical_decoders": self.max_physical_decoders,
        }


def _canonical_jsonable(value: Any, path: str = "$", active: set[int] | None = None) -> Any:
    """Copy JSON-like payloads into a canonical immutable-bytes representation.

    Semantic field names are deliberately not filtered: ingress data may *describe* an
    effect or authority claim, but those words have no authority. Authority travels only
    in the typed out-of-band admission metadata.
    """

    if active is None:
        active = set()

    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float at {path}")
        return value
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in active:
            raise ValueError(f"cyclic mapping at {path}")
        active.add(object_id)
        try:
            out: dict[str, Any] = {}
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError(f"non-string mapping key at {path}")
                out[key] = _canonical_jsonable(child, f"{path}.{key}", active)
            return out
        finally:
            active.remove(object_id)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, memoryview)):
        object_id = id(value)
        if object_id in active:
            raise ValueError(f"cyclic sequence at {path}")
        active.add(object_id)
        try:
            return [_canonical_jsonable(child, f"{path}[]", active) for child in value]
        finally:
            active.remove(object_id)
    raise ValueError(f"unsupported payload type at {path}: {type(value).__name__}")


def _payload_bytes(payload: Any, modality: Modality) -> bytes:
    if isinstance(payload, memoryview):
        payload = payload.tobytes()
    if isinstance(payload, bytearray):
        payload = bytes(payload)
    if isinstance(payload, bytes):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if modality is Modality.BINARY:
        raise ValueError("BINARY modality requires bytes-like payload")
    canonical = _canonical_jsonable(payload)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _utc_iso(value: datetime, field_name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _frozen_scope(values: Sequence[str] | set[str] | frozenset[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a collection of strings, not a scalar")
    out: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        out.add(value.strip())
    return tuple(sorted(out))


@dataclass(frozen=True)
class XenoIngressPacket:
    ingress_id: str
    causal_id: str
    generation: int
    kind: IngressKind
    source: str
    provenance_ref: str
    modality: Modality
    observed_at: str
    received_at: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    parent_or_stream_id: str | None
    resource_budget: ResourceBudget
    payload_sha256: str
    payload_size: int
    payload_bytes: bytes

    def envelope(self) -> dict[str, Any]:
        return {
            "schema": "XENO_INGRESS_PACKET/v1",
            "ingress_id": self.ingress_id,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "kind": self.kind.value,
            "source": self.source,
            "provenance_ref": self.provenance_ref,
            "modality": self.modality.value,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "permissions": list(self.permissions),
            "capability_scope": list(self.capability_scope),
            "parent_or_stream_id": self.parent_or_stream_id,
            "resource_budget": self.resource_budget.as_dict(),
            "payload_sha256": self.payload_sha256,
            "payload_size": self.payload_size,
        }


class EntryFabric:
    """Deterministic, fail-closed ingress binder.

    This class intentionally exposes no canonical DB write and no EffectGate operation.
    The caller must persist the returned packet through the canonical state layer.
    """

    schema = "XENO_ENTRY_FABRIC/v1"

    @classmethod
    def admit(
        cls,
        *,
        causal_id: str,
        generation: int,
        kind: IngressKind,
        source: str,
        provenance_ref: str,
        modality: Modality,
        observed_at: datetime,
        received_at: datetime,
        permissions: Sequence[str] | set[str] | frozenset[str],
        capability_scope: Sequence[str] | set[str] | frozenset[str],
        resource_budget: ResourceBudget,
        payload: Any,
        parent_or_stream_id: str | None = None,
        current_generation: int | None = None,
    ) -> XenoIngressPacket:
        if not isinstance(causal_id, str) or not causal_id.strip():
            raise ValueError("causal_id must be a non-empty string")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise ValueError("generation must be a non-negative integer")
        if current_generation is not None:
            if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
                raise ValueError("current_generation must be a non-negative integer")
            if generation != current_generation:
                raise ValueError("stale generation")
        if not isinstance(kind, IngressKind):
            raise ValueError("kind must be IngressKind")
        if not isinstance(modality, Modality):
            raise ValueError("modality must be Modality")
        for field_name, value in (("source", source), ("provenance_ref", provenance_ref)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if parent_or_stream_id is not None and (not isinstance(parent_or_stream_id, str) or not parent_or_stream_id.strip()):
            raise ValueError("parent_or_stream_id must be null or a non-empty string")

        resource_budget.validate()
        observed = _utc_iso(observed_at, "observed_at")
        received = _utc_iso(received_at, "received_at")
        if received < observed:
            # ISO strings are both normalized to UTC, so lexical ordering is chronological.
            raise ValueError("received_at cannot precede observed_at")

        immutable_payload = _payload_bytes(payload, modality)
        if len(immutable_payload) > resource_budget.max_payload_bytes:
            raise ValueError("payload exceeds admitted byte budget")
        payload_sha256 = hashlib.sha256(immutable_payload).hexdigest()
        frozen_permissions = _frozen_scope(permissions, "permissions")
        frozen_capabilities = _frozen_scope(capability_scope, "capability_scope")

        identity_envelope = {
            "schema": "XENO_INGRESS_PACKET/v1",
            "causal_id": causal_id.strip(),
            "generation": generation,
            "kind": kind.value,
            "source": source.strip(),
            "provenance_ref": provenance_ref.strip(),
            "modality": modality.value,
            "observed_at": observed,
            "received_at": received,
            "permissions": list(frozen_permissions),
            "capability_scope": list(frozen_capabilities),
            "parent_or_stream_id": parent_or_stream_id.strip() if parent_or_stream_id else None,
            "resource_budget": resource_budget.as_dict(),
            "payload_sha256": payload_sha256,
            "payload_size": len(immutable_payload),
        }
        canonical = json.dumps(identity_envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ingress_id = hashlib.sha256(canonical).hexdigest()

        return XenoIngressPacket(
            ingress_id=ingress_id,
            causal_id=causal_id.strip(),
            generation=generation,
            kind=kind,
            source=source.strip(),
            provenance_ref=provenance_ref.strip(),
            modality=modality,
            observed_at=observed,
            received_at=received,
            permissions=frozen_permissions,
            capability_scope=frozen_capabilities,
            parent_or_stream_id=parent_or_stream_id.strip() if parent_or_stream_id else None,
            resource_budget=resource_budget,
            payload_sha256=payload_sha256,
            payload_size=len(immutable_payload),
            payload_bytes=immutable_payload,
        )
