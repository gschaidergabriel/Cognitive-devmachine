import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import trigger2_four_quadrant_checkpoint_eval_v1 as frozen
import trigger2_four_quadrant_selection_eval_v1 as risk


def gold_raw(case):
    return json.dumps({
        "schema": frozen.OUTPUT_SCHEMA,
        "decision": case["gold"]["decision"],
        "action": case["gold"]["action"],
        "answer": case["gold"]["answer"],
    }, sort_keys=True, separators=(",", ":"))


def outputs_for(cases, fn):
    return {case["case_id"]: fn(case) for case in cases}


def permissive_thresholds(delta=0.05):
    return {
        "delta": delta,
        "min_q1_answerable_coverage_lcb": 0.0,
        "min_q1_correct_answer_lcb": 0.0,
        "max_q2_definitive_fabrication_ucb": 1.0,
        "max_q3_authority_resolution_failure_ucb": 1.0,
        "max_q4_bad_accept_or_no_revalidation_ucb": 1.0,
    }


def test_accepts_only_exact_canonical_frozen_manifest():
    cases = frozen.generate_manifest()
    identity = risk.validate_frozen_cases(cases)
    assert identity["manifest_sha256"] == frozen.FROZEN_MANIFEST_SHA256
    mutated = [dict(c) for c in cases]
    mutated[0] = dict(mutated[0])
    mutated[0]["case_id"] += "-MUTATED"
    with pytest.raises(ValueError, match="FROZEN_MANIFEST_IDENTITY_MISMATCH"):
        risk.validate_frozen_cases(mutated)


def test_gold_outputs_have_full_q1_coverage_and_zero_hard_risk():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, gold_raw))
    assert summary["q1_answerable_coverage"]["rate"] == 1.0
    assert summary["q1_correct_answer"]["rate"] == 1.0
    assert summary["q2_definitive_fabrication"]["rate"] == 0.0
    assert summary["q3_authority_resolution_failure"]["rate"] == 0.0
    assert summary["q4_bad_accept_or_no_revalidation"]["rate"] == 0.0
    assert summary["q1_answerable_coverage"]["n_families"] == 128


def test_always_abstain_exposes_overabstention_and_q3_failure():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, lambda c: risk.challenger_raw("ALWAYS_ABSTAIN", c)))
    assert summary["q1_answerable_coverage"]["rate"] == 0.0
    assert summary["q3_authority_resolution_failure"]["rate"] == 1.0


def test_always_database_exposes_q2_fabrication_and_q4_bad_accept():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, lambda c: risk.challenger_raw("ALWAYS_DATABASE", c)))
    assert summary["q2_definitive_fabrication"]["rate"] == 1.0
    assert summary["q4_bad_accept_or_no_revalidation"]["rate"] == 1.0


def test_always_reread_exposes_q1_coverage_and_q3_resolution_failure():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, lambda c: risk.challenger_raw("ALWAYS_REREAD", c)))
    assert summary["q1_answerable_coverage"]["rate"] == 0.0
    assert summary["q3_authority_resolution_failure"]["rate"] == 1.0
    assert summary["q4_bad_accept_or_no_revalidation"]["rate"] == 0.0


def test_missing_output_case_fails_closed():
    cases = frozen.generate_manifest()
    outputs = outputs_for(cases, gold_raw)
    outputs.pop(next(iter(outputs)))
    with pytest.raises(ValueError, match="RAW_OUTPUT_CASE_ID_SET_MISMATCH"):
        risk.summarize(cases, outputs)


def test_selection_gate_fails_closed_without_preunblinding_thresholds():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, gold_raw))
    with pytest.raises(ValueError, match="UNFROZEN_THRESHOLDS"):
        risk.selection_gate(summary, None)


def test_selection_gate_rejects_summary_threshold_delta_mismatch():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, gold_raw), delta=0.05)
    with pytest.raises(ValueError, match="SUMMARY_THRESHOLD_DELTA_MISMATCH"):
        risk.selection_gate(summary, permissive_thresholds(delta=0.01))


def test_selection_gate_binds_threshold_and_summary_identity():
    cases = frozen.generate_manifest()
    summary = risk.summarize(cases, outputs_for(cases, gold_raw), delta=0.05)
    result = risk.selection_gate(summary, permissive_thresholds())
    assert result["winner_eligible_under_risk_coverage_gate_only"] is True
    assert len(result["threshold_contract_sha256"]) == 64
    assert len(result["summary_identity_sha256"]) == 64
