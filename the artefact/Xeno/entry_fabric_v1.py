#!/usr/bin/env python3
"""Deterministic typed ingress boundary for Xeno.

This module binds new data to one immutable ingress identity before cognition.
It performs schema/type/generation/provenance/budget validation only; it does not
infer semantic truth, select model outputs, or grant effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REQUEST_SCHEMA = "XENO_INGRESS_REQUEST/v1"
PACKET_SCHEMA = "XENO_INGRESS_PACKET/v1"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ALLOWED_FIELDS = {
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
    "payload_ref",
    "payload_sha256",
    "payload_size_bytes",
}
_REQUIRED_FIELDS = _ALLOWED_FIELDS - {"parent_or_stream_id"}


class EntryAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class XenoIngressPacket:
    schema: str
    ingress_id: str
    ingress_sha256: str
    causal_id: str
    entity_generation: int
    source: str
    provenance: tuple[str, ...]
    modality: str
    observed_at: str
    received_at: str
    permissions: tuple[str, ...]
    capability_scope: tuple[str, ...]
    parent_or_stream_id: str | None
    resource_budget: tuple[tuple[str, int], ...]
    payload_ref: str
    payload_sha256: str
    payload_size_bytes: int


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


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EntryAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _string_set(value: Any, field: str, *, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EntryAdmissionError(f"{field}:STRING_SEQUENCE_REQUIRED")
    normalized = tuple(sorted({_string(item, field) for item in value}))
    if not allow_empty and not normalized:
        raise EntryAdmissionError(f"{field}:NONEMPTY_REQUIRED")
    return normalized


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntryAdmissionError(f"{field}:NONNEGATIVE_INT_REQUIRED")
    return value


def _budget(value: Any) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping) or not value:
        raise EntryAdmissionError("resource_budget:NONEMPTY_MAPPING_REQUIRED")
    normalized: list[tuple[str, int]] = []
    for raw_key, raw_value in value.items():
        key = _string(raw_key, "resource_budget.key")
        normalized.append((key, _nonnegative_int(raw_value, f"resource_budget.{key}")))
    normalized.sort()
    return tuple(normalized)


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    text = _string(value, field)
    parse_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        dt = datetime.fromisoformat(parse_text)
    except ValueError as exc:
        raise EntryAdmissionError(f"{field}:RFC3339_REQUIRED") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise EntryAdmissionError(f"{field}:TIMEZONE_REQUIRED")
    dt = dt.astimezone(timezone.utc)
    normalized = dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return normalized, dt


def _sha256(value: Any, field: str) -> str:
    text = _string(value, field).lower()
    if not _SHA256_RE.fullmatch(text):
        raise EntryAdmissionError(f"{field}:SHA256_HEX_REQUIRED")
    return text


def admit_ingress(request: Mapping[str, Any], *, current_generation: int) -> XenoIngressPacket:
    """Validate and bind one new-data request to an immutable Xeno ingress packet."""
    if not isinstance(request, Mapping):
        raise EntryAdmissionError("REQUEST_MAPPING_REQUIRED")
    if request.get("schema") != REQUEST_SCHEMA:
        raise EntryAdmissionError("INGRESS_SCHEMA_UNSUPPORTED")

    keys = set(request)
    missing = sorted(_REQUIRED_FIELDS - keys)
    if missing:
        raise EntryAdmissionError("MISSING_REQUIRED_FIELDS:" + ",".join(missing))
    unknown = sorted(keys - _ALLOWED_FIELDS)
    if unknown:
        raise EntryAdmissionError("UNBOUND_FIELDS_FORBIDDEN:" + ",".join(unknown))

    generation = _nonnegative_int(request["entity_generation"], "entity_generation")
    current = _nonnegative_int(current_generation, "current_generation")
    if generation != current:
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    observed_at, observed_dt = _timestamp(request["observed_at"], "observed_at")
    received_at, received_dt = _timestamp(request["received_at"], "received_at")
    if received_dt < observed_dt:
        raise EntryAdmissionError("RECEIVED_BEFORE_OBSERVED")

    parent = request.get("parent_or_stream_id")
    parent = None if parent is None else _string(parent, "parent_or_stream_id")

    normalized = {
        "schema": PACKET_SCHEMA,
        "causal_id": _string(request["causal_id"], "causal_id"),
        "entity_generation": generation,
        "source": _string(request["source"], "source"),
        "provenance": _string_set(request["provenance"], "provenance", allow_empty=False),
        "modality": _string(request["modality"], "modality"),
        "observed_at": observed_at,
        "received_at": received_at,
        "permissions": _string_set(request["permissions"], "permissions", allow_empty=True),
        "capability_scope": _string_set(request["capability_scope"], "capability_scope", allow_empty=True),
        "parent_or_stream_id": parent,
        "resource_budget": _budget(request["resource_budget"]),
        "payload_ref": _string(request["payload_ref"], "payload_ref"),
        "payload_sha256": _sha256(request["payload_sha256"], "payload_sha256"),
        "payload_size_bytes": _nonnegative_int(request["payload_size_bytes"], "payload_size_bytes"),
    }
    digest = hashlib.sha256(_canonical(normalized)).hexdigest()
    return XenoIngressPacket(
        ingress_id=f"xeno:ingress:sha256:{digest}",
        ingress_sha256=digest,
        **normalized,
    )


def packet_json(packet: XenoIngressPacket) -> str:
    """Canonical JSON form suitable for receipts/replay comparisons."""
    if not isinstance(packet, XenoIngressPacket):
        raise EntryAdmissionError("XENO_INGRESS_PACKET_REQUIRED")
    return _canonical(asdict(packet)).decode("utf-8")
