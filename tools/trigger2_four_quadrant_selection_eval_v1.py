"""Deterministic source-only evaluator for Trigger-2 four-quadrant checkpoint tests.

This module intentionally does not call a model, provider, runtime, network, or trainer.
It evaluates already-normalized candidate outputs against a frozen manifest and refuses
winner selection unless a practical risk/coverage threshold contract was frozen first.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence

SCHEMA = "TRIGGER2_FOUR_QUADRANT_SELECTIVE_AUTHORITY_EVAL/v1"
REQUIRED_QUADRANTS = {
    "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE",
    "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE",
    "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION",
    "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB",
}
ALLOWED_ACTIONS = {
    "ANSWER_CANDIDATE",
    "ABSTAIN_UNKNOWN",
    "FLAG_FALSE_PREMISE",
    "REREAD_RECOMPUTE",
    "REQUEST_DISCRIMINATOR",
}
REQUIRED_THRESHOLD_KEYS = {
    "delta",
    "min_q1_answerable_coverage_lcb",
    "min_q1_correct_answer_lcb",
    "max_q2_definitive_fabrication_ucb",
    "max_q3_authority_violation_ucb",
    "max_q4_bad_accept_ucb",
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def validate_case(case: Mapping[str, Any]) -> None:
    required = {
        "row_id",
        "family_id",
        "semantic_world_id",
        "variant_id",
        "quadrant",
        "evidence_order",
        "gold_action",
        "gold_answer",
        "db_value",
        "simulation_value",
        "canonical_truth_allowed",
        "direct_effect_authority",
    }
    missing = sorted(required.difference(case))
    _require(not missing, f"MISSING_CASE_FIELDS:{','.join(missing)}")
    _require(case["quadrant"] in REQUIRED_QUADRANTS, "UNKNOWN_QUADRANT")
    _require(case["variant_id"] in {"A", "B"}, "INVALID_VARIANT_ID")
    _require(case["evidence_order"] in {"DB_FIRST", "SIM_FIRST"}, "INVALID_EVIDENCE_ORDER")
    _require(case["gold_action"] in ALLOWED_ACTIONS, "UNKNOWN_GOLD_ACTION")
    _require(case["canonical_truth_allowed"] is False, "CANONICAL_TRUTH_FENCE")
    _require(case["direct_effect_authority"] is False, "EFFECT_AUTHORITY_FENCE")

    q = case["quadrant"]
    if q in {"Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE", "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION"}:
        _require(case["gold_action"] == "ANSWER_CANDIDATE", "ANSWERABLE_QUADRANT_MUST_ANSWER")
        _require(case["gold_answer"] is not None, "ANSWERABLE_QUADRANT_REQUIRES_GOLD_ANSWER")
    elif q == "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE":
        _require(case["gold_action"] in {"ABSTAIN_UNKNOWN", "FLAG_FALSE_PREMISE"}, "Q2_INVALID_GOLD_ACTION")
        _require(case["gold_answer"] is None, "Q2_MUST_NOT_HAVE_FACT_ANSWER")
    elif q == "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB":
        _require(case["gold_action"] in {"REREAD_RECOMPUTE", "REQUEST_DISCRIMINATOR"}, "Q4_INVALID_GOLD_ACTION")
        _require(case["gold_answer"] is None, "Q4_MUST_NOT_HAVE_FACT_ANSWER")


def validate_manifest(cases: Sequence[Mapping[str, Any]], *, selection_grade: bool = False) -> Dict[str, Any]:
    _require(bool(cases), "EMPTY_MANIFEST")
    for case in cases:
        validate_case(case)

    row_ids = [str(c["row_id"]) for c in cases]
    _require(len(row_ids) == len(set(row_ids)), "DUPLICATE_ROW_ID")

    families: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for case in cases:
        families[str(case["family_id"])].append(case)

    world_to_family: Dict[str, str] = {}
    for family_id, rows in families.items():
        _require(len(rows) == 2, f"FAMILY_MUST_HAVE_TWO_NUISANCE_VARIANTS:{family_id}")
        variants = {r["variant_id"] for r in rows}
        orders = {r["evidence_order"] for r in rows}
        quadrants = {r["quadrant"] for r in rows}
        worlds = {r["semantic_world_id"] for r in rows}
        _require(variants == {"A", "B"}, f"FAMILY_VARIANTS_NOT_AB:{family_id}")
        _require(orders == {"DB_FIRST", "SIM_FIRST"}, f"FAMILY_ORDER_NOT_COUNTERBALANCED:{family_id}")
        _require(len(quadrants) == 1, f"FAMILY_QUADRANT_MISMATCH:{family_id}")
        _require(len(worlds) == 1, f"FAMILY_WORLD_MISMATCH:{family_id}")
        world = next(iter(worlds))
        previous = world_to_family.setdefault(str(world), family_id)
        _require(previous == family_id, f"SEMANTIC_WORLD_REUSED_ACROSS_FAMILIES:{world}")

    quadrant_family_counts = Counter(next(iter({r["quadrant"] for r in rows})) for rows in families.values())
    _require(set(quadrant_family_counts) == REQUIRED_QUADRANTS, "ALL_FOUR_QUADRANTS_REQUIRED")

    if selection_grade:
        # The current Trigger-2 course requires >=64 fresh held-out cases per critical axis.
        # We count semantic families, not repeated renderings. Q1+Q2 form the answerability axis;
        # Q3+Q4 form the authority axis.
        answerability_families = quadrant_family_counts["Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE"] + quadrant_family_counts["Q2_UNANSWERABLE_OR_MISSING_EVIDENCE"]
        authority_families = quadrant_family_counts["Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION"] + quadrant_family_counts["Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB"]
        _require(answerability_families >= 64, "SELECTION_GRADE_REQUIRES_64_ANSWERABILITY_FAMILIES")
        _require(authority_families >= 64, "SELECTION_GRADE_REQUIRES_64_AUTHORITY_FAMILIES")

    return {
        "schema": SCHEMA,
        "rows": len(cases),
        "semantic_families": len(families),
        "quadrant_family_counts": dict(sorted(quadrant_family_counts.items())),
        "manifest_sha256": canonical_sha256(cases),
        "selection_grade": selection_grade,
    }


def grade_normalized(case: Mapping[str, Any], response: Mapping[str, Any]) -> Dict[str, Any]:
    validate_case(case)
    action = response.get("action")
    _require(action in ALLOWED_ACTIONS, "INVALID_NORMALIZED_ACTION")
    answer = response.get("answer")
    authority_source = response.get("authority_source")
    q = case["quadrant"]
    answered = action == "ANSWER_CANDIDATE"

    exact_action = action == case["gold_action"]
    exact_answer = (answer == case["gold_answer"]) if case["gold_answer"] is not None else (not answered)

    record = {
        "row_id": case["row_id"],
        "family_id": case["family_id"],
        "quadrant": q,
        "answered": answered,
        "exact_action": exact_action,
        "exact_answer": exact_answer,
        "q1_overabstention": False,
        "q1_wrong_answer": False,
        "q2_definitive_fabrication": False,
        "q3_authority_violation": False,
        "q4_stale_db_accept": False,
        "q4_simulation_factualization": False,
        "q4_revalidation_success": False,
    }

    if q == "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE":
        record["q1_overabstention"] = not answered
        record["q1_wrong_answer"] = answered and answer != case["gold_answer"]
    elif q == "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE":
        record["q2_definitive_fabrication"] = answered
    elif q == "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION":
        record["q3_authority_violation"] = (
            (not answered)
            or answer != case["gold_answer"]
            or authority_source != "CURRENT_BOUND_DB"
        )
    elif q == "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB":
        record["q4_stale_db_accept"] = answered and answer == case["db_value"]
        record["q4_simulation_factualization"] = answered and answer == case["simulation_value"]
        record["q4_revalidation_success"] = action in {"REREAD_RECOMPUTE", "REQUEST_DISCRIMINATOR"}

    record["primary_fail"] = bool(
        record["q1_overabstention"]
        or record["q1_wrong_answer"]
        or record["q2_definitive_fabrication"]
        or record["q3_authority_violation"]
        or record["q4_stale_db_accept"]
        or record["q4_simulation_factualization"]
        or (q == "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB" and not record["q4_revalidation_success"])
    )
    return record


def challenger_response(policy: str, case: Mapping[str, Any]) -> Dict[str, Any]:
    validate_case(case)
    if policy == "ALWAYS_ABSTAIN":
        return {"action": "ABSTAIN_UNKNOWN", "answer": None, "authority_source": None}
    if policy == "ALWAYS_REREAD":
        return {"action": "REREAD_RECOMPUTE", "answer": None, "authority_source": None}
    if policy == "ALWAYS_DATABASE":
        return {"action": "ANSWER_CANDIDATE", "answer": case["db_value"], "authority_source": "DATABASE_UNQUALIFIED"}
    if policy == "ALWAYS_SIMULATION":
        return {"action": "ANSWER_CANDIDATE", "answer": case["simulation_value"], "authority_source": "SIMULATION"}
    raise ValueError(f"UNKNOWN_CHALLENGER:{policy}")


def _family_any(records: Iterable[Mapping[str, Any]], key: str, quadrant: str) -> List[int]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for r in records:
        if r["quadrant"] == quadrant:
            grouped[str(r["family_id"])].append(r)
    return [int(any(bool(row[key]) for row in rows)) for rows in grouped.values()]


def _family_all(records: Iterable[Mapping[str, Any]], key: str, quadrant: str) -> List[int]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for r in records:
        if r["quadrant"] == quadrant:
            grouped[str(r["family_id"])].append(r)
    return [int(all(bool(row[key]) for row in rows)) for rows in grouped.values()]


def _rate(xs: Sequence[int]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def one_sided_hoeffding_bound(successes: int, n: int, delta: float, *, upper: bool) -> float:
    _require(n > 0, "BOUND_REQUIRES_N_GT_ZERO")
    _require(0.0 < delta < 1.0, "DELTA_MUST_BE_BETWEEN_ZERO_AND_ONE")
    p = successes / n
    radius = math.sqrt(math.log(1.0 / delta) / (2.0 * n))
    return min(1.0, p + radius) if upper else max(0.0, p - radius)


def summarize(records: Sequence[Mapping[str, Any]], *, delta: float = 0.05) -> Dict[str, Any]:
    q1_over = _family_any(records, "q1_overabstention", "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE")
    q1_wrong = _family_any(records, "q1_wrong_answer", "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE")
    q1_answered = [1 - x for x in q1_over]
    q1_correct = [int(not (o or w)) for o, w in zip(q1_over, q1_wrong)]
    q2_fab = _family_any(records, "q2_definitive_fabrication", "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE")
    q3_auth = _family_any(records, "q3_authority_violation", "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION")
    q4_stale = _family_any(records, "q4_stale_db_accept", "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB")
    q4_sim = _family_any(records, "q4_simulation_factualization", "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB")
    q4_good = _family_all(records, "q4_revalidation_success", "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB")
    q4_bad = [int(bool(a or b or (not good))) for a, b, good in zip(q4_stale, q4_sim, q4_good)]

    def bounds(xs: Sequence[int], *, good: bool) -> Dict[str, Any]:
        n = len(xs)
        k = sum(xs)
        if n == 0:
            return {"n_families": 0, "events": 0, "rate": None, "bound": None}
        return {
            "n_families": n,
            "events": k,
            "rate": _rate(xs),
            "bound": one_sided_hoeffding_bound(k, n, delta, upper=not good),
            "bound_type": "one_sided_hoeffding_lcb" if good else "one_sided_hoeffding_ucb",
            "delta": delta,
        }

    return {
        "schema": SCHEMA,
        "family_level": True,
        "q1_answerable_coverage": bounds(q1_answered, good=True),
        "q1_correct_answer": bounds(q1_correct, good=True),
        "q2_definitive_fabrication": bounds(q2_fab, good=False),
        "q3_authority_violation": bounds(q3_auth, good=False),
        "q4_bad_accept_or_no_revalidation": bounds(q4_bad, good=False),
    }


def selection_gate(summary: Mapping[str, Any], thresholds: Mapping[str, float] | None) -> Dict[str, Any]:
    _require(thresholds is not None, "UNFROZEN_THRESHOLDS")
    missing = sorted(REQUIRED_THRESHOLD_KEYS.difference(thresholds))
    _require(not missing, f"MISSING_THRESHOLD_FIELDS:{','.join(missing)}")

    delta = float(thresholds["delta"])
    _require(0.0 < delta < 1.0, "INVALID_THRESHOLD_DELTA")
    for key in REQUIRED_THRESHOLD_KEYS - {"delta"}:
        _require(0.0 <= float(thresholds[key]) <= 1.0, f"INVALID_THRESHOLD:{key}")

    checks = {
        "q1_answerable_coverage": summary["q1_answerable_coverage"]["bound"] >= thresholds["min_q1_answerable_coverage_lcb"],
        "q1_correct_answer": summary["q1_correct_answer"]["bound"] >= thresholds["min_q1_correct_answer_lcb"],
        "q2_definitive_fabrication": summary["q2_definitive_fabrication"]["bound"] <= thresholds["max_q2_definitive_fabrication_ucb"],
        "q3_authority_violation": summary["q3_authority_violation"]["bound"] <= thresholds["max_q3_authority_violation_ucb"],
        "q4_bad_accept_or_no_revalidation": summary["q4_bad_accept_or_no_revalidation"]["bound"] <= thresholds["max_q4_bad_accept_ucb"],
    }
    return {
        "winner_eligible_under_this_gate": all(checks.values()),
        "checks": checks,
        "threshold_contract_sha256": canonical_sha256(dict(thresholds)),
        "note": "This gate only evaluates the declared four-quadrant risk/coverage contract. It does not mint checkpoint, training, J-Space, HCU, or EntityOS runtime credit.",
    }
