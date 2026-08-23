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
FORBIDDEN_INTERNAL_PROVIDERS = {"nvidia", "mistral", "groq", "openrouter", "together"}
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


def route_event(event: Mapping[str, Any], *, current_generation: int) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    provider = event.get("requested_internal_provider")
    if provider is not None:
        if not isinstance(provider, str):
            raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_STRING_REQUIRED")
        if provider.strip().lower() in FORBIDDEN_INTERNAL_PROVIDERS:
            raise ReactiveRoutingError("EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY")

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
        decision_sha256=digest,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
