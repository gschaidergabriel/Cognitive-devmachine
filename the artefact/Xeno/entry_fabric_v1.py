#!/usr/bin/env python3
"""Fail-closed typed ingress admission for the current Xeno bootstrap.

This module is intentionally deterministic and model-free. It binds causal identity,
provenance, generation, permissions, budget and payload identity before any XPU/XCU
cognition. It grants neither truth nor effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping

SCHEMA = "XENO_ENTRY_PACKET/v1"
SOURCE_KINDS = {
    "HUMAN_PROMPT",
    "TOOL_OUTCOME",
    "EXTERNAL_EVENT",
    "SENSOR_STREAM",
    "DATABASE_CHANGE",
    "INTRINSIC_SYSTEM",
}
MODALITIES = {
    "TEXT",
    "JSON",
    "BINARY",
    "IMAGE",
    "AUDIO",
    "VIDEO",
    "STATE_DELTA",
    "METRIC",
}
MODES = {
    "XENO_GRID10",
    "XENO_COGSIM10",
    "XENO_WM_TEST",
    "XENO_NESTED_SIM",
    "XENO_SCALEOUT",
}
REQUIRED_FIELDS = {
    "schema",
    "ingress_id",
    "causal_id",
    "entity_generation",
    "source_kind",
    "modality",
    "observed_at",
    "received_at",
    "provenance_ref",
    "permission_scope",
    "compute_budget",
    "payload_ref",
    "payload_sha256",
    "payload_size",
}
OPTIONAL_FIELDS = {"parent_ingress_id", "stream_id", "mode_hint"}
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EntryAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class ComputeBudget:
    max_wall_ms: int
    max_model_tokens: int
    max_logical_cells: int


@dataclass(frozen=True)
class EntryPacket:
    schema: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    source_kind: str
    modality: str
    observed_at: str
    received_at: str
    provenance_ref: str
    permission_scope: tuple[str, ...]
    compute_budget: ComputeBudget
    payload_ref: str
    payload_sha256: str
    payload_size: int
    parent_ingress_id: str | None
    stream_id: str | None
    mode_hint: str | None
    packet_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _nonempty_string(value: Any, field: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str):
        raise EntryAdmissionError(f"{field}:STRING_REQUIRED")
    value = value.strip()
    if not value:
        raise EntryAdmissionError(f"{field}:NONEMPTY_REQUIRED")
    if len(value) > max_len:
        raise EntryAdmissionError(f"{field}:TOO_LONG")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, field)


def _timestamp(value: Any, field: str) -> str:
    text = _nonempty_string(value, field, max_len=128)
    parse_value = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise EntryAdmissionError(f"{field}:RFC3339_REQUIRED") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EntryAdmissionError(f"{field}:TIMEZONE_REQUIRED")
    return text


def _positive_int(value: Any, field: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EntryAdmissionError(f"{field}:INTEGER_REQUIRED")
    minimum = 0 if allow_zero else 1
    if value < minimum:
        raise EntryAdmissionError(f"{field}:OUT_OF_RANGE")
    return value


def _permission_scope(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EntryAdmissionError("permission_scope:LIST_REQUIRED")
    normalized: set[str] = set()
    for item in value:
        normalized.add(_nonempty_string(item, "permission_scope_item", max_len=160))
    return tuple(sorted(normalized))


def _budget(value: Any) -> ComputeBudget:
    if not isinstance(value, Mapping):
        raise EntryAdmissionError("compute_budget:OBJECT_REQUIRED")
    expected = {"max_wall_ms", "max_model_tokens", "max_logical_cells"}
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise EntryAdmissionError("compute_budget:UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))
    if missing:
        raise EntryAdmissionError("compute_budget:MISSING_FIELDS:" + ",".join(sorted(missing)))
    return ComputeBudget(
        max_wall_ms=_positive_int(value["max_wall_ms"], "max_wall_ms"),
        max_model_tokens=_positive_int(value["max_model_tokens"], "max_model_tokens", allow_zero=True),
        max_logical_cells=_positive_int(value["max_logical_cells"], "max_logical_cells"),
    )


def _identity_payload(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return the normalized causal identity committed into packet_sha256."""
    return {
        "schema": packet["schema"],
        "ingress_id": packet["ingress_id"],
        "causal_id": packet["causal_id"],
        "entity_generation": packet["entity_generation"],
        "source_kind": packet["source_kind"],
        "modality": packet["modality"],
        "observed_at": packet["observed_at"],
        "received_at": packet["received_at"],
        "provenance_ref": packet["provenance_ref"],
        "permission_scope": list(packet["permission_scope"]),
        "compute_budget": asdict(packet["compute_budget"]),
        "payload_ref": packet["payload_ref"],
        "payload_sha256": packet["payload_sha256"],
        "payload_size": packet["payload_size"],
        "parent_ingress_id": packet["parent_ingress_id"],
        "stream_id": packet["stream_id"],
        "mode_hint": packet["mode_hint"],
    }


