#!/usr/bin/env python3
"""Causal route/engine identity binding shared by Xeno modes.

This module closes two classes of false identity: different admitted events producing the
same routing shape, and different cognition engines producing the same route digest.
Provider admission is positive: model activation requires an explicit INTERNAL_LOCAL
engine binding with exact runtime/checkpoint identity.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from entry_fabric_v1 import XenoIngressPacket

ENGINE_SCHEMA = "XENO_ENGINE_BINDING/v1"
ROUTE_SCHEMA = "XENO_ROUTE_BINDING/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ENGINE_KEYS = {
    "schema",
    "engine_id",
    "engine_class",
    "provider_class",
    "runtime_identity",
    "checkpoint_sha256",
}
ALLOWED_ENGINE_CLASSES = {"LOCAL_SHARED_WEIGHT_INFERENCE"}
ALLOWED_PROVIDER_CLASSES = {"INTERNAL_LOCAL"}


class RouteBindingError(ValueError):
    pass


@dataclass(frozen=True)
class EngineBinding:
    schema: str
    engine_id: str
    engine_class: str
    provider_class: str
    runtime_identity: str
    checkpoint_sha256: str


@dataclass(frozen=True)
class RouteBinding:
    schema: str
    route_decision_sha256: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    model_activation: bool
    engine_id: str | None
    engine_class: str | None
    provider_class: str | None
    runtime_identity: str | None
    checkpoint_sha256: str | None
    routing_result_sha256: str


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
        raise RouteBindingError("NONCANONICAL_VALUE") from exc


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RouteBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def admit_engine_binding(raw: Mapping[str, Any]) -> EngineBinding:
    if not isinstance(raw, Mapping) or set(raw) != ENGINE_KEYS:
        raise RouteBindingError("ENGINE_BINDING_KEYSET_INVALID")
    if raw.get("schema") != ENGINE_SCHEMA:
        raise RouteBindingError("ENGINE_BINDING_SCHEMA_UNSUPPORTED")

    engine_class = _text(raw.get("engine_class"), "engine_class")
    provider_class = _text(raw.get("provider_class"), "provider_class")
    if engine_class not in ALLOWED_ENGINE_CLASSES:
        raise RouteBindingError("ENGINE_CLASS_NOT_POSITIVELY_ADMITTED")
    if provider_class not in ALLOWED_PROVIDER_CLASSES:
        raise RouteBindingError("PROVIDER_CLASS_NOT_POSITIVELY_ADMITTED")

    checkpoint_sha256 = _text(raw.get("checkpoint_sha256"), "checkpoint_sha256").lower()
    if not SHA256_RE.fullmatch(checkpoint_sha256):
        raise RouteBindingError("checkpoint_sha256:LOWERCASE_SHA256_REQUIRED")

    return EngineBinding(
        schema=ENGINE_SCHEMA,
        engine_id=_text(raw.get("engine_id"), "engine_id"),
        engine_class=engine_class,
        provider_class=provider_class,
        runtime_identity=_text(raw.get("runtime_identity"), "runtime_identity"),
        checkpoint_sha256=checkpoint_sha256,
    )


def bind_route_decision(
    packet: XenoIngressPacket,
    routing_result: Mapping[str, Any],
    *,
    model_activation: bool,
    engine: EngineBinding | None,
) -> RouteBinding:
    if not isinstance(packet, XenoIngressPacket):
        raise RouteBindingError("ADMITTED_INGRESS_PACKET_REQUIRED")
    if not isinstance(routing_result, Mapping) or not routing_result:
        raise RouteBindingError("ROUTING_RESULT_NONEMPTY_MAPPING_REQUIRED")
    if not isinstance(model_activation, bool):
        raise RouteBindingError("MODEL_ACTIVATION_BOOLEAN_REQUIRED")
    if model_activation and not isinstance(engine, EngineBinding):
        raise RouteBindingError("MODEL_ACTIVATION_REQUIRES_ADMITTED_ENGINE")
    if not model_activation and engine is not None:
        raise RouteBindingError("SCRIPT_ONLY_ROUTE_MUST_NOT_BIND_MODEL_ENGINE")

    routing_result_sha256 = hashlib.sha256(_canonical(routing_result)).hexdigest()
    engine_payload = asdict(engine) if engine is not None else None
    identity_payload = {
        "schema": ROUTE_SCHEMA,
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "model_activation": model_activation,
        "engine": engine_payload,
        "routing_result_sha256": routing_result_sha256,
    }
    route_decision_sha256 = hashlib.sha256(_canonical(identity_payload)).hexdigest()

    return RouteBinding(
        schema=ROUTE_SCHEMA,
        route_decision_sha256=route_decision_sha256,
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        entity_generation=packet.entity_generation,
        model_activation=model_activation,
        engine_id=engine.engine_id if engine else None,
        engine_class=engine.engine_class if engine else None,
        provider_class=engine.provider_class if engine else None,
        runtime_identity=engine.runtime_identity if engine else None,
        checkpoint_sha256=engine.checkpoint_sha256 if engine else None,
        routing_result_sha256=routing_result_sha256,
    )
