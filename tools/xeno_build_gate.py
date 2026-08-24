#!/usr/bin/env python3
"""Deterministic Xeno recursive-improvement promotion gate.

The gate compares two externally measured metric snapshots. Model output cannot
self-promote a candidate. Missing/non-finite metrics fail closed. Normal recursive
promotion requires no regression on every protected metric and strict progress on
all required-progress metrics. A ClayCode migration is stricter: every metric in
its frozen comparison vector must improve in the configured direction.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "XENO_PROMOTION_GATE/v1"

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

REQUIRED_PROGRESS = {
    "capability_pass_rate",
    "task_quality_score",
    "p50_latency_ms",
    "throughput_tokens_s",
    "claycode_fraction",
    "jspace_causal_gain_score",
}


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


def relation(before: float, after: float, direction: int, tolerance: float) -> str:
    signed_delta = direction * (after - before)
    if signed_delta > tolerance:
        return "IMPROVED"
    if signed_delta < -tolerance:
        return "REGRESSED"
    return "EQUAL"


def evaluate(before: dict[str, float], after: dict[str, float], *, claycode_migration: bool,
             tolerance: float = 1e-12) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    regressions: list[str] = []
    equal: list[str] = []
    improved: list[str] = []
    for name, direction in METRICS.items():
        rel = relation(before[name], after[name], direction, tolerance)
        rows[name] = {
            "before": before[name],
            "after": after[name],
            "raw_delta": after[name] - before[name],
            "direction": "HIGHER_IS_BETTER" if direction > 0 else "LOWER_IS_BETTER",
            "relation": rel,
        }
        if rel == "REGRESSED":
            regressions.append(name)
        elif rel == "EQUAL":
            equal.append(name)
        else:
            improved.append(name)

    no_regression = not regressions
    required_progress_ok = REQUIRED_PROGRESS.issubset(improved)
    strict_all_metric_dominance = len(improved) == len(METRICS)

    if claycode_migration:
        passed = strict_all_metric_dominance
        mode = "CLAYCODE_STRICT_ALL_METRIC_DOMINANCE"
    else:
        passed = no_regression and required_progress_ok
        mode = "RECURSIVE_NO_REGRESSION_PLUS_REQUIRED_PROGRESS"

    return {
        "schema": SCHEMA,
        "mode": mode,
        "promotion_pass": passed,
        "candidate_action": "PROMOTE" if passed else "REJECT_OR_REWORK",
        "regressions": regressions,
        "equal_metrics": equal,
        "improved_metrics": improved,
        "required_progress_metrics": sorted(REQUIRED_PROGRESS),
        "strict_all_metric_dominance": strict_all_metric_dominance,
        "metrics": rows,
        "epistemic_boundary": "COMPARISON_ONLY; input measurements must come from bound executable benchmark receipts",
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
