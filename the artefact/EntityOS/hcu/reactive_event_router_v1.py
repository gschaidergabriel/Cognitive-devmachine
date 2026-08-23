#!/usr/bin/env python3
"""Deterministic fail-closed EntityOS/HCU reactive event router.

This component is a control-plane router only. It does not perform inference and it
cannot mint canonical truth or effects. Model activation is admitted only when a
positively identified bundled-local HCU engine artifact is bound. Route identity
commits to causal event identity, router policy, engine identity, and derived route.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

EVENT_SCHEMA = "HCU_REACTIVE_EVENT/v1"
DECISION_SCHEMA = "ENTITYOS_HCU_ROUTE_DECISION/v2"
ADMITTED_ENGINE_CLASS = "HCU_LOCAL_BUNDLED_08B"
SCRIPT_ENGINE_CLASS = "DETERMINISTIC_SCRIPT"
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
THRESHOLDS = {
    "world_novelty": 0.55,
    "world_contradiction": 0.35,
    "hypothesis_contradiction": 0.35,
    "hypothesis_uncertainty": 0.60,
    "simulation_forecast_need": 0.50,
    "simulation_effect_pressure": 0.45,
    "zero_model_effect_pressure": 0.45,
    "zero_model_relevance": 0.70,
    "goal_pressure": 0.70,
    "zero_projection_relevance": 0.60,
}
_ENGINE_FIELDS = {
    "requested_internal_provider",
    "resolved_engine_class",
    "resolved_engine_sha256",
}


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
    engine_class: str
    engine_sha256: str | None
    router_policy_sha256: str
    decision_sha256: str


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
        raise ReactiveRoutingError("EVENT_NOT_CANONICAL_JSON") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


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


def _digest64(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ReactiveRoutingError(f"{field}:SHA256_REQUIRED")
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise ReactiveRoutingError(f"{field}:SHA256_REQUIRED")
    return normalized


def _event_identity(event: Mapping[str, Any]) -> str:
    # Engine resolution is a separate authority dimension. The causal event digest
    # therefore commits to admitted event bytes while keeping engine identity explicit.
    return _sha256({key: value for key, value in event.items() if key not in _ENGINE_FIELDS})


def _policy_digest() -> str:
    return _sha256(
        {
            "decision_schema": DECISION_SCHEMA,
            "event_schema": EVENT_SCHEMA,
            "admitted_engine_class": ADMITTED_ENGINE_CLASS,
            "script_engine_class": SCRIPT_ENGINE_CLASS,
            "script_stages": SCRIPT_STAGES,
            "thresholds": THRESHOLDS,
            "provider_field_policy": "REJECT_ANY_PROVIDER_ALIAS_USE_POSITIVE_ENGINE_IDENTITY",
        }
    )


ROUTER_POLICY_SHA256 = _policy_digest()


def _resolve_engine(event: Mapping[str, Any], *, model_required: bool) -> tuple[str, str | None]:
    # Provider-name deny/allow lists are not authority. Any provider alias is rejected;
    # active model routing requires one exact admitted internal class + artifact digest.
    if "requested_internal_provider" in event:
        raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_UNSUPPORTED_USE_ENGINE_IDENTITY")

    engine_class = event.get("resolved_engine_class")
    engine_sha = event.get("resolved_engine_sha256")

    if not model_required:
        if engine_class is not None or engine_sha is not None:
            raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_BIND_MODEL_ENGINE")
        return SCRIPT_ENGINE_CLASS, None

    if engine_class != ADMITTED_ENGINE_CLASS:
        raise ReactiveRoutingError("INTERNAL_ENGINE_CLASS_NOT_ADMITTED")
    return ADMITTED_ENGINE_CLASS, _digest64(engine_sha, "resolved_engine_sha256")


def route_event(event: Mapping[str, Any], *, current_generation: int) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != EVENT_SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    novelty = _unit(event.get("novelty", 0.0), "novelty")
    contradiction = _unit(event.get("contradiction", 0.0), "contradiction")
    uncertainty = _unit(event.get("uncertainty", 0.0), "uncertainty")
    forecast_need = _unit(event.get("forecast_need", 0.0), "forecast_need")
    effect_pressure = _unit(event.get("effect_pressure", 0.0), "effect_pressure")
    zero_relevance = _unit(event.get("zero_relevance", 0.0), "zero_relevance")
    due_recheck = _bool(event.get("due_recheck", False), "due_recheck")

    lanes: set[str] = set()
    if novelty >= THRESHOLDS["world_novelty"] or contradiction >= THRESHOLDS["world_contradiction"] or due_recheck:
        lanes.add("world")
    if contradiction >= THRESHOLDS["hypothesis_contradiction"] or uncertainty >= THRESHOLDS["hypothesis_uncertainty"]:
        lanes.add("hypothesis")
    if forecast_need >= THRESHOLDS["simulation_forecast_need"] or effect_pressure >= THRESHOLDS["simulation_effect_pressure"]:
        lanes.add("simulation")
    if effect_pressure >= THRESHOLDS["zero_model_effect_pressure"] or zero_relevance >= THRESHOLDS["zero_model_relevance"]:
        lanes.add("zero_model")
    if lanes:
        lanes.add("critic")
    if event.get("provenance_gap") is True:
        lanes.add("provenance")
    if event.get("goal_pressure") is not None and _unit(event["goal_pressure"], "goal_pressure") >= THRESHOLDS["goal_pressure"]:
        lanes.add("goal")
        lanes.add("critic")

    projection = zero_relevance >= THRESHOLDS["zero_projection_relevance"] and bool(lanes)
    engine_class, engine_sha = _resolve_engine(event, model_required=bool(lanes))
    event_sha = _event_identity(event)
    routing_result = {
        "generation": generation,
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
    }
    decision_sha = _sha256(
        {
            "schema": DECISION_SCHEMA,
            "event_sha256": event_sha,
            "router_policy_sha256": ROUTER_POLICY_SHA256,
            "engine_class": engine_class,
            "engine_sha256": engine_sha,
            "routing_result": routing_result,
        }
    )
    return RouteDecision(
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        event_sha256=event_sha,
        engine_class=engine_class,
        engine_sha256=engine_sha,
        router_policy_sha256=ROUTER_POLICY_SHA256,
        decision_sha256=decision_sha,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
