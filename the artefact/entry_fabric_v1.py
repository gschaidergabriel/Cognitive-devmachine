#!/usr/bin/env python3
"""Typed, fail-closed ingress binding for the EntityOS Entry Fabric for HCU.

This module creates immutable entry identities before cognition. It does not
grant truth, model, user-rights, or effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

SCHEMA = "ENTITYOS_ENTRY/v1"
PACKET_SCHEMA = "ENTITYOS_ENTRY_PACKET/v1"
CANONICALIZATION_SCHEMA = "ENTITYOS_ENTRY_CANONICAL_JSON_JCS_SUBSET/v1"
MAX_SAFE_JSON_INTEGER = (1 << 53) - 1
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
HEX_32 = re.compile(r"^[0-9a-f]{32}$")
HEX_16 = re.compile(r"^[0-9a-f]{16}$")
CAPABILITY_TOKEN = re.compile(r"^[a-z][a-z0-9_.:-]{0,127}$")
BUDGET_KEYS = frozenset({"max_tokens", "max_ms", "max_cells", "max_bytes"})


class EntryAdmissionError(ValueError):
    """Raised when an ingress record cannot be admitted deterministically."""


@dataclass(frozen=True)
class EntryPacket:
    schema: str
    canonicalization_schema: str
    event_id: str
    source: str
    event_type: str
    causal_id: str
    entity_generation: int
    modality: str
    observed_at: str
    received_at: str
    capability_scope: tuple[str, ...]
    budget: tuple[tuple[str, int], ...]
    payload_ref: str
    payload_sha256: str
    provenance_sha256: str
    parent_id: str | None
    stream_id: str | None
    trace_id: str | None
    parent_span_id: str | None
    entry_sha256: str


def _canonical(value: Any) -> bytes:
    """Encode the admitted Entry identity subset in a JCS-compatible representation.

    The identity basis contains only fixed ASCII object keys, Unicode strings, null,
    arrays, and non-negative integers <= 2**53-1. Those restrictions intentionally
    avoid Python/ECMAScript number and key-order ambiguity. The schema identifier is
    included in the hashed basis so a future broader canonicalizer cannot alias v1.
    """
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise EntryAdmissionError("NONCANONICAL_VALUE") from exc


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise EntryAdmissionError(f"{field}:STRING_REQUIRED")
    value = value.strip()
    if not value:
        raise EntryAdmissionError(f"{field}:NONEMPTY_REQUIRED")
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise EntryAdmissionError(f"{field}:UNICODE_REQUIRED") from exc
    return value


def _safe_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntryAdmissionError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_JSON_INTEGER:
        raise EntryAdmissionError(f"{field}:JCS_SAFE_INTEGER_REQUIRED")
    return value


def _hex(value: Any, field: str, pattern: re.Pattern[str]) -> str:
    value = _text(value, field).lower()
    if not pattern.fullmatch(value):
        raise EntryAdmissionError(f"{field}:HEX_FORMAT_INVALID")
    return value


def _timestamp(value: Any, field: str) -> str:
    raw = _text(value, field)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EntryAdmissionError(f"{field}:RFC3339_REQUIRED") from exc
    if dt.tzinfo is None:
        raise EntryAdmissionError(f"{field}:TIMEZONE_REQUIRED")
    dt = dt.astimezone(timezone.utc)
    if dt.microsecond:
        text = dt.isoformat(timespec="microseconds")
    else:
        text = dt.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")


def _scope(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise EntryAdmissionError("capability_scope:SEQUENCE_REQUIRED")
    items: set[str] = set()
    for raw in value:
        item = _text(raw, "capability_scope[]")
        if not CAPABILITY_TOKEN.fullmatch(item):
            raise EntryAdmissionError("capability_scope[]:TOKEN_REQUIRED")
        items.add(item)
    return tuple(sorted(items))


def _budget(value: Any) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping):
        raise EntryAdmissionError("budget:MAPPING_REQUIRED")
    unknown = set(value) - BUDGET_KEYS
    if unknown:
        raise EntryAdmissionError("budget:UNKNOWN_KEY")
    items: list[tuple[str, int]] = []
    for key in sorted(value):
        amount = _safe_nonnegative_int(value[key], f"budget.{key}")
        items.append((key, amount))
    return tuple(items)


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def bind_entry(entry: Mapping[str, Any], *, current_generation: int) -> EntryPacket:
    """Validate and bind one ingress record to an immutable packet identity."""
    if not isinstance(entry, Mapping) or entry.get("schema") != SCHEMA:
        raise EntryAdmissionError("ENTRY_SCHEMA_UNSUPPORTED")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise EntryAdmissionError("CURRENT_GENERATION_INVALID")
    if current_generation > MAX_SAFE_JSON_INTEGER:
        raise EntryAdmissionError("CURRENT_GENERATION:JCS_SAFE_INTEGER_REQUIRED")

    generation = entry.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise EntryAdmissionError("ENTITY_GENERATION_INVALID")
    if generation > MAX_SAFE_JSON_INTEGER:
        raise EntryAdmissionError("ENTITY_GENERATION:JCS_SAFE_INTEGER_REQUIRED")
    if generation != current_generation:
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    event_id = _text(entry.get("event_id"), "event_id")
    source = _text(entry.get("source"), "source")
    event_type = _text(entry.get("event_type"), "event_type")
    causal_id = _text(entry.get("causal_id"), "causal_id")
    modality = _text(entry.get("modality"), "modality").upper()
    observed_at = _timestamp(entry.get("observed_at"), "observed_at")
    received_at = _timestamp(entry.get("received_at"), "received_at")
    capability_scope = _scope(entry.get("capability_scope"))
    budget = _budget(entry.get("budget"))
    payload_ref = _text(entry.get("payload_ref"), "payload_ref")
    payload_sha256 = _hex(entry.get("payload_sha256"), "payload_sha256", HEX_64)
    provenance_sha256 = _hex(entry.get("provenance_sha256"), "provenance_sha256", HEX_64)
    parent_id = _optional_text(entry.get("parent_id"), "parent_id")
    stream_id = _optional_text(entry.get("stream_id"), "stream_id")

    trace_id_raw = entry.get("trace_id")
    parent_span_raw = entry.get("parent_span_id")
    trace_id = None if trace_id_raw is None else _hex(trace_id_raw, "trace_id", HEX_32)
    parent_span_id = None if parent_span_raw is None else _hex(parent_span_raw, "parent_span_id", HEX_16)
    if (trace_id is None) != (parent_span_id is None):
        raise EntryAdmissionError("TRACE_CONTEXT_PARTIAL")

    basis = {
        "schema": PACKET_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_id": event_id,
        "source": source,
        "event_type": event_type,
        "causal_id": causal_id,
        "entity_generation": generation,
        "modality": modality,
        "observed_at": observed_at,
        "received_at": received_at,
        "capability_scope": capability_scope,
        "budget": budget,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
        "provenance_sha256": provenance_sha256,
        "parent_id": parent_id,
        "stream_id": stream_id,
        "trace_id": trace_id,
        "parent_span_id": parent_span_id,
    }
    digest = hashlib.sha256(_canonical(basis)).hexdigest()
    return EntryPacket(entry_sha256=digest, **basis)


def packet_json(packet: EntryPacket) -> str:
    return json.dumps(asdict(packet), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
