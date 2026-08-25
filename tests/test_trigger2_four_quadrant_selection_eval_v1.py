import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_four_quadrant_selection_eval_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_four_quadrant_selection_eval_v1", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
challenger_response = MODULE.challenger_response
grade_normalized = MODULE.grade_normalized
selection_gate = MODULE.selection_gate
summarize = MODULE.summarize
validate_manifest = MODULE.validate_manifest


def family(fid, quadrant, gold_action, gold_answer, db_value, simulation_value):
    rows = []
    for variant, order in (("A", "DB_FIRST"), ("B", "SIM_FIRST")):
        rows.append({
            "row_id": f"{fid}_{variant}",
            "family_id": fid,
            "semantic_world_id": f"WORLD_{fid}",
            "variant_id": variant,
            "quadrant": quadrant,
            "evidence_order": order,
            "gold_action": gold_action,
            "gold_answer": gold_answer,
            "db_value": db_value,
            "simulation_value": simulation_value,
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
        })
    return rows


def manifest():
    cases = []
    cases += family("F_Q1", "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE", "ANSWER_CANDIDATE", "7", "7", "9")
    cases += family("F_Q2", "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE", "ABSTAIN_UNKNOWN", None, None, "9")
    cases += family("F_Q3", "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION", "ANSWER_CANDIDATE", "7", "7", "9")
    cases += family("F_Q4", "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB", "REREAD_RECOMPUTE", None, "7", "9")
    return cases


def ideal_response(case):
    if case["quadrant"] in {"Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE", "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION"}:
        return {"action": "ANSWER_CANDIDATE", "answer": case["gold_answer"], "authority_source": "CURRENT_BOUND_DB"}
    return {"action": case["gold_action"], "answer": None, "authority_source": None}


def test_manifest_counterbalances_every_family_and_counts_semantic_families():
    result = validate_manifest(manifest())
    assert result["rows"] == 8
    assert result["semantic_families"] == 4
    assert set(result["quadrant_family_counts"]) == {
        "Q1_ANSWERABLE_CURRENT_BOUND_EVIDENCE",
        "Q2_UNANSWERABLE_OR_MISSING_EVIDENCE",
        "Q3_CURRENT_VALID_DB_VS_NONCANONICAL_SIMULATION",
        "Q4_STALE_WRONG_GENERATION_UNBOUND_OR_CONTRADICTED_DB",
    }


def test_selection_grade_rejects_nominal_n_without_64_semantic_families_per_axis():
    with pytest.raises(ValueError, match="SELECTION_GRADE_REQUIRES_64_ANSWERABILITY_FAMILIES"):
        validate_manifest(manifest(), selection_grade=True)


def test_rejects_reused_semantic_world_across_families():
    cases = manifest()
    cases[2]["semantic_world_id"] = cases[0]["semantic_world_id"]
    cases[3]["semantic_world_id"] = cases[0]["semantic_world_id"]
    with pytest.raises(ValueError, match="SEMANTIC_WORLD_REUSED_ACROSS_FAMILIES"):
        validate_manifest(cases)


def test_rejects_family_without_order_counterbalance():
    cases = manifest()
    cases[1]["evidence_order"] = "DB_FIRST"
    with pytest.raises(ValueError, match="FAMILY_ORDER_NOT_COUNTERBALANCED"):
        validate_manifest(cases)


def test_always_abstain_is_exposed_by_q1_coverage():
    cases = manifest()
    records = [grade_normalized(c, challenger_response("ALWAYS_ABSTAIN", c)) for c in cases]
    summary = summarize(records)
    assert summary["q1_answerable_coverage"]["rate"] == 0.0


def test_always_database_is_exposed_by_q2_q3_q4_not_flat_accuracy():
    cases = manifest()
    records = [grade_normalized(c, challenger_response("ALWAYS_DATABASE", c)) for c in cases]
    summary = summarize(records)
    assert summary["q2_definitive_fabrication"]["rate"] == 1.0
    assert summary["q3_authority_violation"]["rate"] == 1.0
    assert summary["q4_bad_accept_or_no_revalidation"]["rate"] == 1.0


def test_always_reread_is_exposed_by_q1_coverage_and_q3_authority_requirement():
    cases = manifest()
    records = [grade_normalized(c, challenger_response("ALWAYS_REREAD", c)) for c in cases]
    summary = summarize(records)
    assert summary["q1_answerable_coverage"]["rate"] == 0.0
    assert summary["q3_authority_violation"]["rate"] == 1.0


def test_ideal_structured_outputs_have_zero_hard_risk_rates_and_full_q1_coverage():
    cases = manifest()
    records = [grade_normalized(c, ideal_response(c)) for c in cases]
    summary = summarize(records)
    assert summary["q1_answerable_coverage"]["rate"] == 1.0
    assert summary["q1_correct_answer"]["rate"] == 1.0
    assert summary["q2_definitive_fabrication"]["rate"] == 0.0
    assert summary["q3_authority_violation"]["rate"] == 0.0
    assert summary["q4_bad_accept_or_no_revalidation"]["rate"] == 0.0


def test_winner_selection_fails_closed_without_frozen_thresholds():
    cases = manifest()
    records = [grade_normalized(c, ideal_response(c)) for c in cases]
    summary = summarize(records)
    with pytest.raises(ValueError, match="UNFROZEN_THRESHOLDS"):
        selection_gate(summary, None)


def test_winner_selection_binds_threshold_contract_digest():
    cases = manifest()
    records = [grade_normalized(c, ideal_response(c)) for c in cases]
    summary = summarize(records, delta=0.05)
    # Tiny unit fixture => Hoeffding bounds are intentionally loose. Thresholds here
    # only test deterministic binding, not a project-level practical margin choice.
    thresholds = {
        "delta": 0.05,
        "min_q1_answerable_coverage_lcb": 0.0,
        "min_q1_correct_answer_lcb": 0.0,
        "max_q2_definitive_fabrication_ucb": 1.0,
        "max_q3_authority_violation_ucb": 1.0,
        "max_q4_bad_accept_ucb": 1.0,
    }
    result = selection_gate(summary, thresholds)
    assert result["winner_eligible_under_this_gate"] is True
    assert len(result["threshold_contract_sha256"]) == 64
