from __future__ import annotations

import pytest

from clayverse.method_memory import (
    MethodRecordError,
    canonical_problem_signature,
    structural_score,
)
from clayverse.method_stage_b import StageBMethodRetrieval


def test_problem_signature_rejects_single_facet_for_structural_serving():
    """The canonical matcher needs enough explicit structure to compare facets."""
    with pytest.raises(MethodRecordError):
        canonical_problem_signature({"goal": ["recover"]})


def test_problem_signature_rejects_normalized_duplicate_facet_keys():
    with pytest.raises(MethodRecordError):
        canonical_problem_signature(
            {
                " Goal ": ["recover"],
                "goal": ["verify"],
            }
        )


def test_problem_signature_rejects_normalized_duplicate_values():
    with pytest.raises(MethodRecordError):
        canonical_problem_signature(
            {
                "goal": ["Recover", " recover "],
                "mechanism": ["causal"],
            }
        )


def test_structural_match_is_symmetric_equal_facet_average_not_named_facet_weighting():
    query = canonical_problem_signature(
        {
            "goal": ["recover"],
            "mechanism": ["causal"],
        }
    )
    candidate = canonical_problem_signature(
        {
            "goal": ["recover"],
            "mechanism": ["other"],
            "resource_shape": ["database"],
        }
    )
    # One of three union facets matches. The extra candidate facet must count against
    # the match, and the facet name itself must not grant hidden extra weight.
    assert structural_score(query, candidate) == pytest.approx(1.0 / 3.0)
    assert structural_score(query, candidate) == pytest.approx(
        structural_score(candidate, query)
    )


def test_matching_values_in_wrong_facets_score_zero():
    query = canonical_problem_signature(
        {
            "goal": ["recover"],
            "mechanism": ["causal"],
        }
    )
    wrong = canonical_problem_signature(
        {
            "goal": ["causal"],
            "mechanism": ["recover"],
        }
    )
    assert structural_score(query, wrong) == 0.0


def test_matcher_semantics_change_requires_stage_b_receipt_policy_bump():
    """Replay identity must not silently cross the v2 weighted-matcher semantics."""
    assert StageBMethodRetrieval.POLICY_VERSION >= 3
    assert StageBMethodRetrieval.RECEIPT_SCHEMA != "clayverse-stage-b-method-use/v2"
