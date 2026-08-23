#!/usr/bin/env python3
"""Positive engine admission and causal route identity for Xeno.

This module does not choose model outputs or grant authority. It resolves a requested
internal engine only through an explicit admitted-engine policy, then binds that resolved
identity together with the immutable Xeno ingress identity and deterministic routing result.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from entry_fabric_v1 import XenoIngressPacket

ENGINE_POLICY_SCHEMA = "XENO_ENGINE_ADMISSION_POLICY/v1"
ROUTE_IDENTITY_SCHEMA = "XENO_ROUTE_IDENTITY/v1"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ENGINE_FIELDS = {"canonical_id", "engine_class", "artifact_sha256"}


class RouteIdentityError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedEngineIdentity:
    requested_id: str
    canonical_id: str
    engine_class: str
    artifact_sha256: str | None
    admission_policy_sha256: str


@dataclass(frozen=True)
class RouteIdentity:
    schema: str
    ingress_sha256: str
    causal_id: str
    entity_generation: int
    engine_canonical_id: str
    engine_class: str
    engine_artifact_sha256: str | None
    engine_admission_policy_sha256: str
    router_policy_sha256: str
    routing_result_sha256: str
    route_sha256: str


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RouteIdentityError("NON_CANONICAL_JSON_VALUE") from exc


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RouteIdentityError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256(value: Any, field: str) -> str:
    text = _string(value, field).lower()
    if not _SHA256_RE.fullmatch(text):
        raise RouteIdentityError(f"{field}:SHA256_HEX_REQUIRED")
    return text


def _normalize_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(policy, Mapping) or policy.get("schema") != ENGINE_POLICY_SCHEMA:
        raise RouteIdentityError("ENGINE_POLICY_SCHEMA_UNSUPPORTED")
    engines = policy.get("engines")
    if not isinstance(engines, Mapping) or not engines:
        raise RouteIdentityError("ENGINE_POLICY_ENGINES_REQUIRED")

    normalized_engines: dict[str, dict[str, Any]] = {}
    for raw_requested_id, raw_entry in engines.items():
        requested_id = _string(raw_requested_id, "engine_policy.requested_id")
        if not isinstance(raw_entry, Mapping):
            raise RouteIdentityError(f"engine_policy.{requested_id}:MAPPING_REQUIRED")
        unknown = sorted(set(raw_entry) - _ENGINE_FIELDS)
        missing = sorted({"canonical_id", "engine_class"} - set(raw_entry))
        if unknown:
            raise RouteIdentityError(f"engine_policy.{requested_id}:UNBOUND_FIELDS_FORBIDDEN:" + ",".join(unknown))
        if missing:
            raise RouteIdentityError(f"engine_policy.{requested_id}:MISSING_REQUIRED_FIELDS:" + ",".join(missing))
        artifact = raw_entry.get("artifact_sha256")
        normalized_engines[requested_id] = {
            "canonical_id": _string(raw_entry["canonical_id"], f"engine_policy.{requested_id}.canonical_id"),
            "engine_class": _string(raw_entry["engine_class"], f"engine_policy.{requested_id}.engine_class"),
            "artifact_sha256": None if artifact is None else _sha256(artifact, f"engine_policy.{requested_id}.artifact_sha256"),
        }
    return {"schema": ENGINE_POLICY_SCHEMA, "engines": normalized_engines}


def resolve_engine(requested_engine_id: str, policy: Mapping[str, Any]) -> ResolvedEngineIdentity:
    """Resolve only positively admitted engine ids/aliases. Unknown ids fail closed."""
    requested_id = _string(requested_engine_id, "requested_engine_id")
    normalized_policy = _normalize_policy(policy)
    entry = normalized_policy["engines"].get(requested_id)
    if entry is None:
        raise RouteIdentityError("ENGINE_NOT_POSITIVELY_ADMITTED")
    policy_sha = hashlib.sha256(_canonical(normalized_policy)).hexdigest()
    return ResolvedEngineIdentity(
        requested_id=requested_id,
        canonical_id=entry["canonical_id"],
        engine_class=entry["engine_class"],
        artifact_sha256=entry["artifact_sha256"],
        admission_policy_sha256=policy_sha,
    )


def bind_route_identity(
    packet: XenoIngressPacket,
    engine: ResolvedEngineIdentity,
    *,
    router_policy_sha256: str,
    routing_result: Mapping[str, Any],
) -> RouteIdentity:
    """Bind H(ingress, resolved engine, router policy, routing result)."""
    if not isinstance(packet, XenoIngressPacket):
        raise RouteIdentityError("XENO_INGRESS_PACKET_REQUIRED")
    if not isinstance(engine, ResolvedEngineIdentity):
        raise RouteIdentityError("RESOLVED_ENGINE_IDENTITY_REQUIRED")
    if not isinstance(routing_result, Mapping):
        raise RouteIdentityError("ROUTING_RESULT_MAPPING_REQUIRED")

    router_sha = _sha256(router_policy_sha256, "router_policy_sha256")
    routing_result_sha = hashlib.sha256(_canonical(routing_result)).hexdigest()
    identity_payload = {
        "schema": ROUTE_IDENTITY_SCHEMA,
        "ingress_sha256": packet.ingress_sha256,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "engine_canonical_id": engine.canonical_id,
        "engine_class": engine.engine_class,
        "engine_artifact_sha256": engine.artifact_sha256,
        "engine_admission_policy_sha256": engine.admission_policy_sha256,
        "router_policy_sha256": router_sha,
        "routing_result_sha256": routing_result_sha,
    }
    route_sha = hashlib.sha256(_canonical(identity_payload)).hexdigest()
    return RouteIdentity(route_sha256=route_sha, **identity_payload)
