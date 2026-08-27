from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_evidence_provenance_opaque_binding_gate_v1.py"
spec = importlib.util.spec_from_file_location("gate", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def test_gate_is_fully_crossed_disjoint_and_nonpromoting():
    result = gate.validate()
    assert result["pass"] is True
    assert result["rows"] == 576
    assert result["mapping_permutations_per_split"] == 6
    assert result["codebook_orders_per_mapping"] == 6
    assert result["atom_alphabets_disjoint"] is True
    assert result["training_eligible_rows"] == 0
    assert result["accepted_dataset_tokens_delta"] == 0


def test_raw_chain_and_order_shortcuts_are_exactly_chance_in_both_splits():
    result = gate.validate()
    for metrics in result["split_metrics"].values():
        assert metrics["chain_only_majority_accuracy"] == 0.5
        assert metrics["order_only_majority_accuracy"] == 0.5
        assert metrics["atom_multiset_majority_accuracy"] == 0.5
        assert metrics["semantic_codebook_decoder_accuracy"] == 1.0


def test_target_leakage_fails_closed():
    rows = gate.rows()
    bad = deepcopy(rows)
    bad[0]["model_visible_input"]["outcome_class_evaluator_only"] = bad[0]["outcome_class_evaluator_only"]
    bad[0]["model_visible_input_sha256"] = gate.dg(bad[0]["model_visible_input"])
    with pytest.raises(ValueError, match="^TARGET_LEAKAGE$"):
        gate.validate(bad)


def test_duplicate_codebook_atom_fails_closed():
    rows = gate.rows()
    bad = deepcopy(rows)
    bad[0]["model_visible_input"]["episode_codebook"][1]["atom"] = bad[0]["model_visible_input"]["episode_codebook"][0]["atom"]
    bad[0]["model_visible_input_sha256"] = gate.dg(bad[0]["model_visible_input"])
    with pytest.raises(ValueError, match="^CODEBOOK_NOT_BIJECTIVE$"):
        gate.validate(bad)


def test_removed_factorial_cell_fails_closed():
    rows = gate.rows()
    bad = rows[:-1]
    with pytest.raises(ValueError, match="^ROW_COUNT_MISMATCH$"):
        gate.validate(bad)


def test_semantic_chain_target_transplant_fails_closed():
    rows = gate.rows()
    bad = deepcopy(rows)
    bad[0]["outcome_class_evaluator_only"] = (
        "CLAIM_ONLY_NO_PROMOTION"
        if bad[0]["outcome_class_evaluator_only"] == "BOUND_EVIDENCE_CANDIDATE"
        else "BOUND_EVIDENCE_CANDIDATE"
    )
    with pytest.raises(ValueError, match="^OUTCOME_BALANCE_MISMATCH$|^SEMANTIC_TARGET_MISMATCH$"):
        gate.validate(bad)


def test_promotion_fence_fails_closed():
    rows = gate.rows()
    bad = deepcopy(rows)
    bad[0]["accepted_dataset_credit"] = 1
    with pytest.raises(ValueError, match="^PROMOTION_FENCE_VIOLATION$"):
        gate.validate(bad)
