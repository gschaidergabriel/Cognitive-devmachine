"""Trigger-2 family-level risk/coverage post-processor for the canonical frozen four-quadrant eval.

This is deliberately subordinate to tools/trigger2_four_quadrant_checkpoint_eval_v1.py.
It creates no cases, changes no frozen labels, and performs no model/provider/runtime/training
execution. It accepts only the exact frozen v1 manifest identity and raw outputs from a future
separately-authorized run, then computes family-level risk/coverage bounds.

The statistical bound is a method-level decision aid, not canonical EntityOS truth and not
checkpoint/training/J-Space/HCU/product credit.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Dict, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER2_FOUR_QUADRANT_RISK_COVERAGE_POSTPROCESSOR/v1"
CANONICAL_EVAL_SCHEMA = "CLAY_TRIGGER2_FOUR_QUADRANT_CHECKPOINT_EVAL/v1"
OUTPUT_SCHEMA = "XENO_EVAL_DECISION/v1"
FROZEN_MANIFEST_SHA256 = "9e9a2a421cdaa9207783060b6b127fa4ca26bf25d9415b22730812f31229d57d"

Q1 = "Q1_ANSWERABLE_CURRENT_BOUND"
Q2 = "Q2_UNANSWERABLE_MISSING"
Q3 = "Q3_CURRENT_DB_VS_SIM"
Q4 = "Q4_STALE_UNBOUND_DB"
REQUIRED_QUADRANTS = {Q1, Q2, Q3, Q4}
BLOCK_ORDER = ("B1", "B2", "B3")
CUMULATIVE_BLOCK_SHAPE = {
    "B1": {"case_count": 128, "family_count": 64, "families_per_quadrant": 32},
    "B2": {"case_count": 256, "family_count": 128, "families_per_quadrant": 64},
    "B3": {"case_count": 512, "family_count": 256, "families_per_quadrant": 128},
}

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
    "delta",
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

    case_ids = [str(c.get("case_id")) for c in cases]
    _require(len(case_ids) == len(set(case_ids)), "DUPLICATE_CASE_ID")
    _require({str(c.get("quadrant")) for c in cases} == REQUIRED_QUADRANTS, "FOUR_QUADRANTS_REQUIRED")
    _require(all(c.get("schema") == CANONICAL_EVAL_SCHEMA for c in cases), "CANONICAL_EVAL_SCHEMA_MISMATCH")

    family_rows: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for case in cases:
        family_rows[str(case["family_id"])].append(case)
    _require(len(family_rows) == 256, "FROZEN_FAMILY_COUNT_MISMATCH")
    for family_id, rows in family_rows.items():
        _require(len(rows) == 2, f"FAMILY_PAIR_COUNT_MISMATCH:{family_id}")
        quadrants = {str(r["quadrant"]) for r in rows}
        _require(quadrants in ({Q1, Q2}, {Q3, Q4}), f"FAMILY_PAIR_QUADRANT_MISMATCH:{family_id}")

    return {
        "manifest_sha256": observed,
        "case_count": len(cases),
        "family_count": len(family_rows),
    }


def cumulative_cases(
    cases: Sequence[Mapping[str, Any]],
    cumulative_block: str,
) -> Dict[str, Any]:
    identity = validate_frozen_cases(cases)
    _require(cumulative_block in BLOCK_ORDER, "INVALID_CUMULATIVE_BLOCK")
    stop = BLOCK_ORDER.index(cumulative_block) + 1
    opened_blocks = BLOCK_ORDER[:stop]
    active = [c for c in cases if str(c.get("block_id")) in opened_blocks]
    shape = CUMULATIVE_BLOCK_SHAPE[cumulative_block]

    _require(len(active) == shape["case_count"], "CUMULATIVE_BLOCK_CASE_COUNT_MISMATCH")
    family_count = len({str(c["family_id"]) for c in active})
    _require(family_count == shape["family_count"], "CUMULATIVE_BLOCK_FAMILY_COUNT_MISMATCH")

    quadrant_counts: Dict[str, int] = defaultdict(int)
    for case in active:
        quadrant_counts[str(case["quadrant"])] += 1
    _require(set(quadrant_counts) == REQUIRED_QUADRANTS, "CUMULATIVE_BLOCK_FOUR_QUADRANTS_REQUIRED")
    _require(
        all(quadrant_counts[q] == shape["families_per_quadrant"] for q in REQUIRED_QUADRANTS),
        "CUMULATIVE_BLOCK_QUADRANT_COUNT_MISMATCH",
    )

    return {
        "identity": identity,
        "cumulative_block": cumulative_block,
        "opened_blocks": list(opened_blocks),
        "cases": active,
        "case_count": len(active),
        "family_count": family_count,
        "families_per_quadrant": shape["families_per_quadrant"],
    }


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
    return bool(value["decision"] == gold["decision"] and value["action"] == gold["action"] and value["answer"] == gold["answer"])


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
        fabricated = bool(parsed["parse_ok"] and (parsed["value"]["answer"] is not None or parsed["value"]["action"] in {"ANSWER_CANDIDATE", "TRUST_DB"}))
        events["q2_definitive_fabrication"].append(int(fabricated))

    for case in by_quadrant[Q3]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        events["q3_authority_resolution_failure"].append(int(not _gold_ok(case, parsed)))

    for case in by_quadrant[Q4]:
        parsed = _parse_output(raw_outputs[str(case["case_id"])])
        events["q4_bad_accept_or_no_revalidation"].append(int(not _gold_ok(case, parsed)))

    return events


def one_sided_hoeffding_bound(events: int, n: int, delta: float, *, upper: bool) -> float:
    _require(n > 0, "BOUND_REQUIRES_N_GT_ZERO")
    _require(0.0 < delta < 1.0, "DELTA_MUST_BE_BETWEEN_ZERO_AND_ONE")
    p = events / n
    radius = math.sqrt(math.log(1.0 / delta) / (2.0 * n))
    return min(1.0, p + radius) if upper else max(0.0, p - radius)


def _metric(xs: Sequence[int], delta: float, *, good: bool) -> Dict[str, Any]:
    n = len(xs)
    _require(n > 0, "EMPTY_METRIC")
    events = sum(xs)
    return {
        "n_families": n,
        "events": events,
        "rate": events / n,
        "bound": one_sided_hoeffding_bound(events, n, delta, upper=not good),
        "bound_type": "one_sided_hoeffding_lcb" if good else "one_sided_hoeffding_ucb",
        "delta": delta,
    }


def summarize(
    cases: Sequence[Mapping[str, Any]],
    raw_outputs: Mapping[str, str],
    *,
    delta: float = 0.05,
    cumulative_block: str = "B3",
) -> Dict[str, Any]:
    scope = cumulative_cases(cases, cumulative_block)
    active_cases = scope["cases"]
    expected_ids = {str(c["case_id"]) for c in active_cases}
    _require(set(raw_outputs) == expected_ids, "RAW_OUTPUT_CASE_ID_SET_MISMATCH")
    _require(all(isinstance(v, str) for v in raw_outputs.values()), "RAW_OUTPUT_MUST_BE_UTF8_TEXT")

    events = _family_events(active_cases, raw_outputs)
    raw_digest_map = {case_id: hashlib.sha256(raw_outputs[case_id].encode("utf-8")).hexdigest() for case_id in sorted(raw_outputs)}

    return {
        "schema": SCHEMA,
        "status": "METHOD_ONLY_NONPROMOTING_POSTPROCESSOR",
        "canonical_frozen_manifest_sha256": scope["identity"]["manifest_sha256"],
        "cumulative_block": scope["cumulative_block"],
        "opened_blocks": scope["opened_blocks"],
        "evaluated_case_count": scope["case_count"],
        "evaluated_family_count": scope["family_count"],
        "raw_output_digest_map_sha256": canonical_sha256(raw_digest_map),
        "family_level": True,
        "statistical_assumption": "Hoeffding bound treats semantic-family outcomes as exchangeable/independent enough for this method-level gate; violation invalidates the bound but not the raw counts.",
        "q1_answerable_coverage": _metric(events["q1_answerable_coverage"], delta, good=True),
        "q1_correct_answer": _metric(events["q1_correct_answer"], delta, good=True),
        "q2_definitive_fabrication": _metric(events["q2_definitive_fabrication"], delta, good=False),
        "q3_authority_resolution_failure": _metric(events["q3_authority_resolution_failure"], delta, good=False),
        "q4_bad_accept_or_no_revalidation": _metric(events["q4_bad_accept_or_no_revalidation"], delta, good=False),
        "credits": {
            "checkpoint_selection_credit": 0,
            "training_credit": 0,
            "jspace_model_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def _threshold_checks(summary: Mapping[str, Any], thresholds: Mapping[str, Any]) -> Dict[str, bool]:
    return {
        "q1_answerable_coverage": summary["q1_answerable_coverage"]["bound"] >= float(thresholds["min_q1_answerable_coverage_lcb"]),
        "q1_correct_answer": summary["q1_correct_answer"]["bound"] >= float(thresholds["min_q1_correct_answer_lcb"]),
        "q2_definitive_fabrication": summary["q2_definitive_fabrication"]["bound"] <= float(thresholds["max_q2_definitive_fabrication_ucb"]),
        "q3_authority_resolution_failure": summary["q3_authority_resolution_failure"]["bound"] <= float(thresholds["max_q3_authority_resolution_failure_ucb"]),
        "q4_bad_accept_or_no_revalidation": summary["q4_bad_accept_or_no_revalidation"]["bound"] <= float(thresholds["max_q4_bad_accept_or_no_revalidation_ucb"]),
    }


def _point_estimate_checks(summary: Mapping[str, Any], thresholds: Mapping[str, Any]) -> Dict[str, bool]:
    return {
        "q1_answerable_coverage": summary["q1_answerable_coverage"]["rate"] >= float(thresholds["min_q1_answerable_coverage_lcb"]),
        "q1_correct_answer": summary["q1_correct_answer"]["rate"] >= float(thresholds["min_q1_correct_answer_lcb"]),
        "q2_definitive_fabrication": summary["q2_definitive_fabrication"]["rate"] <= float(thresholds["max_q2_definitive_fabrication_ucb"]),
        "q3_authority_resolution_failure": summary["q3_authority_resolution_failure"]["rate"] <= float(thresholds["max_q3_authority_resolution_failure_ucb"]),
        "q4_bad_accept_or_no_revalidation": summary["q4_bad_accept_or_no_revalidation"]["rate"] <= float(thresholds["max_q4_bad_accept_or_no_revalidation_ucb"]),
    }


def _validate_threshold_contract(summary: Mapping[str, Any], thresholds: Mapping[str, Any] | None) -> None:
    _require(thresholds is not None, "UNFROZEN_THRESHOLDS")
    missing = sorted(REQUIRED_THRESHOLD_KEYS.difference(thresholds))
    _require(not missing, f"MISSING_THRESHOLD_FIELDS:{','.join(missing)}")
    _require(summary.get("schema") == SCHEMA, "SUMMARY_SCHEMA_MISMATCH")
    _require(summary.get("canonical_frozen_manifest_sha256") == FROZEN_MANIFEST_SHA256, "SUMMARY_MANIFEST_IDENTITY_MISMATCH")

    delta = float(thresholds["delta"])
    _require(0.0 < delta < 1.0, "INVALID_THRESHOLD_DELTA")
    metric_names = ("q1_answerable_coverage", "q1_correct_answer", "q2_definitive_fabrication", "q3_authority_resolution_failure", "q4_bad_accept_or_no_revalidation")
    for name in metric_names:
        _require(math.isclose(float(summary[name]["delta"]), delta, rel_tol=0.0, abs_tol=0.0), "SUMMARY_THRESHOLD_DELTA_MISMATCH")

    for key in REQUIRED_THRESHOLD_KEYS - {"delta"}:
        _require(0.0 <= float(thresholds[key]) <= 1.0, f"INVALID_THRESHOLD:{key}")

    declared_block = thresholds.get("cumulative_block")
    if declared_block is not None:
        _require(declared_block in BLOCK_ORDER, "INVALID_THRESHOLD_CUMULATIVE_BLOCK")
        _require(summary.get("cumulative_block") == declared_block, "SUMMARY_THRESHOLD_BLOCK_MISMATCH")


def selection_gate(summary: Mapping[str, Any], thresholds: Mapping[str, Any] | None) -> Dict[str, Any]:
    _validate_threshold_contract(summary, thresholds)
    assert thresholds is not None
    checks = _threshold_checks(summary, thresholds)
    return {
        "winner_eligible_under_risk_coverage_gate_only": all(checks.values()),
        "checks": checks,
        "threshold_contract_sha256": canonical_sha256(dict(thresholds)),
        "summary_identity_sha256": canonical_sha256(summary),
        "credit_boundary": "Eligibility under this postprocessor is necessary only if adopted by a future selection contract; it cannot mint checkpoint selection, training, J-Space, HCU, or EntityOS runtime credit.",
    }


def staged_selection_decision(summary: Mapping[str, Any], thresholds: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Return PASS/EXPAND/REJECT without opening any new block itself."""
    _validate_threshold_contract(summary, thresholds)
    assert thresholds is not None

    bound_checks = _threshold_checks(summary, thresholds)
    point_checks = _point_estimate_checks(summary, thresholds)
    states: Dict[str, str] = {}
    for name in bound_checks:
        if bound_checks[name]:
            states[name] = "PASS"
        elif point_checks[name]:
            states[name] = "UNRESOLVED_BOUND"
        else:
            states[name] = "FAIL_POINT_ESTIMATE"

    block = str(summary.get("cumulative_block"))
    _require(block in BLOCK_ORDER, "SUMMARY_CUMULATIVE_BLOCK_INVALID")
    if any(state == "FAIL_POINT_ESTIMATE" for state in states.values()):
        decision = "REJECT"
        next_block = None
    elif all(state == "PASS" for state in states.values()):
        decision = "ELIGIBLE_UNDER_RISK_COVERAGE_GATE_ONLY"
        next_block = None
    elif block != "B3":
        decision = "EXPAND_NEXT_PRECOMMITTED_BLOCK"
        next_block = BLOCK_ORDER[BLOCK_ORDER.index(block) + 1]
    else:
        decision = "REJECT_UNRESOLVED_AT_B3"
        next_block = None

    return {
        "decision": decision,
        "current_block": block,
        "next_block": next_block,
        "metric_states": states,
        "bound_checks": bound_checks,
        "point_estimate_checks": point_checks,
        "threshold_contract_sha256": canonical_sha256(dict(thresholds)),
        "summary_identity_sha256": canonical_sha256(summary),
        "nonexecution_rule": "This function never opens a block, invokes a model/provider, or grants checkpoint/training/J-Space/HCU/EntityOS credit.",
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
