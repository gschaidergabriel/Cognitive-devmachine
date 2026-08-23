#!/usr/bin/env python3
"""Typed Entry Fabric admission for EntityOS/HCU cognition.

Deterministic and non-cognitive. It binds immutable causal event identity separately
from transport/admission receipt identity before any HCU/model work. It does not mint
truth, permissions, compute budget or effects.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

ENTRY_SCHEMA = "XENO_ENTRY_PACKET/v1"  # compatibility wire name; product authority is EntityOS/HCU
ENTRY_EVENT_IDENTITY_SCHEMA = "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v3"
ENTRY_ADMISSION_IDENTITY_SCHEMA = "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v3"
HCU_EVENT_SCHEMA = "HCU_REACTIVE_EVENT/v1"

SOURCE_KINDS = {
    "HUMAN_PROMPT", "EXTERNAL_EVENT", "TOOL_OUTCOME", "SENSOR_STREAM",
    "DATABASE_CHANGE", "INTRINSIC_SYSTEM_EVENT",
}
MODALITIES = {"TEXT", "JSON", "BINARY_REF", "SENSOR", "EVENT"}
ENTRY_FIELDS = {
    "schema", "ingress_id", "causal_id", "entity_generation", "source_kind", "source_id",
    "modality", "observed_time", "received_time", "provenance_ref", "provenance_sha256",
    "capabilities", "capability_binding_sha256", "parent_id", "stream_id", "budget",
    "payload_ref", "payload_sha256",
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
    event_sha256: str
    admission_sha256: str


def _identity_sha256(value: Any, field: str) -> str:
    try:
        encoded = canonicalize(value)
    except CanonicalizationError as exc:
        raise EntryFabricError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


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
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _generation(value: Any, current_generation: int) -> int:
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise EntryFabricError("current_generation:NONNEGATIVE_INTEGER_REQUIRED")
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


def _budget(value: Any, field: str = "budget") -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping):
        raise EntryFabricError(f"{field}:MAPPING_REQUIRED")
    unknown = set(value) - BUDGET_FIELDS
    if unknown:
        raise EntryFabricError(f"{field}:UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
    if set(value) != BUDGET_FIELDS:
        raise EntryFabricError(f"{field}:ALL_FIELDS_REQUIRED")
    normalized: dict[str, int] = {}
    for budget_field in sorted(BUDGET_FIELDS):
        item = value[budget_field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise EntryFabricError(f"{field}.{budget_field}:NONNEGATIVE_INTEGER_REQUIRED")
        if item > 9_007_199_254_740_991:
            raise EntryFabricError(f"{field}.{budget_field}:IJSON_SAFE_INTEGER_REQUIRED")
        normalized[budget_field] = item
    return tuple(normalized.items())


def _admit_budget(
    requested_budget: tuple[tuple[str, int], ...],
    admitted_budget: Mapping[str, Any],
) -> tuple[tuple[str, int], ...]:
    """Allow Entry to narrow, never broaden, an externally supplied compute budget."""
    authority_budget = dict(_budget(admitted_budget, "admitted_budget"))
    requested = dict(requested_budget)
    exceeded = sorted(
        field for field in BUDGET_FIELDS if requested[field] > authority_budget[field]
    )
    if exceeded:
        raise EntryFabricError(f"BUDGET_NOT_ADMITTED:{','.join(exceeded)}")
    return requested_budget


def _raw_json_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate object names before Mapping construction can erase evidence."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EntryFabricError(f"RAW_JSON_DUPLICATE_PROPERTY:{key}")
        result[key] = value
    return result


def _reject_nonfinite_json_constant(value: str) -> None:
    raise EntryFabricError(f"RAW_JSON_NONFINITE_NUMBER_FORBIDDEN:{value}")


def _reject_lone_surrogates(value: Any, path: str = "$") -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise EntryFabricError(f"RAW_JSON_LONE_SURROGATE_FORBIDDEN:{path}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_lone_surrogates(key, f"{path}.<key>")
            _reject_lone_surrogates(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_lone_surrogates(item, f"{path}[{index}]")


def parse_entry_json(raw: str | bytes | bytearray) -> Mapping[str, Any]:
    """Parse untrusted raw JSON before typed admission or causal identity creation.

    This closes the pre-Mapping prerequisite in ENTRY_CANONICALIZATION_CONTRACT.json.
    Canonical identity is produced only by the selected versioned RFC8785/JCS profile.
    """
    if not isinstance(raw, (str, bytes, bytearray)):
        raise EntryFabricError("RAW_JSON_TEXT_OR_BYTES_REQUIRED")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_raw_json_pairs_no_duplicates,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except EntryFabricError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EntryFabricError("RAW_JSON_PARSE_FAILED") from exc
    if not isinstance(value, Mapping):
        raise EntryFabricError("ENTRY_MAPPING_REQUIRED")
    _reject_lone_surrogates(value)
    return value


def admit_entry(
    entry: Mapping[str, Any],
    *,
    current_generation: int,
    expected_capability_binding_sha256: str,
    admitted_capabilities: Sequence[str],
    admitted_budget: Mapping[str, Any],
) -> EntryPacket:
    """Admit Typed Entry against externally supplied capability and compute-budget views.

    `admitted_capabilities`, `expected_capability_binding_sha256`, and `admitted_budget`
    are authority inputs; none may be derived from the untrusted Entry payload itself.
    Entry claims may narrow those views but may not broaden them.
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
    capability_binding_sha256 = _sha256(entry.get("capability_binding_sha256"), "capability_binding_sha256")
    expected_capability_binding_sha256 = _sha256(expected_capability_binding_sha256, "expected_capability_binding_sha256")
    if capability_binding_sha256 != expected_capability_binding_sha256:
        raise EntryFabricError("CAPABILITY_BINDING_MISMATCH")
    payload_sha256 = _sha256(entry.get("payload_sha256"), "payload_sha256")
    capabilities = _capabilities(entry.get("capabilities"))
    authority_capabilities = _capabilities(admitted_capabilities, "admitted_capabilities")
    unauthorized = sorted(set(capabilities) - set(authority_capabilities))
    if unauthorized:
        raise EntryFabricError(f"CAPABILITY_NOT_ADMITTED:{','.join(unauthorized)}")
    budget = _admit_budget(_budget(entry.get("budget")), admitted_budget)
    parent_id = _text(entry.get("parent_id"), "parent_id", optional=True)
    stream_id = _text(entry.get("stream_id"), "stream_id", optional=True)

    # Causal event identity is intentionally generation-independent. A recovery may
    # re-admit the same immutable event under a new live generation without changing
    # what event occurred. Generation remains an admission/control-plane fence below.
    event_identity = {
        "schema": ENTRY_EVENT_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "causal_id": causal_id,
        "source_kind": source_kind,
        "source_id": source_id,
        "modality": modality,
        "observed_time": observed_time,
        "provenance_ref": provenance_ref,
        "provenance_sha256": provenance_sha256,
        "parent_id": parent_id,
        "stream_id": stream_id,
        "payload_sha256": payload_sha256,
    }
    event_sha256 = _identity_sha256(event_identity, "ENTRY_EVENT_IDENTITY")
    admission_sha256 = _identity_sha256(
        {
            "schema": ENTRY_ADMISSION_IDENTITY_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "event_sha256": event_sha256,
            "entity_generation": generation,
            "ingress_id": ingress_id,
            "received_time": received_time,
            "capabilities": list(capabilities),
            "capability_binding_sha256": capability_binding_sha256,
            "budget": dict(budget),
            "payload_ref": payload_ref,
        },
        "ENTRY_ADMISSION_IDENTITY",
    )
    return EntryPacket(
        schema=ENTRY_SCHEMA,
        ingress_id=ingress_id,
        causal_id=causal_id,
        entity_generation=generation,
        source_kind=source_kind,
        source_id=source_id,
        modality=modality,
        observed_time=observed_time,
        received_time=received_time,
        provenance_ref=provenance_ref,
        provenance_sha256=provenance_sha256,
        capabilities=capabilities,
        capability_binding_sha256=capability_binding_sha256,
        parent_id=parent_id,
        stream_id=stream_id,
        budget=budget,
        payload_ref=payload_ref,
        payload_sha256=payload_sha256,
        event_sha256=event_sha256,
        admission_sha256=admission_sha256,
    )


