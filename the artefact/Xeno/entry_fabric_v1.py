#!/usr/bin/env python3
"""Deterministic typed ingress and causal route binding for Xeno.

This module is authority-neutral: it validates and binds ingress identity before
cognition. It does not decide semantic truth and it does not grant effect rights.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

INGRESS_SCHEMA = "XENO_INGRESS_PACKET/v1"
ROUTE_BINDING_SCHEMA = "XENO_ROUTE_DECISION_BINDING/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EntryAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class EntryAdmission:
    status: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    source: str
    modality: str
    observed_at: str
    received_at: str
    payload_ref: str
    payload_sha256: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    event_sha256: str
    admission_sha256: str


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


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EntryAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256(value: Any, field: str) -> str:
    value = _string(value, field).lower()
    if _SHA256_RE.fullmatch(value) is None:
        raise EntryAdmissionError(f"{field}:SHA256_REQUIRED")
    return value


def _string_set(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise EntryAdmissionError(f"{field}:STRING_SEQUENCE_REQUIRED")
    items = tuple(sorted({_string(item, field) for item in value}))
    if not items:
        raise EntryAdmissionError(f"{field}:NONEMPTY_REQUIRED")
    return items


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EntryAdmissionError(f"{field}:MAPPING_REQUIRED")
    _canonical(value)
    return value


def admit_ingress(packet: Mapping[str, Any], *, current_generation: int) -> EntryAdmission:
    """Validate one Xeno ingress packet and bind event/admission identities.

    event_sha256 is replay-stable for the same causal event and excludes transport
    arrival identity. admission_sha256 binds the concrete admitted ingress instance,
    permissions, capability scope and resource budget.
    """
    if not isinstance(packet, Mapping) or packet.get("schema") != INGRESS_SCHEMA:
        raise EntryAdmissionError("INGRESS_SCHEMA_UNSUPPORTED")

    generation = packet.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise EntryAdmissionError("ENTITY_GENERATION_INVALID")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise EntryAdmissionError("CURRENT_GENERATION_INVALID")
    if generation != current_generation:
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    ingress_id = _string(packet.get("ingress_id"), "ingress_id")
    causal_id = _string(packet.get("causal_id"), "causal_id")
    source = _string(packet.get("source"), "source")
    modality = _string(packet.get("modality"), "modality")
    observed_at = _string(packet.get("observed_at"), "observed_at")
    received_at = _string(packet.get("received_at"), "received_at")
    payload_ref = _string(packet.get("payload_ref"), "payload_ref")
    payload_sha256 = _sha256(packet.get("payload_sha256"), "payload_sha256")
    permissions = _string_set(packet.get("permissions"), "permissions")
    capability_scope = _string_set(packet.get("capability_scope"), "capability_scope")
    provenance = _mapping(packet.get("provenance"), "provenance")
    resource_budget = _mapping(packet.get("resource_budget"), "resource_budget")

    event_identity = {
        "schema": INGRESS_SCHEMA,
        "causal_id": causal_id,
        "entity_generation": generation,
        "source": source,
        "modality": modality,
        "observed_at": observed_at,
        "payload_sha256": payload_sha256,
        "provenance": provenance,
    }
    event_sha256 = _digest(event_identity)

    admission_identity = {
        "schema": INGRESS_SCHEMA,
        "event_sha256": event_sha256,
        "ingress_id": ingress_id,
        "received_at": received_at,
        "payload_ref": payload_ref,
        "permissions": permissions,
        "capability_scope": capability_scope,
        "resource_budget": resource_budget,
    }
    admission_sha256 = _digest(admission_identity)

    return EntryAdmission(
        status="ADMITTED",
        ingress_id=ingress_id,
        causal_id=causal_id,
        entity_generation=generation,
        source=source,
        modality=modality,
        observed_at=observed_at,
        received_at=received_at,
        payload_ref=payload_ref,
        payload_sha256=payload_sha256,
        permissions=permissions,
        capability_scope=capability_scope,
        event_sha256=event_sha256,
        admission_sha256=admission_sha256,
    )


def route_decision_sha256(
    *,
    event_sha256: str,
    route_policy_sha256: str,
    requested_engine_identity: str,
    resolved_engine_identity: str,
    resolved_engine_class: str,
    route_result: Mapping[str, Any],
) -> str:
    """Bind a route decision to event, policy, engine identity and result.

    Callers must resolve engine aliases through a positive internal engine registry
    before invoking this function. Unknown/unadmitted engines must fail closed there.
    """
    payload = {
        "schema": ROUTE_BINDING_SCHEMA,
        "event_sha256": _sha256(event_sha256, "event_sha256"),
        "route_policy_sha256": _sha256(route_policy_sha256, "route_policy_sha256"),
        "requested_engine_identity": _string(requested_engine_identity, "requested_engine_identity"),
        "resolved_engine_identity": _string(resolved_engine_identity, "resolved_engine_identity"),
        "resolved_engine_class": _string(resolved_engine_class, "resolved_engine_class"),
        "route_result": _mapping(route_result, "route_result"),
    }
    return _digest(payload)


def admission_json(admission: EntryAdmission) -> str:
    return json.dumps(asdict(admission), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
