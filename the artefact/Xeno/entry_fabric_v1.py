#!/usr/bin/env python3
"""Deterministic typed ingress admission for Xeno.

The Entry Fabric binds new data to one canonical ingress identity before cognition.
It does not decide semantic truth and it grants no effects. Downstream HCU/XCU route,
workspace and effect receipts can commit to ``ingress_sha256`` without reinterpreting
raw caller dictionaries.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

SCHEMA = "XENO_INGRESS_PACKET/v1"
ADMITTED_SCHEMA = "XENO_ADMITTED_INGRESS/v1"

_ALLOWED_KEYS = frozenset({
    "schema",
    "ingress_id",
    "causal_id",
    "generation",
    "source",
    "source_ref",
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
})
_REQUIRED_KEYS = _ALLOWED_KEYS - {"parent_or_stream_id"}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class IngressAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class AdmittedIngress:
    schema: str
    ingress_id: str
    causal_id: str
    generation: int
    source: str
    source_ref: str
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
    ingress_sha256: str

    def causal_binding(self) -> dict[str, Any]:
        """Small immutable binding for downstream route/workspace/effect identities."""
        return {
            "schema": ADMITTED_SCHEMA,
            "ingress_sha256": self.ingress_sha256,
            "ingress_id": self.ingress_id,
            "causal_id": self.causal_id,
            "generation": self.generation,
        }


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
        raise IngressAdmissionError("CANONICALIZATION_FAILED") from exc


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str):
        raise IngressAdmissionError(f"{field}:STRING_REQUIRED")
    value = value.strip()
    if not value or len(value) > max_len:
        raise IngressAdmissionError(f"{field}:BOUNDS_INVALID")
    return value


def _identifier(value: Any, field: str) -> str:
    value = _text(value, field, max_len=128)
    if not _ID_RE.fullmatch(value):
        raise IngressAdmissionError(f"{field}:IDENTIFIER_INVALID")
    return value


def _optional_identifier(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _identifier(value, field)


def _string_set(value: Any, field: str, *, max_items: int = 64) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise IngressAdmissionError(f"{field}:LIST_REQUIRED")
    if len(value) > max_items:
        raise IngressAdmissionError(f"{field}:TOO_MANY_ITEMS")
    normalized = tuple(sorted({_identifier(item, field) for item in value}))
    return normalized


def _timestamp(value: Any, field: str) -> str:
    text = _text(value, field, max_len=64)
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise IngressAdmissionError(f"{field}:RFC3339_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise IngressAdmissionError(f"{field}:TIMEZONE_REQUIRED")
    utc = parsed.astimezone(timezone.utc)
    timespec = "microseconds" if utc.microsecond else "seconds"
    return utc.isoformat(timespec=timespec).replace("+00:00", "Z")


def _budget(
    value: Any,
    *,
    max_budget: Mapping[str, int],
) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping):
        raise IngressAdmissionError("resource_budget:OBJECT_REQUIRED")
    if not max_budget:
        if value:
            raise IngressAdmissionError("resource_budget:NO_DIMENSIONS_ADMITTED")
        return ()
    unknown = set(value) - set(max_budget)
    if unknown:
        raise IngressAdmissionError("resource_budget:UNKNOWN_DIMENSION")
    normalized: list[tuple[str, int]] = []
    for key, requested in value.items():
        if isinstance(requested, bool) or not isinstance(requested, int) or requested < 0:
            raise IngressAdmissionError(f"resource_budget.{key}:NONNEGATIVE_INTEGER_REQUIRED")
        maximum = max_budget.get(key)
        if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 0:
            raise IngressAdmissionError(f"policy.max_budget.{key}:INVALID")
        if requested > maximum:
            raise IngressAdmissionError(f"resource_budget.{key}:POLICY_LIMIT_EXCEEDED")
        normalized.append((_identifier(key, "resource_budget.key"), requested))
    return tuple(sorted(normalized))


def admit_ingress(
    packet: Mapping[str, Any],
    *,
    current_generation: int,
    allowed_sources: Sequence[str],
    allowed_source_refs: Sequence[str],
    allowed_permissions: Sequence[str],
    allowed_capabilities: Sequence[str],
    max_budget: Mapping[str, int],
) -> AdmittedIngress:
    """Validate, normalize and hash one ingress packet.

    All ``allowed_*`` values and ``max_budget`` are deterministic XPU/authority inputs,
    not caller-provided policy. The returned digest is a causal identity receipt, not a
    truth score or permission token.
    """
    if not isinstance(packet, Mapping):
        raise IngressAdmissionError("PACKET_OBJECT_REQUIRED")
    keys = set(packet)
    if keys - _ALLOWED_KEYS:
        raise IngressAdmissionError("UNKNOWN_TOP_LEVEL_FIELD")
    if _REQUIRED_KEYS - keys:
        raise IngressAdmissionError("REQUIRED_FIELD_MISSING")
    if packet.get("schema") != SCHEMA:
        raise IngressAdmissionError("SCHEMA_UNSUPPORTED")

    generation = packet.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise IngressAdmissionError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise IngressAdmissionError("current_generation:INVALID")
    if generation != current_generation:
        raise IngressAdmissionError("STALE_GENERATION")

    source = _identifier(packet["source"], "source")
    source_ref = _identifier(packet["source_ref"], "source_ref")
    admitted_sources = set(_string_set(allowed_sources, "policy.allowed_sources"))
    admitted_source_refs = set(_string_set(allowed_source_refs, "policy.allowed_source_refs"))
    if source not in admitted_sources:
        raise IngressAdmissionError("SOURCE_NOT_ADMITTED")
    if source_ref not in admitted_source_refs:
        raise IngressAdmissionError("SOURCE_REF_NOT_ADMITTED")

    admitted_permissions = set(_string_set(allowed_permissions, "policy.allowed_permissions"))
    permissions = _string_set(packet["permissions"], "permissions")
    if not set(permissions).issubset(admitted_permissions):
        raise IngressAdmissionError("PERMISSIONS_NOT_ADMITTED")

    admitted_capabilities = set(_string_set(allowed_capabilities, "policy.allowed_capabilities"))
    capability_scope = _string_set(packet["capability_scope"], "capability_scope")
    if not set(capability_scope).issubset(admitted_capabilities):
        raise IngressAdmissionError("CAPABILITY_SCOPE_NOT_ADMITTED")

    provenance = _string_set(packet["provenance"], "provenance")
    budget = _budget(packet["resource_budget"], max_budget=max_budget)

    payload_sha256 = _text(packet["payload_sha256"], "payload_sha256", max_len=64).lower()
    if not _SHA256_RE.fullmatch(payload_sha256):
        raise IngressAdmissionError("payload_sha256:SHA256_REQUIRED")

    normalized = {
        "schema": ADMITTED_SCHEMA,
        "ingress_id": _identifier(packet["ingress_id"], "ingress_id"),
        "causal_id": _identifier(packet["causal_id"], "causal_id"),
        "generation": generation,
        "source": source,
        "source_ref": source_ref,
        "provenance": provenance,
        "modality": _identifier(packet["modality"], "modality"),
        "observed_at": _timestamp(packet["observed_at"], "observed_at"),
        "received_at": _timestamp(packet["received_at"], "received_at"),
        "permissions": permissions,
        "capability_scope": capability_scope,
        "parent_or_stream_id": _optional_identifier(packet.get("parent_or_stream_id"), "parent_or_stream_id"),
        "resource_budget": budget,
        "payload_ref": _text(packet["payload_ref"], "payload_ref", max_len=2048),
        "payload_sha256": payload_sha256,
    }
    ingress_sha256 = hashlib.sha256(_canonical(normalized)).hexdigest()
    return AdmittedIngress(**normalized, ingress_sha256=ingress_sha256)


def admitted_json(admitted: AdmittedIngress) -> str:
    return json.dumps(asdict(admitted), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
