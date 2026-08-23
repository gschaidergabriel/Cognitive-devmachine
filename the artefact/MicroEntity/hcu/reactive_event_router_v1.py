#!/usr/bin/env python3
"""Deterministic script-first router for the HCU reactive world model.

This source component does not perform model inference. It decides which bounded HCU
lanes, if any, deserve model work and whether Zero should receive a compact ClayCode
projection. External providers are explicitly excluded from the internal cognitive
routing graph.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v1"

# Internal cognition is admitted positively. Unknown/future provider or engine labels do
# not become internal merely because they are absent from a denylist.
ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ADMITTED_INTERNAL_ENGINES = {
    "hcu_local_08b": "LOCAL_SHARED_WEIGHT_08B",
}

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


class ReactiveRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    status: str
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    event_sha256: str
    resolved_engine_identity: str | None
    resolved_engine_class: str | None
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256_canonical(value: Any, field: str) -> str:
    try:
        encoded = _canonical(value)
    except (TypeError, ValueError) as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


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


def _validate_internal_provider(event: Mapping[str, Any]) -> None:
    provider = event.get("requested_internal_provider")
    if provider is None:
        return
    if not isinstance(provider, str) or not provider.strip():
        raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_STRING_REQUIRED")
    if provider.strip().lower() not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise ReactiveRoutingError("UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY")


def _resolve_internal_engine(event: Mapping[str, Any]) -> tuple[str | None, str | None]:
    identity = event.get("resolved_internal_engine")
    engine_class = event.get("resolved_internal_engine_class")
    if identity is None and engine_class is None:
        return None, None
    if not isinstance(identity, str) or not identity.strip():
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_IDENTITY_REQUIRED")
    if not isinstance(engine_class, str) or not engine_class.strip():
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CLASS_REQUIRED")
    identity = identity.strip().lower()
    engine_class = engine_class.strip().upper()
    admitted_class = ADMITTED_INTERNAL_ENGINES.get(identity)
    if admitted_class is None:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_NOT_ADMITTED")
    if engine_class != admitted_class:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CLASS_MISMATCH")
    return identity, engine_class


def route_event(event: Mapping[str, Any], *, current_generation: int) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    _validate_internal_provider(event)
    resolved_engine_identity, resolved_engine_class = _resolve_internal_engine(event)

    novelty = _unit(event.get("novelty", 0.0), "novelty")
    contradiction = _unit(event.get("contradiction", 0.0), "contradiction")
    uncertainty = _unit(event.get("uncertainty", 0.0), "uncertainty")
    forecast_need = _unit(event.get("forecast_need", 0.0), "forecast_need")
    effect_pressure = _unit(event.get("effect_pressure", 0.0), "effect_pressure")
    zero_relevance = _unit(event.get("zero_relevance", 0.0), "zero_relevance")
    due_recheck = _bool(event.get("due_recheck", False), "due_recheck")

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
    if event.get("provenance_gap") is True:
        lanes.add("provenance")

    # Goal cognition is selective; a plain event cannot create a goal lane by default.
    if event.get("goal_pressure") is not None and _unit(event["goal_pressure"], "goal_pressure") >= 0.70:
        lanes.add("goal")
        lanes.add("critic")

    # A route that asks for model work must already carry a positively admitted exact
    # internal engine identity/class. Script-only events require no model identity.
    if lanes and resolved_engine_identity is None:
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE")

    projection = zero_relevance >= 0.60 and bool(lanes)
    event_sha256 = _sha256_canonical(dict(event), "EVENT")
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "event_sha256": event_sha256,
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
        "generation": generation,
        "resolved_engine_identity": resolved_engine_identity,
        "resolved_engine_class": resolved_engine_class,
    }
    digest = _sha256_canonical(payload, "ROUTE_DECISION")
    return RouteDecision(
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        event_sha256=event_sha256,
        resolved_engine_identity=resolved_engine_identity,
        resolved_engine_class=resolved_engine_class,
        decision_sha256=digest,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
