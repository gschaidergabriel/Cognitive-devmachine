#!/usr/bin/env python3
"""Typed Xeno Entry Fabric v1.

The Entry Fabric binds untrusted/new inputs to causal/provenance/generation metadata before
cognition. It is deliberately authority-light: durable admission/replay state belongs in the
canonical state store, and this module exposes no canonical write or real-effect primitive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

INGRESS_SCHEMA_ID = "XENO_INGRESS_PACKET/v1"
ADMISSION_SCHEMA_ID = "XENO_ENTRY_ADMISSION/v1"


class EntryFabricError(ValueError):
    """Base fail-closed Entry Fabric error."""


class StaleGenerationError(EntryFabricError):
    """Ingress or dispatch is bound to a stale entity generation."""


class ReplayRejectedError(EntryFabricError):
    """A producer event identity has already been admitted canonically."""


class DispatchBindingError(EntryFabricError):
    """Packet/receipt/canonical admission binding is incomplete or inconsistent."""


class IngressKind(str, Enum):
    HUMAN_PROMPT = "HUMAN_PROMPT"
    EXTERNAL_EVENT = "EXTERNAL_EVENT"
    TOOL_OUTCOME = "TOOL_OUTCOME"
    SENSOR_STREAM = "SENSOR_STREAM"
    DATABASE_CHANGE = "DATABASE_CHANGE"
    SYSTEM_EVENT = "SYSTEM_EVENT"


@dataclass(frozen=True)
class ResourceBudget:
    max_logical_cells: int
    max_tokens: int
    max_wall_ms: int
    max_branches: int

    def validate(self) -> None:
        values = {
            "max_logical_cells": self.max_logical_cells,
            "max_tokens": self.max_tokens,
            "max_wall_ms": self.max_wall_ms,
            "max_branches": self.max_branches,
        }
        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise EntryFabricError(f"{name} must be an integer")
            if value <= 0:
                raise EntryFabricError(f"{name} must be > 0")

    def canonical_obj(self) -> dict[str, int]:
        self.validate()
        return {
            "max_logical_cells": self.max_logical_cells,
            "max_tokens": self.max_tokens,
            "max_wall_ms": self.max_wall_ms,
            "max_branches": self.max_branches,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResourceBudget":
        allowed = {"max_logical_cells", "max_tokens", "max_wall_ms", "max_branches"}
        unknown = set(value) - allowed
        missing = allowed - set(value)
        if unknown or missing:
            raise EntryFabricError(
                f"resource_budget keys mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
            )
        budget = cls(**{key: value[key] for key in allowed})
        budget.validate()
        return budget


@dataclass(frozen=True)
class IngressRequest:
    event_id: str
    source: str
    event_type: str
    kind: IngressKind
    causal_id: str
    generation: int
    modality: str
    observed_at: str
    received_at: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    resource_budget: ResourceBudget
    payload_ref: str
    parent_or_stream_id: str | None = None
    traceparent: str | None = None

    def validate(self) -> None:
        required_strings = {
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type,
            "causal_id": self.causal_id,
            "modality": self.modality,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "payload_ref": self.payload_ref,
        }
        for name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise EntryFabricError(f"{name} must be a non-empty string")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise EntryFabricError("generation must be a non-negative integer")
        if not isinstance(self.kind, IngressKind):
            raise EntryFabricError("kind must be an IngressKind")
        observed = _parse_aware_time(self.observed_at, "observed_at")
        received = _parse_aware_time(self.received_at, "received_at")
        if received < observed:
            raise EntryFabricError("received_at must be >= observed_at")
        _validate_sorted_unique_strings(self.permissions, "permissions")
        _validate_sorted_unique_strings(self.capability_scope, "capability_scope")
        if self.parent_or_stream_id is not None and not self.parent_or_stream_id.strip():
            raise EntryFabricError("parent_or_stream_id must be non-empty when present")
        if self.traceparent is not None and not self.traceparent.strip():
            raise EntryFabricError("traceparent must be non-empty when present")
        self.resource_budget.validate()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "IngressRequest":
        allowed = {
            "event_id",
            "source",
            "event_type",
            "kind",
            "causal_id",
            "generation",
            "modality",
            "observed_at",
            "received_at",
            "permissions",
            "capability_scope",
            "resource_budget",
            "payload_ref",
            "parent_or_stream_id",
            "traceparent",
        }
        required = allowed - {"parent_or_stream_id", "traceparent"}
        unknown = set(value) - allowed
        missing = required - set(value)
        if unknown or missing:
            raise EntryFabricError(f"ingress keys mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")
        try:
            kind = IngressKind(value["kind"])
        except (KeyError, ValueError) as exc:
            raise EntryFabricError("invalid ingress kind") from exc
        permissions = _tuple_of_strings(value["permissions"], "permissions")
        capability_scope = _tuple_of_strings(value["capability_scope"], "capability_scope")
        budget_raw = value["resource_budget"]
        if not isinstance(budget_raw, Mapping):
            raise EntryFabricError("resource_budget must be a mapping")
        request = cls(
            event_id=value["event_id"],
            source=value["source"],
            event_type=value["event_type"],
            kind=kind,
            causal_id=value["causal_id"],
            generation=value["generation"],
            modality=value["modality"],
            observed_at=value["observed_at"],
            received_at=value["received_at"],
            permissions=permissions,
            capability_scope=capability_scope,
            resource_budget=ResourceBudget.from_mapping(budget_raw),
            payload_ref=value["payload_ref"],
            parent_or_stream_id=value.get("parent_or_stream_id"),
            traceparent=value.get("traceparent"),
        )
        request.validate()
        return request


@dataclass(frozen=True)
class XenoIngressPacket:
    ingress_id: str
    event_key: str
    event_id: str
    source: str
    event_type: str
    kind: IngressKind
    causal_id: str
    generation: int
    modality: str
    observed_at: str
    received_at: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    resource_budget: ResourceBudget
    payload_ref: str
    parent_or_stream_id: str | None = None
    traceparent: str | None = None
    schema_id: str = INGRESS_SCHEMA_ID

    def validate(self) -> None:
        if self.schema_id != INGRESS_SCHEMA_ID:
            raise EntryFabricError("unexpected ingress schema_id")
        req = IngressRequest(
            event_id=self.event_id,
            source=self.source,
            event_type=self.event_type,
            kind=self.kind,
            causal_id=self.causal_id,
            generation=self.generation,
            modality=self.modality,
            observed_at=self.observed_at,
            received_at=self.received_at,
            permissions=self.permissions,
            capability_scope=self.capability_scope,
            resource_budget=self.resource_budget,
            payload_ref=self.payload_ref,
            parent_or_stream_id=self.parent_or_stream_id,
            traceparent=self.traceparent,
        )
        req.validate()
        expected_event_key = event_key(self.source, self.event_id)
        if self.event_key != expected_event_key:
            raise EntryFabricError("event_key mismatch")
        expected_ingress_id = ingress_id_for(req, expected_event_key)
        if self.ingress_id != expected_ingress_id:
            raise EntryFabricError("ingress_id mismatch")

    def canonical_obj(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_id": self.schema_id,
            "ingress_id": self.ingress_id,
            "event_key": self.event_key,
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type,
            "kind": self.kind.value,
            "causal_id": self.causal_id,
            "generation": self.generation,
            "modality": self.modality,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "permissions": list(self.permissions),
            "capability_scope": list(self.capability_scope),
            "resource_budget": self.resource_budget.canonical_obj(),
            "payload_ref": self.payload_ref,
            "parent_or_stream_id": self.parent_or_stream_id,
            "traceparent": self.traceparent,
        }

    def packet_digest(self) -> str:
        return _sha256_json(self.canonical_obj())


@dataclass(frozen=True)
class EntryAdmissionReceipt:
    ingress_id: str
    event_key: str
    packet_digest: str
    admitted_generation: int
    source: str
    event_id: str
    schema_id: str = ADMISSION_SCHEMA_ID

    def validate(self) -> None:
        if self.schema_id != ADMISSION_SCHEMA_ID:
            raise EntryFabricError("unexpected admission schema_id")
        for name, value in {
            "ingress_id": self.ingress_id,
            "event_key": self.event_key,
            "packet_digest": self.packet_digest,
            "source": self.source,
            "event_id": self.event_id,
        }.items():
            if not isinstance(value, str) or not value:
                raise EntryFabricError(f"{name} must be non-empty")
        if isinstance(self.admitted_generation, bool) or not isinstance(self.admitted_generation, int):
            raise EntryFabricError("admitted_generation must be an integer")
        if self.admitted_generation < 0:
            raise EntryFabricError("admitted_generation must be >= 0")

    def canonical_obj(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_id": self.schema_id,
            "ingress_id": self.ingress_id,
            "event_key": self.event_key,
            "packet_digest": self.packet_digest,
            "admitted_generation": self.admitted_generation,
            "source": self.source,
            "event_id": self.event_id,
        }

    def receipt_digest(self) -> str:
        return _sha256_json(self.canonical_obj())


def event_key(source: str, event_id: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise EntryFabricError("source must be non-empty")
    if not isinstance(event_id, str) or not event_id.strip():
        raise EntryFabricError("event_id must be non-empty")
    return hashlib.sha256((source + "\x00" + event_id).encode("utf-8")).hexdigest()


def ingress_id_for(request: IngressRequest, bound_event_key: str | None = None) -> str:
    request.validate()
    key = bound_event_key or event_key(request.source, request.event_id)
    return _sha256_json(
        {
            "schema_id": INGRESS_SCHEMA_ID,
            "event_key": key,
            "causal_id": request.causal_id,
            "generation": request.generation,
            "event_type": request.event_type,
            "kind": request.kind.value,
            "payload_ref": request.payload_ref,
            "parent_or_stream_id": request.parent_or_stream_id,
        }
    )


def admit_ingress(
    request: IngressRequest,
    *,
    current_generation: int,
    canonical_seen_event_keys: Iterable[str] = (),
) -> tuple[XenoIngressPacket, EntryAdmissionReceipt]:
    """Validate/bind ingress without becoming a durable replay authority.

    `canonical_seen_event_keys` is a caller-provided snapshot from the canonical state store.
    The returned receipt must be durably recorded there before dispatch credit is granted.
    """

    request.validate()
    _validate_generation_value(current_generation, "current_generation")
    if request.generation != current_generation:
        raise StaleGenerationError("ingress generation does not match current entity generation")

    key = event_key(request.source, request.event_id)
    seen = set(canonical_seen_event_keys)
    if key in seen:
        raise ReplayRejectedError("source+event_id already admitted")

    packet = XenoIngressPacket(
        ingress_id=ingress_id_for(request, key),
        event_key=key,
        event_id=request.event_id,
        source=request.source,
        event_type=request.event_type,
        kind=request.kind,
        causal_id=request.causal_id,
        generation=request.generation,
        modality=request.modality,
        observed_at=request.observed_at,
        received_at=request.received_at,
        permissions=request.permissions,
        capability_scope=request.capability_scope,
        resource_budget=request.resource_budget,
        payload_ref=request.payload_ref,
        parent_or_stream_id=request.parent_or_stream_id,
        traceparent=request.traceparent,
    )
    packet.validate()
    receipt = EntryAdmissionReceipt(
        ingress_id=packet.ingress_id,
        event_key=packet.event_key,
        packet_digest=packet.packet_digest(),
        admitted_generation=packet.generation,
        source=packet.source,
        event_id=packet.event_id,
    )
    receipt.validate()
    return packet, receipt


def validate_for_dispatch(
    packet: XenoIngressPacket,
    receipt: EntryAdmissionReceipt,
    *,
    current_generation: int,
    canonical_receipt_digest: str,
) -> None:
    """Re-check the canonical admission and live generation immediately before cognition.

    This second generation fence closes admission->queue->generation-change TOCTOU/replay debt.
    The caller supplies `canonical_receipt_digest` from the canonical state store; this module does
    not maintain its own durable replay ledger.
    """

    packet.validate()
    receipt.validate()
    _validate_generation_value(current_generation, "current_generation")
    if not isinstance(canonical_receipt_digest, str) or not canonical_receipt_digest:
        raise DispatchBindingError("canonical_receipt_digest must be non-empty")
    if receipt.receipt_digest() != canonical_receipt_digest:
        raise DispatchBindingError("admission receipt is not bound to canonical receipt digest")
    if receipt.ingress_id != packet.ingress_id:
        raise DispatchBindingError("receipt ingress_id mismatch")
    if receipt.event_key != packet.event_key:
        raise DispatchBindingError("receipt event_key mismatch")
    if receipt.packet_digest != packet.packet_digest():
        raise DispatchBindingError("receipt packet_digest mismatch")
    if receipt.source != packet.source or receipt.event_id != packet.event_id:
        raise DispatchBindingError("receipt producer identity mismatch")
    if receipt.admitted_generation != packet.generation:
        raise DispatchBindingError("receipt generation mismatch")
    if packet.generation != current_generation:
        raise StaleGenerationError("queued ingress became stale before dispatch")


def _tuple_of_strings(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise EntryFabricError(f"{name} must be a list/tuple")
    if any(not isinstance(item, str) for item in value):
        raise EntryFabricError(f"{name} entries must be strings")
    result = tuple(value)
    _validate_sorted_unique_strings(result, name)
    return result


def _validate_sorted_unique_strings(values: tuple[str, ...], name: str) -> None:
    if any(not item.strip() for item in values):
        raise EntryFabricError(f"{name} entries must be non-empty")
    if tuple(sorted(set(values))) != values:
        raise EntryFabricError(f"{name} must be sorted and unique")


def _parse_aware_time(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EntryFabricError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EntryFabricError(f"{name} must include a timezone")
    return parsed


def _validate_generation_value(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntryFabricError(f"{name} must be a non-negative integer")


def _sha256_json(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
