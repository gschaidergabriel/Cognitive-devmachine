import importlib.util
from pathlib import Path
MODULE=Path(__file__).resolve().parents[1]/"tools"/"trigger1_jspace_label_free_target_code_design_v2.py"
spec=importlib.util.spec_from_file_location("design",MODULE); design=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(design)

def test_basis_is_label_free_and_domain_matched():
    r=design.validate_label_free_basis(); assert r["pass"],r; assert r["prompt_count"]==9; assert r["domains"]==["access","motion","workflow"]

def test_splits_are_full_factorials_and_disjoint():
    cal=design.build_factorial_split("CALIBRATION"); hold=design.build_factorial_split("FRESH_HOLDOUT")
    cv=design.validate_factorial_split(cal,"CALIBRATION"); hv=design.validate_factorial_split(hold,"FRESH_HOLDOUT")
    assert cv["target_x_code_full_factorial"] and hv["target_x_code_full_factorial"] and cv["family_id"]!=hv["family_id"]
    assert {r["lexical_family"] for r in cal}.isdisjoint({r["lexical_family"] for r in hold})

def synthetic(generic=False,bad_nuisance=False):
    rows=[]
    for case in design.build_factorial_split("FRESH_HOLDOUT"):
        t=case["semantic_target"]; common={"seed":case["seed"],"lexical_family":case["lexical_family"],"semantic_target":t}
        rows += [{**common,"control":"BASELINE","target_score":0.0},{**common,"control":"SIGN_FLIP","target_score":-0.4},{**common,"control":"NULL_VECTOR","target_score":0.0},{**common,"control":"ORTHOGONAL_SAME_NORM","target_score":0.05},{**common,"control":"PERMUTED_SAME_NORM","target_score":0.04},{**common,"control":"LABEL_ONLY_NUISANCE_VECTOR","target_score":0.30 if bad_nuisance else 0.02}]
        for applied in design.SEMANTIC_TARGETS:
            rows.append({**common,"control":"+VECTOR","applied_semantic_target":applied,"target_score":0.5 if generic else (0.7 if applied==t else 0.1)})
    return rows

def test_metric_accepts_target_specific_tri_vector_pattern(): assert design.cross_target_specificity_metrics(synthetic())["pass"]
def test_metric_rejects_generic_compliance(): assert not design.cross_target_specificity_metrics(synthetic(generic=True))["pass"]
def test_metric_rejects_label_nuisance(): assert not design.cross_target_specificity_metrics(synthetic(bad_nuisance=True))["pass"]

def test_rank_deficient_nuisance_projection_uses_numerical_span_only():
    import torch
    v=torch.tensor([0.,0.,1.,1.]); nuisance=[torch.tensor([1.,0.,0.,0.]),torch.tensor([2.,0.,0.,0.]),torch.tensor([-3.,0.,0.,0.])]
    out=design.project_out_subspace(torch,v,nuisance); assert torch.allclose(out,v/torch.linalg.vector_norm(v),atol=1e-6)

def test_manifest_preregisters_scope_and_norm():
    m=design.protocol_manifest(); assert m["model_facing_basis_label_free"] and m["target_x_code_full_factorial"] and m["cross_target_vector_specificity_test"]
    assert m["token_scope_required"]=="ALL_PROMPT_TOKENS_CVEC" and m["residual_norm_relative_operating_point_required"] and m["operating_point_selected_on_calibration_only"]
