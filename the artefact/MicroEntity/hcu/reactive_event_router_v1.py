#!/usr/bin/env python3
"""Deterministic script-first router for the HCU reactive world model.

This source component does not perform model inference. It decides which bounded HCU
lanes, if any, deserve model work and whether Zero should receive a compact ClayCode
projection.

Route identity is deliberately causal rather than output-only: an admitted decision
commits to the immutable input-event digest, the positively resolved local/internal
cognition-engine identity, the semantic router-policy digest, and the derived routing
result. External or unresolved provider labels cannot acquire internal-cognition
authority by merely not appearing on a denylist.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTER_POLICY_SCHEMA = "HCU_REACTIVE_ROUTER_POLICY/v2"
KNOWN_EXTERNAL_PROVIDERS = {"nvidia", "mistral", "groq", "openrouter", "together", "claude_code"}
ADMITTED_MODEL_ENGINE_CLASSES = {"BUNDLED_LOCAL_MODEL", "LOCAL_MODEL_RUNTIME"}
ADMITTED_INTERNAL_PROVIDER_IDENTITIES = {"local", "internal"}
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
ROUTER_POLICY_DESCRIPTOR = {
    "schema": ROUTER_POLICY_SCHEMA,
    "event_schema": SCHEMA,
    "script_stages": SCRIPT_STAGES,
    "known_external_providers": sorted(KNOWN_EXTERNAL_PROVIDERS),
    "admitted_model_engine_classes": sorted(ADMITTED_MODEL_ENGINE_CLASSES),
    "admitted_internal_provider_identities": sorted(ADMITTED_INTERNAL_PROVIDER_IDENTITIES),
    "thresholds": {
        "world_novelty": 0.55,
        "world_contradiction": 0.35,
        "hypothesis_contradiction": 0.35,
        "hypothesis_uncertainty": 0.60,
        "simulation_forecast_need": 0.50,
        "simulation_effect_pressure": 0.45,
        "zero_model_effect_pressure": 0.45,
        "zero_model_zero_relevance": 0.70,
        "zero_projection_zero_relevance": 0.60,
        "goal_pressure": 0.70,
    },
    "decision_identity_formula": "sha256(router_policy_sha256,event_sha256,requested_provider_identity,resolved_engine,routing_result)",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReactiveRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class EngineBinding:
    engine_identity: str
    engine_class: str
    provider_identity: str
    requested_provider_identity: str | None = None
    checkpoint_sha256: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    status: str
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    router_policy_sha256: str
    event_sha256: str
    requested_provider_identity: str | None
    engine_identity: str
    engine_class: str
    engine_provider_identity: str
    engine_checkpoint_sha256: str | None
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
        raise ReactiveRoutingError("CANONICAL_JSON_REQUIRED") from exc


def router_policy_sha256() -> str:
    return hashlib.sha256(_canonical(ROUTER_POLICY_DESCRIPTOR)).hexdigest()


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


def _optional_identifier(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReactiveRoutingError(f"{field}:STRING_REQUIRED")
    normalized = value.strip().lower()
    if not normalized or len(normalized) > 200:
        raise ReactiveRoutingError(f"{field}:IDENTIFIER_INVALID")
    return normalized


def _required_identifier(value: Any, field: str) -> str:
    normalized = _optional_identifier(value, field)
    if normalized is None:
        raise ReactiveRoutingError(f"{field}:IDENTIFIER_REQUIRED")
    return normalized


def _coerce_engine_binding(value: EngineBinding | Mapping[str, Any] | None) -> EngineBinding | None:
    if value is None:
        return None
    if isinstance(value, EngineBinding):
        binding = value
    elif isinstance(value, Mapping):
        binding = EngineBinding(
            engine_identity=value.get("engine_identity"),
            engine_class=value.get("engine_class"),
            provider_identity=value.get("provider_identity"),
            requested_provider_identity=value.get("requested_provider_identity"),
            checkpoint_sha256=value.get("checkpoint_sha256"),
        )
    else:
        raise ReactiveRoutingError("ENGINE_BINDING_MAPPING_REQUIRED")

    engine_identity = _required_identifier(binding.engine_identity, "engine_identity")
    if not isinstance(binding.engine_class, str):
        raise ReactiveRoutingError("engine_class:STRING_REQUIRED")
    engine_class = binding.engine_class.strip().upper()
    if engine_class not in ADMITTED_MODEL_ENGINE_CLASSES:
        raise ReactiveRoutingError("ENGINE_CLASS_NOT_ADMITTED_FOR_INTERNAL_COGNITION")

    provider_identity = _required_identifier(binding.provider_identity, "provider_identity")
    if provider_identity not in ADMITTED_INTERNAL_PROVIDER_IDENTITIES:
        raise ReactiveRoutingError("ENGINE_PROVIDER_NOT_ADMITTED_FOR_INTERNAL_COGNITION")

    requested_provider_identity = _optional_identifier(
        binding.requested_provider_identity,
        "requested_provider_identity",
    )

    checkpoint_sha256 = binding.checkpoint_sha256
    if checkpoint_sha256 is not None:
        if not isinstance(checkpoint_sha256, str):
            raise ReactiveRoutingError("checkpoint_sha256:STRING_REQUIRED")
        checkpoint_sha256 = checkpoint_sha256.strip().lower()
    if engine_class == "BUNDLED_LOCAL_MODEL" and not checkpoint_sha256:
        raise ReactiveRoutingError("LOCAL_MODEL_CHECKPOINT_SHA256_REQUIRED")
    if checkpoint_sha256 is not None and not _SHA256_RE.fullmatch(checkpoint_sha256):
        raise ReactiveRoutingError("CHECKPOINT_SHA256_INVALID")

    return EngineBinding(
        engine_identity=engine_identity,
        engine_class=engine_class,
        provider_identity=provider_identity,
        requested_provider_identity=requested_provider_identity,
        checkpoint_sha256=checkpoint_sha256,
    )


def _script_engine_binding() -> EngineBinding:
    return EngineBinding(
        engine_identity="hcu.script-plane.v1",
        engine_class="DETERMINISTIC_SCRIPT",
        provider_identity="internal",
    )


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    resolved_engine: EngineBinding | Mapping[str, Any] | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    # Bind the exact admitted causal input before deriving routing output. Canonical JSON
    # guarantees mapping-order independence while preserving materially different events.
    event_sha256 = hashlib.sha256(_canonical(dict(event))).hexdigest()
    policy_sha256 = router_policy_sha256()

    requested_provider = _optional_identifier(
        event.get("requested_internal_provider"),
        "requested_internal_provider",
    )
    if requested_provider in KNOWN_EXTERNAL_PROVIDERS:
        raise ReactiveRoutingError("EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY")

    engine = _coerce_engine_binding(resolved_engine)
    if requested_provider is not None:
        if engine is None:
            raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_UNRESOLVED")
        if engine.requested_provider_identity != requested_provider:
            raise ReactiveRoutingError("REQUESTED_PROVIDER_ENGINE_RESOLUTION_MISMATCH")
    elif engine is not None and engine.requested_provider_identity is not None:
        raise ReactiveRoutingError("UNREQUESTED_PROVIDER_ALIAS_IN_ENGINE_BINDING")

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

    if lanes and engine is None:
        raise ReactiveRoutingError("INTERNAL_MODEL_ENGINE_BINDING_REQUIRED")
    if not lanes and engine is None:
        engine = _script_engine_binding()

    assert engine is not None
    projection = zero_relevance >= 0.60 and bool(lanes)
    status = "SCRIPT_ONLY" if not lanes else "SELECTIVE_MODEL_ACTIVATION"
    routing_result = {
        "status": status,
        "scripts": SCRIPT_STAGES,
        "model_lanes": sorted(lanes),
        "zero_projection": projection,
        "zero_projection_format": "ClayCode" if projection else None,
        "external_provider_dependency": False,
        "generation": generation,
    }
    identity_payload = {
        "router_policy_sha256": policy_sha256,
        "event_sha256": event_sha256,
        "requested_provider_identity": requested_provider,
        "resolved_engine": asdict(engine),
        "routing_result": routing_result,
    }
    digest = hashlib.sha256(_canonical(identity_payload)).hexdigest()
    return RouteDecision(
        status=status,
        scripts=SCRIPT_STAGES,
        model_lanes=tuple(sorted(lanes)),
        zero_projection=projection,
        zero_projection_format="ClayCode" if projection else None,
        external_provider_dependency=False,
        router_policy_sha256=policy_sha256,
        event_sha256=event_sha256,
        requested_provider_identity=requested_provider,
        engine_identity=engine.engine_identity,
        engine_class=engine.engine_class,
        engine_provider_identity=engine.provider_identity,
        engine_checkpoint_sha256=engine.checkpoint_sha256,
        decision_sha256=digest,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
