#!/usr/bin/env python3
"""Typed, deterministic ingress admission for Xeno.

This module is an authority-preserving boundary:
- it binds new data to causal/generation/provenance/resource identity before cognition;
- it does not write canonical state;
- it does not grant effect authority;
- it produces deterministic packet identity suitable for replay/audit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

ENTRY_SCHEMA = "XENO_ENTRY_REQUEST/v1"
PACKET_SCHEMA = "XENO_ENTRY_PACKET/v1"
POLICY_VERSION = "XENO_ENTRY_POLICY/v1"

EVENT_KINDS = frozenset({
    "human_prompt",
    "tool_outcome",
    "external_event",
    "sensor_sample",
    "db_change",
    "intrinsic_event",
})
MODALITIES = frozenset({"text", "json", "metrics", "vector_ref", "binary_ref"})
PERMISSIONS = frozenset({"read_state", "retrieve", "cognition", "simulation", "propose_effect"})
ALLOWED_KEYS = frozenset({
    "schema",
    "event_kind",
    "entity_generation",
    "causal_id",
    "source_id",
    "source_type",
    "provenance",
    "modality",
    "observed_at_ns",
    "received_at_ns",
    "permission_scope",
    "parent_packet_ids",
    "budget",
    "payload",
    "payload_ref",
    "payload_sha256",
})
BUDGET_KEYS = frozenset({"max_cells", "max_model_calls", "max_wall_ms", "max_output_bytes"})


class EntryAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class EntryBudget:
    max_cells: int
    max_model_calls: int
    max_wall_ms: int
    max_output_bytes: int


@dataclass(frozen=True)
class EntryPacket:
    schema: str
    policy_version: str
    packet_id: str
    event_kind: str
    entity_generation: int
    causal_id: str
    source_id: str
    source_type: str
    provenance_json: str
    modality: str
    observed_at_ns: int
    received_at_ns: int
    permission_scope: tuple[str, ...]
    parent_packet_ids: tuple[str, ...]
    budget: EntryBudget
    payload_sha256: str
    payload_ref: str | None
    canonical_payload_json: str | None


def _canonical_json_bytes(value: Any, field: str) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise EntryAdmissionError(f"{field}:CANONICAL_JSON_REQUIRED") from exc
    return text.encode("utf-8")


def _canonical_json_text(value: Any, field: str) -> str:
    return _canonical_json_bytes(value, field).decode("utf-8")


def _text(value: Any, field: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str):
        raise EntryAdmissionError(f"{field}:STRING_REQUIRED")
    if not value or value.strip() != value or len(value) > max_len:
        raise EntryAdmissionError(f"{field}:CANONICAL_STRING_REQUIRED")
    if any(ord(ch) < 0x20 for ch in value):
        raise EntryAdmissionError(f"{field}:CONTROL_CHARACTER_FORBIDDEN")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntryAdmissionError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _bounded_int(value: Any, field: str, *, minimum: int, maximum: int) -> int:
    value = _nonnegative_int(value, field)
    if value < minimum or value > maximum:
        raise EntryAdmissionError(f"{field}:OUT_OF_RANGE")
    return value


def _sequence_of_strings(
    value: Any,
    field: str,
    *,
    allowed: frozenset[str] | None = None,
    max_items: int = 32,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EntryAdmissionError(f"{field}:SEQUENCE_REQUIRED")
    items = tuple(_text(item, field, max_len=256) for item in value)
    if len(items) > max_items:
        raise EntryAdmissionError(f"{field}:TOO_MANY_ITEMS")
    if len(set(items)) != len(items):
        raise EntryAdmissionError(f"{field}:DUPLICATE_ITEM")
    if allowed is not None and any(item not in allowed for item in items):
        raise EntryAdmissionError(f"{field}:UNSUPPORTED_ITEM")
    return tuple(sorted(items))


def _parse_budget(raw: Any) -> EntryBudget:
    if not isinstance(raw, Mapping):
        raise EntryAdmissionError("budget:MAPPING_REQUIRED")
    unknown = set(raw) - BUDGET_KEYS
    if unknown:
        raise EntryAdmissionError("budget:UNKNOWN_FIELD")
    missing = BUDGET_KEYS - set(raw)
    if missing:
        raise EntryAdmissionError("budget:MISSING_FIELD")
    return EntryBudget(
        max_cells=_bounded_int(raw["max_cells"], "budget.max_cells", minimum=0, maximum=600),
        max_model_calls=_bounded_int(
            raw["max_model_calls"], "budget.max_model_calls", minimum=0, maximum=600
        ),
        max_wall_ms=_bounded_int(raw["max_wall_ms"], "budget.max_wall_ms", minimum=1, maximum=3_600_000),
        max_output_bytes=_bounded_int(
            raw["max_output_bytes"], "budget.max_output_bytes", minimum=1, maximum=16_777_216
        ),
    )


def _payload_binding(request: Mapping[str, Any], modality: str) -> tuple[str, str | None, str | None]:
    has_inline = "payload" in request
    has_ref = "payload_ref" in request
    supplied_digest = request.get("payload_sha256")

    if modality in {"vector_ref", "binary_ref"}:
        if has_inline:
            raise EntryAdmissionError("payload:INLINE_FORBIDDEN_FOR_REFERENCE_MODALITY")
        if not has_ref or not isinstance(supplied_digest, str):
            raise EntryAdmissionError("payload:REFERENCE_AND_SHA256_REQUIRED")
        payload_ref = _text(request["payload_ref"], "payload_ref", max_len=1024)
        digest = supplied_digest.lower()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise EntryAdmissionError("payload_sha256:LOWER_HEX_SHA256_REQUIRED")
        return digest, payload_ref, None

    if has_ref or supplied_digest is not None:
        raise EntryAdmissionError("payload:REFERENCE_FIELDS_FORBIDDEN_FOR_INLINE_MODALITY")
    if not has_inline:
        raise EntryAdmissionError("payload:INLINE_REQUIRED")
    canonical_payload = _canonical_json_text(request["payload"], "payload")
    digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    return digest, None, canonical_payload


def admit_entry(request: Mapping[str, Any], *, current_generation: int) -> EntryPacket:
    if not isinstance(request, Mapping):
        raise EntryAdmissionError("REQUEST_MAPPING_REQUIRED")
    unknown = set(request) - ALLOWED_KEYS
    if unknown:
        raise EntryAdmissionError("REQUEST_UNKNOWN_FIELD")
    if request.get("schema") != ENTRY_SCHEMA:
        raise EntryAdmissionError("REQUEST_SCHEMA_UNSUPPORTED")

    generation = _nonnegative_int(request.get("entity_generation"), "entity_generation")
    if generation != _nonnegative_int(current_generation, "current_generation"):
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    event_kind = _text(request.get("event_kind"), "event_kind")
    if event_kind not in EVENT_KINDS:
        raise EntryAdmissionError("EVENT_KIND_UNSUPPORTED")

    modality = _text(request.get("modality"), "modality")
    if modality not in MODALITIES:
        raise EntryAdmissionError("MODALITY_UNSUPPORTED")

    causal_id = _text(request.get("causal_id"), "causal_id", max_len=128)
    source_id = _text(request.get("source_id"), "source_id", max_len=256)
    source_type = _text(request.get("source_type"), "source_type", max_len=128)

    provenance = request.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        raise EntryAdmissionError("provenance:NONEMPTY_MAPPING_REQUIRED")
    provenance_json = _canonical_json_text(provenance, "provenance")

    observed_at_ns = _nonnegative_int(request.get("observed_at_ns"), "observed_at_ns")
    received_at_ns = _nonnegative_int(request.get("received_at_ns"), "received_at_ns")

    permission_scope = _sequence_of_strings(
        request.get("permission_scope"), "permission_scope", allowed=PERMISSIONS, max_items=8
    )
    parent_packet_ids = _sequence_of_strings(
        request.get("parent_packet_ids", ()), "parent_packet_ids", max_items=32
    )
    budget = _parse_budget(request.get("budget"))
    payload_sha256, payload_ref, canonical_payload_json = _payload_binding(request, modality)

    identity = {
        "schema": PACKET_SCHEMA,
        "policy_version": POLICY_VERSION,
        "event_kind": event_kind,
        "entity_generation": generation,
        "causal_id": causal_id,
        "source_id": source_id,
        "source_type": source_type,
        "provenance": json.loads(provenance_json),
        "modality": modality,
        "observed_at_ns": observed_at_ns,
        "received_at_ns": received_at_ns,
        "permission_scope": permission_scope,
        "parent_packet_ids": parent_packet_ids,
        "budget": {
            "max_cells": budget.max_cells,
            "max_model_calls": budget.max_model_calls,
            "max_wall_ms": budget.max_wall_ms,
            "max_output_bytes": budget.max_output_bytes,
        },
        "payload_sha256": payload_sha256,
        "payload_ref": payload_ref,
    }
    packet_id = hashlib.sha256(_canonical_json_bytes(identity, "packet_identity")).hexdigest()

    return EntryPacket(
        schema=PACKET_SCHEMA,
        policy_version=POLICY_VERSION,
        packet_id=packet_id,
        event_kind=event_kind,
        entity_generation=generation,
        causal_id=causal_id,
        source_id=source_id,
        source_type=source_type,
        provenance_json=provenance_json,
        modality=modality,
        observed_at_ns=observed_at_ns,
        received_at_ns=received_at_ns,
        permission_scope=permission_scope,
        parent_packet_ids=parent_packet_ids,
        budget=budget,
        payload_sha256=payload_sha256,
        payload_ref=payload_ref,
        canonical_payload_json=canonical_payload_json,
    )