def admit_entry_json(
    raw: str | bytes | bytearray,
    *,
    current_generation: int,
    expected_capability_binding_sha256: str,
    admitted_capabilities: Sequence[str],
    admitted_budget: Mapping[str, Any],
) -> EntryPacket:
    """Loss-preserving raw-ingress boundary followed by normal typed admission."""
    return admit_entry(
        parse_entry_json(raw),
        current_generation=current_generation,
        expected_capability_binding_sha256=expected_capability_binding_sha256,
        admitted_capabilities=admitted_capabilities,
        admitted_budget=admitted_budget,
    )


def to_hcu_reactive_event(packet: EntryPacket, *, novelty: float = 0.0, contradiction: float = 0.0,
                          uncertainty: float = 0.0, forecast_need: float = 0.0,
                          effect_pressure: float = 0.0, zero_relevance: float = 0.0,
                          due_recheck: bool = False, provenance_gap: bool = False,
                          goal_pressure: float | None = None) -> dict[str, Any]:
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
        "entry_event_sha256": packet.event_sha256,
        "entry_admission_sha256": packet.admission_sha256,
        "entry_canonicalization_schema": CANONICALIZATION_SCHEMA,
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
    return json.dumps(asdict(packet), sort_keys=True, separators=(",", ":"), ensure_ascii=False)