#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tools" / "trigger2_cognitive_process_trajectory_generator_v1.py"
GATE = ROOT / "tools" / "entityos_hcu_trainingtrace_candidate_gate_v1.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


gen = load("trigger2_cp_gen", GEN)
gate = load("candidate_gate", GATE)
rows = gen.rows()
audit = gen.audit(rows)
assert audit["pass"], audit
assert len(rows) == 208
assert len({r["family_id"] for r in rows}) == 13
assert audit["split_counts"] == {"TRAIN": 144, "VALIDATION": 32, "HOLDOUT": 32}
assert audit["family_split_counts"] == {"TRAIN": 9, "VALIDATION": 2, "HOLDOUT": 2}
assert all(r["canonical_truth_allowed"] is False for r in rows)
assert all(r["direct_effect_authority"] is False for r in rows)
assert all(r["selected_using_holdout"] is False for r in rows)
assert all(r["target_type"] == gen.TARGET_TYPE for r in rows)
assert all(r["training_boundary"]["accepted_dataset_credit"] == 0 for r in rows)
assert all(r["model_visible_fields"] == ["prompt"] and r["metadata_model_visible"] is False for r in rows)
assert all(not any(m in r["prompt"] for m in gen.FORBIDDEN_MODEL_VISIBLE_MARKERS) for r in rows)
for family in gen.BLUEPRINTS:
    fr = [r for r in rows if r["family_id"] == family]
    assert len(fr) == 16
    assert len({r["split"] for r in fr}) == 1
    assert len({r["provenance_ancestry_id"] for r in fr}) == 1
    for case in ("POSITIVE", "HARD_NEGATIVE"):
        cr = [r for r in fr if r["trajectory_case_evaluator_only"] == case]
        assert len(cr) == 8
        assert sorted(r["nuisance_controls_evaluator_only"]["n"] for r in cr) == [10, 10, 10, 10, 20, 20, 20, 20]
        assert len({(r["nuisance_controls_evaluator_only"]["n"], r["nuisance_controls_evaluator_only"]["executor"]) for r in cr}) == 4
        assert len({(r["nuisance_controls_evaluator_only"]["n"], r["nuisance_controls_evaluator_only"]["executor"], r["nuisance_controls_evaluator_only"]["presentation"]) for r in cr}) == 8
        assert len({(r["nuisance_controls_evaluator_only"]["n"], r["nuisance_controls_evaluator_only"]["presentation"]) for r in cr}) == 4
        assert len({(r["nuisance_controls_evaluator_only"]["executor"], r["nuisance_controls_evaluator_only"]["presentation"]) for r in cr}) == 4
        for r in cr:
            t = json.loads(r["target"])
            assert t["canonical_truth_minted"] is False
            assert t["direct_effect_authority"] is False
            assert t["authority"] == "CANDIDATE_ONLY"
results = [gate.adjudicate(r) for r in rows]
assert all(x["candidate_admission_pass"] for x in results), [x for x in results if not x["candidate_admission_pass"]]
assert all(x["training_credit_minted"] is False for x in results)
print("PASS 13 families / 208 rows / prompt-blind family metadata / full 2x2x2 nuisance cross / 208 candidate-gate passes")
