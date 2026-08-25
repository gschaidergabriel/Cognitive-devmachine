import copy
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_generation_provenance_pilot_gate_v1.py"
spec = importlib.util.spec_from_file_location("gp_gate", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def row(prompt="Use the provenance-bound DB state."):
    return {
        "generation_case_id": gate.generator.CASE_ID,
        "generation_parameters_evaluator_only": gate.generator.default_parameters(),
        "prompt": prompt,
    }


def test_trusted_reconstruction_pilot_delegates_to_retained_gate_and_mints_zero_credit():
    result = gate.adjudicate(row())
    assert result["pass"], result
    assert result["trusted_generator_invoked"] is True
    assert result["caller_selects_generator_identity"] is False
    assert result["caller_supplies_evaluator_subjects"] is False
    assert result["reconstructed_subjects_model_visible"] is False
    assert result["generation_receipt"]["schema"] == gate.GENERATION_RECEIPT_SCHEMA
    assert result["retained_gate_result"]["underlying_gate_called"] is True
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


@pytest.mark.parametrize("field,value", [
    ("generator_repo_path", "tools/other.py"),
    ("formal_task_world_evaluator_only", {"world_id": "swap"}),
    ("event_dependence_registry_evaluator_only", {"schema": "swap"}),
    ("synthetic_test_event_evaluator_only", {"event_id": "same-id-mutated"}),
    ("materials_manifest", {"materials": ["mutated"]}),
    ("discriminator_execution_receipts_evaluator_only", [{"executed": True}]),
    ("generation_receipt", {"schema": gate.GENERATION_RECEIPT_SCHEMA}),
])
def test_gp_01_02_03_04_07_caller_cannot_swap_generator_subjects_materials_or_receipts(field, value):
    candidate = row()
    candidate[field] = value
    result = gate.adjudicate(candidate)
    assert not result["pass"]
    assert f"CALLER_EVALUATOR_OVERRIDE_FORBIDDEN:{field}" in result["failures"]
    assert result["trusted_generator_invoked"] is False


def test_gp_05_jcs_key_order_invariance_for_deterministic_parameters():
    p = gate.generator.default_parameters()
    reversed_parameters = {k: p[k] for k in reversed(list(p))}
    a = gate.adjudicate(row())
    b_row = row()
    b_row["generation_parameters_evaluator_only"] = reversed_parameters
    b = gate.adjudicate(b_row)
    assert a["pass"] and b["pass"]
    assert a["generation_receipt"]["invocation"] == b["generation_receipt"]["invocation"]
    assert a["generation_receipt"]["receipt_jcs_sha256"] == b["generation_receipt"]["receipt_jcs_sha256"]
    assert a["semantic_target_jcs_sha256"] == b["semantic_target_jcs_sha256"]


def test_gp_06_parameter_mutation_fails_closed_before_retained_semantics():
    candidate = row()
    candidate["generation_parameters_evaluator_only"] = copy.deepcopy(candidate["generation_parameters_evaluator_only"])
    candidate["generation_parameters_evaluator_only"]["case_variant"] = "MUTATED"
    result = gate.adjudicate(candidate)
    assert not result["pass"]
    assert "GENERATION_PARAMETERS_MISMATCH" in result["failures"]
    assert "retained_gate_result" not in result


def test_gp_08_prompt_paraphrase_does_not_change_evaluator_semantic_target():
    a = gate.adjudicate(row("The DB probe matches; update the synthetic branches."))
    b = gate.adjudicate(row("Given a matching database check, apply the formal evidence transition."))
    assert a["pass"] and b["pass"]
    assert a["semantic_target_jcs_sha256"] == b["semantic_target_jcs_sha256"]
    assert a["generation_receipt"]["receipt_jcs_sha256"] == b["generation_receipt"]["receipt_jcs_sha256"]


def test_unknown_case_fails_closed():
    candidate = row()
    candidate["generation_case_id"] = "NOT_AUTHORIZED"
    result = gate.adjudicate(candidate)
    assert not result["pass"]
    assert "GENERATION_CASE_NOT_AUTHORIZED" in result["failures"]
