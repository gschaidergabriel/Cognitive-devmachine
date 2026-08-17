from __future__ import annotations

import pytest

from clayverse.method_memory import (
    MethodRecordError,
    canonical_problem_signature,
    structural_score,
)


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
