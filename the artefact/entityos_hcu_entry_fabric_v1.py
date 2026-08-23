#!/usr/bin/env python3
"""Deterministic typed ingress for the current EntityOS/HCU GRID10 baseline.

The Entry Fabric binds immutable observed-event identity separately from the
admission envelope before HCU cognition. It does not decide truth, grant
permissions/capabilities, or authorize effects; EffectGate/EffectJournal remain
outside this boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

EVENT_SCHEMA = "ENTITYOS_ENTRY_EVENT/v1"
PACKET_SCHEMA = "ENTITYOS_HCU_INGRESS_PACKET/v1"
AUTHORITY_STATUS = "CARRIED_NOT_GRANTED"
MAX_BASELINE_LOGICAL_CELLS = 10

ADMITTED_SOURCES = {
    "human_prompt",
    "external_event",
    "tool_outcome",
    "sensor_stream",
    "db_change",
    "intrinsic_system",
}
ADMITTED_MODALITIES = {
    "text",
    "json",
    "event",
    "metric",
    "binary_ref",
    "state_delta",
    "tool_receipt",
}
REQUIRED_BUDGET_KEYS = {
    "max_logical_cells",
    "max_inference_calls",
    "max_wall_ms",
    "max_payload_bytes",
}
ALLOWED_EVENT_KEYS = {
    "schema",
    "causal_id",
    "entity_generation",
    "source",
    "provenance",
    "modality",
    "observed_at",
    "received_at",
    "permissions",
    "capability_scope",
    "parent_or_stream_id",
    "resource_budget",
    "payload",
}


class EntryAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class EntityOSIngressPacket:
    schema: str
    ingress_id: str
    event_sha256: str
    causal_id: str
    generation: int
    source: str
    provenance_sha256: str
    modality: str
    observed_at: str
    received_at: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    authority_status: str
    parent_or_stream_id: str | None
    resource_budget: tuple[tuple[str, int], ...]
    payload_ref: str


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EntryAdmissionError("NON_CANONICAL_JSON_VALUE") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _bounded_text(value: Any, field: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str):
        raise EntryAdmissionError(f"{field}:STRING_REQUIRED")
    value = value.strip()
    if not value:
        raise EntryAdmissionError(f"{field}:NONEMPTY_REQUIRED")
    if len(value) > maximum:
        raise EntryAdmissionError(f"{field}:TOO_LONG")
    return value


def _timestamp(value: Any, field: str) -> str:
    raw = _bounded_text(value, field, maximum=64)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EntryAdmissionError(f"{field}:RFC3339_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise EntryAdmissionError(f"{field}:TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _claims(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EntryAdmissionError(f"{field}:SEQUENCE_REQUIRED")
    normalized: set[str] = set()
    for item in value:
        normalized.add(_bounded_text(item, field, maximum=128))
    return tuple(sorted(normalized))


def _budget(value: Any) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping):
        raise EntryAdmissionError("resource_budget:MAPPING_REQUIRED")
    keys = set(value)
    if keys != REQUIRED_BUDGET_KEYS:
        raise EntryAdmissionError("resource_budget:EXACT_V1_KEYS_REQUIRED")
    normalized: dict[str, int] = {}
    for key in sorted(REQUIRED_BUDGET_KEYS):
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise EntryAdmissionError(f"resource_budget.{key}:NONNEGATIVE_INT_REQUIRED")
        normalized[key] = item
    if normalized["max_logical_cells"] > MAX_BASELINE_LOGICAL_CELLS:
        raise EntryAdmissionError("resource_budget.max_logical_cells:GRID10_LIMIT")
    return tuple(sorted(normalized.items()))


def admit_event(event: Mapping[str, Any], *, current_generation: int) -> EntityOSIngressPacket:
    if not isinstance(event, Mapping):
        raise EntryAdmissionError("EVENT_MAPPING_REQUIRED")
    if event.get("schema") != EVENT_SCHEMA:
        raise EntryAdmissionError("EVENT_SCHEMA_UNSUPPORTED")

    unknown = sorted(set(event) - ALLOWED_EVENT_KEYS)
    if unknown:
        raise EntryAdmissionError(f"UNKNOWN_INGRESS_FIELD:{unknown[0]}")

    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise EntryAdmissionError("CURRENT_GENERATION_INVALID")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise EntryAdmissionError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    causal_id = _bounded_text(event.get("causal_id"), "causal_id")
    source = _bounded_text(event.get("source"), "source").lower()
    if source not in ADMITTED_SOURCES:
        raise EntryAdmissionError("SOURCE_NOT_ADMITTED")
    modality = _bounded_text(event.get("modality"), "modality").lower()
    if modality not in ADMITTED_MODALITIES:
        raise EntryAdmissionError("MODALITY_NOT_ADMITTED")

    provenance = event.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        raise EntryAdmissionError("PROVENANCE_NONEMPTY_MAPPING_REQUIRED")
    provenance_sha256 = _digest(provenance)

    observed_at = _timestamp(event.get("observed_at"), "observed_at")
    received_at = _timestamp(event.get("received_at"), "received_at")
    permissions = _claims(event.get("permissions"), "permissions")
    capability_scope = _claims(event.get("capability_scope"), "capability_scope")

    parent = event.get("parent_or_stream_id")
    if parent is not None:
        parent = _bounded_text(parent, "parent_or_stream_id")

    resource_budget = _budget(event.get("resource_budget"))
    budget_dict = dict(resource_budget)

    payload_bytes = _canonical(event.get("payload"))
    if len(payload_bytes) > budget_dict["max_payload_bytes"]:
        raise EntryAdmissionError("PAYLOAD_EXCEEDS_BOUND_BUDGET")
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    payload_ref = f"sha256:{payload_sha256}"

    event_binding = {
        "schema": EVENT_SCHEMA,
        "causal_id": causal_id,
        "generation": generation,
        "source": source,
        "provenance_sha256": provenance_sha256,
        "modality": modality,
        "observed_at": observed_at,
        "parent_or_stream_id": parent,
        "payload_ref": payload_ref,
    }
    event_sha256 = _digest(event_binding)

    admission_binding = {
        "schema": PACKET_SCHEMA,
        "event_sha256": event_sha256,
        "received_at": received_at,
        "permissions": permissions,
        "capability_scope": capability_scope,
        "authority_status": AUTHORITY_STATUS,
        "resource_budget": budget_dict,
    }
    ingress_id = f"ingress:{_digest(admission_binding)}"

    return EntityOSIngressPacket(
        schema=PACKET_SCHEMA,
        ingress_id=ingress_id,
        event_sha256=event_sha256,
        causal_id=causal_id,
        generation=generation,
        source=source,
        provenance_sha256=provenance_sha256,
        modality=modality,
        observed_at=observed_at,
        received_at=received_at,
        permissions=permissions,
        capability_scope=capability_scope,
        authority_status=AUTHORITY_STATUS,
        parent_or_stream_id=parent,
        resource_budget=resource_budget,
        payload_ref=payload_ref,
    )


def packet_json(packet: EntityOSIngressPacket) -> str:
    value = asdict(packet)
    value["resource_budget"] = dict(packet.resource_budget)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
