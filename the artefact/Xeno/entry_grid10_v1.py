#!/usr/bin/env python3
"""Xeno typed Entry Fabric + deterministic GRID10 baseline.

This module is a bounded current-facing primitive over the existing canonical state/effect
authorities. It does not persist canonical truth, run model inference, or execute effects.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

ENTRY_SCHEMA = "XENO_ENTRY_PACKET/v1"
PLAN_SCHEMA = "XENO_GRID10_PLAN/v1"
MODE = "XENO_GRID10"

INGRESS_KINDS = {
    "human_prompt",
    "external_event",
    "tool_outcome",
    "sensor_stream",
    "db_change",
    "intrinsic_event",
}
MODALITIES = {"text", "json", "measurement", "state_delta", "binary_ref"}
CELL_FUNCTIONS = (
    "entry_validate",
    "retrieval",
    "hypothesis",
    "counterhypothesis",
    "critic",
    "simulation",
    "provenance",
    "calibration",
    "workspace_reduce",
    "effect_candidate_translate",
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class XenoEntryError(ValueError):
    pass


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
        raise XenoEntryError("NON_CANONICAL_JSON_VALUE") from exc


def _text(value: Any, field: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str):
        raise XenoEntryError(f"{field}:STRING_REQUIRED")
    value = value.strip()
    if not value or len(value) > max_len:
        raise XenoEntryError(f"{field}:NONEMPTY_BOUNDED_STRING_REQUIRED")
    return value


def _uint(value: Any, field: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise XenoEntryError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if maximum is not None and value > maximum:
        raise XenoEntryError(f"{field}:LIMIT_EXCEEDED")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64).lower()
    if not _HEX64.fullmatch(value):
        raise XenoEntryError(f"{field}:SHA256_HEX_REQUIRED")
    return value


@dataclass(frozen=True)
class EntryBudget:
    max_tokens: int
    max_ms: int
    max_bytes: int


@dataclass(frozen=True)
class AdmittedEntry:
    schema: str
    entry_id: str
    ingress_kind: str
    causal_id: str
    entity_generation: int
    provenance_source: str
    provenance_sha256: str
    modality: str
    observed_at_ns: int
    payload_sha256: str
    payload_bytes: int
    permission_scopes: tuple[str, ...]
    budget: EntryBudget


@dataclass(frozen=True)
class Grid10Cell:
    slot: int
    function: str
    worker_lane: int
    effect_authority: bool


@dataclass(frozen=True)
class Grid10Plan:
    schema: str
    mode: str
    plan_id: str
    entry_id: str
    causal_id: str
    entity_generation: int
    logical_cell_count: int
    physical_worker_lanes: int
    cells: tuple[Grid10Cell, ...]


def admit_entry(raw: Mapping[str, Any], *, current_generation: int) -> AdmittedEntry:
    if not isinstance(raw, Mapping) or raw.get("schema") != ENTRY_SCHEMA:
        raise XenoEntryError("ENTRY_SCHEMA_UNSUPPORTED")

    generation = _uint(raw.get("entity_generation"), "entity_generation")
    if generation != current_generation:
        raise XenoEntryError("STALE_ENTITY_GENERATION")

    ingress_kind = _text(raw.get("ingress_kind"), "ingress_kind", max_len=64)
    if ingress_kind not in INGRESS_KINDS:
        raise XenoEntryError("INGRESS_KIND_UNSUPPORTED")

    modality = _text(raw.get("modality"), "modality", max_len=64)
    if modality not in MODALITIES:
        raise XenoEntryError("MODALITY_UNSUPPORTED")

    provenance = raw.get("provenance")
    if not isinstance(provenance, Mapping):
        raise XenoEntryError("PROVENANCE_MAPPING_REQUIRED")
    provenance_source = _text(provenance.get("source"), "provenance.source")
    provenance_sha256 = _sha256(provenance.get("sha256"), "provenance.sha256")

    payload_sha256 = _sha256(raw.get("payload_sha256"), "payload_sha256")
    payload_bytes = _uint(raw.get("payload_bytes"), "payload_bytes", maximum=16 * 1024 * 1024)
    observed_at_ns = _uint(raw.get("observed_at_ns"), "observed_at_ns")
    causal_id = _text(raw.get("causal_id"), "causal_id", max_len=128)

    scopes = raw.get("permission_scopes", ())
    if not isinstance(scopes, Sequence) or isinstance(scopes, (str, bytes, bytearray)):
        raise XenoEntryError("PERMISSION_SCOPES_SEQUENCE_REQUIRED")
    normalized_scopes: list[str] = []
    for scope in scopes:
        normalized_scopes.append(_text(scope, "permission_scope", max_len=96))
    if len(normalized_scopes) != len(set(normalized_scopes)):
        raise XenoEntryError("DUPLICATE_PERMISSION_SCOPE")
    normalized_scopes.sort()

    budget_raw = raw.get("budget")
    if not isinstance(budget_raw, Mapping):
        raise XenoEntryError("BUDGET_MAPPING_REQUIRED")
    budget = EntryBudget(
        max_tokens=_uint(budget_raw.get("max_tokens"), "budget.max_tokens", maximum=1_000_000),
        max_ms=_uint(budget_raw.get("max_ms"), "budget.max_ms", maximum=86_400_000),
        max_bytes=_uint(budget_raw.get("max_bytes"), "budget.max_bytes", maximum=64 * 1024 * 1024),
    )
    if payload_bytes > budget.max_bytes:
        raise XenoEntryError("PAYLOAD_EXCEEDS_ENTRY_BUDGET")

    identity_payload = {
        "schema": ENTRY_SCHEMA,
        "ingress_kind": ingress_kind,
        "causal_id": causal_id,
        "entity_generation": generation,
        "provenance": {"source": provenance_source, "sha256": provenance_sha256},
        "modality": modality,
        "observed_at_ns": observed_at_ns,
        "payload_sha256": payload_sha256,
        "payload_bytes": payload_bytes,
        "permission_scopes": normalized_scopes,
        "budget": asdict(budget),
    }
    entry_id = hashlib.sha256(_canonical(identity_payload)).hexdigest()
    return AdmittedEntry(
        schema=ENTRY_SCHEMA,
        entry_id=entry_id,
        ingress_kind=ingress_kind,
        causal_id=causal_id,
        entity_generation=generation,
        provenance_source=provenance_source,
        provenance_sha256=provenance_sha256,
        modality=modality,
        observed_at_ns=observed_at_ns,
        payload_sha256=payload_sha256,
        payload_bytes=payload_bytes,
        permission_scopes=tuple(normalized_scopes),
        budget=budget,
    )


def compile_grid10(entry: AdmittedEntry, *, physical_worker_lanes: int = 1) -> Grid10Plan:
    if not isinstance(entry, AdmittedEntry):
        raise XenoEntryError("ADMITTED_ENTRY_REQUIRED")
    lanes = _uint(physical_worker_lanes, "physical_worker_lanes", maximum=10)
    if lanes < 1:
        raise XenoEntryError("PHYSICAL_WORKER_LANES_AT_LEAST_ONE")

    cells = tuple(
        Grid10Cell(
            slot=slot,
            function=function,
            worker_lane=slot % lanes,
            effect_authority=False,
        )
        for slot, function in enumerate(CELL_FUNCTIONS)
    )
    plan_payload = {
        "schema": PLAN_SCHEMA,
        "mode": MODE,
        "entry_id": entry.entry_id,
        "causal_id": entry.causal_id,
        "entity_generation": entry.entity_generation,
        "logical_cell_count": len(cells),
        "physical_worker_lanes": lanes,
        "cells": [asdict(cell) for cell in cells],
    }
    plan_id = hashlib.sha256(_canonical(plan_payload)).hexdigest()
    return Grid10Plan(
        schema=PLAN_SCHEMA,
        mode=MODE,
        plan_id=plan_id,
        entry_id=entry.entry_id,
        causal_id=entry.causal_id,
        entity_generation=entry.entity_generation,
        logical_cell_count=len(cells),
        physical_worker_lanes=lanes,
        cells=cells,
    )
