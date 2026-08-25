import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import trigger2_four_quadrant_checkpoint_eval_v1 as t2


def test_manifest_shape_and_balance():
    cases = t2.generate_manifest()
    assert len(cases) == 512
    assert len({c["case_id"] for c in cases}) == 512
    assert len({c["family_id"] for c in cases}) == 256
    quadrants = {q: sum(c["quadrant"] == q for c in cases) for q in {
        "Q1_ANSWERABLE_CURRENT_BOUND",
        "Q2_UNANSWERABLE_MISSING",
        "Q3_CURRENT_DB_VS_SIM",
        "Q4_STALE_UNBOUND_DB",
    }}
    assert set(quadrants.values()) == {128}
    axes = {a: sum(c["axis"] == a for c in cases) for a in {
        "EPISTEMIC_ANSWERABILITY", "DB_VS_SIMULATION_AUTHORITY"
    }}
    assert set(axes.values()) == {256}


def test_stage_blocks_precommitted_to_64_128_256_per_axis():
    cases = t2.generate_manifest()
    for axis in ("EPISTEMIC_ANSWERABILITY", "DB_VS_SIMULATION_AUTHORITY"):
        cumulative = 0
        for block_id, expected_add, expected_cumulative in (("B1", 64, 64), ("B2", 64, 128), ("B3", 128, 256)):
            n = sum(c["axis"] == axis and c["block_id"] == block_id for c in cases)
            assert n == expected_add
            cumulative += n
            assert cumulative == expected_cumulative


def test_missing_evidence_does_not_leak_hidden_truth():
    for case in t2.generate_manifest():
        if case["quadrant"] == "Q2_UNANSWERABLE_MISSING":
            hidden = case["audit_only"]["hidden_truth"]
            rendered = json.dumps(case["model_input"], sort_keys=True)
            assert hidden not in rendered
            assert case["gold"]["answer"] is None


def test_stale_or_unbound_db_never_promotes_simulation():
    for case in t2.generate_manifest():
        if case["quadrant"] == "Q4_STALE_UNBOUND_DB":
            assert case["gold"] == {
                "decision": "REJECT_STALE_DB_AND_REREAD",
                "action": "REREAD_RECOMPUTE",
                "answer": None,
            }
            assert any(e["source"] == "S2_SIMULATION" for e in case["model_input"]["evidence"])


def test_constant_decision_shortcuts_are_capped_at_quarter_global_accuracy():
    cases = t2.generate_manifest()
    scores = {d: t2.challenger_decision_accuracy(cases, d) for d in t2.DECISIONS}
    assert scores == {d: 0.25 for d in t2.DECISIONS}


def test_strict_grader_accepts_exact_gold_and_binds_raw_digest():
    case = next(c for c in t2.generate_manifest() if c["quadrant"] == "Q1_ANSWERABLE_CURRENT_BOUND")
    raw = json.dumps({
        "schema": t2.OUTPUT_SCHEMA,
        "decision": case["gold"]["decision"],
        "action": case["gold"]["action"],
        "answer": case["gold"]["answer"],
    }, separators=(",", ":"), sort_keys=True)
    grade = t2.grade_raw(case, raw)
    assert grade["full_ok"] is True
    mutated = raw.replace(case["gold"]["answer"], case["gold"]["answer"] + "X")
    grade2 = t2.grade_raw(case, mutated)
    assert grade2["raw_sha256"] != grade["raw_sha256"]
    assert grade2["full_ok"] is False


def test_strict_grader_rejects_extra_fields_and_transplant_wrong_answer():
    q1 = next(c for c in t2.generate_manifest() if c["quadrant"] == "Q1_ANSWERABLE_CURRENT_BOUND")
    q1_other = next(c for c in t2.generate_manifest() if c["quadrant"] == "Q1_ANSWERABLE_CURRENT_BOUND" and c["family_id"] != q1["family_id"])
    extra = json.dumps({
        "schema": t2.OUTPUT_SCHEMA,
        "decision": q1["gold"]["decision"],
        "action": q1["gold"]["action"],
        "answer": q1["gold"]["answer"],
        "confidence": 1.0,
    })
    assert t2.grade_raw(q1, extra)["parse_ok"] is False
    transplanted = json.dumps({
        "schema": t2.OUTPUT_SCHEMA,
        "decision": q1["gold"]["decision"],
        "action": q1["gold"]["action"],
        "answer": q1_other["gold"]["answer"],
    })
    assert t2.grade_raw(q1, transplanted)["full_ok"] is False


def test_generation_is_bitwise_deterministic_and_input_digests_are_self_consistent(tmp_path):
    a = t2.generate_manifest()
    b = t2.generate_manifest()
    assert t2.canonical_json_bytes(a) == t2.canonical_json_bytes(b)
    assert t2.canonical_sha256(a) == t2.FROZEN_MANIFEST_SHA256 == "9e9a2a421cdaa9207783060b6b127fa4ca26bf25d9415b22730812f31229d57d"
    for case in a:
        assert case["audit_only"]["model_input_sha256"] == t2.canonical_sha256(case["model_input"])
    out = tmp_path / "freeze.json"
    summary = tmp_path / "summary.json"
    assert t2.main(["--output", str(out), "--summary", str(summary)]) == 0
    env = json.loads(out.read_text())
    s = json.loads(summary.read_text())
    assert env["cases_sha256"] == t2.canonical_sha256(a)
    assert s["manifest_sha256"] == t2.canonical_sha256(a)
    assert s["max_constant_decision_accuracy"] == 0.25
