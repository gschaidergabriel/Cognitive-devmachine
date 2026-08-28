import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "tools" / "trigger2_jspace_future_consumer_equivalence_gate_v1.py"
SEED = ROOT / "research_entity" / "global" / "j-space" / "research" / "trigger2_jspace_future_consumer_equivalence_seed_v1.jsonl"

spec = importlib.util.spec_from_file_location("gate", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def rows():
    return [json.loads(x) for x in SEED.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_exact_seed_passes_nonpromoting_gate():
    result = gate.adjudicate_seed(rows())
    assert result["pass"], result
    assert result["source_seed_rows"] == 8
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["positive_jspace_causal_credit_minted"] == 0
    assert result["training_credit_minted"] == 0


def test_positive_jspace_label_is_rejected():
    r = copy.deepcopy(rows()[0])
    r["positive_jspace_label"] = True
    result = gate.adjudicate(r)
    assert not result["pass"]
    assert "POSITIVE_JSPACE_LABEL_FORBIDDEN" in result["failures"]


def test_causal_promotion_fields_are_rejected_from_method_seed():
    r = copy.deepcopy(rows()[0])
    r["causal_receipt_sha256"] = "0" * 64
    result = gate.adjudicate(r)
    assert not result["pass"]
    assert any(x.startswith("NONPROMOTING_METHOD_ROW_CONTAINS_CAUSAL_PROMOTION_FIELDS") for x in result["failures"])


def test_duplicate_family_is_rejected():
    rs = rows()
    rs[-1]["family_id"] = rs[0]["family_id"]
    result = gate.adjudicate_seed(rs)
    assert not result["pass"]
    assert "DUPLICATE_FAMILY_ID" in result["failures"]


def test_holdout_selected_row_is_rejected():
    r = copy.deepcopy(rows()[0])
    r["selected_using_holdout"] = True
    result = gate.adjudicate(r)
    assert not result["pass"]
    assert "HOLDOUT_SELECTION_FORBIDDEN" in result["failures"]


def test_transient_commit_identity_in_model_text_is_rejected():
    r = copy.deepcopy(rows()[0])
    r["prompt"] += " commit " + ("a" * 40)
    result = gate.adjudicate(r)
    assert not result["pass"]
    assert "PROMPT_MUST_NOT_MEMORIZE_TRANSIENT_COMMIT_IDENTITY" in result["failures"]
