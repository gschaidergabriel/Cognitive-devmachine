#!/usr/bin/env python3
"""Typed deterministic ingress admission for Xeno.

This module is deliberately semantic-light: it binds identity, generation, provenance,
permissions and resource budgets before cognition. It does not infer truth, route effects,
or grant capabilities beyond the explicitly supplied admission envelope.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "XENO_INGRESS_PACKET/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_SOURCES = {
    "human",
    "external_event",
    "tool_outcome",
    "sensor_stream",
    "canonical_db_change",
    "intrinsic_system_event",
}
ALLOWED_MODALITIES = {
    "text",
    "json",
    "binary",
    "image",
    "audio",
    "video",
    "sensor",
    "state_delta",
    "effect_receipt",
}
REQUIRED_KEYS = {
    "schema",
    "causal_id",
    "entity_generation",
    "source",
    "provenance",
    "modality",
    "observed_at_ns",
    "received_at_ns",
    "permissions",
    "capability_scope",
    "resource_budget",
    "payload_ref",
    "payload_sha256",
}
OPTIONAL_KEYS = {"ingress_id", "parent_or_stream_id"}
BUDGET_KEYS = {
    "max_wall_ms",
    "max_model_calls",
    "max_context_tokens",
    "max_logical_cells",
}


class IngressAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class ResourceBudget:
    max_wall_ms: int
    max_model_calls: int
    max_context_tokens: int
    max_logical_cells: int


@dataclass(frozen=True)
class XenoIngressPacket:
    schema: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    source: str
    provenance: Mapping[str, Any]
    modality: str
    observed_at_ns: int
    received_at_ns: int
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    parent_or_stream_id: str | None
    resource_budget: ResourceBudget
    payload_ref: str
    payload_sha256: str


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
        raise IngressAdmissionError("NONCANONICAL_VALUE") from exc


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IngressAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise IngressAdmissionError(f"{field}:NONNEGATIVE_INT_REQUIRED")
    return value


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise IngressAdmissionError(f"{field}:SEQUENCE_REQUIRED")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        item = _nonempty_string(item, field)
        if item in seen:
            raise IngressAdmissionError(f"{field}:DUPLICATE_VALUE")
        seen.add(item)
        normalized.append(item)
    return tuple(sorted(normalized))


def _budget(value: Any) -> ResourceBudget:
    if not isinstance(value, Mapping):
        raise IngressAdmissionError("resource_budget:MAPPING_REQUIRED")
    if set(value) != BUDGET_KEYS:
        raise IngressAdmissionError("resource_budget:KEYSET_INVALID")
    budget = ResourceBudget(
        max_wall_ms=_nonnegative_int(value["max_wall_ms"], "max_wall_ms"),
        max_model_calls=_nonnegative_int(value["max_model_calls"], "max_model_calls"),
        max_context_tokens=_nonnegative_int(value["max_context_tokens"], "max_context_tokens"),
        max_logical_cells=_nonnegative_int(value["max_logical_cells"], "max_logical_cells"),
    )
    if budget.max_logical_cells > 600:
        raise IngressAdmissionError("max_logical_cells:ABOVE_CURRENT_RESEARCH_CEILING")
    return budget


def _identity_payload(packet_fields: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": packet_fields["schema"],
        "causal_id": packet_fields["causal_id"],
        "entity_generation": packet_fields["entity_generation"],
        "source": packet_fields["source"],
        "provenance": packet_fields["provenance"],
        "modality": packet_fields["modality"],
        "observed_at_ns": packet_fields["observed_at_ns"],
        "received_at_ns": packet_fields["received_at_ns"],
        "permissions": list(packet_fields["permissions"]),
        "capability_scope": list(packet_fields["capability_scope"]),
        "parent_or_stream_id": packet_fields["parent_or_stream_id"],
        "resource_budget": asdict(packet_fields["resource_budget"]),
        "payload_ref": packet_fields["payload_ref"],
        "payload_sha256": packet_fields["payload_sha256"],
    }


def admit_ingress(raw: Mapping[str, Any], *, current_generation: int) -> XenoIngressPacket:
    if not isinstance(raw, Mapping):
        raise IngressAdmissionError("INGRESS_MAPPING_REQUIRED")
    keys = set(raw)
    if not REQUIRED_KEYS.issubset(keys) or not keys.issubset(REQUIRED_KEYS | OPTIONAL_KEYS):
        raise IngressAdmissionError("INGRESS_KEYSET_INVALID")
    if raw.get("schema") != SCHEMA:
        raise IngressAdmissionError("INGRESS_SCHEMA_UNSUPPORTED")

    generation = _nonnegative_int(raw.get("entity_generation"), "entity_generation")
    current_generation = _nonnegative_int(current_generation, "current_generation")
    if generation != current_generation:
        raise IngressAdmissionError("STALE_ENTITY_GENERATION")

    source = _nonempty_string(raw.get("source"), "source")
    if source not in ALLOWED_SOURCES:
        raise IngressAdmissionError("SOURCE_CLASS_UNSUPPORTED")
    modality = _nonempty_string(raw.get("modality"), "modality")
    if modality not in ALLOWED_MODALITIES:
        raise IngressAdmissionError("MODALITY_UNSUPPORTED")

    provenance = raw.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        raise IngressAdmissionError("provenance:NONEMPTY_MAPPING_REQUIRED")
    # Canonicalization is part of admission: opaque non-JSON objects cannot enter identity.
    _canonical(provenance)

    payload_sha256 = _nonempty_string(raw.get("payload_sha256"), "payload_sha256").lower()
    if not SHA256_RE.fullmatch(payload_sha256):
        raise IngressAdmissionError("payload_sha256:LOWERCASE_SHA256_REQUIRED")

    fields = {
        "schema": SCHEMA,
        "causal_id": _nonempty_string(raw.get("causal_id"), "causal_id"),
        "entity_generation": generation,
        "source": source,
        "provenance": dict(provenance),
        "modality": modality,
        "observed_at_ns": _nonnegative_int(raw.get("observed_at_ns"), "observed_at_ns"),
        "received_at_ns": _nonnegative_int(raw.get("received_at_ns"), "received_at_ns"),
        "permissions": _string_tuple(raw.get("permissions"), "permissions"),
        "capability_scope": _string_tuple(raw.get("capability_scope"), "capability_scope"),
        "parent_or_stream_id": None,
        "resource_budget": _budget(raw.get("resource_budget")),
        "payload_ref": _nonempty_string(raw.get("payload_ref"), "payload_ref"),
        "payload_sha256": payload_sha256,
    }
    if raw.get("parent_or_stream_id") is not None:
        fields["parent_or_stream_id"] = _nonempty_string(
            raw.get("parent_or_stream_id"), "parent_or_stream_id"
        )

    ingress_id = hashlib.sha256(_canonical(_identity_payload(fields))).hexdigest()
    supplied = raw.get("ingress_id")
    if supplied is not None:
        supplied = _nonempty_string(supplied, "ingress_id").lower()
        if supplied != ingress_id:
            raise IngressAdmissionError("INGRESS_ID_MISMATCH")

    return XenoIngressPacket(ingress_id=ingress_id, **fields)


def packet_json(packet: XenoIngressPacket) -> str:
    body = asdict(packet)
    body["permissions"] = list(packet.permissions)
    body["capability_scope"] = list(packet.capability_scope)
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
