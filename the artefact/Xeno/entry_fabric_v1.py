#!/usr/bin/env python3
"""Typed deterministic ingress admission for EntityOS/HCU compatibility paths.

The module separates immutable causal-event identity from concrete admission identity.
Untrusted ingress may *claim* permissions/capabilities, but admitted permissions come only
from a separately supplied trusted capability snapshot. It does not infer truth, grant
capabilities, write canonical state, or route real effects.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "XENO_INGRESS_PACKET/v1"  # compatibility schema name
EVENT_IDENTITY_SCHEMA = "ENTITYOS_HCU_CAUSAL_EVENT_ID/v1"
ADMISSION_IDENTITY_SCHEMA = "ENTITYOS_HCU_ENTRY_ADMISSION_ID/v1"
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
OPTIONAL_KEYS = {
    "event_sha256",
    "admission_sha256",
    "ingress_id",  # compatibility alias for admission_sha256
    "parent_or_stream_id",
}
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
class TrustedCapabilitySnapshot:
    """Capability state resolved by an authority outside untrusted ingress.

    Structural validation occurs here; provenance/authorization of this object must be
    established by the canonical permission/capability authority before Entry admission.
    """

    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    authority_binding_sha256: str


@dataclass(frozen=True)
class XenoIngressPacket:
    schema: str
    event_sha256: str
    admission_sha256: str
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
    capability_authority_sha256: str
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
    value = value.strip()
    if any(ord(ch) < 0x20 for ch in value):
        raise IngressAdmissionError(f"{field}:CONTROL_CHARACTER_FORBIDDEN")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _nonempty_string(value, field).lower()
    if not SHA256_RE.fullmatch(value):
        raise IngressAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


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


def _trusted_snapshot(value: Any) -> TrustedCapabilitySnapshot:
    if not isinstance(value, TrustedCapabilitySnapshot):
        raise IngressAdmissionError("TRUSTED_CAPABILITY_SNAPSHOT_REQUIRED")
    permissions = _string_tuple(value.permissions, "trusted_permissions")
    capability_scope = _string_tuple(value.capability_scope, "trusted_capability_scope")
    binding = _sha256(value.authority_binding_sha256, "capability_authority_sha256")
    return TrustedCapabilitySnapshot(
        permissions=permissions,
        capability_scope=capability_scope,
        authority_binding_sha256=binding,
    )


def _event_identity_payload(fields: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": EVENT_IDENTITY_SCHEMA,
        "ingress_schema": fields["schema"],
        "causal_id": fields["causal_id"],
        "entity_generation": fields["entity_generation"],
        "source": fields["source"],
        "provenance": fields["provenance"],
        "modality": fields["modality"],
        "observed_at_ns": fields["observed_at_ns"],
        "parent_or_stream_id": fields["parent_or_stream_id"],
        "payload_sha256": fields["payload_sha256"],
    }


def _admission_identity_payload(
    fields: Mapping[str, Any],
    *,
    event_sha256: str,
    capability_authority_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": ADMISSION_IDENTITY_SCHEMA,
        "event_sha256": event_sha256,
        "received_at_ns": fields["received_at_ns"],
        "permissions": list(fields["permissions"]),
        "capability_scope": list(fields["capability_scope"]),
        "capability_authority_sha256": capability_authority_sha256,
        "resource_budget": asdict(fields["resource_budget"]),
        "payload_ref": fields["payload_ref"],
    }


def admit_ingress(
    raw: Mapping[str, Any],
    *,
    current_generation: int,
    trusted_capability_snapshot: TrustedCapabilitySnapshot,
) -> XenoIngressPacket:
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
    _canonical(provenance)

    snapshot = _trusted_snapshot(trusted_capability_snapshot)
    claimed_permissions = _string_tuple(raw.get("permissions"), "permissions")
    claimed_capabilities = _string_tuple(raw.get("capability_scope"), "capability_scope")
    if claimed_permissions != snapshot.permissions:
        raise IngressAdmissionError("PERMISSION_AUTHORITY_MISMATCH")
    if claimed_capabilities != snapshot.capability_scope:
        raise IngressAdmissionError("CAPABILITY_AUTHORITY_MISMATCH")

    fields = {
        "schema": SCHEMA,
        "causal_id": _nonempty_string(raw.get("causal_id"), "causal_id"),
        "entity_generation": generation,
        "source": source,
        "provenance": dict(provenance),
        "modality": modality,
        "observed_at_ns": _nonnegative_int(raw.get("observed_at_ns"), "observed_at_ns"),
        "received_at_ns": _nonnegative_int(raw.get("received_at_ns"), "received_at_ns"),
        "permissions": snapshot.permissions,
        "capability_scope": snapshot.capability_scope,
        "parent_or_stream_id": None,
        "resource_budget": _budget(raw.get("resource_budget")),
        "payload_ref": _nonempty_string(raw.get("payload_ref"), "payload_ref"),
        "payload_sha256": _sha256(raw.get("payload_sha256"), "payload_sha256"),
    }
    if raw.get("parent_or_stream_id") is not None:
        fields["parent_or_stream_id"] = _nonempty_string(
            raw.get("parent_or_stream_id"), "parent_or_stream_id"
        )

    event_sha256 = hashlib.sha256(_canonical(_event_identity_payload(fields))).hexdigest()
    admission_sha256 = hashlib.sha256(
        _canonical(
            _admission_identity_payload(
                fields,
                event_sha256=event_sha256,
                capability_authority_sha256=snapshot.authority_binding_sha256,
            )
        )
    ).hexdigest()

    supplied_event = raw.get("event_sha256")
    if supplied_event is not None and _sha256(supplied_event, "event_sha256") != event_sha256:
        raise IngressAdmissionError("EVENT_SHA256_MISMATCH")

    supplied_admission = raw.get("admission_sha256")
    if supplied_admission is not None and _sha256(
        supplied_admission, "admission_sha256"
    ) != admission_sha256:
        raise IngressAdmissionError("ADMISSION_SHA256_MISMATCH")

    supplied_ingress = raw.get("ingress_id")
    if supplied_ingress is not None and _sha256(supplied_ingress, "ingress_id") != admission_sha256:
        raise IngressAdmissionError("INGRESS_ID_MISMATCH")

    return XenoIngressPacket(
        event_sha256=event_sha256,
        admission_sha256=admission_sha256,
        ingress_id=admission_sha256,
        capability_authority_sha256=snapshot.authority_binding_sha256,
        **fields,
    )


def packet_json(packet: XenoIngressPacket) -> str:
    body = asdict(packet)
    body["permissions"] = list(packet.permissions)
    body["capability_scope"] = list(packet.capability_scope)
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
