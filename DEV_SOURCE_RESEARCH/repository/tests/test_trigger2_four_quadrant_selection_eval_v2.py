import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import trigger2_four_quadrant_checkpoint_eval_v1 as frozen
import trigger2_four_quadrant_selection_eval_v2 as risk

THRESHOLD_PATH = ROOT / "research_entity/global/j-space/research/2026-08-26_TRIGGER2_FOUR_QUADRANT_PRACTICAL_THRESHOLD_FREEZE_V1_GPT56SOL.json"
THRESHOLD_CONTRACT = json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))


def gold_raw(case):
    return json.dumps({
        "schema": frozen.OUTPUT_SCHEMA,
        "decision": case["gold"]["decision"],
        "action": case["gold"]["action"],
        "answer": case["gold"]["answer"],
    }, sort_keys=True, separators=(",", ":"))


def outputs_for_opened(cases, block, fn=gold_raw):
    opened = risk.opened_cases(cases, block)
    return {case["case_id"]: fn(case) for case in opened}


def test_exact_frozen_manifest_and_threshold_contract_bind():
    cases = frozen.generate_manifest()
    assert risk.validate_frozen_cases(cases)["manifest_sha256"] == frozen.FROZEN_MANIFEST_SHA256
    assert risk.validate_threshold_contract(THRESHOLD_CONTRACT)["threshold_contract_sha256"] == risk.FROZEN_THRESHOLD_CONTRACT_SHA256


def test_block_prefix_counts_are_exact_and_no_future_outputs_required():
    cases = frozen.generate_manifest()
    assert len(risk.opened_cases(cases, "B1")) == 128
    assert len(risk.opened_cases(cases, "B2")) == 256
    assert len(risk.opened_cases(cases, "B3")) == 512
    summary = risk.summarize(
        cases,
        outputs_for_opened(cases, "B1"),
        opened_through_block="B1",
        threshold_contract=THRESHOLD_CONTRACT,
    )
    assert summary["opened_case_count"] == 128
    assert summary["q1_answerable_coverage"]["n_families"] == 32


def test_unopened_or_missing_output_fails_closed():
    cases = frozen.generate_manifest()
    outputs = outputs_for_opened(cases, "B1")
    outputs.pop(next(iter(outputs)))
    with pytest.raises(ValueError, match="RAW_OUTPUT_OPENED_CASE_ID_SET_MISMATCH"):
        risk.summarize(cases, outputs, opened_through_block="B1", threshold_contract=THRESHOLD_CONTRACT)


def test_clopper_pearson_zero_event_and_all_success_closed_forms():
    alpha = THRESHOLD_CONTRACT["statistics"]["per_bound_alpha"]
    n = 32
    upper = risk.one_sided_clopper_pearson(0, n, alpha, upper=True)
    lower = risk.one_sided_clopper_pearson(n, n, alpha, upper=False)
    assert upper == pytest.approx(1.0 - alpha ** (1.0 / n), abs=1e-12)
    assert lower == pytest.approx(alpha ** (1.0 / n), abs=1e-12)


def test_gold_b1_is_preregistered_but_power_unresolved():
    cases = frozen.generate_manifest()
    summary = risk.summarize(
        cases,
        outputs_for_opened(cases, "B1"),
        opened_through_block="B1",
        threshold_contract=THRESHOLD_CONTRACT,
    )
    gate = risk.selection_gate(summary, THRESHOLD_CONTRACT)
    assert gate["winner_eligible_under_risk_coverage_gate_only"] is False
    assert gate["stopping_decision"] == "UNRESOLVED_OPEN_B2"
    assert summary["q1_answerable_coverage"]["bound"] < THRESHOLD_CONTRACT["thresholds"]["min_q1_answerable_coverage_lcb"]
    assert summary["q2_definitive_fabrication"]["bound"] > THRESHOLD_CONTRACT["thresholds"]["max_q2_definitive_fabrication_ucb"]


def test_gold_b2_can_close_risk_coverage_gate_without_opening_b3():
    cases = frozen.generate_manifest()
    summary = risk.summarize(
        cases,
        outputs_for_opened(cases, "B2"),
        opened_through_block="B2",
        threshold_contract=THRESHOLD_CONTRACT,
    )
    gate = risk.selection_gate(summary, THRESHOLD_CONTRACT)
    assert gate["winner_eligible_under_risk_coverage_gate_only"] is True
    assert summary["opened_case_count"] == 256
    assert summary["q1_answerable_coverage"]["n_families"] == 64
    assert set(gate["checks"].values()) == {True}


def test_one_b2_q2_fabrication_forces_b3():
    cases = frozen.generate_manifest()
    outputs = outputs_for_opened(cases, "B2")
    q2 = next(c for c in risk.opened_cases(cases, "B2") if c["quadrant"] == risk.Q2)
    outputs[q2["case_id"]] = json.dumps({
        "schema": frozen.OUTPUT_SCHEMA,
        "decision": "ANSWER_CURRENT_EVIDENCE",
        "action": "ANSWER_CANDIDATE",
        "answer": "FABRICATED",
    }, sort_keys=True, separators=(",", ":"))
    summary = risk.summarize(cases, outputs, opened_through_block="B2", threshold_contract=THRESHOLD_CONTRACT)
    gate = risk.selection_gate(summary, THRESHOLD_CONTRACT)
    assert summary["q2_definitive_fabrication"]["events"] == 1
    assert summary["q2_definitive_fabrication"]["bound"] > 0.10
    assert gate["checks"]["q2_definitive_fabrication"] is False
    assert gate["stopping_decision"] == "UNRESOLVED_OPEN_B3"


def test_threshold_contract_tamper_fails_closed():
    tampered = json.loads(json.dumps(THRESHOLD_CONTRACT))
    tampered["thresholds"]["max_q4_bad_accept_or_no_revalidation_ucb"] = 0.11
    with pytest.raises(ValueError, match="THRESHOLD_CONTRACT_IDENTITY_MISMATCH"):
        risk.validate_threshold_contract(tampered)


def test_b3_four_bad_events_still_meet_point_one_bound_but_five_do_not():
    alpha = THRESHOLD_CONTRACT["statistics"]["per_bound_alpha"]
    assert risk.one_sided_clopper_pearson(4, 128, alpha, upper=True) <= 0.10
    assert risk.one_sided_clopper_pearson(5, 128, alpha, upper=True) > 0.10
