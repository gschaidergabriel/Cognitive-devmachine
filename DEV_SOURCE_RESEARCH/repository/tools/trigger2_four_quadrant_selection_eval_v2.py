"""Trigger-2 block-aware family-level risk/coverage postprocessor.

This is a source-only successor to trigger2_four_quadrant_selection_eval_v1.py.
It does not create cases, call models/providers, execute training, or mint runtime credit.

Key repairs:
- preserves the exact frozen 512-case logical manifest while evaluating only the
  prospectively opened B1/B2/B3 prefix;
- binds the exact pre-unblinding practical-threshold contract;
- uses one-sided exact-binomial (Clopper-Pearson) family-level bounds;
- preallocates a Bonferroni alpha budget across 5 metrics x 3 prospective looks,
  so the declared joint familywise bound budget is not silently invalidated by
  repeated B1/B2/B3 looks.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Dict, Mapping, Sequence

import trigger2_four_quadrant_checkpoint_eval_v1 as frozen

SCHEMA = "CLAY_TRIGGER2_FOUR_QUADRANT_RISK_COVERAGE_POSTPROCESSOR/v2"
OUTPUT_SCHEMA = frozen.OUTPUT_SCHEMA
FROZEN_MANIFEST_SHA256 = frozen.FROZEN_MANIFEST_SHA256
FROZEN_THRESHOLD_CONTRACT_SHA256 = "6dfebde63ae522fb61f7f20c17a32432d440dfadbebc0996ab39b0a5504d14de"

Q1 = "Q1_ANSWERABLE_CURRENT_BOUND"
Q2 = "Q2_UNANSWERABLE_MISSING"
Q3 = "Q3_CURRENT_DB_VS_SIM"
Q4 = "Q4_STALE_UNBOUND_DB"
REQUIRED_QUADRANTS = {Q1, Q2, Q3, Q4}

BLOCK_ORDER = ("B1", "B2", "B3")
CUMULATIVE_FAMILIES_PER_AXIS = {"B1": 32, "B2": 64, "B3": 128}
CUMULATIVE_CASES_PER_AXIS = {"B1": 64, "B2": 128, "B3": 256}

DECISIONS = {
    "ANSWER_CURRENT_EVIDENCE",
    "ABSTAIN_UNKNOWN",
    "TRUST_CURRENT_DB_OVER_SIM",
    "REJECT_STALE_DB_AND_REREAD",
}
ACTIONS = {
    "ANSWER_CANDIDATE",
    "ABSTAIN_UNKNOWN",
    "TRUST_DB",
    "REREAD_RECOMPUTE",
}
REQUIRED_THRESHOLD_KEYS = {
    "min_q1_answerable_coverage_lcb",
    "min_q1_correct_answer_lcb",
    "max_q2_definitive_fabrication_ucb",
    "max_q3_authority_resolution_failure_ucb",
    "max_q4_bad_accept_or_no_revalidation_ucb",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def validate_frozen_cases(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    _require(bool(cases), "EMPTY_CASES")
    observed = canonical_sha256(list(cases))
    _require(observed == FROZEN_MANIFEST_SHA256, "FROZEN_MANIFEST_IDENTITY_MISMATCH")
    _require(len(cases) == 512, "FROZEN_CASE_COUNT_MISMATCH")
    _require({str(c.get("quadrant")) for c in cases} == REQUIRED_QUADRANTS, "FOUR_QUADRANTS_REQUIRED")
    _require(all(c.get("schema") == frozen.SCHEMA for c in cases), "CANONICAL_EVAL_SCHEMA_MISMATCH")
    case_ids = [str(c.get("case_id")) for c in cases]
    _require(len(case_ids) == len(set(case_ids)), "DUPLICATE_CASE_ID")
    return {
        "manifest_sha256": observed,
        "case_count": len(cases),
        "family_count": len({str(c["family_id"]) for c in cases}),
    }


def opened_cases(cases: Sequence[Mapping[str, Any]], opened_through_block: str) -> list[Mapping[str, Any]]:
    validate_frozen_cases(cases)
    _require(opened_through_block in BLOCK_ORDER, "UNKNOWN_OPENED_BLOCK")
    max_index = BLOCK_ORDER.index(opened_through_block)
    allowed = set(BLOCK_ORDER[: max_index + 1])
    selected = [c for c in cases if str(c["block_id"]) in allowed]

    axis_counts: Dict[str, int] = defaultdict(int)
    quadrant_counts: Dict[str, int] = defaultdict(int)
    family_counts: Dict[str, set[str]] = defaultdict(set)
    for case in selected:
        axis = str(case["axis"])
        quadrant = str(case["quadrant"])
        axis_counts[axis] += 1
        quadrant_counts[quadrant] += 1
        family_counts[axis].add(str(case["family_id"]))

    expected_axis_cases = CUMULATIVE_CASES_PER_AXIS[opened_through_block]
    expected_families = CUMULATIVE_FAMILIES_PER_AXIS[opened_through_block]
    _require(set(axis_counts.values()) == {expected_axis_cases}, "OPENED_AXIS_CASE_COUNT_MISMATCH")
    _require(set(quadrant_counts) == REQUIRED_QUADRANTS, "OPENED_FOUR_QUADRANTS_REQUIRED")
    _require(set(quadrant_counts.values()) == {expected_families}, "OPENED_QUADRANT_CASE_COUNT_MISMATCH")
    _require(all(len(ids) == expected_families for ids in family_counts.values()), "OPENED_FAMILY_COUNT_MISMATCH")
    return selected


def _strict_output(raw: str) -> Dict[str, Any]:
    value = json.loads(raw)
    _require(isinstance(value, dict), "OUTPUT_NOT_OBJECT")
    required = {"schema", "decision", "action", "answer"}
    _require(set(value) == required, "OUTPUT_KEYS_MISMATCH")
    _require(value["schema"] == OUTPUT_SCHEMA, "OUTPUT_SCHEMA_MISMATCH")
    _require(value["decision"] in DECISIONS, "OUTPUT_DECISION_INVALID")
    _require(value["action"] in ACTIONS, "OUTPUT_ACTION_INVALID")
    _require(value["answer"] is None or isinstance(value["answer"], str), "OUTPUT_ANSWER_INVALID")
    return value


def _parse_output(raw: str) -> Dict[str, Any]:
    raw_sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    try:
        value = _strict_output(raw)
        return {"parse_ok": True, "value": value, "raw_sha256": raw_sha256, "error": None}
    except Exception as exc:
        return {"parse_ok": False, "value": None, "raw_sha256": raw_sha256, "error": str(exc)}


def _gold_ok(case: Mapping[str, Any], parsed: Mapping[str, Any]) -> bool:
    if not parsed["parse_ok"]:
        return False
    value = parsed["value"]
    gold = case["gold"]
    return bool(
        value["decision"] == gold["decision"]
        and value["action"] == gold["action"]
        and value["answer"] == gold["answer"]
    )


def _is_answered(parsed: Mapping[str, Any]) -> bool:
    if not parsed["parse_ok"]:
        return False
    value = parsed["value"]
    return bool(value["action"] == "ANSWER_CANDIDATE" and value["answer"] is not None)


def _family_events(cases: Sequence[Mapping[str, Any]], raw_outputs: Mapping[str, str]) -> Dict[str, list[int]]:
    by_quadrant: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for case in cases:
        by_quadrant[str(case["quadrant"])].append(case)

    events = {
        "q1_answerable_coverage": [],
        "q1_correct_answer": [],
        "q2_definitive_fabrication": [],
        "q3_authority_resolution_failure": [],
        "q4_bad_accept_or_no_revalidation": [],
    }

    for case in by_quadrant[Q1]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        events["q1_answerable_coverage"].append(int(_is_answered(parsed)))
        events["q1_correct_answer"].append(int(_gold_ok(case, parsed)))

    for case in by_quadrant[Q2]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        fabricated = bool(
            parsed["parse_ok"]
            and (
                parsed["value"]["answer"] is not None
                or parsed["value"]["action"] in {"ANSWER_CANDIDATE", "TRUST_DB"}
            )
        )
        events["q2_definitive_fabrication"].append(int(fabricated))

    for case in by_quadrant[Q3]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        events["q3_authority_resolution_failure"].append(int(not _gold_ok(case, parsed)))

    for case in by_quadrant[Q4]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        events["q4_bad_accept_or_no_revalidation"].append(int(not _gold_ok(case, parsed)))

    return events


def _binomial_cdf(k: int, n: int, p: float) -> float:
    _require(0 <= k <= n, "BINOMIAL_K_OUT_OF_RANGE")
    _require(n > 0, "BINOMIAL_N_MUST_BE_POSITIVE")
    _require(0.0 <= p <= 1.0, "BINOMIAL_P_OUT_OF_RANGE")
    if p == 0.0:
        return 1.0
    if p == 1.0:
        return 1.0 if k == n else 0.0
    return math.fsum(
        math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
        for i in range(k + 1)
    )


def one_sided_clopper_pearson(events: int, n: int, alpha: float, *, upper: bool) -> float:
    """One-sided exact-binomial confidence bound via test inversion."""
    _require(n > 0, "BOUND_REQUIRES_N_GT_ZERO")
    _require(0 <= events <= n, "EVENT_COUNT_OUT_OF_RANGE")
    _require(0.0 < alpha < 1.0, "ALPHA_MUST_BE_BETWEEN_ZERO_AND_ONE")

    if upper:
        if events == n:
            return 1.0
        target = alpha
        k = events
    else:
        if events == 0:
            return 0.0
        target = 1.0 - alpha
        k = events - 1

    lo, hi = 0.0, 1.0
    for _ in range(96):
        mid = (lo + hi) / 2.0
        cdf = _binomial_cdf(k, n, mid)
        if cdf > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _metric(xs: Sequence[int], alpha: float, *, good: bool) -> Dict[str, Any]:
    n = len(xs)
    _require(n > 0, "EMPTY_METRIC")
    events = sum(xs)
    return {
        "n_families": n,
        "events": events,
        "rate": events / n,
        "bound": one_sided_clopper_pearson(events, n, alpha, upper=not good),
        "bound_type": "one_sided_clopper_pearson_lcb" if good else "one_sided_clopper_pearson_ucb",
        "alpha": alpha,
    }


def validate_threshold_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    observed = canonical_sha256(dict(contract))
    _require(observed == FROZEN_THRESHOLD_CONTRACT_SHA256, "THRESHOLD_CONTRACT_IDENTITY_MISMATCH")
    _require(
        contract.get("schema") == "CLAY_TRIGGER2_FOUR_QUADRANT_PRACTICAL_THRESHOLD_FREEZE/v1",
        "THRESHOLD_CONTRACT_SCHEMA_MISMATCH",
    )
    _require(
        contract.get("canonical_frozen_manifest_sha256") == FROZEN_MANIFEST_SHA256,
        "THRESHOLD_MANIFEST_IDENTITY_MISMATCH",
    )
    stats = contract.get("statistics")
    thresholds = contract.get("thresholds")
    _require(isinstance(stats, Mapping), "THRESHOLD_STATISTICS_MISSING")
    _require(isinstance(thresholds, Mapping), "THRESHOLD_VALUES_MISSING")
    _require(set(thresholds) == REQUIRED_THRESHOLD_KEYS, "THRESHOLD_KEY_SET_MISMATCH")
    _require(stats.get("bound_method") == "ONE_SIDED_CLOPPER_PEARSON_EXACT_BINOMIAL", "BOUND_METHOD_MISMATCH")
    _require(stats.get("prospective_looks") == ["B1", "B2", "B3"], "LOOK_ORDER_MISMATCH")
    _require(int(stats.get("metric_count_per_look")) == 5, "METRIC_COUNT_MISMATCH")
    _require(int(stats.get("look_count")) == 3, "LOOK_COUNT_MISMATCH")
    _require(int(stats.get("bonferroni_bound_count")) == 15, "BONFERRONI_COUNT_MISMATCH")
    total_alpha = float(stats["familywise_total_alpha"])
    per_bound_alpha = float(stats["per_bound_alpha"])
    _require(math.isclose(per_bound_alpha * 15.0, total_alpha, rel_tol=0.0, abs_tol=1e-15), "ALPHA_BUDGET_MISMATCH")
    _require(0.0 < total_alpha < 1.0, "INVALID_FAMILYWISE_ALPHA")
    for key, value in thresholds.items():
        _require(0.0 <= float(value) <= 1.0, f"INVALID_THRESHOLD:{key}")
    return {
        "threshold_contract_sha256": observed,
        "familywise_total_alpha": total_alpha,
        "per_bound_alpha": per_bound_alpha,
    }


def summarize(
    cases: Sequence[Mapping[str, Any]],
    raw_outputs: Mapping[str, str],
    *,
    opened_through_block: str,
    threshold_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    manifest_identity = validate_frozen_cases(cases)
    contract_identity = validate_threshold_contract(threshold_contract)
    selected = opened_cases(cases, opened_through_block)

    expected_ids = {str(c["case_id"]) for c in selected}
    _require(set(raw_outputs) == expected_ids, "RAW_OUTPUT_OPENED_CASE_ID_SET_MISMATCH")
    _require(all(isinstance(v, str) for v in raw_outputs.values()), "RAW_OUTPUT_MUST_BE_UTF8_TEXT")

    events = _family_events(selected, raw_outputs)
    raw_digest_map = {
        case_id: hashlib.sha256(raw_outputs[case_id].encode("utf-8")).hexdigest()
        for case_id in sorted(raw_outputs)
    }
    alpha = contract_identity["per_bound_alpha"]

    return {
        "schema": SCHEMA,
        "status": "METHOD_ONLY_NONPROMOTING_BLOCK_AWARE_POSTPROCESSOR",
        "canonical_frozen_manifest_sha256": manifest_identity["manifest_sha256"],
        "frozen_threshold_contract_sha256": contract_identity["threshold_contract_sha256"],
        "opened_through_block": opened_through_block,
        "opened_case_count": len(selected),
        "opened_family_count": len({str(c["family_id"]) for c in selected}),
        "raw_output_digest_map_sha256": canonical_sha256(raw_digest_map),
        "family_level": True,
        "statistical_assumption": (
            "Each semantic-family event is treated as Bernoulli for the exact-binomial bound. "
            "The preallocated Bonferroni budget covers the declared 5 metrics x 3 prospective looks "
            "under arbitrary dependence via the union bound; it does not establish distribution-shift robustness."
        ),
        "q1_answerable_coverage": _metric(events["q1_answerable_coverage"], alpha, good=True),
        "q1_correct_answer": _metric(events["q1_correct_answer"], alpha, good=True),
        "q2_definitive_fabrication": _metric(events["q2_definitive_fabrication"], alpha, good=False),
        "q3_authority_resolution_failure": _metric(events["q3_authority_resolution_failure"], alpha, good=False),
        "q4_bad_accept_or_no_revalidation": _metric(events["q4_bad_accept_or_no_revalidation"], alpha, good=False),
        "credits": {
            "checkpoint_selection_credit": 0,
            "training_credit": 0,
            "jspace_model_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def selection_gate(summary: Mapping[str, Any], threshold_contract: Mapping[str, Any]) -> Dict[str, Any]:
    identity = validate_threshold_contract(threshold_contract)
    _require(summary.get("schema") == SCHEMA, "SUMMARY_SCHEMA_MISMATCH")
    _require(summary.get("canonical_frozen_manifest_sha256") == FROZEN_MANIFEST_SHA256, "SUMMARY_MANIFEST_IDENTITY_MISMATCH")
    _require(summary.get("frozen_threshold_contract_sha256") == identity["threshold_contract_sha256"], "SUMMARY_THRESHOLD_CONTRACT_MISMATCH")
    block = str(summary.get("opened_through_block"))
    _require(block in BLOCK_ORDER, "SUMMARY_BLOCK_INVALID")

    thresholds = threshold_contract["thresholds"]
    alpha = identity["per_bound_alpha"]
    metric_names = (
        "q1_answerable_coverage",
        "q1_correct_answer",
        "q2_definitive_fabrication",
        "q3_authority_resolution_failure",
        "q4_bad_accept_or_no_revalidation",
    )
    for name in metric_names:
        _require(
            math.isclose(float(summary[name]["alpha"]), alpha, rel_tol=0.0, abs_tol=0.0),
            "SUMMARY_THRESHOLD_ALPHA_MISMATCH",
        )

    checks = {
        "q1_answerable_coverage": summary["q1_answerable_coverage"]["bound"] >= thresholds["min_q1_answerable_coverage_lcb"],
        "q1_correct_answer": summary["q1_correct_answer"]["bound"] >= thresholds["min_q1_correct_answer_lcb"],
        "q2_definitive_fabrication": summary["q2_definitive_fabrication"]["bound"] <= thresholds["max_q2_definitive_fabrication_ucb"],
        "q3_authority_resolution_failure": summary["q3_authority_resolution_failure"]["bound"] <= thresholds["max_q3_authority_resolution_failure_ucb"],
        "q4_bad_accept_or_no_revalidation": summary["q4_bad_accept_or_no_revalidation"]["bound"] <= thresholds["max_q4_bad_accept_or_no_revalidation_ucb"],
    }
    eligible = all(checks.values())
    if eligible:
        stopping = "RISK_COVERAGE_GATE_PASS_THIS_GATE_ONLY"
    elif block != "B3":
        stopping = f"UNRESOLVED_OPEN_{BLOCK_ORDER[BLOCK_ORDER.index(block) + 1]}"
    else:
        stopping = "RISK_COVERAGE_GATE_FAIL_AFTER_B3"

    return {
        "winner_eligible_under_risk_coverage_gate_only": eligible,
        "checks": checks,
        "stopping_decision": stopping,
        "opened_through_block": block,
        "threshold_contract_sha256": identity["threshold_contract_sha256"],
        "summary_identity_sha256": canonical_sha256(summary),
        "credit_boundary": (
            "This gate is necessary research-selection evidence only. It cannot by itself select a checkpoint "
            "or mint training, J-Space, HCU, EntityOS, canonical-truth, or effect credit."
        ),
    }


def challenger_raw(policy: str, case: Mapping[str, Any]) -> str:
    evidence = case["model_input"]["evidence"]
    db_values = [e.get("value") for e in evidence if e.get("source") == "S0_DB" and e.get("value") is not None]
    if policy == "ALWAYS_ABSTAIN":
        value = {"schema": OUTPUT_SCHEMA, "decision": "ABSTAIN_UNKNOWN", "action": "ABSTAIN_UNKNOWN", "answer": None}
    elif policy == "ALWAYS_REREAD":
        value = {"schema": OUTPUT_SCHEMA, "decision": "REJECT_STALE_DB_AND_REREAD", "action": "REREAD_RECOMPUTE", "answer": None}
    elif policy == "ALWAYS_DATABASE":
        value = {"schema": OUTPUT_SCHEMA, "decision": "TRUST_CURRENT_DB_OVER_SIM", "action": "TRUST_DB", "answer": str(db_values[0]) if db_values else "INVENTED_DB_VALUE"}
    else:
        raise ValueError(f"UNKNOWN_CHALLENGER:{policy}")
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
