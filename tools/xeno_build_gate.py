#!/usr/bin/env python3
"""Deterministic anti-Goodhart Xeno recursive-improvement promotion gate.

The gate compares two externally measured metric snapshots. Model output cannot
self-promote a candidate. Missing/non-finite metrics fail closed. Promotion uses
an epsilon-Pareto rule: no protected metric may meaningfully regress, tiny/noisy
changes do not count as progress, and a candidate must improve multiple independent
metric groups. ClayCode migration additionally requires meaningful ClayCode progress.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "XENO_PROMOTION_GATE/v2"

# direction: +1 => higher is better, -1 => lower is better
METRICS: dict[str, int] = {
    "capability_pass_rate": +1,
    "task_quality_score": +1,
    "p50_latency_ms": -1,
    "p95_latency_ms": -1,
    "throughput_tokens_s": +1,
    "rss_mb": -1,
    "recovery_pass_rate": +1,
    "authority_boundary_pass_rate": +1,
    "token_efficiency_score": +1,
    "claycode_fraction": +1,
    "engine_swap_pass_rate": +1,
    "two_slot_harness_pass_rate": +1,
    "prestage_pipeline_pass_rate": +1,
    "grid10_pass_rate": +1,
    "peer_link_pass_rate": +1,
    "dashboard_config_pass_rate": +1,
    "jspace_causal_gain_score": +1,
}

# Deterministic correctness-style pass rates are hard fences: any directional
# regression is a regression. Other metrics use practical-significance floors so
# benchmark jitter cannot manufacture either progress or failure.
HARD_NO_REGRESSION = {
    "recovery_pass_rate",
    "authority_boundary_pass_rate",
    "engine_swap_pass_rate",
    "two_slot_harness_pass_rate",
    "prestage_pipeline_pass_rate",
    "grid10_pass_rate",
    "peer_link_pass_rate",
    "dashboard_config_pass_rate",
}

ABS_PROGRESS_FLOOR: dict[str, float] = {
    "capability_pass_rate": 0.002,
    "task_quality_score": 0.002,
    "p50_latency_ms": 0.5,
    "p95_latency_ms": 0.5,
    "throughput_tokens_s": 0.2,
    "rss_mb": 5.0,
    "recovery_pass_rate": 0.001,
    "authority_boundary_pass_rate": 0.001,
    "token_efficiency_score": 0.002,
    "claycode_fraction": 0.002,
    "engine_swap_pass_rate": 0.001,
    "two_slot_harness_pass_rate": 0.001,
    "prestage_pipeline_pass_rate": 0.001,
    "grid10_pass_rate": 0.001,
    "peer_link_pass_rate": 0.001,
    "dashboard_config_pass_rate": 0.001,
    "jspace_causal_gain_score": 0.002,
}
REL_PROGRESS_FLOOR = 0.005

PROGRESS_GROUPS: dict[str, set[str]] = {
    "capability_quality": {"capability_pass_rate", "task_quality_score"},
    "efficiency": {"p50_latency_ms", "p95_latency_ms", "throughput_tokens_s", "rss_mb", "token_efficiency_score"},
    "architecture_cognition": {"claycode_fraction", "grid10_pass_rate", "jspace_causal_gain_score"},
    "robustness_authority": {
        "recovery_pass_rate",
        "authority_boundary_pass_rate",
        "engine_swap_pass_rate",
        "two_slot_harness_pass_rate",
        "prestage_pipeline_pass_rate",
        "peer_link_pass_rate",
        "dashboard_config_pass_rate",
    },
}
CORE_PROGRESS_GROUPS = {"capability_quality", "efficiency", "architecture_cognition"}
MIN_PROGRESS_GROUPS = 2


def load_metrics(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("METRICS_NOT_OBJECT")
    obj = raw.get("metrics", raw)
    if not isinstance(obj, dict):
        raise ValueError("METRICS_PAYLOAD_NOT_OBJECT")
    out: dict[str, float] = {}
    for name in METRICS:
        value = obj.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"MISSING_OR_NONNUMERIC:{name}")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"NONFINITE:{name}")
        out[name] = value
    return out


def progress_threshold(name: str, before: float) -> float:
    return max(ABS_PROGRESS_FLOOR[name], abs(before) * REL_PROGRESS_FLOOR)


def relation(name: str, before: float, after: float, direction: int) -> tuple[str, float]:
    signed_delta = direction * (after - before)
    threshold = progress_threshold(name, before)
    if signed_delta > threshold:
        return "IMPROVED", threshold
    regression_threshold = 0.0 if name in HARD_NO_REGRESSION else threshold
    if signed_delta < -regression_threshold:
        return "REGRESSED", threshold
    return "STABLE", threshold


def evaluate(before: dict[str, float], after: dict[str, float], *, claycode_migration: bool) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    regressions: list[str] = []
    stable: list[str] = []
    improved: list[str] = []
    for name, direction in METRICS.items():
        rel, threshold = relation(name, before[name], after[name], direction)
        rows[name] = {
            "before": before[name],
            "after": after[name],
            "raw_delta": after[name] - before[name],
            "direction": "HIGHER_IS_BETTER" if direction > 0 else "LOWER_IS_BETTER",
            "meaningful_change_threshold": threshold,
            "hard_no_regression": name in HARD_NO_REGRESSION,
            "relation": rel,
        }
        if rel == "REGRESSED":
            regressions.append(name)
        elif rel == "STABLE":
            stable.append(name)
        else:
            improved.append(name)

    improved_set = set(improved)
    improved_groups = sorted(name for name, members in PROGRESS_GROUPS.items() if members & improved_set)
    core_progress = bool(CORE_PROGRESS_GROUPS & set(improved_groups))
    enough_groups = len(improved_groups) >= MIN_PROGRESS_GROUPS
    no_regression = not regressions
    claycode_progress = "claycode_fraction" in improved_set

    if claycode_migration:
        passed = no_regression and enough_groups and core_progress and claycode_progress
        mode = "CLAYCODE_EPSILON_PARETO_CROSS_GROUP"
    else:
        passed = no_regression and enough_groups and core_progress
        mode = "RECURSIVE_EPSILON_PARETO_CROSS_GROUP"

    return {
        "schema": SCHEMA,
        "mode": mode,
        "promotion_pass": passed,
        "candidate_action": "PROMOTE" if passed else "REJECT_OR_REWORK",
        "regressions": regressions,
        "stable_metrics": stable,
        "improved_metrics": improved,
        "improved_groups": improved_groups,
        "minimum_progress_groups": MIN_PROGRESS_GROUPS,
        "core_progress_required": True,
        "core_progress_observed": core_progress,
        "claycode_progress_required": claycode_migration,
        "claycode_progress_observed": claycode_progress,
        "metrics": rows,
        "anti_goodhart_boundary": "tiny/noisy deltas do not count; cross-group progress required; protected regressions reject; no single scalar can self-promote",
        "epistemic_boundary": "COMPARISON_ONLY; input measurements must come from bound executable benchmark receipts and composite scores must not be model self-report",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--claycode-migration", action="store_true")
    p.add_argument("--output", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        before = load_metrics(args.before)
        after = load_metrics(args.after)
        result = evaluate(before, after, claycode_migration=args.claycode_migration)
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "promotion_pass": False,
            "candidate_action": "REJECT_OR_REWORK",
            "error": f"{type(exc).__name__}:{exc}",
        }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("promotion_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
