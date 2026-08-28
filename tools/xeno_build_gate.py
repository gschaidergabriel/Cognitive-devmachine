#!/usr/bin/env python3
"""Deterministic anti-Goodhart Xeno recursive-improvement promotion gate.

Promotion compares two bound executable benchmark receipts, not free-form metric JSON.
The gate preserves the epsilon-Pareto/cross-group anti-Goodhart rule while binding
baseline and candidate measurements to exact source, benchmark, runner, environment,
metric-contract and harness-contract identities.

Receipt integrity is a deterministic provenance boundary, not proof that the benchmark
runner itself is trustworthy. Runtime promotion still requires an admitted executable
benchmark surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HARNESS_CONTRACT = ROOT / "the artefact/Xeno/XENO_HARNESS_V1_ACCEPTANCE_CONTRACT.md"
SCHEMA = "XENO_PROMOTION_GATE/v2"
RECEIPT_SCHEMA = "XENO_BENCHMARK_RECEIPT/v1"
EVIDENCE_CLASS = "EXECUTABLE_BENCHMARK_RECEIPT"
HEX = frozenset("0123456789abcdef")

METRICS: dict[str, int] = {
    "capability_pass_rate": +1, "task_quality_score": +1, "p50_latency_ms": -1,
    "p95_latency_ms": -1, "throughput_tokens_s": +1, "rss_mb": -1,
    "recovery_pass_rate": +1, "authority_boundary_pass_rate": +1,
    "token_efficiency_score": +1, "claycode_fraction": +1,
    "engine_swap_pass_rate": +1, "two_slot_harness_pass_rate": +1,
    "prestage_pipeline_pass_rate": +1, "grid10_pass_rate": +1,
    "peer_link_pass_rate": +1, "dashboard_config_pass_rate": +1,
    "jspace_causal_gain_score": +1,
}

HARD_NO_REGRESSION = {
    "recovery_pass_rate", "authority_boundary_pass_rate", "engine_swap_pass_rate",
    "two_slot_harness_pass_rate", "prestage_pipeline_pass_rate", "grid10_pass_rate",
    "peer_link_pass_rate", "dashboard_config_pass_rate",
}

ABS_PROGRESS_FLOOR: dict[str, float] = {
    "capability_pass_rate": 0.002, "task_quality_score": 0.002,
    "p50_latency_ms": 0.5, "p95_latency_ms": 0.5,
    "throughput_tokens_s": 0.2, "rss_mb": 5.0,
    "recovery_pass_rate": 0.001, "authority_boundary_pass_rate": 0.001,
    "token_efficiency_score": 0.002, "claycode_fraction": 0.002,
    "engine_swap_pass_rate": 0.001, "two_slot_harness_pass_rate": 0.001,
    "prestage_pipeline_pass_rate": 0.001, "grid10_pass_rate": 0.001,
    "peer_link_pass_rate": 0.001, "dashboard_config_pass_rate": 0.001,
    "jspace_causal_gain_score": 0.002,
}
REL_PROGRESS_FLOOR = 0.005

PROGRESS_GROUPS: dict[str, set[str]] = {
    "capability_quality": {"capability_pass_rate", "task_quality_score"},
    "efficiency": {"p50_latency_ms", "p95_latency_ms", "throughput_tokens_s", "rss_mb", "token_efficiency_score"},
    "architecture_cognition": {"claycode_fraction", "grid10_pass_rate", "jspace_causal_gain_score"},
    "robustness_authority": {
        "recovery_pass_rate", "authority_boundary_pass_rate", "engine_swap_pass_rate",
        "two_slot_harness_pass_rate", "prestage_pipeline_pass_rate", "peer_link_pass_rate",
        "dashboard_config_pass_rate",
    },
}
CORE_PROGRESS_GROUPS = {"capability_quality", "efficiency", "architecture_cognition"}
MIN_PROGRESS_GROUPS = 2


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def _is_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(ch in HEX for ch in value.lower())


def canonical_sha256(obj: Any) -> str:
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def metric_contract_sha256() -> str:
    return canonical_sha256({
        "schema": SCHEMA,
        "metrics": METRICS,
        "hard_no_regression": sorted(HARD_NO_REGRESSION),
        "abs_progress_floor": ABS_PROGRESS_FLOOR,
        "rel_progress_floor": REL_PROGRESS_FLOOR,
        "progress_groups": {k: sorted(v) for k, v in PROGRESS_GROUPS.items()},
        "core_progress_groups": sorted(CORE_PROGRESS_GROUPS),
        "minimum_progress_groups": MIN_PROGRESS_GROUPS,
    })


def harness_contract_sha256() -> str:
    return hashlib.sha256(HARNESS_CONTRACT.read_bytes()).hexdigest()


def load_metrics_object(obj: Any) -> dict[str, float]:
    _require(isinstance(obj, dict), "METRICS_PAYLOAD_NOT_OBJECT")
    _require(set(obj) == set(METRICS), "METRIC_SET_MISMATCH")
    out: dict[str, float] = {}
    for name in METRICS:
        value = obj.get(name)
        _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"MISSING_OR_NONNUMERIC:{name}")
        value = float(value)
        _require(math.isfinite(value), f"NONFINITE:{name}")
        out[name] = value
    return out


def load_bound_receipt(path: Path, *, expected_role: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), "RECEIPT_NOT_OBJECT")
    _require(raw.get("schema") == RECEIPT_SCHEMA, "RECEIPT_SCHEMA_MISMATCH")
    _require(raw.get("status") == "PASS", "RECEIPT_STATUS_NOT_PASS")
    _require(raw.get("evidence_class") == EVIDENCE_CLASS, "RECEIPT_EVIDENCE_CLASS_MISMATCH")
    _require(raw.get("promotion_eligible") is True, "RECEIPT_NOT_PROMOTION_ELIGIBLE")
    _require(raw.get("model_generated") is False, "MODEL_GENERATED_RECEIPT_FORBIDDEN")
    _require(raw.get("role") == expected_role, f"RECEIPT_ROLE_EXPECTED_{expected_role}")
    for field in ("measurement_id", "candidate_id", "benchmark_suite_id", "environment_id", "runner_identity"):
        _require(isinstance(raw.get(field), str) and raw[field].strip(), f"MISSING:{field}")
    _require(_is_hex(raw.get("source_commit"), 40), "SOURCE_COMMIT_INVALID")
    _require(_is_hex(raw.get("source_tree"), 40), "SOURCE_TREE_INVALID")
    _require(_is_hex(raw.get("benchmark_command_digest"), 64), "BENCHMARK_COMMAND_DIGEST_INVALID")
    _require(_is_hex(raw.get("metric_contract_sha256"), 64), "METRIC_CONTRACT_DIGEST_INVALID")
    _require(_is_hex(raw.get("harness_contract_sha256"), 64), "HARNESS_CONTRACT_DIGEST_INVALID")
    _require(_is_hex(raw.get("result_digest"), 64), "RESULT_DIGEST_INVALID")
    _require(raw["metric_contract_sha256"] == metric_contract_sha256(), "METRIC_CONTRACT_DIGEST_MISMATCH")
    _require(raw["harness_contract_sha256"] == harness_contract_sha256(), "HARNESS_CONTRACT_DIGEST_MISMATCH")
    if expected_role == "BASELINE":
        _require(raw.get("baseline_measurement_id") in {None, ""}, "BASELINE_MUST_NOT_BIND_BASELINE")
        _require(raw.get("baseline_source_commit") in {None, ""}, "BASELINE_MUST_NOT_BIND_PARENT")
    else:
        _require(isinstance(raw.get("baseline_measurement_id"), str) and raw["baseline_measurement_id"].strip(), "CANDIDATE_BASELINE_MEASUREMENT_ID_MISSING")
        _require(_is_hex(raw.get("baseline_source_commit"), 40), "CANDIDATE_BASELINE_SOURCE_INVALID")
    metrics = load_metrics_object(raw.get("metrics"))
    digest_payload = dict(raw)
    claimed = digest_payload.pop("result_digest")
    _require(claimed == canonical_sha256(digest_payload), "RESULT_DIGEST_MISMATCH")
    return {**raw, "metrics": metrics}


def validate_pair(before: dict[str, Any], after: dict[str, Any]) -> None:
    _require(before["role"] == "BASELINE", "BEFORE_NOT_BASELINE")
    _require(after["role"] == "CANDIDATE", "AFTER_NOT_CANDIDATE")
    _require(before["measurement_id"] != after["measurement_id"], "MEASUREMENT_ID_REUSED")
    _require(before["candidate_id"] != after["candidate_id"], "CANDIDATE_ID_REUSED")
    _require(after["baseline_measurement_id"] == before["measurement_id"], "CANDIDATE_BASELINE_MEASUREMENT_MISMATCH")
    _require(after["baseline_source_commit"] == before["source_commit"], "CANDIDATE_BASELINE_SOURCE_MISMATCH")
    for field in ("benchmark_suite_id", "environment_id", "runner_identity", "benchmark_command_digest", "metric_contract_sha256", "harness_contract_sha256"):
        _require(before[field] == after[field], f"PAIR_BINDING_MISMATCH:{field}")
    _require(before["source_commit"] != after["source_commit"], "CANDIDATE_SOURCE_COMMIT_MUST_DIFFER")


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
            "before": before[name], "after": after[name], "raw_delta": after[name] - before[name],
            "direction": "HIGHER_IS_BETTER" if direction > 0 else "LOWER_IS_BETTER",
            "meaningful_change_threshold": threshold, "hard_no_regression": name in HARD_NO_REGRESSION,
            "relation": rel,
        }
        if rel == "REGRESSED": regressions.append(name)
        elif rel == "STABLE": stable.append(name)
        else: improved.append(name)
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
        "schema": SCHEMA, "mode": mode, "promotion_pass": passed,
        "candidate_action": "PROMOTE" if passed else "REJECT_OR_REWORK",
        "regressions": regressions, "stable_metrics": stable, "improved_metrics": improved,
        "improved_groups": improved_groups, "minimum_progress_groups": MIN_PROGRESS_GROUPS,
        "core_progress_required": True, "core_progress_observed": core_progress,
        "claycode_progress_required": claycode_migration, "claycode_progress_observed": claycode_progress,
        "metrics": rows,
        "anti_goodhart_boundary": "tiny/noisy deltas do not count; cross-group progress required; protected regressions reject; no single scalar can self-promote",
        "epistemic_boundary": "BOUND_EXECUTABLE_BENCHMARK_RECEIPTS_ONLY; receipt integrity alone does not prove runner trust or whole-product acceptance",
    }


def evaluate_receipts(before_receipt: dict[str, Any], after_receipt: dict[str, Any], *, claycode_migration: bool) -> dict[str, Any]:
    validate_pair(before_receipt, after_receipt)
    result = evaluate(before_receipt["metrics"], after_receipt["metrics"], claycode_migration=claycode_migration)
    result["evidence_binding"] = {
        "before_measurement_id": before_receipt["measurement_id"], "after_measurement_id": after_receipt["measurement_id"],
        "before_source_commit": before_receipt["source_commit"], "after_source_commit": after_receipt["source_commit"],
        "benchmark_suite_id": before_receipt["benchmark_suite_id"], "environment_id": before_receipt["environment_id"],
        "runner_identity": before_receipt["runner_identity"], "benchmark_command_digest": before_receipt["benchmark_command_digest"],
        "metric_contract_sha256": before_receipt["metric_contract_sha256"], "harness_contract_sha256": before_receipt["harness_contract_sha256"],
        "before_result_digest": before_receipt["result_digest"], "after_result_digest": after_receipt["result_digest"],
    }
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True, help="baseline XENO_BENCHMARK_RECEIPT/v1")
    p.add_argument("--after", type=Path, required=True, help="candidate XENO_BENCHMARK_RECEIPT/v1")
    p.add_argument("--claycode-migration", action="store_true")
    p.add_argument("--output", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        before = load_bound_receipt(args.before, expected_role="BASELINE")
        after = load_bound_receipt(args.after, expected_role="CANDIDATE")
        result = evaluate_receipts(before, after, claycode_migration=args.claycode_migration)
    except Exception as exc:
        result = {"schema": SCHEMA, "promotion_pass": False, "candidate_action": "REJECT_OR_REWORK", "error": f"{type(exc).__name__}:{exc}"}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("promotion_pass") else 1

if __name__ == "__main__":
    raise SystemExit(main())
