#!/usr/bin/env python3
"""Typed legacy-Xeno Entry Fabric admission for EntityOS/HCU cognition.

This module is deterministic and non-cognitive. It binds identity, generation,
provenance, modality, an externally-authorized capability snapshot, resource budget and
payload identity before any HCU/model work. It does not mint truth, permissions or effects.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

ENTRY_SCHEMA = "XENO_ENTRY_PACKET/v1"
HCU_EVENT_SCHEMA = "HCU_REACTIVE_EVENT/v1"

SOURCE_KINDS = {
    "HUMAN_PROMPT",
    "EXTERNAL_EVENT",
    "TOOL_OUTCOME",
    "SENSOR_STREAM",
    "DATABASE_CHANGE",
    "INTRINSIC_SYSTEM_EVENT",
}
MODALITIES = {"TEXT", "JSON", "BINARY_REF", "SENSOR", "EVENT"}
ENTRY_FIELDS = {
    "schema",
    "ingress_id",
    "causal_id",
    "entity_generation",
    "source_kind",
    "source_id",
    "modality",
    "observed_time",
    "received_time",
    "provenance_ref",
    "provenance_sha256",
    "capabilities",
    "capability_binding_sha256",
    "parent_id",
    "stream_id",
    "budget",
    "payload_ref",
    "payload_sha256",
}
BUDGET_FIELDS = {"max_model_calls", "max_tokens", "max_wall_ms"}


class EntryFabricError(ValueError):
    pass


@dataclass(frozen=True)
class EntryPacket:
    schema: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    source_kind: str
    source_id: str
    modality: str
    observed_time: str | None
    received_time: str
    provenance_ref: str
    provenance_sha256: str
    capabilities: tuple[str, ...]
    capability_binding_sha256: str
    parent_id: str | None
    stream_id: str | None
    budget: tuple[tuple[str, int], ...]
    payload_ref: str
    payload_sha256: str
    admission_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EntryFabricError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 512:
        raise EntryFabricError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise EntryFabricError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise EntryFabricError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _timestamp(value: Any, field: str, *, optional: bool = False) -> str | None:
    value = _text(value, field, optional=optional)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EntryFabricError(f"{field}:RFC3339_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise EntryFabricError(f"{field}:TIMEZONE_REQUIRED")
    return value


def _generation(value: Any, current_generation: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntryFabricError("entity_generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value != current_generation:
        raise EntryFabricError("STALE_ENTITY_GENERATION")
    return value


def _capabilities(value: Any, field: str = "capabilities") -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EntryFabricError(f"{field}:SEQUENCE_REQUIRED")
    normalized: list[str] = []
    for item in value:
        text = _text(item, "capability")
        assert text is not None
        normalized.append(text)
    if len(set(normalized)) != len(normalized):
        raise EntryFabricError(f"{field}:DUPLICATE_FORBIDDEN")
    return tuple(sorted(normalized))


def _budget(value: Any) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping):
        raise EntryFabricError("budget:MAPPING_REQUIRED")
    unknown = set(value) - BUDGET_FIELDS
    if unknown:
        raise EntryFabricError(f"budget:UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
    if set(value) != BUDGET_FIELDS:
        raise EntryFabricError("budget:ALL_FIELDS_REQUIRED")
    normalized: dict[str, int] = {}
    for field in sorted(BUDGET_FIELDS):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise EntryFabricError(f"budget.{field}:NONNEGATIVE_INTEGER_REQUIRED")
        normalized[field] = item
    return tuple(normalized.items())


def admit_entry(
    entry: Mapping[str, Any],
    *,
    current_generation: int,
    expected_capability_binding_sha256: str,
    admitted_capabilities: Sequence[str],
) -> EntryPacket:
    """Admit one typed ingress packet against an externally-authorized capability view.

    `expected_capability_binding_sha256` and `admitted_capabilities` must come from the
    deterministic authority/control plane for the current identity/generation. The entry
    may narrow that set, but it cannot self-grant a capability or substitute another
    capability-binding receipt.
    """
    if not isinstance(entry, Mapping):
        raise EntryFabricError("ENTRY_MAPPING_REQUIRED")
    unknown = set(entry) - ENTRY_FIELDS
    if unknown:
        raise EntryFabricError(f"ENTRY_UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
    if entry.get("schema") != ENTRY_SCHEMA:
        raise EntryFabricError("ENTRY_SCHEMA_UNSUPPORTED")

    generation = _generation(entry.get("entity_generation"), current_generation)
    ingress_id = _text(entry.get("ingress_id"), "ingress_id")
    causal_id = _text(entry.get("causal_id"), "causal_id")
    source_id = _text(entry.get("source_id"), "source_id")
    provenance_ref = _text(entry.get("provenance_ref"), "provenance_ref")
    payload_ref = _text(entry.get("payload_ref"), "payload_ref")
    assert ingress_id and causal_id and source_id and provenance_ref and payload_ref

    source_kind = entry.get("source_kind")
    if source_kind not in SOURCE_KINDS:
        raise EntryFabricError("source_kind:UNSUPPORTED")
    modality = entry.get("modality")
    if modality not in MODALITIES:
        raise EntryFabricError("modality:UNSUPPORTED")

    observed_time = _timestamp(entry.get("observed_time"), "observed_time", optional=True)
    received_time = _timestamp(entry.get("received_time"), "received_time")
    assert received_time is not None

    provenance_sha256 = _sha256(entry.get("provenance_sha256"), "provenance_sha256")
    capability_binding_sha256 = _sha256(
        entry.get("capability_binding_sha256"),
        "capability_binding_sha256",
    )
    expected_capability_binding_sha256 = _sha256(
        expected_capability_binding_sha256,
        "expected_capability_binding_sha256",
    )
    if capability_binding_sha256 != expected_capability_binding_sha256:
        raise EntryFabricError("CAPABILITY_BINDING_MISMATCH")

    payload_sha256 = _sha256(entry.get("payload_sha256"), "payload_sha256")
    capabilities = _capabilities(entry.get("capabilities"))
    authority_capabilities = _capabilities(admitted_capabilities, "admitted_capabilities")
    unauthorized = sorted(set(capabilities) - set(authority_capabilities))
    if unauthorized:
        raise EntryFabricError(f"CAPABILITY_NOT_ADMITTED:{','.join(unauthorized)}")

    budget = _budget(entry.get("budget"))
    parent_id = _text(entry.get("parent_id"), "parent_id", optional=True)
    stream_id = _text(entry.get("stream_id"), "stream_id", optional=True)

    normalized = {
        "schema": ENTRY_SCHEMA,
        "ingress_id": ingress_id,
        "causal_id": causal_id,
        "entity_generation": generation,
        "source_kind": source_kind,
        "source_id": source_id,
        "modality": modality,
        "observed_time": observed_time,
        "received_time": received_time,
        "provenance_ref": provenance_ref,
        "provenance_sha256": provenance_sha256,
        "capabilities": capabilities,
        "capability_binding_sha256": capability_binding_sha256,
        "parent_id": parent_id,
        "stream_id": stream_id,
        "budget": budget,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
    }
    admission_sha256 = hashlib.sha256(_canonical(normalized)).hexdigest()
    return EntryPacket(**normalized, admission_sha256=admission_sha256)


def to_hcu_reactive_event(
    packet: EntryPacket,
    *,
    novelty: float = 0.0,
    contradiction: float = 0.0,
    uncertainty: float = 0.0,
    forecast_need: float = 0.0,
    effect_pressure: float = 0.0,
    zero_relevance: float = 0.0,
    due_recheck: bool = False,
    provenance_gap: bool = False,
    goal_pressure: float | None = None,
) -> dict[str, Any]:
    if not isinstance(packet, EntryPacket):
        raise EntryFabricError("ENTRY_PACKET_REQUIRED")

    def unit(value: Any, field: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EntryFabricError(f"{field}:NUMBER_REQUIRED")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise EntryFabricError(f"{field}:UNIT_INTERVAL_REQUIRED")
        return value

    if not isinstance(due_recheck, bool) or not isinstance(provenance_gap, bool):
        raise EntryFabricError("BOOLEAN_REACTIVE_FLAG_REQUIRED")

    event: dict[str, Any] = {
        "schema": HCU_EVENT_SCHEMA,
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "entry_admission_sha256": packet.admission_sha256,
        "entity_generation": packet.entity_generation,
        "novelty": unit(novelty, "novelty"),
        "contradiction": unit(contradiction, "contradiction"),
        "uncertainty": unit(uncertainty, "uncertainty"),
        "forecast_need": unit(forecast_need, "forecast_need"),
        "effect_pressure": unit(effect_pressure, "effect_pressure"),
        "zero_relevance": unit(zero_relevance, "zero_relevance"),
        "due_recheck": due_recheck,
        "provenance_gap": provenance_gap,
    }
    if goal_pressure is not None:
        event["goal_pressure"] = unit(goal_pressure, "goal_pressure")
    return event


def packet_json(packet: EntryPacket) -> str:
    return json.dumps(
        asdict(packet),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
