#!/usr/bin/env python3
"""Deterministic Clay GateFlow v1.1 compiler/checker.

Coordination-only. This tool never mutates Frank, promotes a gate, or changes
workspace credit. It validates a GateFlow state snapshot and computes flow,
conversion, staleness and anti-Goodhart metrics from explicitly supplied
evidence. Missing denominators remain None.
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
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

PROMOTION_STAGES = [
    "DISCOVERED",
    "REPRODUCED",
    "REPAIR_CANDIDATE",
    "LOCAL_VERIFIED",
    "TARGET_VERIFIED",
    "FRESH_MAIN_VERIFIED",
    "INTEGRATION_VERIFIED",
    "PRODUCT_MAIN_MERGED",
    "RECEIPT_READY",
    "ADMITTED",
    "WORKSPACE_CREDITED",
]
STAGE_RANK = {name: index for index, name in enumerate(PROMOTION_STAGES)}
PENDING_STAGE_RANK = {
    "TARGET_VERIFICATION_PENDING": STAGE_RANK["LOCAL_VERIFIED"],
    "FRESH_MAIN_VERIFICATION_PENDING": STAGE_RANK["TARGET_VERIFIED"],
}
SIDE_STATES = {
    "NEGATIVE_EVIDENCE",
    "INFRA_FAILURE",
    "HARNESS_FAILURE",
    "STALE_BASE",
    "DUPLICATE",
    "SUPERSEDED",
    "BLOCKED_EXTERNAL",
}
ALLOWED_STATES = set(PROMOTION_STAGES) | set(PENDING_STAGE_RANK) | SIDE_STATES
ALLOWED_FRESHNESS = {"GREEN", "AMBER", "RED"}

_REQUIRED_OBJECTIVES = {
    "accepted_gate_weight_delta_per_1m_tokens",
    "accepted_gate_weight_delta_per_worker_hour",
    "risk_retired_per_1m_tokens",
}


def _parse_ts(value: str) -> datetime:
    """Parse an ISO-8601 timestamp; normalize Z to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _seconds_between(start: str, end: str) -> float:
    return (_parse_ts(end) - _parse_ts(start)).total_seconds()


def _median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def stage_rank(stage: str) -> int | None:
    if stage in STAGE_RANK:
        return STAGE_RANK[stage]
    return PENDING_STAGE_RANK.get(stage)


def risk_units(event: dict[str, Any]) -> float:
    return (
        SEVERITY[event["severity"]]
        * EVIDENCE[event["evidence_class"]]
        * DISPOSITION[event["disposition"]]
    )


def _validate_conversion_event(event: dict[str, Any], errors: list[str]) -> None:
    eid = event.get("event_id", "<missing>")
    stage = event.get("current_stage")
    if stage not in ALLOWED_STATES:
        errors.append(f"invalid conversion current_stage {eid}: {stage}")
        return

    stage_times = event.get("stage_times", {})
    prior_time: datetime | None = None
    prior_stage: str | None = None
    for named_stage in PROMOTION_STAGES:
        value = stage_times.get(named_stage)
        if value is None:
            continue
        try:
            current_time = _parse_ts(value)
        except (TypeError, ValueError) as exc:
            errors.append(f"invalid conversion timestamp {eid}/{named_stage}: {exc}")
            continue
        if prior_time is not None and current_time < prior_time:
            errors.append(
                f"conversion time regression {eid}: {named_stage} < {prior_stage}"
            )
        prior_time = current_time
        prior_stage = named_stage

    rank = stage_rank(stage)
    if rank is not None:
        observed_later = [
            s
            for s, ts in stage_times.items()
            if ts is not None and s in STAGE_RANK and STAGE_RANK[s] > rank
        ]
        if observed_later:
            errors.append(
                f"conversion current_stage behind observed history {eid}: {sorted(observed_later)}"
            )

    if rank is not None and rank >= STAGE_RANK["PRODUCT_MAIN_MERGED"]:
        if not event.get("product_main_sha"):
            errors.append(f"missing product_main_sha for merged conversion event: {eid}")
    if rank is not None and rank >= STAGE_RANK["RECEIPT_READY"]:
        if not event.get("receipt_ref"):
            errors.append(f"missing receipt_ref for receipt-ready conversion event: {eid}")
    if rank is not None and rank >= STAGE_RANK["WORKSPACE_CREDITED"]:
        if not event.get("workspace_credit_ref"):
            errors.append(f"missing workspace_credit_ref for credited conversion event: {eid}")
        credited = event.get("workspace_credited_weight")
        if credited is None or float(credited) <= 0:
            errors.append(f"missing positive workspace_credited_weight for credited event: {eid}")


