from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


_TOOL = Path(__file__).parents[1] / "tools" / "trigger2_evidence_provenance_topology_ood_probe_v1.py"
_SPEC = importlib.util.spec_from_file_location("trigger2_evidence_provenance_topology_ood_probe_v1", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe)

OUTCOMES = probe.OUTCOMES
lexical_bag_sha256 = probe.lexical_bag_sha256
rows = probe.rows
semantic_topology_decision = probe.semantic_topology_decision
validate = probe.validate


def test_probe_validates_and_stays_method_only():
    report = validate()
    assert report["pass"] is True
    assert report["rows"] == 64
    assert report["counterfactual_pairs"] == 32
    assert report["pairwise_visible_lexical_bag_upper_bound"] == 0.5
    assert report["semantic_topology_reference_accuracy"] == 1.0
    assert report["training_eligible_rows"] == 0
    assert report["accepted_dataset_tokens_delta"] == 0
    assert report["model_runtime_credit"] == 0
    assert report["training_credit"] == 0


def test_every_opposite_label_pair_has_identical_visible_token_bag():
    grouped = defaultdict(list)
    for row in rows():
        grouped[row["pair_key"]].append(row)
    assert len(grouped) == 32
    for pair in grouped.values():
        assert {r["outcome_class_evaluator_only"] for r in pair} == set(OUTCOMES)
        assert pair[0]["visible_lexical_bag_sha256"] == pair[1]["visible_lexical_bag_sha256"]
        assert lexical_bag_sha256(pair[0]["model_visible_input"]) == lexical_bag_sha256(
            pair[1]["model_visible_input"]
        )


def test_development_and_ood_carrier_vocabularies_are_disjoint():
    vocab = defaultdict(set)
    for row in rows():
        vocab[row["split_evaluator_only"]].update(row["carrier_tokens_evaluator_only"])
    assert vocab["DEVELOPMENT"]
    assert vocab["OOD_HOLDOUT"]
    assert vocab["DEVELOPMENT"].isdisjoint(vocab["OOD_HOLDOUT"])


def test_structural_reference_generalizes_to_both_splits():
    by_split = defaultdict(list)
    for row in rows():
        by_split[row["split_evaluator_only"]].append(row)
    assert set(by_split) == {"DEVELOPMENT", "OOD_HOLDOUT"}
    for split_rows in by_split.values():
        assert all(
            semantic_topology_decision(row["model_visible_input"])
            == row["outcome_class_evaluator_only"]
            for row in split_rows
        )


def test_topology_counterfactual_flips_decision_without_changing_lexical_bag():
    pair = [row for row in rows() if row["pair_key"] == "OOD_HOLDOUT:01:01"]
    bound = next(r for r in pair if r["outcome_class_evaluator_only"] == OUTCOMES[0])
    claim_only = next(r for r in pair if r["outcome_class_evaluator_only"] == OUTCOMES[1])
    assert lexical_bag_sha256(bound["model_visible_input"]) == lexical_bag_sha256(
        claim_only["model_visible_input"]
    )
    assert semantic_topology_decision(bound["model_visible_input"]) == OUTCOMES[0]
    assert semantic_topology_decision(claim_only["model_visible_input"]) == OUTCOMES[1]


def test_target_or_split_leakage_fails_closed():
    bad = deepcopy(rows())
    bad[0]["model_visible_input"]["outcome_class_evaluator_only"] = bad[0][
        "outcome_class_evaluator_only"
    ]
    with pytest.raises(ValueError, match="^TARGET_OR_SPLIT_LEAKAGE$"):
        validate(bad)


def test_promotion_fence_violation_fails_closed():
    bad = deepcopy(rows())
    bad[0]["training_eligible"] = True
    with pytest.raises(ValueError, match="^PROMOTION_FENCE_VIOLATION$"):
        validate(bad)
