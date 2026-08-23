#!/usr/bin/env python3
"""Deterministic script-first router for the HCU reactive world model.

This component does not perform model inference. It consumes only HCU events carrying
a typed Entry-Fabric admission identity, decides which bounded HCU lanes deserve model
work, and requires model routes to match an independently admitted local engine record.
Event/provider fields alone never mint engine authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v3"
ROUTER_POLICY_SCHEMA = "HCU_REACTIVE_ROUTER_POLICY/v2"
ENGINE_IDENTITY_SCHEMA = "HCU_INTERNAL_ENGINE_IDENTITY/v2"
# Exact implementation-scoped hash serialization profile. This is deliberately NOT a
# claim of RFC 8785 JCS or heterogeneous Entry-Fabric canonicalization. Any future
# cross-language profile must use a distinct versioned identity.
HASH_SERIALIZATION_SCHEMA = "HCU_PYTHON_JSON_DUMPS_SORT_KEYS_UTF8/v1"

ADMITTED_INTERNAL_PROVIDER_ALIASES = {"hcu", "local", "xeno"}
ADMITTED_INTERNAL_ENGINES = {
    "hcu_local_08b": "LOCAL_SHARED_WEIGHT_08B",
}

SCRIPT_STAGES = (
    "generation_check",
    "entry_admission_rebind",
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
    "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
    "scripts": SCRIPT_STAGES,
    "entry_handshake": ("ingress_id", "causal_id", "entry_admission_sha256"),
    "admitted_internal_provider_aliases": tuple(sorted(ADMITTED_INTERNAL_PROVIDER_ALIASES)),
    "admitted_internal_engines": tuple(sorted(ADMITTED_INTERNAL_ENGINES.items())),
    "model_route_engine_lock": (
        "engine_id",
        "engine_class",
        "artifact_sha256",
        "runtime_identity",
        "checkpoint_identity",
        "tokenizer_identity",
        "network_required=false",
        "secret_lookup_required=false",
    ),
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
    scripts: tuple[str, ...]
    model_lanes: tuple[str, ...]
    zero_projection: bool
    zero_projection_format: str | None
    external_provider_dependency: bool
    hash_serialization_schema: str
    ingress_id: str
    causal_id: str
    entry_admission_sha256: str
    event_sha256: str
    router_policy_sha256: str
    resolved_engine_identity: str | None
    resolved_engine_class: str | None
    resolved_engine_artifact_sha256: str | None
    resolved_engine_runtime_identity: str | None
    resolved_engine_checkpoint_identity: str | None
    resolved_engine_tokenizer_identity: str | None
    engine_identity_sha256: str | None
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_canonical(value: Any, field: str) -> str:
    try:
        encoded = _canonical(value)
    except (TypeError, ValueError) as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


def _text(value: Any, field: str) -> str:
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


def _sha256_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ReactiveRoutingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _validate_entry_handshake(event: Mapping[str, Any]) -> tuple[str, str, str]:
    ingress_id = _text(event.get("ingress_id"), "ingress_id")
    causal_id = _text(event.get("causal_id"), "causal_id")
    entry_admission_sha256 = _sha256_text(
        event.get("entry_admission_sha256"),
        "ENTRY_ADMISSION_SHA256",
    )
    return ingress_id, causal_id, entry_admission_sha256


def _validate_internal_provider(event: Mapping[str, Any]) -> None:
    provider = event.get("requested_internal_provider")
    if provider is None:
        return
    if not isinstance(provider, str) or not provider.strip():
        raise ReactiveRoutingError("REQUESTED_INTERNAL_PROVIDER_STRING_REQUIRED")
    if provider.strip().lower() not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise ReactiveRoutingError(
            "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN_AS_INTERNAL_COGNITIVE_DEPENDENCY"
        )


def _resolve_internal_engine(
    event: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any] | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None, str | None]:
    identity = event.get("resolved_internal_engine")
    engine_class = event.get("resolved_internal_engine_class")
    artifact_sha256 = event.get("resolved_internal_engine_artifact_sha256")
    if identity is None and engine_class is None and artifact_sha256 is None:
        return None, None, None, None, None, None, None
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
    artifact_sha256 = _sha256_text(
        artifact_sha256,
        "RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256",
    )

    # Compatibility argument name retained, but values are now full trusted engine locks.
    # An event-reported artifact digest or a bare digest map is not sufficient authority.
    if not isinstance(admitted_engine_artifacts, Mapping):
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_REGISTRY_REQUIRED")
    registry_entry = admitted_engine_artifacts.get(identity)
    if not isinstance(registry_entry, Mapping):
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_REGISTRY_ENTRY_REQUIRED")

    registry_id = _text(registry_entry.get("engine_id"), "engine_registry.engine_id").lower()
    registry_class = _text(registry_entry.get("engine_class"), "engine_registry.engine_class").upper()
    registry_artifact_sha256 = _sha256_text(
        registry_entry.get("artifact_sha256"),
        "ADMITTED_INTERNAL_ENGINE_ARTIFACT_SHA256",
    )
    if registry_id != identity:
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_IDENTITY_MISMATCH")
    if registry_class != engine_class:
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_CLASS_MISMATCH")
    if registry_artifact_sha256 != artifact_sha256:
        raise ReactiveRoutingError("RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256_MISMATCH")

    runtime_identity = _text(
        registry_entry.get("runtime_identity"),
        "engine_registry.runtime_identity",
    )
    checkpoint_identity = _text(
        registry_entry.get("checkpoint_identity"),
        "engine_registry.checkpoint_identity",
    )
    tokenizer_identity = _text(
        registry_entry.get("tokenizer_identity"),
        "engine_registry.tokenizer_identity",
    )
    if registry_entry.get("network_required") is not False:
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_NETWORK_DEPENDENCY_FORBIDDEN")
    if registry_entry.get("secret_lookup_required") is not False:
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_SECRET_DEPENDENCY_FORBIDDEN")

    engine_identity_sha256 = _sha256_canonical(
        {
            "schema": ENGINE_IDENTITY_SCHEMA,
            "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
            "resolved_engine_identity": identity,
            "resolved_engine_class": engine_class,
            "resolved_engine_artifact_sha256": artifact_sha256,
            "runtime_identity": runtime_identity,
            "checkpoint_identity": checkpoint_identity,
            "tokenizer_identity": tokenizer_identity,
            "network_required": False,
            "secret_lookup_required": False,
        },
        "ENGINE_IDENTITY",
    )
    return (
        identity,
        engine_class,
        artifact_sha256,
        runtime_identity,
        checkpoint_identity,
        tokenizer_identity,
        engine_identity_sha256,
    )


def _event_identity(event: Mapping[str, Any]) -> str:
    # Engine/provider resolution is routing metadata, not the immutable causal event.
    # Entry admission identity remains part of the causal event.
    payload = dict(event)
    for key in (
        "requested_internal_provider",
        "resolved_internal_engine",
        "resolved_internal_engine_class",
        "resolved_internal_engine_artifact_sha256",
    ):
        payload.pop(key, None)
    return _sha256_canonical(
        {
            "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
            "event": payload,
        },
        "EVENT",
    )


def route_event(
    event: Mapping[str, Any],
    *,
    current_generation: int,
    admitted_engine_artifacts: Mapping[str, Any] | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    ingress_id, causal_id, entry_admission_sha256 = _validate_entry_handshake(event)
    _validate_internal_provider(event)
    (
        resolved_engine_identity,
        resolved_engine_class,
        resolved_engine_artifact_sha256,
        resolved_engine_runtime_identity,
        resolved_engine_checkpoint_identity,
        resolved_engine_tokenizer_identity,
        engine_identity_sha256,
    ) = _resolve_internal_engine(event, admitted_engine_artifacts)

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

    if event.get("goal_pressure") is not None and _unit(
        event["goal_pressure"], "goal_pressure"
    ) >= 0.70:
        lanes.add("goal")
        lanes.add("critic")

    if lanes and resolved_engine_identity is None:
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE")
    if not lanes and resolved_engine_identity is not None:
        raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE")

    projection = zero_relevance >= 0.60 and bool(lanes)
    event_sha256 = _event_identity(event)
    router_policy_sha256 = _sha256_canonical(ROUTER_POLICY, "ROUTER_POLICY")
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
        "ingress_id": ingress_id,
        "causal_id": causal_id,
        "entry_admission_sha256": entry_admission_sha256,
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
        hash_serialization_schema=HASH_SERIALIZATION_SCHEMA,
        ingress_id=ingress_id,
        causal_id=causal_id,
        entry_admission_sha256=entry_admission_sha256,
        event_sha256=event_sha256,
        router_policy_sha256=router_policy_sha256,
        resolved_engine_identity=resolved_engine_identity,
        resolved_engine_class=resolved_engine_class,
        resolved_engine_artifact_sha256=resolved_engine_artifact_sha256,
        resolved_engine_runtime_identity=resolved_engine_runtime_identity,
        resolved_engine_checkpoint_identity=resolved_engine_checkpoint_identity,
        resolved_engine_tokenizer_identity=resolved_engine_tokenizer_identity,
        engine_identity_sha256=engine_identity_sha256,
        decision_sha256=digest,
    )


def assert_inference_echo(decision: RouteDecision, receipt: Mapping[str, Any]) -> None:
    """Fail closed unless inference echoes exact serializer/entry/event/route/engine identity."""
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise ReactiveRoutingError("INFERENCE_ECHO_NOT_VALID_FOR_SCRIPT_ONLY_ROUTE")
    if not isinstance(receipt, Mapping):
        raise ReactiveRoutingError("INFERENCE_RECEIPT_MAPPING_REQUIRED")
    expected = {
        "hash_serialization_schema": decision.hash_serialization_schema,
        "ingress_id": decision.ingress_id,
        "causal_id": decision.causal_id,
        "entry_admission_sha256": decision.entry_admission_sha256,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
        "resolved_engine_runtime_identity": decision.resolved_engine_runtime_identity,
        "resolved_engine_checkpoint_identity": decision.resolved_engine_checkpoint_identity,
        "resolved_engine_tokenizer_identity": decision.resolved_engine_tokenizer_identity,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ReactiveRoutingError(f"INFERENCE_RECEIPT_{field.upper()}_MISMATCH")


def decision_json(decision: RouteDecision) -> str:
    return json.dumps(
        asdict(decision),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