def validate(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    objectives = set(state.get("primary_objectives", []))
    missing = _REQUIRED_OBJECTIVES - objectives
    if missing:
        errors.append(f"missing primary objectives: {sorted(missing)}")

    seen: dict[tuple[str, str], str] = {}
    for item in state.get("frontier", []):
        if item.get("state") not in ALLOWED_STATES:
            errors.append(f"invalid state: {item.get('state')}")
        if item.get("freshness") not in ALLOWED_FRESHNESS:
            errors.append(f"invalid freshness: {item.get('freshness')}")
        if (
            item.get("freshness") == "RED"
            and item.get("state") in {"RECEIPT_READY", "ADMITTED", "WORKSPACE_CREDITED"}
        ):
            errors.append(
                f"RED freshness cannot be promotion-ready: {item.get('semantic_surface')}"
            )
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
            errors.append(
                f"risk_units mismatch {rid}: declared={declared}, computed={computed}"
            )

    conversion_ids: set[str] = set()
    for event in state.get("conversion_events", []):
        eid = event.get("event_id")
        if not eid:
            errors.append("conversion event missing event_id")
            continue
        if eid in conversion_ids:
            errors.append(f"duplicate conversion event_id: {eid}")
        conversion_ids.add(eid)
        _validate_conversion_event(event, errors)

    metrics = state.get("metrics", {})
    if "risk_retired_units_current_snapshot" in metrics:
        total = sum(risk_units(e) for e in state.get("risk_events", []))
        if abs(float(metrics["risk_retired_units_current_snapshot"]) - total) > 1e-9:
            errors.append(
                "risk_retired_units_current_snapshot mismatch: "
                f"declared={metrics['risk_retired_units_current_snapshot']}, computed={total}"
            )
    return errors


def compile_conversion_metrics(
    state: dict[str, Any], now: str | None = None
) -> dict[str, Any]:
    events = state.get("conversion_events", [])
    ranks = [
        stage_rank(event.get("current_stage", ""))
        for event in events
        if stage_rank(event.get("current_stage", "")) is not None
    ]
    max_rank = STAGE_RANK["WORKSPACE_CREDITED"]

    target_to_product: list[float] = []
    product_to_credit: list[float] = []
    evidence_to_admission: list[float] = []
    wip_ages: list[float] = []
    fresh_attempts = 0
    fresh_successes = 0

    now_dt = _parse_ts(now) if now is not None else datetime.now(timezone.utc)

    product_merged = 0
    workspace_credited = 0
    target_verified_unmerged = 0
    product_merged_uncredited = 0

    for event in events:
        rank = stage_rank(event.get("current_stage", ""))
        times = event.get("stage_times", {})
        if rank is not None and rank >= STAGE_RANK["PRODUCT_MAIN_MERGED"]:
            product_merged += 1
        if rank is not None and rank >= STAGE_RANK["WORKSPACE_CREDITED"]:
            workspace_credited += 1
        if (
            rank is not None
            and rank >= STAGE_RANK["TARGET_VERIFIED"]
            and rank < STAGE_RANK["PRODUCT_MAIN_MERGED"]
        ):
            target_verified_unmerged += 1
        if (
            rank is not None
            and rank >= STAGE_RANK["PRODUCT_MAIN_MERGED"]
            and rank < STAGE_RANK["WORKSPACE_CREDITED"]
        ):
            product_merged_uncredited += 1

        if times.get("TARGET_VERIFIED") and times.get("PRODUCT_MAIN_MERGED"):
            target_to_product.append(
                _seconds_between(times["TARGET_VERIFIED"], times["PRODUCT_MAIN_MERGED"])
            )
        if times.get("PRODUCT_MAIN_MERGED") and times.get("WORKSPACE_CREDITED"):
            product_to_credit.append(
                _seconds_between(
                    times["PRODUCT_MAIN_MERGED"], times["WORKSPACE_CREDITED"]
                )
            )
        first_evidence = (
            times.get("REPRODUCED")
            or times.get("TARGET_VERIFIED")
            or times.get("DISCOVERED")
        )
        if first_evidence and times.get("ADMITTED"):
            evidence_to_admission.append(
                _seconds_between(first_evidence, times["ADMITTED"])
            )

        discovered = times.get("DISCOVERED")
        terminal = event.get("current_stage") in {
            "WORKSPACE_CREDITED",
            "SUPERSEDED",
            "DUPLICATE",
            "BLOCKED_EXTERNAL",
        }
        if discovered and not terminal:
            wip_ages.append((now_dt - _parse_ts(discovered)).total_seconds())

        attempts = event.get("fresh_main_attempts")
        successes = event.get("fresh_main_successes")
        if attempts is not None:
            attempts_i = int(attempts)
            successes_i = int(successes or 0)
            if attempts_i < 0 or successes_i < 0 or successes_i > attempts_i:
                continue
            fresh_attempts += attempts_i
            fresh_successes += successes_i

    population = state.get("conversion_population", {})
    population_complete = bool(population.get("complete", False))
    population_n = len(events)
    observed_product_fraction = product_merged / population_n if population_n else None
    observed_credit_fraction = workspace_credited / population_n if population_n else None

    workspace_staleness_seconds = None
    workspace_last = state.get("workspace_snapshot", {}).get("last_updated")
    product_commit_at = state.get("head_observation", {}).get(
        "product_main_head_commit_at"
    )
    if workspace_last and product_commit_at:
        workspace_staleness_seconds = max(
            0.0, _seconds_between(workspace_last, product_commit_at)
        )

    return {
        # Process-depth is deliberately NOT Frank product progress.
        "observed_conversion_pipeline_depth_index": (
            sum(ranks) / (len(ranks) * max_rank) if ranks else None
        ),
        "observed_product_main_merged_fraction": observed_product_fraction,
        "observed_workspace_credited_fraction": observed_credit_fraction,
        "research_to_product_main_conversion_rate": (
            observed_product_fraction if population_complete else None
        ),
        "research_to_workspace_credit_conversion_rate": (
            observed_credit_fraction if population_complete else None
        ),
        "target_verified_to_product_main_median_latency_seconds": _median(
            target_to_product
        ),
        "product_main_to_workspace_credit_median_latency_seconds": _median(
            product_to_credit
        ),
        "evidence_to_admission_median_latency_seconds": _median(
            evidence_to_admission
        ),
        "median_wip_age_seconds": _median(wip_ages),
        "fresh_main_survival_rate": (
            fresh_successes / fresh_attempts if fresh_attempts else None
        ),
        "target_verified_unmerged_events": target_verified_unmerged,
        "product_main_merged_uncredited_events": product_merged_uncredited,
        "workspace_staleness_seconds_at_observation": workspace_staleness_seconds,
        "conversion_population_complete": population_complete,
        "conversion_population_size": population_n,
    }


def compile_metrics(
    state: dict[str, Any],
    tokens: float | None,
    worker_hours: float | None,
    now: str | None = None,
) -> dict[str, Any]:
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
    out.update(compile_conversion_metrics(state, now=now))
    return out


def _apply_conversion_overlay(state: dict[str, Any], overlay: dict[str, Any]) -> None:
    state["conversion_population"] = overlay.get(
        "conversion_population", {"complete": False}
    )
    state["conversion_events"] = overlay.get("conversion_events", [])
    if "head_observation" in overlay:
        state["head_observation"] = overlay["head_observation"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument(
        "--conversion-events",
        type=Path,
        default=None,
        help="Optional measured conversion-window JSON overlay",
    )
    parser.add_argument(
        "--tokens",
        type=float,
        default=None,
        help="Measured generated repo text tokens for the selected window",
    )
    parser.add_argument("--worker-hours", type=float, default=None)
    parser.add_argument(
        "--now",
        default=None,
        help="ISO timestamp for deterministic WIP-age calculation",
    )
    args = parser.parse_args()

    state = json.loads(args.state.read_text())
    if args.conversion_events is not None:
        overlay = json.loads(args.conversion_events.read_text())
        _apply_conversion_overlay(state, overlay)
    errors = validate(state)
    result = {
        "valid": not errors,
        "errors": errors,
        "metrics": compile_metrics(
            state, args.tokens, args.worker_hours, now=args.now
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
