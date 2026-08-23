#!/usr/bin/env python3
"""Deterministic script-first router for the current EntityOS/HCU execution lane.

This module re-derives the useful reactive-router mechanism from donor PR #1263 under
the current EntityOS + HCU authority. It is not a state, truth, identity, recovery, or
effect authority. Canonical durable state remains outside this router and real effects
remain behind the admitted EffectGate/EffectJournal path.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

EVENT_SCHEMA = "HCU_REACTIVE_EVENT/v1"
EVENT_IDENTITY_SCHEMA = "ENTITYOS_HCU_EVENT_IDENTITY/v1"
ROUTE_DECISION_SCHEMA = "ENTITYOS_HCU_ROUTE_DECISION/v2"
CANONICALIZATION = "PYTHON_JSON_SORT_KEYS_V1"
LOCAL_ENGINE_CLASS = "LOCAL_HCU_MODEL"
SCRIPT_ENGINE_CLASS = "DETERMINISTIC_SCRIPT"
SCRIPT_ENGINE_ID = "entityos.hcu.script_router.v1"
SCRIPT_STAGES = (
    "generation_check",
    "canonical_rebind",
    "temporal_delta",
    "provenance_join",
    "contradiction_index",
    "falsifier_update",
    "calibration_update",
    "incremental_field_projection",
    "zero_relevance_score",
)
EVENT_FIELDS = frozenset(
    {
        "schema",
        "event_source",
        "event_id",
        "entity_generation",
        "novelty",
        "contradiction",
        "uncertainty",
        "forecast_need",
        "effect_pressure",
        "zero_relevance",
        "due_recheck",
        "provenance_gap",
        "goal_pressure",
    }
)
ENGINE_FIELDS = frozenset(
    {"engine_id", "engine_class", "checkpoint_sha256", "tokenizer_sha256", "runtime_id"}
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReactiveRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    status: str
    event_source: str
    event_id: str
    event_sha256: str
    cognition_engine_id: str
    cognition_engine_class: str
    cognition_checkpoint_sha256: str | None
    cognition_tokenizer_sha256: str | None
    cognition_runtime_id: str
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    """Stable Python-local canonical bytes; this does not claim RFC 8785/JCS compliance."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReactiveRoutingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _unit(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReactiveRoutingError(f"{field}:NUMBER_REQUIRED")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ReactiveRoutingError(f"{field}:UNIT_INTERVAL_REQUIRED")
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ReactiveRoutingError(f"{field}:BOOLEAN_REQUIRED")
    return value


def _normalize_event(event: Mapping[str, Any], current_generation: int) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise ReactiveRoutingError("EVENT_MAPPING_REQUIRED")
    if any(not isinstance(key, str) for key in event):
        raise ReactiveRoutingError("EVENT_FIELD_NAME_STRING_REQUIRED")
    unknown = sorted(set(event) - EVENT_FIELDS)
    if unknown:
        raise ReactiveRoutingError(f"EVENT_FIELD_UNSUPPORTED:{','.join(unknown)}")
    if event.get("schema") != EVENT_SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")

    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    goal_raw = event.get("goal_pressure")
    goal_pressure = None if goal_raw is None else _unit(goal_raw, "goal_pressure")
    return {
        "schema": EVENT_SCHEMA,
        "event_source": _nonempty_string(event.get("event_source"), "event_source"),
        "event_id": _nonempty_string(event.get("event_id"), "event_id"),
        "entity_generation": generation,
        "novelty": _unit(event.get("novelty", 0.0), "novelty"),
        "contradiction": _unit(event.get("contradiction", 0.0), "contradiction"),
        "uncertainty": _unit(event.get("uncertainty", 0.0), "uncertainty"),
        "forecast_need": _unit(event.get("forecast_need", 0.0), "forecast_need"),
        "effect_pressure": _unit(event.get("effect_pressure", 0.0), "effect_pressure"),
        "zero_relevance": _unit(event.get("zero_relevance", 0.0), "zero_relevance"),
        "due_recheck": _bool(event.get("due_recheck", False), "due_recheck"),
        "provenance_gap": _bool(event.get("provenance_gap", False), "provenance_gap"),
        "goal_pressure": goal_pressure,
    }


