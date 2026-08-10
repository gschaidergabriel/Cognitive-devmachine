#!/usr/bin/env python3
"""Deterministic Clay GateFlow v1 compiler/checker.

This tool is coordination-only. It never mutates Frank, promotes a gate, or changes
workspace credit. It validates a GateFlow state snapshot and computes flow/safety
metrics when a measured token denominator is supplied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SEVERITY = {"P0": 8.0, "P1": 5.0, "P2": 3.0, "P3": 1.0}
EVIDENCE = {
    "TARGET_VPS": 1.0,
    "EXACT_CURRENT_CI": 0.8,
    "LOCAL_EXECUTABLE": 0.5,
    "MECHANISM_ONLY": 0.25,
    "THEORETICAL": 0.0,
}
DISPOSITION = {"RETIRED": 1.0, "PROMOTION_BLOCKED": 0.6, "OPEN": 0.0}

ALLOWED_STATES = {
    "DISCOVERED", "REPRODUCED", "REPAIR_CANDIDATE", "LOCAL_VERIFIED",
    "TARGET_VERIFIED", "TARGET_VERIFICATION_PENDING", "FRESH_MAIN_VERIFIED",
    "FRESH_MAIN_VERIFICATION_PENDING", "INTEGRATION_VERIFIED", "RECEIPT_READY",
    "ADMITTED", "WORKSPACE_CREDITED", "NEGATIVE_EVIDENCE", "INFRA_FAILURE",
    "HARNESS_FAILURE", "STALE_BASE", "DUPLICATE", "SUPERSEDED", "BLOCKED_EXTERNAL",
}
ALLOWED_FRESHNESS = {"GREEN", "AMBER", "RED"}


def risk_units(event: dict[str, Any]) -> float:
    return (
        SEVERITY[event["severity"]]
        * EVIDENCE[event["evidence_class"]]
        * DISPOSITION[event["disposition"]]
    )


def validate(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    objectives = set(state.get("primary_objectives", []))
    required = {
        "accepted_gate_weight_delta_per_1m_tokens",
        "accepted_gate_weight_delta_per_worker_hour",
        "risk_retired_per_1m_tokens",
    }
    missing = required - objectives
    if missing:
        errors.append(f"missing primary objectives: {sorted(missing)}")

    seen: dict[tuple[str, str], str] = {}
    for item in state.get("frontier", []):
        if item.get("state") not in ALLOWED_STATES:
            errors.append(f"invalid state: {item.get('state')}")
        if item.get("freshness") not in ALLOWED_FRESHNESS:
            errors.append(f"invalid freshness: {item.get('freshness')}")
        surface = item.get("semantic_surface", "")
        for role in ("implementation_owner", "falsifier", "promotion_owner"):
            owner = item.get(role)
            if not owner:
                continue
            key = (surface, role)
            prior = seen.get(key)
            if prior and prior != owner:
                errors.append(f"WIP violation {surface}/{role}: {prior} vs {owner}")
            seen[key] = owner

    risk_ids: set[str] = set()
    for event in state.get("risk_events", []):
        rid = event.get("risk_id")
        if rid in risk_ids:
            errors.append(f"duplicate risk_id: {rid}")
        risk_ids.add(rid)
        try:
            computed = risk_units(event)
        except KeyError as exc:
            errors.append(f"invalid risk enum for {rid}: {exc}")
            continue
        declared = event.get("risk_units")
        if declared is not None and abs(float(declared) - computed) > 1e-9:
            errors.append(f"risk_units mismatch {rid}: declared={declared}, computed={computed}")

    metrics = state.get("metrics", {})
    if "risk_retired_units_current_snapshot" in metrics:
        total = sum(risk_units(e) for e in state.get("risk_events", []))
        if abs(float(metrics["risk_retired_units_current_snapshot"]) - total) > 1e-9:
            errors.append(
                "risk_retired_units_current_snapshot mismatch: "
                f"declared={metrics['risk_retired_units_current_snapshot']}, computed={total}"
            )
    return errors


def compile_metrics(state: dict[str, Any], tokens: float | None, worker_hours: float | None) -> dict[str, Any]:
    accepted = float(state.get("metrics", {}).get("accepted_gate_weight_delta", 0.0))
    risk = sum(risk_units(e) for e in state.get("risk_events", []))
    out: dict[str, Any] = {
        "accepted_gate_weight_delta": accepted,
        "risk_retired_units": risk,
        "accepted_gate_weight_delta_per_1m_tokens": None,
        "risk_retired_per_1m_tokens": None,
        "accepted_gate_weight_delta_per_worker_hour": None,
    }
    if tokens is not None:
        if tokens <= 0:
            raise ValueError("tokens must be > 0")
        millions = tokens / 1_000_000.0
        out["accepted_gate_weight_delta_per_1m_tokens"] = accepted / millions
        out["risk_retired_per_1m_tokens"] = risk / millions
    if worker_hours is not None:
        if worker_hours <= 0:
            raise ValueError("worker_hours must be > 0")
        out["accepted_gate_weight_delta_per_worker_hour"] = accepted / worker_hours
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--tokens", type=float, default=None, help="Measured generated repo text tokens for the selected window")
    parser.add_argument("--worker-hours", type=float, default=None)
    args = parser.parse_args()

    state = json.loads(args.state.read_text())
    errors = validate(state)
    result = {
        "valid": not errors,
        "errors": errors,
        "metrics": compile_metrics(state, args.tokens, args.worker_hours),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
