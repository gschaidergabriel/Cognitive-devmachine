#!/usr/bin/env python3
"""Deterministic script-first router for the EntityOS/HCU reactive world model.

This source component does not perform model inference. It decides which bounded HCU
lanes, if any, deserve model work and whether Zero should receive a compact ClayCode
projection. Causal Entry data and engine-admission authority are separate trust domains.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

SCHEMA = "HCU_REACTIVE_EVENT/v1"
ROUTE_IDENTITY_SCHEMA = "HCU_CAUSAL_ROUTE_IDENTITY/v4"
ROUTER_POLICY_SCHEMA = "HCU_REACTIVE_ROUTER_POLICY/v2"
ENGINE_IDENTITY_SCHEMA = "HCU_INTERNAL_ENGINE_IDENTITY/v2"
ENTRY_BINDING_SCHEMA = "ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/v2"
HASH_SERIALIZATION_SCHEMA = CANONICALIZATION_SCHEMA
ENTRY_BINDING_FIELDS = frozenset({"schema", "canonicalization_schema", "event_sha256"})

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
    "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
    "entry_binding_schema": ENTRY_BINDING_SCHEMA,
    "scripts": SCRIPT_STAGES,
    "admitted_internal_provider_aliases": tuple(sorted(ADMITTED_INTERNAL_PROVIDER_ALIASES)),
    "admitted_internal_engines": tuple(sorted(ADMITTED_INTERNAL_ENGINES.items())),
    "engine_authority_source": "SEPARATE_ENTITYOS_HCU_CONTROL_PLANE_ADMISSION",
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
    """Exact engine selection supplied by the deterministic EntityOS/HCU control plane.

    Construction of this object is not itself runtime proof of authority. The real caller
    must bind it to the verified loaded runtime/checkpoint identity in an execution receipt.
    The crucial source-level invariant is that causal Entry data cannot mint these fields.
    """

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
    hash_serialization_schema: str
    event_sha256: str
    entry_admission_sha256: str | None
    router_policy_sha256: str
    resolved_engine_identity: str | None
    resolved_engine_class: str | None
    resolved_engine_artifact_sha256: str | None
    engine_identity_sha256: str | None
    decision_sha256: str


def _canonical(value: Any) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise ReactiveRoutingError(f"CANONICALIZATION_FAILED:{exc}") from exc


def _sha256_canonical(value: Any, field: str) -> str:
    try:
        encoded = _canonical(value)
    except ReactiveRoutingError as exc:
        raise ReactiveRoutingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
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


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReactiveRoutingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _provider_alias(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReactiveRoutingError(f"{field}:STRING_REQUIRED")
    value = value.strip().lower()
    if value not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise ReactiveRoutingError(f"{field}:NOT_ADMITTED")
    return value


def _validate_event_authority_boundary(event: Mapping[str, Any]) -> None:
    forbidden = sorted(field for field in RESERVED_EVENT_AUTHORITY_FIELDS if field in event)
    if forbidden:
        raise ReactiveRoutingError("EVENT_MUST_NOT_MINT_ENGINE_AUTHORITY:" + ",".join(forbidden))


def _requested_provider(event: Mapping[str, Any]) -> str | None:
    provider = event.get("requested_internal_provider")
    if provider is None:
        return None
    return _provider_alias(provider, "REQUESTED_INTERNAL_PROVIDER")


def resolve_admitted_entry_binding(
    admitted_entry_bindings: Mapping[str, Any] | None,
    admission_sha256: str,
    *,
    expected_event_sha256: str | None = None,
) -> str:
    """Resolve a versioned admission->event binding from independent authority state.

    A bare admission->digest mapping is intentionally no longer admitted: without the
    canonicalization schema, historical CBOR/custom/Python-JSON identities could be
    relabelled as the selected RFC8785/JCS identity after migration.
    """
    admission_sha256 = _sha256_text(admission_sha256, "ENTRY_ADMISSION_SHA256")
    if not isinstance(admitted_entry_bindings, Mapping):
        raise ReactiveRoutingError("ADMITTED_ENTRY_BINDING_REGISTRY_REQUIRED")
    binding = admitted_entry_bindings.get(admission_sha256)
    if binding is None:
        raise ReactiveRoutingError("ENTRY_ADMISSION_NOT_ADMITTED")
    if not isinstance(binding, Mapping):
        raise ReactiveRoutingError("ENTRY_ADMISSION_BINDING_V2_REQUIRED")
    unknown = sorted(set(binding) - ENTRY_BINDING_FIELDS)
    if unknown:
        raise ReactiveRoutingError("ENTRY_BINDING_UNKNOWN_FIELDS:" + ",".join(unknown))
    if set(binding) != ENTRY_BINDING_FIELDS:
        raise ReactiveRoutingError("ENTRY_BINDING_ALL_FIELDS_REQUIRED")
    if binding.get("schema") != ENTRY_BINDING_SCHEMA:
        raise ReactiveRoutingError("ENTRY_BINDING_SCHEMA_UNSUPPORTED")
    if binding.get("canonicalization_schema") != HASH_SERIALIZATION_SCHEMA:
        raise ReactiveRoutingError("ENTRY_BINDING_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    event_sha256 = _sha256_text(binding.get("event_sha256"), "ADMITTED_ENTRY_EVENT_SHA256")
    if expected_event_sha256 is not None:
        expected_event_sha256 = _sha256_text(expected_event_sha256, "ENTRY_EVENT_SHA256")
        if event_sha256 != expected_event_sha256:
            raise ReactiveRoutingError("ENTRY_EVENT_SHA256_MISMATCH")
    return event_sha256


def _resolve_internal_engine(
    admission: EngineAdmission | None,
    admitted_engine_artifacts: Mapping[str, Any] | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
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

    if not isinstance(admitted_engine_artifacts, Mapping):
        raise ReactiveRoutingError("ADMITTED_INTERNAL_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    admitted_artifact_sha256 = admitted_engine_artifacts.get(identity)
    if admitted_artifact_sha256 is None:
        raise ReactiveRoutingError("ENGINE_ADMISSION_ARTIFACT_NOT_ADMITTED")
    admitted_artifact_sha256 = _sha256_text(
        admitted_artifact_sha256,
        "ADMITTED_INTERNAL_ENGINE_ARTIFACT_SHA256",
    )
    if artifact_sha256 != admitted_artifact_sha256:
        raise ReactiveRoutingError("ENGINE_ADMISSION_ARTIFACT_SHA256_MISMATCH")

    engine_identity_sha256 = _sha256_canonical(
        {
            "schema": ENGINE_IDENTITY_SCHEMA,
            "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
            "provider_alias": provider_alias,
            "resolved_engine_identity": identity,
            "resolved_engine_class": engine_class,
            "resolved_engine_artifact_sha256": artifact_sha256,
        },
        "ENGINE_IDENTITY",
    )
    return provider_alias, identity, engine_class, artifact_sha256, engine_identity_sha256


def _event_identity(
    event: Mapping[str, Any],
    admitted_entry_bindings: Mapping[str, Any] | None,
) -> str:
    """Resolve immutable causal event identity without trusting ingress claims."""
    has_entry_projection = any(
        event.get(field) is not None
        for field in (
            "ingress_id",
            "entry_event_sha256",
            "entry_admission_sha256",
            "entry_canonicalization_schema",
        )
    )
    if has_entry_projection:
        _nonempty_text(event.get("ingress_id"), "INGRESS_ID")
        _nonempty_text(event.get("causal_id"), "CAUSAL_ID")
        if event.get("entry_canonicalization_schema") != HASH_SERIALIZATION_SCHEMA:
            raise ReactiveRoutingError("ENTRY_CANONICALIZATION_SCHEMA_UNSUPPORTED")
        event_sha256 = _sha256_text(event.get("entry_event_sha256"), "ENTRY_EVENT_SHA256")
        admission_sha256 = _sha256_text(event.get("entry_admission_sha256"), "ENTRY_ADMISSION_SHA256")
        return resolve_admitted_entry_binding(
            admitted_entry_bindings,
            admission_sha256,
            expected_event_sha256=event_sha256,
        )

    payload = dict(event)
    payload.pop("requested_internal_provider", None)
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
    engine_admission: EngineAdmission | None = None,
    admitted_engine_artifacts: Mapping[str, Any] | None = None,
    admitted_entry_bindings: Mapping[str, Any] | None = None,
) -> RouteDecision:
    if not isinstance(event, Mapping) or event.get("schema") != SCHEMA:
        raise ReactiveRoutingError("EVENT_SCHEMA_UNSUPPORTED")
    _validate_event_authority_boundary(event)

    generation = event.get("entity_generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ReactiveRoutingError("ENTITY_GENERATION_INVALID")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise ReactiveRoutingError("CURRENT_GENERATION_INVALID")
    if generation != current_generation:
        raise ReactiveRoutingError("STALE_ENTITY_GENERATION")

    requested_provider = _requested_provider(event)
    (
        admitted_provider,
        resolved_engine_identity,
        resolved_engine_class,
        resolved_engine_artifact_sha256,
        engine_identity_sha256,
    ) = _resolve_internal_engine(engine_admission, admitted_engine_artifacts)
    if requested_provider is not None and admitted_provider is not None and requested_provider != admitted_provider:
        raise ReactiveRoutingError("REQUESTED_PROVIDER_ENGINE_ADMISSION_MISMATCH")

    novelty = _unit(event.get("novelty", 0.0), "novelty")
    contradiction = _unit(event.get("contradiction", 0.0), "contradiction")
    uncertainty = _unit(event.get("uncertainty", 0.0), "uncertainty")
    forecast_need = _unit(event.get("forecast_need", 0.0), "forecast_need")
    effect_pressure = _unit(event.get("effect_pressure", 0.0), "effect_pressure")
    zero_relevance = _unit(event.get("zero_relevance", 0.0), "zero_relevance")
    due_recheck = _bool(event.get("due_recheck", False), "due_recheck")

    thresholds = ROUTER_POLICY["thresholds"]
    lanes: set[str] = set()
    if novelty >= thresholds["world_novelty"] or contradiction >= thresholds["world_contradiction"] or due_recheck:
        lanes.add("world")
    if contradiction >= thresholds["hypothesis_contradiction"] or uncertainty >= thresholds["hypothesis_uncertainty"]:
        lanes.add("hypothesis")
    if forecast_need >= thresholds["simulation_forecast_need"] or effect_pressure >= thresholds["simulation_effect_pressure"]:
        lanes.add("simulation")
    if effect_pressure >= thresholds["zero_model_effect_pressure"] or zero_relevance >= thresholds["zero_model_relevance"]:
        lanes.add("zero_model")
    if lanes:
        lanes.add("critic")
    if event.get("provenance_gap") is True:
        lanes.add("provenance")
    if event.get("goal_pressure") is not None and _unit(event["goal_pressure"], "goal_pressure") >= thresholds["goal_pressure"]:
        lanes.add("goal")
        lanes.add("critic")

    if lanes and resolved_engine_identity is None:
        raise ReactiveRoutingError("MODEL_ACTIVATION_REQUIRES_CONTROL_PLANE_ENGINE_ADMISSION")
    if not lanes and resolved_engine_identity is not None:
        raise ReactiveRoutingError("SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE")

    projection = zero_relevance >= thresholds["zero_projection_relevance"] and bool(lanes)
    event_sha256 = _event_identity(event, admitted_entry_bindings)
    entry_admission_sha256 = (
        _sha256_text(event.get("entry_admission_sha256"), "ENTRY_ADMISSION_SHA256")
        if event.get("entry_event_sha256") is not None
        else None
    )
    router_policy_sha256 = _sha256_canonical(ROUTER_POLICY, "ROUTER_POLICY")
    payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA if entry_admission_sha256 is not None else None,
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
        event_sha256=event_sha256,
        entry_admission_sha256=entry_admission_sha256,
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
        "hash_serialization_schema": decision.hash_serialization_schema,
        "event_sha256": decision.event_sha256,
        "entry_admission_sha256": decision.entry_admission_sha256,
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
