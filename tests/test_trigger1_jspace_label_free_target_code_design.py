import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "trigger1_jspace_label_free_target_code_design.py"
spec = importlib.util.spec_from_file_location("design", MODULE)
design = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(design)


def test_basis_is_label_free_and_domain_matched():
    result = design.validate_label_free_basis()
    assert result["pass"], result
    assert result["prompt_count"] == 9
    assert result["domains"] == ["access", "motion", "workflow"]


def test_calibration_and_holdout_are_full_target_x_code_factorials():
    cal = design.build_factorial_split("CALIBRATION")
    hold = design.build_factorial_split("FRESH_HOLDOUT")
    cal_v = design.validate_factorial_split(cal, "CALIBRATION")
    hold_v = design.validate_factorial_split(hold, "FRESH_HOLDOUT")
    assert cal_v["target_x_code_full_factorial"] is True
    assert hold_v["target_x_code_full_factorial"] is True
    assert cal_v["family_id"] != hold_v["family_id"]
    assert {row["lexical_family"] for row in cal}.isdisjoint({row["lexical_family"] for row in hold})


def _synthetic_rows(generic=False, bad_nuisance=False):
    rows = []
    cases = design.build_factorial_split("FRESH_HOLDOUT")
    for case in cases:
        target = case["semantic_target"]
        common = {
            "seed": case["seed"],
            "lexical_family": case["lexical_family"],
            "semantic_target": target,
        }
        rows.extend([
            {**common, "control": "BASELINE", "target_score": 0.0},
            {**common, "control": "SIGN_FLIP", "target_score": -0.40},
            {**common, "control": "NULL_VECTOR", "target_score": 0.0},
            {**common, "control": "ORTHOGONAL_SAME_NORM", "target_score": 0.05},
            {**common, "control": "PERMUTED_SAME_NORM", "target_score": 0.04},
            {**common, "control": "LABEL_ONLY_NUISANCE_VECTOR", "target_score": 0.30 if bad_nuisance else 0.02},
        ])
        for applied in design.SEMANTIC_TARGETS:
            score = 0.50 if generic else (0.70 if applied == target else 0.10)
            rows.append({
                **common,
                "control": "+VECTOR",
                "applied_semantic_target": applied,
                "target_score": score,
            })
    return rows


def test_cross_target_metric_accepts_target_specific_tri_vector_pattern():
    result = design.cross_target_specificity_metrics(_synthetic_rows())
    assert result["pass"], result
    assert all(result["targets"][target]["pass"] for target in design.SEMANTIC_TARGETS)


def test_cross_target_metric_rejects_generic_compliance_uplift():
    result = design.cross_target_specificity_metrics(_synthetic_rows(generic=True))
    assert result["pass"] is False
    assert any(
        result["targets"][target]["min_match_vs_best_mismatch"] <= 0
        for target in design.SEMANTIC_TARGETS
    )


def test_cross_target_metric_rejects_label_only_nuisance_reproduction():
    result = design.cross_target_specificity_metrics(_synthetic_rows(bad_nuisance=True))
    assert result["pass"] is False


def test_protocol_manifest_preregisters_scope_and_norm_calibration():
    manifest = design.protocol_manifest()
    assert manifest["model_facing_basis_label_free"] is True
    assert manifest["semantic_target_counterbalanced"] is True
    assert manifest["target_x_code_full_factorial"] is True
    assert manifest["cross_target_vector_specificity_test"] is True
    assert manifest["token_scope_required"] == "ALL_PROMPT_TOKENS_CVEC"
    assert manifest["residual_norm_relative_operating_point_required"] is True
    assert manifest["operating_point_selected_on_calibration_only"] is True
