#!/usr/bin/env python3
"""Fail-closed OpenRouter runtime-route identity for Trigger-1 matched controls.

OpenRouter model slugs are not sufficient runtime identity because routing can choose
among eligible providers. Router metadata is direct response evidence for the selected
provider/model and router pipeline, but it does not by itself attest exact model weight
bytes or quantization. This module therefore emits a bounded ROUTE identity and keeps
quantization explicitly UNKNOWN unless some stronger provider evidence supplies it.

No provider network I/O is performed here.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER1_OPENROUTER_RUNTIME_ROUTE_IDENTITY/v1"
BATCH_SCHEMA = "CLAY_TRIGGER1_OPENROUTER_RUNTIME_ROUTE_FAMILY/v1"
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


class RuntimeRouteIdentityError(ValueError):
    pass


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeRouteIdentityError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def extract_runtime_route_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract one selected OpenRouter route from opted-in router metadata."""
    if not isinstance(payload, Mapping):
        raise RuntimeRouteIdentityError("PAYLOAD_MAPPING_REQUIRED")
    meta = payload.get("openrouter_metadata")
    if not isinstance(meta, Mapping):
        raise RuntimeRouteIdentityError("OPENROUTER_METADATA_REQUIRED")

    requested = _text(meta.get("requested"), "requested")
    strategy = _text(meta.get("strategy"), "strategy")
    attempt = meta.get("attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise RuntimeRouteIdentityError("ATTEMPT_POSITIVE_INTEGER_REQUIRED")
    if attempt != 1:
        raise RuntimeRouteIdentityError("FIRST_ATTEMPT_ROUTE_REQUIRED")

    endpoints = meta.get("endpoints")
    available = endpoints.get("available") if isinstance(endpoints, Mapping) else None
    if not isinstance(available, Sequence) or isinstance(available, (str, bytes, bytearray)):
        raise RuntimeRouteIdentityError("ENDPOINTS_AVAILABLE_REQUIRED")
    selected = [row for row in available if isinstance(row, Mapping) and row.get("selected") is True]
    if len(selected) != 1:
        raise RuntimeRouteIdentityError("EXACTLY_ONE_SELECTED_ENDPOINT_REQUIRED")
    selected_provider = _text(selected[0].get("provider"), "selected_provider")
    selected_model = _text(selected[0].get("model"), "selected_model")

    pipeline = meta.get("pipeline")
    if pipeline is None:
        pipeline_rows: list[Any] = []
    elif isinstance(pipeline, Sequence) and not isinstance(pipeline, (str, bytes, bytearray)):
        pipeline_rows = list(pipeline)
    else:
        raise RuntimeRouteIdentityError("PIPELINE_SEQUENCE_REQUIRED")

    route_core = {
        "requested": requested,
        "strategy": strategy,
        "attempt": attempt,
        "is_byok": bool(meta.get("is_byok")) if "is_byok" in meta else None,
        "selected_provider": selected_provider,
        "selected_model": selected_model,
        "pipeline_sha256": _canonical_sha(pipeline_rows),
    }
    return {
        "schema": SCHEMA,
        **route_core,
        "route_identity_sha256": _canonical_sha(route_core),
        "region_observed": meta.get("region"),
        "router_metadata_sha256": _canonical_sha(meta),
        "quantization": "UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA",
        "exact_model_weight_bytes_attested": False,
        "credit_scope": "OPENROUTER_SELECTED_ROUTE_IDENTITY_COMPONENT_ONLY",
    }


def validate_control_family_runtime_identity(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Require all six controls to share one observed selected route identity.

    The function accepts experiment rows whose ``observation`` contains
    ``runtime_route_identity``. Missing metadata, missing controls, multiple route
    identities, duplicate control/seed coordinates, or non-success rows fail closed.
    Quantization remains UNKNOWN even on success.
    """
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)) or not rows:
        raise RuntimeRouteIdentityError("NONEMPTY_ROW_SEQUENCE_REQUIRED")

    seen_coordinates: set[tuple[str, int]] = set()
    controls_seen: set[str] = set()
    identities: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            failures.append(f"ROW_{index}_MAPPING_REQUIRED")
            continue
        control = str(row.get("control") or "").strip()
        seed = row.get("seed")
        if control not in REQUIRED_CONTROLS:
            failures.append(f"ROW_{index}_CONTROL_UNKNOWN")
            continue
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            failures.append(f"ROW_{index}_SEED_INVALID")
            continue
        coordinate = (control, seed)
        if coordinate in seen_coordinates:
            failures.append(f"DUPLICATE_CONTROL_SEED:{control}:{seed}")
            continue
        seen_coordinates.add(coordinate)
        controls_seen.add(control)
        if row.get("status") != "SUCCESS":
            failures.append(f"ROW_NOT_SUCCESS:{control}:{seed}")
            continue
        observation = row.get("observation")
        identity = observation.get("runtime_route_identity") if isinstance(observation, Mapping) else None
        if not isinstance(identity, Mapping):
            failures.append(f"RUNTIME_ROUTE_IDENTITY_MISSING:{control}:{seed}")
            continue
        digest = identity.get("route_identity_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            failures.append(f"RUNTIME_ROUTE_IDENTITY_DIGEST_INVALID:{control}:{seed}")
            continue
        identities.setdefault(digest, dict(identity))

    missing = sorted(set(REQUIRED_CONTROLS) - controls_seen)
    if missing:
        failures.append("MISSING_CONTROLS:" + ",".join(missing))
    stable = not failures and len(identities) == 1
    if not failures and len(identities) != 1:
        failures.append("RUNTIME_ROUTE_IDENTITY_CHANGED_ACROSS_CONTROLS")

    selected = next(iter(identities.values())) if len(identities) == 1 else None
    return {
        "schema": BATCH_SCHEMA,
        "stable_selected_route": stable,
        "unique_route_identities": len(identities),
        "controls_seen": sorted(controls_seen),
        "selected_route_identity": selected,
        "quantization": "UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA",
        "exact_model_weight_bytes_attested": False,
        "failures": failures,
        "credit_scope": "OPENROUTER_SELECTED_ROUTE_IDENTITY_COMPONENT_ONLY",
    }


__all__ = [
    "SCHEMA",
    "BATCH_SCHEMA",
    "REQUIRED_CONTROLS",
    "RuntimeRouteIdentityError",
    "extract_runtime_route_identity",
    "validate_control_family_runtime_identity",
]
