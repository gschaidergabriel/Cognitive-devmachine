#!/usr/bin/env python3
"""Deterministic script-first router for the EntityOS HCU reactive world model.

This source component does not perform model inference. It decides which bounded HCU
lanes, if any, deserve model work and whether Zero should receive a compact ClayCode
projection. Internal cognition uses positive admission. Every model route binds causal
event identity, router policy, exact admitted engine identity/class/checkpoint and the
routing result into one deterministic decision digest.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v2"

# Internal cognition is admitted positively. Unknown/future provider or engine labels do
# not become internal merely because they are absent from a denylist. The checkpoint hash
# carried by an event is identity/provenance input only; exact runtime acceptance must also
# verify it against the actual loaded bytes/runtime receipt.
ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ADMITTED_INTERNAL_ENGINES = {
    "hcu_local_08b": {
        "class": "LOCAL_SHARED_WEIGHT_08B",
        "checkpoint_sha256_required": True,
    },
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
ROUTER_POLICY = {
    "schema": "HCU_REACTIVE_ROUTER_POLICY/v1",
    "scripts": SCRIPT_STAGES,
    "thresholds": {
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
    },
}
_ENGINE_SELECTION_FIELDS = {
    "requested_internal_provider",
    "resolved_internal_engine",
    "resolved_internal_engine_class",
    "resolved_internal_engine_checkpoint_sha256",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    router_policy_sha256: str
    resolved_engine_identity: str | None
    resolved_engine_class: str | None
    resolved_engine_checkpoint_sha256: str | None
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256_canonical(value: Any, field: str) -> str:
    try:
        encoded = _canonical(value)
    except (TypeError, ValueError) as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


ROUTER_POLICY_SHA256 = _sha256_canonical(ROUTER_POLICY, "ROUTER_POLICY")


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


def _resolve_internal_engine(event: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    identity = event.get("resolved_internal_engine")
    engine_class = event.get("resolved_internal_engine_class")
    checkpoint_sha256 = event.get("resolved_internal_engine_checkpoint_sha256")

    if identity is None and engine_class is None and checkpoint_sha256 is None:
        return None, None, None
    if not isinstance(identity, str) or not identity.strip():
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_IDENTITY_REQUIRED")
    if not isinstance(engine_class, str) or not engine_class.strip():
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CLASS_REQUIRED")

    identity = identity.strip().lower()
    engine_class = engine_class.strip().upper()
    admitted = ADMITTED_INTERNAL_ENGINES.get(identity)
    if admitted is None:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_NOT_ADMITTED")
    if engine_class != admitted["class"]:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CLASS_MISMATCH")

    if admitted.get("checkpoint_sha256_required"):
        if not isinstance(checkpoint_sha256, str):
            raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CHECKPOINT_SHA256_REQUIRED")
        checkpoint_sha256 = checkpoint_sha256.strip().lower()
        if not _SHA256_RE.fullmatch(checkpoint_sha256):
            raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CHECKPOINT_SHA256_INVALID")
    elif checkpoint_sha256 is not None:
        if not isinstance(checkpoint_sha256, str):
            raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CHECKPOINT_SHA256_INVALID")
        checkpoint_sha256 = checkpoint_sha256.strip().lower()
        if not _SHA256_RE.fullmatch(checkpoint_sha256):
            raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_CHECKPOINT_SHA256_INVALID")

    return identity, engine_class, checkpoint_sha256


def _causal_event_sha256(event: Mapping[str, Any]) -> str:
    # Engine/provider aliases are selection metadata, not causal content. The resolved
    # canonical engine identity/class/checkpoint are committed separately in route identity.
    # Thus explicitly admitted aliases can collapse only after canonical resolution, while
    # materially different event content still produces a different causal event hash.
    causal_event = {key: value for key, value in event.items() if key not in _ENGINE_SELECTION_FIELDS}
    return _sha256_canonical(causal_event, "EVENT")


def route_event(event: Mapping[str, Any], *, current_generation: int) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    # Resolve positive admission before any model route can be returned.
    _validate_internal_provider(event)
    resolved_engine_identity, resolved_engine_class, resolved_engine_checkpoint_sha256 = _resolve_internal_engine(event)

    novelty = _unit(event.get("novelty", 0.0), "novelty")
    contradiction = _unit(event.get("contradiction", 0.0), "contradiction")
    uncertainty = _unit(event.get("uncertainty", 0.0), "uncertainty")
    forecast_need = _unit(event.get("forecast_need", 0.0), "forecast_need")
    effect_pressure = _unit(event.get("effect_pressure", 0.0), "effect_pressure")
    zero_relevance = _unit(event.get("zero_relevance", 0.0), "zero_relevance")
    due_recheck = _bool(event.get("due_recheck", False), "due_recheck")

    t = ROUTER_POLICY["thresholds"]
    lanes: set[str] = set()
    if novelty >= t["world_novelty"] or contradiction >= t["world_contradiction"] or due_recheck:
        lanes.add("world")
    if contradiction >= t["hypothesis_contradiction"] or uncertainty >= t["hypothesis_uncertainty"]:
        lanes.add("hypothesis")
    if forecast_need >= t["simulation_forecast_need"] or effect_pressure >= t["simulation_effect_pressure"]:
        lanes.add("simulation")
    if effect_pressure >= t["zero_model_effect_pressure"] or zero_relevance >= t["zero_model_relevance"]:
        lanes.add("zero_model")
    if lanes:
        lanes.add("critic")
    if event.get("provenance_gap") is True:
        lanes.add("provenance")

    if event.get("goal_pressure") is not None and _unit(event["goal_pressure"], "goal_pressure") >= t["goal_pressure"]:
        lanes.add("goal")
        lanes.add("critic")

    # A route that asks for model work must already carry a positively admitted exact
    # internal engine identity/class/checkpoint. Script-only events require no model identity.
    if lanes and resolved_engine_identity is None:
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE")

    projection = zero_relevance >= t["zero_projection_relevance"] and bool(lanes)
    event_sha256 = _causal_event_sha256(event)
    routing_result = {
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
        "generation": generation,
    }
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "event_sha256": event_sha256,
        "router_policy_sha256": ROUTER_POLICY_SHA256,
        "resolved_engine_identity": resolved_engine_identity,
        "resolved_engine_class": resolved_engine_class,
        "resolved_engine_checkpoint_sha256": resolved_engine_checkpoint_sha256,
        "routing_result": routing_result,
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
        router_policy_sha256=ROUTER_POLICY_SHA256,
        resolved_engine_identity=resolved_engine_identity,
        resolved_engine_class=resolved_engine_class,
        resolved_engine_checkpoint_sha256=resolved_engine_checkpoint_sha256,
        decision_sha256=digest,
    )


def expected_inference_echo(decision: RouteDecision) -> dict[str, Any]:
    """Identity fields a downstream HCU inference receipt must echo unchanged."""
    return {
        "event_sha256": decision.event_sha256,
        "route_decision_sha256": decision.decision_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_checkpoint_sha256": decision.resolved_engine_checkpoint_sha256,
    }


def validate_inference_echo(decision: RouteDecision, echo: Mapping[str, Any]) -> None:
    if not isinstance(echo, Mapping):
        raise ReactiveRoutingError("INFERENCE_ECHO_MAPPING_REQUIRED")
    expected = expected_inference_echo(decision)
    observed = {key: echo.get(key) for key in expected}
    if observed != expected:
        raise ReactiveRoutingError("INFERENCE_ECHO_IDENTITY_MISMATCH")


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
