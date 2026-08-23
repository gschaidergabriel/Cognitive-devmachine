#!/usr/bin/env python3
"""Deterministic fail-closed HCU reactive event router.

This component is an EntityOS/HCU donor-compatible path retained under the historical
MicroEntity package root. It performs no model inference and mints no canonical truth.
It binds every route decision to the complete causal event identity, deterministic
router policy, and an explicitly admitted local cognition-engine identity.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

EVENT_SCHEMA = "HCU_REACTIVE_EVENT/v1"
ENGINE_BINDING_SCHEMA = "HCU_ENGINE_BINDING/v1"
INFERENCE_RECEIPT_SCHEMA = "HCU_INFERENCE_RECEIPT/v1"
ROUTE_DECISION_SCHEMA = "HCU_ROUTE_DECISION/v2"

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
    "schema": "HCU_REACTIVE_ROUTER_POLICY/v2",
    "thresholds": {
        "world_novelty": 0.55,
        "world_contradiction": 0.35,
        "hypothesis_contradiction": 0.35,
        "hypothesis_uncertainty": 0.60,
        "simulation_forecast": 0.50,
        "simulation_effect": 0.45,
        "zero_effect": 0.45,
        "zero_relevance_lane": 0.70,
        "zero_projection": 0.60,
        "goal": 0.70,
    },
    "model_engine_classes": ["LOCAL_SHARED_WEIGHT_08B"],
    "script_engine": {
        "engine_id": "xpu.script.v1",
        "engine_class": "DETERMINISTIC_XPU",
    },
}

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReactiveRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    schema: str
    status: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    event_sha256: str
    router_policy_sha256: str
    resolved_engine_id: str
    resolved_engine_class: str
    resolved_runtime_identity_sha256: str | None
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _required_id(event: Mapping[str, Any], field: str) -> str:
    value = event.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ReactiveRoutingError(f"{field.upper()}:NONEMPTY_STRING_REQUIRED")
    if len(value) > 256:
        raise ReactiveRoutingError(f"{field.upper()}:TOO_LONG")
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


def _validate_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise ReactiveRoutingError(f"{field}:LOWER_HEX_SHA256_REQUIRED")
    return value


def _resolve_model_engine(binding: Mapping[str, Any] | None) -> tuple[str, str, str]:
    if not isinstance(binding, Mapping):
        raise ReactiveRoutingError("MODEL_ENGINE_BINDING_REQUIRED")
    if binding.get("schema") != ENGINE_BINDING_SCHEMA:
        raise ReactiveRoutingError("MODEL_ENGINE_BINDING_SCHEMA_UNSUPPORTED")
    if binding.get("execution_scope") != "LOCAL_ONLY":
        raise ReactiveRoutingError("MODEL_ENGINE_EXECUTION_SCOPE_NOT_LOCAL")

    engine_id = binding.get("engine_id")
    if not isinstance(engine_id, str) or not engine_id.strip():
        raise ReactiveRoutingError("MODEL_ENGINE_ID_REQUIRED")
    engine_id = engine_id.strip()

    engine_class = binding.get("engine_class")
    if engine_class not in ROUTER_POLICY["model_engine_classes"]:
        raise ReactiveRoutingError("MODEL_ENGINE_CLASS_NOT_ADMITTED")

    runtime_identity = _validate_sha256(
        binding.get("runtime_identity_sha256"),
        "MODEL_RUNTIME_IDENTITY_SHA256",
    )

    if "provider" in binding or "provider_url" in binding:
        raise ReactiveRoutingError("PROVIDER_SELECTOR_NOT_ADMITTED_IN_INTERNAL_ENGINE_BINDING")

    return engine_id, engine_class, runtime_identity


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    engine_binding: Mapping[str, Any] | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != EVENT_SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")

    ingress_id = _required_id(event, "ingress_id")
    causal_id = _required_id(event, "causal_id")

    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    # Finite provider denylists are fail-open. Provider names are therefore not a
    # routing authority at all; callers must pass a positively admitted engine binding.
    if "requested_internal_provider" in event:
        raise ReactiveRoutingError("LEGACY_PROVIDER_SELECTOR_NOT_ADMITTED")

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
    if event.get("goal_pressure") is not None and _unit(event["goal_pressure"], "goal_pressure") >= 0.70:
        lanes.add("goal")
        lanes.add("critic")

    if lanes:
        engine_id, engine_class, runtime_identity = _resolve_model_engine(engine_binding)
    else:
        if engine_binding is not None:
            raise ReactiveRoutingError("MODEL_ENGINE_BINDING_UNEXPECTED_FOR_SCRIPT_ONLY")
        engine_id = ROUTER_POLICY["script_engine"]["engine_id"]
        engine_class = ROUTER_POLICY["script_engine"]["engine_class"]
        runtime_identity = None

    projection = zero_relevance >= 0.60 and bool(lanes)
    event_sha256 = _sha256(event)
    router_policy_sha256 = _sha256(ROUTER_POLICY)

    identity_payload = {
        "schema": ROUTE_DECISION_SCHEMA,
        "event_sha256": event_sha256,
        "router_policy_sha256": router_policy_sha256,
        "ingress_id": ingress_id,
        "causal_id": causal_id,
        "entity_generation": generation,
        "resolved_engine_id": engine_id,
        "resolved_engine_class": engine_class,
        "resolved_runtime_identity_sha256": runtime_identity,
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
    }
    digest = _sha256(identity_payload)

    return RouteDecision(
        schema=ROUTE_DECISION_SCHEMA,
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
        ingress_id=ingress_id,
        causal_id=causal_id,
        entity_generation=generation,
        event_sha256=event_sha256,
        router_policy_sha256=router_policy_sha256,
        resolved_engine_id=engine_id,
        resolved_engine_class=engine_class,
        resolved_runtime_identity_sha256=runtime_identity,
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        decision_sha256=digest,
    )


def verify_inference_receipt(decision: RouteDecision, receipt: Mapping[str, Any]) -> None:
    """Fail closed unless downstream inference echoes the admitted causal/engine spine."""
    if not isinstance(receipt, Mapping) or receipt.get("schema") != INFERENCE_RECEIPT_SCHEMA:
        raise ReactiveRoutingError("INFERENCE_RECEIPT_SCHEMA_UNSUPPORTED")
    expected = {
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "entity_generation": decision.entity_generation,
        "resolved_engine_id": decision.resolved_engine_id,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_runtime_identity_sha256": decision.resolved_runtime_identity_sha256,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ReactiveRoutingError(f"INFERENCE_RECEIPT_{field.upper()}_MISMATCH")


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
