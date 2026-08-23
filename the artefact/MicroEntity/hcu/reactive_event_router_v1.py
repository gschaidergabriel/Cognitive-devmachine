#!/usr/bin/env python3
"""Deterministic script-first router for the HCU reactive world model.

This source component does not perform model inference. It first validates a bounded
typed entry envelope, then decides which HCU lanes deserve model work. Any model route
must resolve through an explicitly supplied local/internal engine registry containing
runtime/checkpoint/tokenizer identity. Provider-name absence is never treated as proof
of cognitive independence.

Canonical truth/effect authority stays outside this component.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v1"
SCRIPT_ENGINE_ID = "hcu.script-plane/v1"
ALLOWED_MODALITIES = {"text", "external_event", "tool_outcome", "sensor", "database", "intrinsic"}
ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ALLOWED_INTERNAL_ENGINE_CLASSES = {"LOCAL_BUNDLED_MODEL", "LOCAL_INPROCESS_MODEL"}
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
    causal_id: str
    resolved_engine_id: str
    resolved_engine_class: str
    resolved_engine_identity_sha256: str
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256_canonical(value: Any, field: str) -> str:
    try:
        encoded = _canonical(value)
    except (TypeError, ValueError) as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


def _canonical_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ReactiveRoutingError(f"{field}:NONEMPTY_CANONICAL_STRING_REQUIRED")
    return value


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


def _validate_entry_envelope(
    event: Mapping[str, Any],
    *,
    current_generation: int,
) -> tuple[str, str, Mapping[str, Any], Mapping[str, Any]]:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")

    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    _canonical_text(event.get("event_id"), "event_id")
    causal_id = _canonical_text(event.get("causal_id"), "causal_id")

    modality = _canonical_text(event.get("modality"), "modality")
    if modality not in ALLOWED_MODALITIES:
        raise ReactiveRoutingError("MODALITY_UNSUPPORTED")

    observed_at = _canonical_text(event.get("observed_at"), "observed_at")
    try:
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReactiveRoutingError("OBSERVED_AT_RFC3339_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise ReactiveRoutingError("OBSERVED_AT_TIMEZONE_REQUIRED")

    provenance = event.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ReactiveRoutingError("PROVENANCE_MAPPING_REQUIRED")
    _canonical_text(provenance.get("source_type"), "provenance.source_type")
    _canonical_text(provenance.get("source_id"), "provenance.source_id")

    permissions = event.get("permissions")
    if not isinstance(permissions, Mapping):
        raise ReactiveRoutingError("PERMISSIONS_MAPPING_REQUIRED")
    _bool(permissions.get("cognition"), "permissions.cognition")

    budget = event.get("budget")
    if not isinstance(budget, Mapping):
        raise ReactiveRoutingError("BUDGET_MAPPING_REQUIRED")
    _bool(budget.get("allow_model_cognition"), "budget.allow_model_cognition")
    max_model_lanes = budget.get("max_model_lanes")
    if isinstance(max_model_lanes, bool) or not isinstance(max_model_lanes, int) or not 0 <= max_model_lanes <= 8:
        raise ReactiveRoutingError("budget.max_model_lanes:INTEGER_0_TO_8_REQUIRED")

    provider = event.get("requested_internal_provider")
    if provider is not None:
        if not isinstance(provider, str) or not provider.strip():
            raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_STRING_REQUIRED")
        if provider.strip().lower() not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
            raise ReactiveRoutingError("UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY")

    return _sha256_canonical(dict(event), "EVENT"), causal_id, permissions, budget


def _resolve_internal_engine(
    engine_registry: Mapping[str, Mapping[str, Any]] | None,
    requested_engine_id: Any,
) -> tuple[str, str, str]:
    engine_id = _canonical_text(requested_engine_id, "requested_engine_id")
    if not isinstance(engine_registry, Mapping):
        raise ReactiveRoutingError("INTERNAL_ENGINE_REGISTRY_REQUIRED")
    engine = engine_registry.get(engine_id)
    if not isinstance(engine, Mapping):
        raise ReactiveRoutingError("INTERNAL_ENGINE_NOT_ADMITTED")

    canonical_engine_id = _canonical_text(engine.get("engine_id"), "engine.engine_id")
    if canonical_engine_id != engine_id:
        raise ReactiveRoutingError("INTERNAL_ENGINE_IDENTITY_MISMATCH")

    engine_class = _canonical_text(engine.get("engine_class"), "engine.engine_class")
    if engine_class not in ALLOWED_INTERNAL_ENGINE_CLASSES:
        raise ReactiveRoutingError("INTERNAL_ENGINE_CLASS_NOT_ADMITTED")

    _canonical_text(engine.get("runtime_identity"), "engine.runtime_identity")
    _canonical_text(engine.get("checkpoint_identity"), "engine.checkpoint_identity")
    _canonical_text(engine.get("tokenizer_identity"), "engine.tokenizer_identity")
    if engine.get("network_required") is not False:
        raise ReactiveRoutingError("INTERNAL_ENGINE_NETWORK_DEPENDENCY_FORBIDDEN")
    if engine.get("secret_lookup_required") is not False:
        raise ReactiveRoutingError("INTERNAL_ENGINE_SECRET_DEPENDENCY_FORBIDDEN")

    return canonical_engine_id, engine_class, _sha256_canonical(dict(engine), "ENGINE_IDENTITY")


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    requested_engine_id: str | None = None,
    engine_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> RouteDecision:
    event_sha256, causal_id, permissions, budget = _validate_entry_envelope(
        event,
        current_generation=current_generation,
    )
    generation = event["entity_generation"]

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
        if permissions["cognition"] is not True:
            raise ReactiveRoutingError("COGNITION_PERMISSION_DENIED")
        if budget["allow_model_cognition"] is not True:
            raise ReactiveRoutingError("MODEL_COGNITION_BUDGET_DENIED")
        if len(lanes) > budget["max_model_lanes"]:
            raise ReactiveRoutingError("MODEL_LANE_BUDGET_EXCEEDED")
        resolved_engine_id, resolved_engine_class, resolved_engine_identity_sha256 = _resolve_internal_engine(
            engine_registry,
            requested_engine_id,
        )
    else:
        if requested_engine_id is not None:
            raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_BIND_MODEL_ENGINE")
        resolved_engine_id = SCRIPT_ENGINE_ID
        resolved_engine_class = "DETERMINISTIC_SCRIPT_PLANE"
        resolved_engine_identity_sha256 = _sha256_canonical(
            {
                "engine_id": SCRIPT_ENGINE_ID,
                "engine_class": resolved_engine_class,
                "network_required": False,
                "secret_lookup_required": False,
            },
            "SCRIPT_ENGINE_IDENTITY",
        )

    projection = zero_relevance >= 0.60 and bool(lanes)
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "event_sha256": event_sha256,
        "causal_id": causal_id,
        "resolved_engine_id": resolved_engine_id,
        "resolved_engine_class": resolved_engine_class,
        "resolved_engine_identity_sha256": resolved_engine_identity_sha256,
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
        causal_id=causal_id,
        resolved_engine_id=resolved_engine_id,
        resolved_engine_class=resolved_engine_class,
        resolved_engine_identity_sha256=resolved_engine_identity_sha256,
        decision_sha256=digest,
    )


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