def admit_entry(event: Mapping[str, Any], *, current_generation: int) -> EntryPacket:
    if not isinstance(event, Mapping):
        raise EntryAdmissionError("ENTRY_OBJECT_REQUIRED")
    unknown = set(event) - ALLOWED_FIELDS
    missing = REQUIRED_FIELDS - set(event)
    if unknown:
        raise EntryAdmissionError("ENTRY_UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))
    if missing:
        raise EntryAdmissionError("ENTRY_MISSING_FIELDS:" + ",".join(sorted(missing)))
    if event.get("schema") != SCHEMA:
        raise EntryAdmissionError("ENTRY_SCHEMA_UNSUPPORTED")

    generation = _positive_int(event.get("entity_generation"), "entity_generation", allow_zero=True)
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise EntryAdmissionError("CURRENT_GENERATION_INVALID")
    if generation != current_generation:
        raise EntryAdmissionError("STALE_ENTITY_GENERATION")

    source_kind = _nonempty_string(event.get("source_kind"), "source_kind", max_len=64).upper()
    if source_kind not in SOURCE_KINDS:
        raise EntryAdmissionError("SOURCE_KIND_UNSUPPORTED")
    modality = _nonempty_string(event.get("modality"), "modality", max_len=64).upper()
    if modality not in MODALITIES:
        raise EntryAdmissionError("MODALITY_UNSUPPORTED")

    payload_sha256 = _nonempty_string(event.get("payload_sha256"), "payload_sha256", max_len=64).lower()
    if not _SHA256_RE.fullmatch(payload_sha256):
        raise EntryAdmissionError("PAYLOAD_SHA256_INVALID")

    mode_hint = _optional_string(event.get("mode_hint"), "mode_hint")
    if mode_hint is not None:
        mode_hint = mode_hint.upper()
        if mode_hint not in MODES:
            raise EntryAdmissionError("MODE_HINT_UNSUPPORTED")

    normalized = {
        "schema": SCHEMA,
        "ingress_id": _nonempty_string(event.get("ingress_id"), "ingress_id"),
        "causal_id": _nonempty_string(event.get("causal_id"), "causal_id"),
        "entity_generation": generation,
        "source_kind": source_kind,
        "modality": modality,
        "observed_at": _timestamp(event.get("observed_at"), "observed_at"),
        "received_at": _timestamp(event.get("received_at"), "received_at"),
        "provenance_ref": _nonempty_string(event.get("provenance_ref"), "provenance_ref", max_len=1024),
        "permission_scope": _permission_scope(event.get("permission_scope")),
        "compute_budget": _budget(event.get("compute_budget")),
        "payload_ref": _nonempty_string(event.get("payload_ref"), "payload_ref", max_len=1024),
        "payload_sha256": payload_sha256,
        "payload_size": _positive_int(event.get("payload_size"), "payload_size", allow_zero=True),
        "parent_ingress_id": _optional_string(event.get("parent_ingress_id"), "parent_ingress_id"),
        "stream_id": _optional_string(event.get("stream_id"), "stream_id"),
        "mode_hint": mode_hint,
    }
    digest = hashlib.sha256(_canonical(_identity_payload(normalized))).hexdigest()
    return EntryPacket(packet_sha256=digest, **normalized)


def packet_json(packet: EntryPacket) -> str:
    return json.dumps(asdict(packet), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
