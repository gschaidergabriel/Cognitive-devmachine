#!/usr/bin/env python3
"""Deterministic script-first router for the EntityOS HCU reactive world model.

This source component does not perform model inference. It decides which bounded HCU
lanes, if any, deserve model work and whether Zero should receive a compact ClayCode
projection.

Trust domains are intentionally separated:
- ``event`` is causal Entry-Fabric input and may express a requested internal provider;
- ``EngineAdmission`` is a deterministic HCU control-plane binding and cannot be minted by
  copying ``resolved_*`` fields into the event mapping;
- route identity commits to event, router policy, admitted engine bytes and routing result.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v3"
ROUTER_POLICY_SCHEMA = "HCU_REACTIVE_ROUTER_POLICY/v1"
ENGINE_IDENTITY_SCHEMA = "HCU_INTERNAL_ENGINE_IDENTITY/v1"

ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ADMITTED_INTERNAL_ENGINES = {
    "hcu_local_08b": "LOCAL_SHARED_WEIGHT_08B",
}
RESERVED_EVENT_AUTHORITY_FIELDS = frozenset({
    "resolved_internal_engine",
    "resolved_internal_engine_class",
    "resolved_internal_engine_artifact_sha256",
    "engine_identity_sha256",
})

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
    "scripts": SCRIPT_STAGES,
    "admitted_internal_provider_aliases": tuple(sorted(ADMITTED_INTERNAL_PROVIDER_ALIASES)),
    "admitted_internal_engines": tuple(sorted(ADMITTED_INTERNAL_ENGINES.items())),
    "engine_authority_source": "SEPARATE_HCU_CONTROL_PLANE_ADMISSION",
    "reserved_event_authority_fields": tuple(sorted(RESERVED_EVENT_AUTHORITY_FIELDS)),
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
class EngineAdmission:
    """Deterministic control-plane authorization for one exact internal engine artifact."""

    provider_alias: str
    engine_identity: str
    engine_class: str
    engine_artifact_sha256: str


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
    resolved_engine_artifact_sha256: str | None
    engine_identity_sha256: str | None
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


def _sha256_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _provider_alias(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReactiveRoutingError(f"{field}:STRING_REQUIRED")
    value = value.strip().lower()
    if value not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise ReactiveRoutingError(f"{field}:NOT_ADMITTED")
    return value


def _validate_event_authority_boundary(event: Mapping[str, Any]) -> None:
    forbidden = sorted(key for key in RESERVED_EVENT_AUTHORITY_FIELDS if key in event)
    if forbidden:
        raise ReactiveRoutingError("EVENT_MUST_NOT_MINT_ENGINE_AUTHORITY:" + ",".join(forbidden))


def _requested_provider(event: Mapping[str, Any]) -> str | None:
    provider = event.get("requested_internal_provider")
    if provider is None:
        return None
    return _provider_alias(provider, "REQUESTED_INTERNAL_PROVIDER")


def _resolve_internal_engine(admission: EngineAdmission | None) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    if admission is None:
        return None, None, None, None, None
    if not isinstance(admission, EngineAdmission):
        raise ReactiveRoutingError("ENGINE_ADMISSION_TYPE_REQUIRED")

    provider_alias = _provider_alias(admission.provider_alias, "ENGINE_ADMISSION_PROVIDER")
    if not isinstance(admission.engine_identity, str) or not admission.engine_identity.strip():
        raise ReactiveRoutingError("ENGINE_ADMISSION_IDENTITY_REQUIRED")
    if not isinstance(admission.engine_class, str) or not admission.engine_class.strip():
        raise ReactiveRoutingError("ENGINE_ADMISSION_CLASS_REQUIRED")

    identity = admission.engine_identity.strip().lower()
    engine_class = admission.engine_class.strip().upper()
    admitted_class = ADMITTED_INTERNAL_ENGINES.get(identity)
    if admitted_class is None:
        raise ReactiveRoutingError("ENGINE_ADMISSION_IDENTITY_NOT_ADMITTED")
    if engine_class != admitted_class:
        raise ReactiveRoutingError("ENGINE_ADMISSION_CLASS_MISMATCH")
    artifact_sha256 = _sha256_text(admission.engine_artifact_sha256, "ENGINE_ADMISSION_ARTIFACT_SHA256")
    engine_identity_sha256 = _sha256_canonical(
        {
            "schema": ENGINE_IDENTITY_SCHEMA,
            "provider_alias": provider_alias,
            "resolved_engine_identity": identity,
            "resolved_engine_class": engine_class,
            "resolved_engine_artifact_sha256": artifact_sha256,
        },
        "ENGINE_IDENTITY",
    )
    return provider_alias, identity, engine_class, artifact_sha256, engine_identity_sha256


def _event_identity(event: Mapping[str, Any]) -> str:
    # Provider selection is routing metadata rather than causal event content. Exact engine
    # authority is never accepted from the event and is committed separately.
    payload = dict(event)
    payload.pop("requested_internal_provider", None)
    return _sha256_canonical(payload, "EVENT")


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    engine_admission: EngineAdmission | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    _validate_event_authority_boundary(event)

    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    requested_provider = _requested_provider(event)
    (
        admitted_provider,
        resolved_engine_identity,
        resolved_engine_class,
        resolved_engine_artifact_sha256,
        engine_identity_sha256,
    ) = _resolve_internal_engine(engine_admission)
    if requested_provider is not None and admitted_provider is not None and requested_provider != admitted_provider:
        raise ReactiveRoutingError("REQUESTED_PROVIDER_ENGINE_ADMISSION_MISMATCH")

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
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_CONTROL_PLANE_ENGINE_ADMISSION")
    if not lanes and resolved_engine_identity is not None:
        raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE")

    projection = zero_relevance >= t["zero_projection_relevance"] and bool(lanes)
    event_sha256 = _event_identity(event)
    router_policy_sha256 = _sha256_canonical(ROUTER_POLICY, "ROUTER_POLICY")
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
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
    digest = _sha256_canonical(payload, "ROUTE_DECISION")
    return RouteDecision(
        status="SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION",
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
    """Fail closed unless inference echoes the exact admitted event/route/engine tuple."""
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise ReactiveRoutingError("INFERENCE_ECHO_NOT_VALID_FOR_SCRIPT_ONLY_ROUTE")
    if not isinstance(receipt, Mapping):
        raise ReactiveRoutingError("INFERENCE_RECEIPT_MAPPING_REQUIRED")
    expected = {
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ReactiveRoutingError(f"INFERENCE_RECEIPT_{field.upper()}_MISMATCH")


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
