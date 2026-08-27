from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_evidence_provenance_counterfactual_probe_v1.py"
spec = importlib.util.spec_from_file_location("probe", MODULE_PATH)
probe = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(probe)


def test_current_probe_passes_and_is_nonpromoting():
    result = probe.validate()
    assert result["pass"] is True
    assert result["rows"] == 32
    assert result["counterfactual_pairs"] == 16
    assert result["nuisance_only_majority_accuracy"] == 0.5
    assert result["training_eligible_rows"] == 0
    assert result["accepted_dataset_tokens_delta"] == 0


def test_each_pair_keeps_claim_and_presentation_equal_but_flips_provenance_outcome():
    rows = probe.rows()
    by_pair = {}
    for row in rows:
        by_pair.setdefault(row["pair_key"], []).append(row)
    for pair in by_pair.values():
        assert len(pair) == 2
        assert pair[0]["model_visible_input"]["claim_payload"] == pair[1]["model_visible_input"]["claim_payload"]
        assert pair[0]["model_visible_input"]["presentation"] == pair[1]["model_visible_input"]["presentation"]
        assert pair[0]["model_visible_input"]["provenance"] != pair[1]["model_visible_input"]["provenance"]
        assert pair[0]["outcome_class_evaluator_only"] != pair[1]["outcome_class_evaluator_only"]


def test_target_leakage_fails_closed():
    rows = probe.rows()
    bad = deepcopy(rows)
    bad[0]["model_visible_input"]["evaluator_target"] = bad[0]["evaluator_target"]
    bad[0]["model_visible_input_sha256"] = probe.dg(bad[0]["model_visible_input"])
    with pytest.raises(ValueError, match="^TARGET_LEAKAGE$"):
        probe.validate(bad)


def test_presentation_shortcut_fails_pair_invariant():
    rows = probe.rows()
    bad = deepcopy(rows)
    for row in bad:
        row["model_visible_input"]["presentation"]["carrier_name"] = (
            "positive-carrier"
            if row["outcome_class_evaluator_only"] == "BOUND_EVIDENCE_CANDIDATE"
            else "negative-carrier"
        )
        row["model_visible_input_sha256"] = probe.dg(row["model_visible_input"])
    with pytest.raises(ValueError, match="^PAIR_PRESENTATION_MISMATCH:"):
        probe.validate(bad)


def test_claim_content_transplant_breaks_counterfactual_pair():
    rows = probe.rows()
    bad = deepcopy(rows)
    pair_key = bad[0]["pair_key"]
    mate_index = next(i for i, row in enumerate(bad[1:], 1) if row["pair_key"] == pair_key)
    bad[mate_index]["model_visible_input"]["claim_payload"]["member_count"] = 9
    bad[mate_index]["model_visible_input"]["claim_payload_sha256"] = probe.dg(
        bad[mate_index]["model_visible_input"]["claim_payload"]
    )
    bad[mate_index]["model_visible_input_sha256"] = probe.dg(bad[mate_index]["model_visible_input"])
    with pytest.raises(ValueError, match="^PAIR_CLAIM_CONTENT_MISMATCH:"):
        probe.validate(bad)


def test_training_promotion_fence_fails_closed():
    rows = probe.rows()
    bad = deepcopy(rows)
    bad[0]["training_eligible"] = True
    with pytest.raises(ValueError, match="^PROMOTION_FENCE_VIOLATION$"):
        probe.validate(bad)
