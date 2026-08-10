#!/usr/bin/env python3
"""Deterministic Clay GateFlow v1 compiler/checker.

Coordination-only: validates GateFlow state, computes gate/risk metrics, and maps
changed paths to Frank v0.1 gate/subcheck surfaces. It never mutates Frank,
promotes a gate, or changes workspace credit.
"""
from __future__ import annotations

import argparse
import fnmatch
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
PROMOTION_READY_STATES = {"RECEIPT_READY", "ADMITTED", "WORKSPACE_CREDITED"}


def risk_units(event: dict[str, Any]) -> float:
    return (
        SEVERITY[event["severity"]]
        * EVIDENCE[event["evidence_class"]]
        * DISPOSITION[event["disposition"]]
    )


def lease_scope(item: dict[str, Any]) -> str:
    explicit = item.get("lease_scope")
    if explicit:
        return str(explicit)
    return "::".join([
        str(item.get("work_package", "")),
        str(item.get("subcheck", "")),
        str(item.get("semantic_surface", "")),
    ])


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
        state_name = item.get("state")
        freshness = item.get("freshness")
        if state_name not in ALLOWED_STATES:
            errors.append(f"invalid state: {state_name}")
        if freshness not in ALLOWED_FRESHNESS:
            errors.append(f"invalid freshness: {freshness}")
        if not item.get("dependency_cone"):
            errors.append(f"missing dependency_cone: {lease_scope(item)}")
        if freshness == "RED" and state_name in PROMOTION_READY_STATES:
            errors.append(f"RED freshness cannot be promotion-ready: {lease_scope(item)}")

        scope = lease_scope(item)
        for role in ("implementation_owner", "falsifier", "promotion_owner"):
            owner = item.get(role)
            if not owner:
                continue
            key = (scope, role)
            prior = seen.get(key)
            if prior and prior != owner:
                errors.append(f"WIP violation {scope}/{role}: {prior} vs {owner}")
            seen[key] = owner

    risk_ids: set[str] = set()
    domains: dict[str, str] = {}
    for event in state.get("risk_events", []):
        rid = event.get("risk_id")
        domain = event.get("unique_failure_domain")
        if rid in risk_ids:
            errors.append(f"duplicate risk_id: {rid}")
        risk_ids.add(rid)
        if not domain:
            errors.append(f"missing unique_failure_domain: {rid}")
        elif domain in domains and domains[domain] != rid:
            errors.append(f"duplicate failure domain: {domain} ({domains[domain]} vs {rid})")
        else:
            domains[domain] = rid

        disposition = event.get("disposition")
        residual_open = event.get("residual_open")
        if disposition == "RETIRED" and residual_open is not False:
            errors.append(f"RETIRED risk must set residual_open=false: {rid}")
        if disposition in {"PROMOTION_BLOCKED", "OPEN"} and residual_open is not True:
            errors.append(f"{disposition} risk must set residual_open=true: {rid}")
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
    fully_retired = sum(
        risk_units(e) for e in state.get("risk_events", []) if e.get("disposition") == "RETIRED"
    )
    blocked = sum(
        risk_units(e) for e in state.get("risk_events", []) if e.get("disposition") == "PROMOTION_BLOCKED"
    )
    out: dict[str, Any] = {
        "accepted_gate_weight_delta": accepted,
        "risk_retired_units": risk,
        "fully_retired_risk_units": fully_retired,
        "promotion_block_risk_units": blocked,
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


def map_paths(paths: list[str], rules: dict[str, Any]) -> list[dict[str, Any]]:
    by_target: dict[tuple[str, str], dict[str, Any]] = {}
    for rule in rules.get("rules", []):
        matched = sorted({
            path for path in paths
            if any(fnmatch.fnmatch(path, pattern) for pattern in rule.get("patterns", []))
        })
        if not matched:
            continue
        key = (rule["work_package"], rule["subcheck"])
        row = by_target.setdefault(key, {
            "work_package": rule["work_package"],
            "subcheck": rule["subcheck"],
            "matched_paths": [],
            "rule_ids": [],
            "missing_evidence_template": [],
        })
        row["matched_paths"] = sorted(set(row["matched_paths"]) | set(matched))
        row["rule_ids"] = sorted(set(row["rule_ids"]) | {rule["rule_id"]})
        row["missing_evidence_template"] = sorted(
            set(row["missing_evidence_template"]) | set(rule.get("missing_evidence_template", []))
        )
    return sorted(by_target.values(), key=lambda r: (r["work_package"], r["subcheck"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--tokens", type=float, default=None, help="Measured generated repo text tokens for selected window")
    parser.add_argument("--worker-hours", type=float, default=None)
    parser.add_argument("--rules", type=Path, default=None)
    parser.add_argument("--changed-path", action="append", default=[])
    args = parser.parse_args()

    state = json.loads(args.state.read_text())
    errors = validate(state)
    result: dict[str, Any] = {
        "valid": not errors,
        "errors": errors,
        "metrics": compile_metrics(state, args.tokens, args.worker_hours),
    }
    if args.changed_path:
        if args.rules is None:
            raise SystemExit("--rules is required with --changed-path")
        rules = json.loads(args.rules.read_text())
        result["affected_gate_surfaces"] = map_paths(args.changed_path, rules)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
