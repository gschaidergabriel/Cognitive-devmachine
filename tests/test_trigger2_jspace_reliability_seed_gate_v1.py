from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "tools" / "trigger2_jspace_reliability_seed_gate_v1.py"
SEED_PATH = ROOT / "research_entity" / "global" / "j-space" / "research" / "trigger2_jspace_steering_reliability_hardnegative_seed_v1.jsonl"

spec = importlib.util.spec_from_file_location("trigger2_jsr_gate", GATE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def _rows():
    return mod.load_jsonl(SEED_PATH)


def test_seed_passes_source_gate():
    result = mod.adjudicate(_rows())
    assert result["pass"], result
    assert result["rows"] == 8
    assert result["families"] == 8
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["positive_jspace_labels_minted"] == 0
    assert result["training_credit_minted"] is False


def test_positive_jspace_label_fails_closed():
    rows = _rows()
    rows[0]["positive_jspace_label"] = True
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("POSITIVE_JSPACE_LABEL_MUST_BE_FALSE" in f for f in result["failures"])


def test_training_eligibility_fails_closed():
    rows = _rows()
    rows[1]["training_eligible"] = True
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("TRAINING_ELIGIBLE_MUST_BE_FALSE" in f for f in result["failures"])


def test_destructive_projection_fails_closed():
    rows = _rows()
    rows[2]["semantic_hyperposition"]["projection"]["operation"] = "DELETE_HIDDEN_BRANCHES"
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("PROJECTION_MUST_BE_NONDESTRUCTIVE" in f for f in result["failures"])


def test_cross_model_positive_control_payload_fails_closed():
    rows = _rows()
    rows[1]["steering_vector"] = [0.1, 0.2]
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("FORBIDDEN_POSITIVE_CONTROL_FIELDS" in f for f in result["failures"])


def test_unresolved_composition_requires_discriminator():
    rows = _rows()
    target = next(r for r in rows if r["family_id"] == "JSR_VECTOR_COMPOSITION_UNRESOLVED_F05")
    target["semantic_hyperposition"].pop("requested_discriminator")
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("UNRESOLVED_REQUIRES_DISCRIMINATOR" in f for f in result["failures"])


def test_duplicate_family_fails_closed():
    rows = _rows()
    rows[-1]["family_id"] = rows[0]["family_id"]
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert "EXPECTED_FAMILY_SET_MISMATCH" in result["failures"]


def test_canonical_truth_leak_fails_closed():
    rows = deepcopy(_rows())
    rows[0]["canonical_truth_allowed"] = True
    result = mod.adjudicate(rows)
    assert not result["pass"]
    assert any("CANONICAL_TRUTH_MUST_BE_FALSE" in f for f in result["failures"])
