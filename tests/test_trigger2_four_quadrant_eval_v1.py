import importlib.util
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("m",REPO/"tools"/"trigger2_four_quadrant_eval_v1.py")
m=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
manifest=m.load_manifest(REPO/"research_entity"/"global"/"j-space"/"research"/"manifests"/"TRIGGER2_FOUR_QUADRANT_SELECTIVE_ANSWERABILITY_AUTHORITY_EVAL_V1.json")

def test_manifest_valid_and_balanced():
    assert m.validate_manifest(manifest)
    assert len(manifest["cases"])==32

def test_constant_label_challengers_are_exactly_quarter():
    for d in m.ALLOWED: assert m.challenger_accuracy(manifest,d)==0.25

def test_q3_q4_order_is_crossed_within_each_family():
    fams={c["family_id"] for c in manifest["cases"]}
    for f in fams:
        rows=[c for c in manifest["cases"] if c["family_id"]==f and c["quadrant"].startswith(("Q3_","Q4_"))]
        assert {c["evidence_order_arm"] for c in rows}=={"DB_FIRST","SIM_FIRST"}

def test_exact_parser_rejects_extra_text():
    assert m.parse_output("DECISION=ANSWER\nVALUE=23.4\nextra") is None

def test_answer_grade_requires_exact_value():
    c=next(c for c in manifest["cases"] if c["expected_decision"]=="ANSWER")
    assert m.grade(c,f"DECISION=ANSWER\nVALUE={c['expected_value']}")["correct"]
    assert not m.grade(c,"DECISION=ANSWER\nVALUE=wrong")["correct"]

def test_abstain_requires_none():
    c=next(c for c in manifest["cases"] if c["expected_decision"]=="ABSTAIN_UNKNOWN")
    assert m.grade(c,"DECISION=ABSTAIN_UNKNOWN\nVALUE=NONE")["correct"]
    assert not m.grade(c,"DECISION=ABSTAIN_UNKNOWN\nVALUE=guess")["correct"]

def test_q4_never_accepts_simulation_as_fact():
    c=next(c for c in manifest["cases"] if c["expected_decision"]=="REREAD_RECONCILE")
    assert m.grade(c,"DECISION=REREAD_RECONCILE\nVALUE=NONE")["correct"]
    assert not m.grade(c,"DECISION=TRUST_DB\nVALUE=NONE")["correct"]

def test_perfect_outputs_score_one_and_constant_margin_three_quarters():
    outs={c["case_id"]:f"DECISION={c['expected_decision']}\nVALUE={c['expected_value']}" for c in manifest["cases"]}
    s=m.summary(manifest,outs)
    assert s["accuracy"]==1.0 and s["hard_quadrant_floor"]==1.0 and s["margin_over_best_constant_label"]==0.75
