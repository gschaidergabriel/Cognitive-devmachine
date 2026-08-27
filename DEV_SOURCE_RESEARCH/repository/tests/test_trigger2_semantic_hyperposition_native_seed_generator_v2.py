import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_native_seed_generator_v2.py"
spec = importlib.util.spec_from_file_location("gen", P)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_seed_builds_owner_targeted_hyperposition_native_rows():
    rows = gen.build_rows()
    assert len(rows) == 11
    families = {r["family_id"] for r in rows}
    assert {
        "SHP3_DB_VS_SIM_F01",
        "SHP3_UNKNOWN_EFFECT_F01",
        "SHP3_EVIDENCE_REPACKAGING_F01",
        "SHP3_VARIABLE_GRID_AUTHORITY_F01",
        "SHP3_CLAUDE_REENTRY_F01",
        "SHP3_GWT_RECURRENCE_F01",
        "SHP3_CLAYCODE_BINDING_F01",
        "SHP3_LOW_REFUSAL_RETENTION_F01",
        "SHP3_JSPACE_CAUSAL_BOUNDARY_F01",
        "SHP3_REJOIN_PERM_F01",
    }.issubset(families)
    assert all(r["formal_hyperposition"]["schema"] == gen.gate.EPISODE_SCHEMA for r in rows)
    assert all(r["audit_metadata_model_visible"] is False for r in rows)
    assert all(r["training_admission_scope"] == "CANDIDATE_SOURCE_ONLY" for r in rows)


def test_all_rows_pass_exact_current_derivation_bound_gate_self_check():
    rows = gen.build_rows()
    result = gen.self_check(rows)
    assert result["pass"], result
    assert result["row_failures"] == []
    assert result["permutation_group_failures"] == []
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] is False


def test_unknown_effect_and_gwt_cases_remain_unresolved():
    rows = {r["family_id"]: r for r in gen.build_rows() if r["family_id"] != "SHP3_REJOIN_PERM_F01"}
    assert rows["SHP3_UNKNOWN_EFFECT_F01"]["formal_hyperposition"]["task_resolution"]["status"] == "UNRESOLVED"
    assert rows["SHP3_GWT_RECURRENCE_F01"]["formal_hyperposition"]["task_resolution"]["status"] == "UNRESOLVED"


def test_evidence_repackaging_case_receives_no_independent_credit():
    rows = gen.build_rows()
    row = next(r for r in rows if r["family_id"] == "SHP3_EVIDENCE_REPACKAGING_F01")
    ep = row["formal_hyperposition"]
    assert ep["independent_evidence_credit"] is False
    assert "PAYLOAD_REPACKAGING" in ep["nonindependence_reasons"]


def test_rejoin_pair_is_explicit_permutation_group():
    rows = [r for r in gen.build_rows() if r["family_id"] == "SHP3_REJOIN_PERM_F01"]
    assert len(rows) == 2
    result = gen.gate.adjudicate_permutation_group(rows)
    assert result["permutation_group_pass"], result


def test_no_row_uses_legacy_causal_hyperposition_field():
    assert all("hyperposition" not in row for row in gen.build_rows())
