#!/usr/bin/env python3
"""Deterministic script-first router for the EntityOS/HCU reactive world model.

Hashes in this candidate use an explicitly versioned typed canonical byte codec rather
than host-language JSON serialization. This is a source mechanism only; cross-language
identity remains unpromoted until an independent implementation reproduces the vectors.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from typed_canonical_v1 import SCHEMA as CANONICALIZATION_SCHEMA
from typed_canonical_v1 import CanonicalizationError, canonical_sha256

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v3"
ROUTER_POLICY_SCHEMA = "HCU_REACTIVE_ROUTER_POLICY/v2"
ENGINE_IDENTITY_SCHEMA = "HCU_INTERNAL_ENGINE_IDENTITY/v2"

ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ADMITTED_INTERNAL_ENGINES = {"hcu_local_08b": "LOCAL_SHARED_WEIGHT_08B"}

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
    "schema": ROUTER_POLICY_SCHEMA,
    "canonicalization_schema": CANONICALIZATION_SCHEMA,
    "scripts": SCRIPT_STAGES,
    "admitted_internal_provider_aliases": tuple(sorted(ADMITTED_INTERNAL_PROVIDER_ALIASES)),
    "admitted_internal_engines": tuple(sorted(ADMITTED_INTERNAL_ENGINES.items())),
    "thresholds": {
        "world_novelty": 0.55,
        "world_contradiction": 0.35,
        "hypothesis_contradiction": 0.35,
        "hypothesis_uncertainty": 0.60,
        "simulation_forecast_need": 0.50,
        "simulation_effect_pressure": 0.45,
        "zero_model_effect_pressure": 0.45,
        "zero_model_relevance": 0.70,
        "zero_projection_relevance": 0.60,
        "goal_pressure": 0.70,
    },
}


class ReactiveRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    status: str
    canonicalization_schema: str
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    event_sha256: str
    router_policy_sha256: str
    resolved_engine_identity: str | None
    resolved_engine_class: str | None
    resolved_engine_artifact_sha256: str | None
    engine_identity_sha256: str | None
    decision_sha256: str


def _sha256_canonical(value: Any, field: str, *, domain: str) -> str:
    try:
        return canonical_sha256(value, domain=domain)
    except CanonicalizationError as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _unit(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReactiveRoutingError(f"{field}:NUMBER_REQUIRED")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ReactiveRoutingError(f"{field}:UNIT_INTERVAL_REQUIRED")
    if value == 0.0:
        value = 0.0
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ReactiveRoutingError(f"{field}:BOOLEAN_REQUIRED")
    return value


def _sha256_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _validate_canonicalization_schema(event: Mapping[str, Any]) -> None:
    if event.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise ReactiveRoutingError("CANONICALIZATION_SCHEMA_MISMATCH_OR_DOWNGRADE")


def _validate_internal_provider(event: Mapping[str, Any]) -> None:
    provider = event.get("requested_internal_provider")
    if provider is None:
        return
    if not isinstance(provider, str) or not provider.strip():
        raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_STRING_REQUIRED")
    if provider.strip().lower() not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise ReactiveRoutingError("UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY")


def _resolve_internal_engine(
    event: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any] | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    identity = event.get("resolved_internal_engine")
    engine_class = event.get("resolved_internal_engine_class")
    artifact_sha256 = event.get("resolved_internal_engine_artifact_sha256")
    if identity is None and engine_class is None and artifact_sha256 is None:
        return None, None, None, None
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
    artifact_sha256 = _sha256_text(artifact_sha256, "RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256")

    if not isinstance(admitted_engine_artifacts, Mapping):
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    admitted_artifact_sha256 = admitted_engine_artifacts.get(identity)
    if admitted_artifact_sha256 is None:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_ARTIFACT_NOT_ADMITTED")
    admitted_artifact_sha256 = _sha256_text(admitted_artifact_sha256, "ADMITTED_INTERNAL_ENGINE_ARTIFACT_SHA256")
    if artifact_sha256 != admitted_artifact_sha256:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256_MISMATCH")

    engine_identity_sha256 = _sha256_canonical(
        {
            "schema": ENGINE_IDENTITY_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "resolved_engine_identity": identity,
            "resolved_engine_class": engine_class,
            "resolved_engine_artifact_sha256": artifact_sha256,
        },
        "ENGINE_IDENTITY",
        domain="ENTITYOS_HCU_ENGINE_IDENTITY/v2",
    )
    return identity, engine_class, artifact_sha256, engine_identity_sha256


def _event_identity(event: Mapping[str, Any]) -> str:
    payload = dict(event)
    for key in (
        "requested_internal_provider",
        "resolved_internal_engine",
        "resolved_internal_engine_class",
        "resolved_internal_engine_artifact_sha256",
    ):
        payload.pop(key, None)
    return _sha256_canonical(payload, "EVENT", domain="ENTITYOS_HCU_CAUSAL_EVENT/v2")


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    admitted_engine_artifacts: Mapping[str, Any] | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    _validate_canonicalization_schema(event)
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    _validate_internal_provider(event)
    (
        resolved_engine_identity,
        resolved_engine_class,
        resolved_engine_artifact_sha256,
        engine_identity_sha256,
    ) = _resolve_internal_engine(event, admitted_engine_artifacts)

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

    if lanes and resolved_engine_identity is None:
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE")
    if not lanes and resolved_engine_identity is not None:
        raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE")

    projection = zero_relevance >= t["zero_projection_relevance"] and bool(lanes)
    event_sha256 = _event_identity(event)
    router_policy_sha256 = _sha256_canonical(
        ROUTER_POLICY,
        "ROUTER_POLICY",
        domain="ENTITYOS_HCU_ROUTER_POLICY/v2",
    )
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": event_sha256,
        "router_policy_sha256": router_policy_sha256,
        "engine_identity_sha256": engine_identity_sha256,
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
        "generation": generation,
    }
    digest = _sha256_canonical(payload, "ROUTE_DECISION", domain="ENTITYOS_HCU_ROUTE_DECISION/v3")
    return RouteDecision(
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        event_sha256=event_sha256,
        router_policy_sha256=router_policy_sha256,
        resolved_engine_identity=resolved_engine_identity,
        resolved_engine_class=resolved_engine_class,
        resolved_engine_artifact_sha256=resolved_engine_artifact_sha256,
        engine_identity_sha256=engine_identity_sha256,
        decision_sha256=digest,
    )


def assert_inference_echo(decision: RouteDecision, receipt: Mapping[str, Any]) -> None:
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise ReactiveRoutingError("INFERENCE_ECHO_NOT_VALID_FOR_SCRIPT_ONLY_ROUTE")
    if not isinstance(receipt, Mapping):
        raise ReactiveRoutingError("INFERENCE_RECEIPT_MAPPING_REQUIRED")
    expected = {
        "canonicalization_schema": decision.canonicalization_schema,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ReactiveRoutingError(f"INFERENCE_RECEIPT_{field.upper()}_MISMATCH")


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