def _event_identity(normalized_event: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    envelope = {
        "schema": EVENT_IDENTITY_SCHEMA,
        "canonicalization": CANONICALIZATION,
        "source": normalized_event["event_source"],
        "id": normalized_event["event_id"],
        "event": normalized_event,
    }
    return envelope, _digest(envelope)


def _script_engine() -> dict[str, Any]:
    return {
        "engine_id": SCRIPT_ENGINE_ID,
        "engine_class": SCRIPT_ENGINE_CLASS,
        "checkpoint_sha256": None,
        "tokenizer_sha256": None,
        "runtime_id": "python",
    }


def _admit_local_engine(engine: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(engine, Mapping):
        raise ReactiveRoutingError("LOCAL_HCU_ENGINE_REQUIRED")
    if any(not isinstance(key, str) for key in engine):
        raise ReactiveRoutingError("ENGINE_FIELD_NAME_STRING_REQUIRED")
    unknown = sorted(set(engine) - ENGINE_FIELDS)
    if unknown:
        raise ReactiveRoutingError(f"ENGINE_FIELD_UNSUPPORTED:{','.join(unknown)}")
    missing = sorted(ENGINE_FIELDS - set(engine))
    if missing:
        raise ReactiveRoutingError(f"ENGINE_FIELD_REQUIRED:{','.join(missing)}")

    engine_class = _nonempty_string(engine.get("engine_class"), "engine_class")
    if engine_class != LOCAL_ENGINE_CLASS:
        raise ReactiveRoutingError("UNADMITTED_COGNITION_ENGINE_CLASS")
    engine_id = _nonempty_string(engine.get("engine_id"), "engine_id")
    runtime_id = _nonempty_string(engine.get("runtime_id"), "runtime_id")
    checkpoint = _nonempty_string(engine.get("checkpoint_sha256"), "checkpoint_sha256")
    tokenizer = _nonempty_string(engine.get("tokenizer_sha256"), "tokenizer_sha256")
    if not _SHA256_RE.fullmatch(checkpoint):
        raise ReactiveRoutingError("CHECKPOINT_SHA256_LOWER_HEX_REQUIRED")
    if not _SHA256_RE.fullmatch(tokenizer):
        raise ReactiveRoutingError("TOKENIZER_SHA256_LOWER_HEX_REQUIRED")
    return {
        "engine_id": engine_id,
        "engine_class": engine_class,
        "checkpoint_sha256": checkpoint,
        "tokenizer_sha256": tokenizer,
        "runtime_id": runtime_id,
    }


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    engine: Mapping[str, Any] | None = None,
) -> RouteDecision:
    normalized = _normalize_event(event, current_generation)
    _, event_sha256 = _event_identity(normalized)

    novelty = normalized["novelty"]
    contradiction = normalized["contradiction"]
    uncertainty = normalized["uncertainty"]
    forecast_need = normalized["forecast_need"]
    effect_pressure = normalized["effect_pressure"]
    zero_relevance = normalized["zero_relevance"]
    due_recheck = normalized["due_recheck"]

    lanes: set[str] = set()
    if novelty >= 0.55 or contradiction >= 0.35 or due_recheck:
        lanes.add("world")
    if contradiction >= 0.35 or uncertainty >= 0.60:
        lanes.add("hypothesis")
    if forecast_need >= 0.50 or effect_pressure >= 0.45:
        lanes.add("simulation")
    if effect_pressure >= 0.45 or zero_relevance >= 0.70:
        lanes.add("zero_model")
    if lanes:
        lanes.add("critic")
    if normalized["provenance_gap"]:
        lanes.add("provenance")
    if normalized["goal_pressure"] is not None and normalized["goal_pressure"] >= 0.70:
        lanes.add("goal")
        lanes.add("critic")

    if lanes:
        admitted_engine = _admit_local_engine(engine)
    else:
        if engine is not None:
            raise ReactiveRoutingError("MODEL_ENGINE_FORBIDDEN_FOR_SCRIPT_ONLY_ROUTE")
        admitted_engine = _script_engine()

    projection = zero_relevance >= 0.60 and bool(lanes)
    routing = {
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
        "generation": normalized["entity_generation"],
    }
    decision_envelope = {
        "schema": ROUTE_DECISION_SCHEMA,
        "canonicalization": CANONICALIZATION,
        "event_sha256": event_sha256,
        "engine": admitted_engine,
        "routing": routing,
    }
    decision_sha256 = _digest(decision_envelope)

    return RouteDecision(
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
        event_source=normalized["event_source"],
        event_id=normalized["event_id"],
        event_sha256=event_sha256,
        cognition_engine_id=admitted_engine["engine_id"],
        cognition_engine_class=admitted_engine["engine_class"],
        cognition_checkpoint_sha256=admitted_engine["checkpoint_sha256"],
        cognition_tokenizer_sha256=admitted_engine["tokenizer_sha256"],
        cognition_runtime_id=admitted_engine["runtime_id"],
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        decision_sha256=decision_sha256,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
