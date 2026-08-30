#!/usr/bin/env python3
"""Deterministic open-world execution-surface resolver.

This tool grants no authority. It combines an already-resolved authority decision,
direct capability observations, and a non-authoritative federated route registry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "EXECUTION_SURFACE_RESOLUTION/v1"
DIRECT_AVAILABLE = "DIRECT_AVAILABLE"
REACHABLE_VIA_BRIDGE = "REACHABLE_VIA_BRIDGE"
DISCOVERY_REQUIRED = "DISCOVERY_REQUIRED"
TRANSIENTLY_UNREACHABLE = "TRANSIENTLY_UNREACHABLE"
AUTHORITY_DENIED = "AUTHORITY_DENIED"
ECONOMICALLY_DENIED = "ECONOMICALLY_DENIED"
CAPABILITY_ABSENT_PROVEN = "CAPABILITY_ABSENT_PROVEN"
STALE_RESOLUTION = "STALE_RESOLUTION_REQUIRES_RECONCILIATION"

TERMINAL_ABSENT = {"ABSENT_PROVEN", "TERMINAL_ABSENT"}
TRANSIENT = {"OFFLINE", "QUEUED", "RATE_LIMITED", "TIMEOUT", "TRANSIENT_FAILURE", "UNREACHABLE"}
REACHABLE = {"PASS", "REACHABLE", "AVAILABLE", "HEALTHY"}
UNKNOWN = {"UNKNOWN", "UNPROBED", "DISCOVERY_REQUIRED", None}


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object in {path}")
    return data


def applicable_routes(registry: dict[str, Any], requested: set[str]) -> list[dict[str, Any]]:
    routes = []
    for route in registry.get("routes", []):
        caps = set(route.get("capabilities", []))
        if requested.issubset(caps):
            routes.append(route)
    return routes


def _status(observations: dict[str, Any], route_id: str) -> str | None:
    raw = (observations.get("routes") or {}).get(route_id, {})
    if isinstance(raw, str):
        return raw.upper()
    if isinstance(raw, dict):
        value = raw.get("status")
        return str(value).upper() if value is not None else None
    return None


def resolve(registry: dict[str, Any], request: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    requested = set(request.get("capabilities") or [])
    if not requested:
        raise ValueError("request.capabilities must be non-empty")

    authority_generation = request.get("authority_generation")
    if not authority_generation:
        raise ValueError("request.authority_generation is required")

    authority = request.get("authority") or {}
    if authority.get("allowed") is False:
        classification = AUTHORITY_DENIED
        return _receipt(request, [], None, classification, observations, "authority explicitly denies requested action")

    economic = request.get("economic") or {}
    if economic.get("required") and economic.get("allowed") is False:
        classification = ECONOMICALLY_DENIED
        return _receipt(request, [], None, classification, observations, "economic/provider gate denies concrete route")

    direct = observations.get("direct") or {}
    direct_caps = {k for k, v in direct.items() if v is True}
    if requested.issubset(direct_caps):
        return _receipt(request, [], "DIRECT", DIRECT_AVAILABLE, observations, "all requested capabilities directly observed")

    candidates = applicable_routes(registry, requested)
    candidate_rows = []
    any_unknown = False
    any_transient = False
    all_terminal_absent = bool(candidates)

    for route in candidates:
        rid = route["route_id"]
        status = _status(observations, rid)
        row = {
            "route_id": rid,
            "to": route.get("to"),
            "status": status or "UNPROBED",
            "negative_ttl_seconds": route.get("negative_ttl_seconds"),
        }
        candidate_rows.append(row)
        if status in REACHABLE:
            return _receipt(request, candidate_rows, rid, REACHABLE_VIA_BRIDGE, observations, "registered indirect route observed reachable")
        if status in TRANSIENT:
            any_transient = True
            all_terminal_absent = False
        elif status in TERMINAL_ABSENT:
            pass
        else:
            any_unknown = True
            all_terminal_absent = False

    if any_unknown or (not candidates):
        classification = DISCOVERY_REQUIRED
        reason = "known route health is unprobed/unknown" if candidates else "registry has no exhaustive applicable route proof"
    elif any_transient:
        classification = TRANSIENTLY_UNREACHABLE
        reason = "all non-terminal candidate routes are presently transient/queued/offline"
    elif all_terminal_absent:
        classification = CAPABILITY_ABSENT_PROVEN
        reason = "all registered applicable routes are freshly terminal-absent and direct capability is absent"
    else:
        classification = DISCOVERY_REQUIRED
        reason = "route state incomplete"

    return _receipt(request, candidate_rows, None, classification, observations, reason)


def _receipt(request: dict[str, Any], candidates: list[dict[str, Any]], selected: str | None,
             classification: str, observations: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "requested_capabilities": request.get("capabilities"),
        "authority_identity": request.get("authority_identity"),
        "authority_generation": request.get("authority_generation"),
        "policy_axes": {
            "authority": request.get("authority") or {},
            "economic": request.get("economic") or {},
        },
        "direct_observations": observations.get("direct") or {},
        "candidate_routes": candidates,
        "selected_route": selected,
        "classification": classification,
        "reason": reason,
        "revalidate_before_use": classification in {DIRECT_AVAILABLE, REACHABLE_VIA_BRIDGE},
        "evidence_scope": "ROUTING_ONLY",
        "global_absence_proven": classification == CAPABILITY_ABSENT_PROVEN,
    }


def validate_generation(receipt: dict[str, Any], current_authority_generation: str) -> dict[str, Any]:
    observed = receipt.get("authority_generation")
    if observed != current_authority_generation:
        return {
            "valid": False,
            "classification": STALE_RESOLUTION,
            "receipt_authority_generation": observed,
            "current_authority_generation": current_authority_generation,
        }
    return {"valid": True, "classification": "CURRENT_GENERATION"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--request", required=True, help="JSON file")
    ap.add_argument("--observations", required=True, help="JSON file")
    ap.add_argument("--current-authority-generation")
    args = ap.parse_args()

    registry = load_json(args.registry)
    request = load_json(args.request)
    observations = load_json(args.observations)
    receipt = resolve(registry, request, observations)
    if args.current_authority_generation:
        receipt["generation_validation"] = validate_generation(receipt, args.current_authority_generation)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
