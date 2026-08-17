from __future__ import annotations

import pytest

from clayverse.method_memory import MethodRecordError, canonical_problem_signature, structural_similarity


def test_extra_candidate_structure_is_penalized_symmetrically():
    query = canonical_problem_signature({
        "topology": ["shared state"],
        "risk": ["stale replay"],
    })
    candidate = canonical_problem_signature({
        "topology": ["shared state"],
        "risk": ["stale replay"],
        "storage": ["immutable snapshot"],
        "authority": ["independent writer"],
        "goal": ["format output"],
    })
    assert structural_similarity(query, candidate) == pytest.approx(0.4)


def test_values_in_wrong_facet_do_not_count_as_structure_match():
    query = canonical_problem_signature({
        "topology": ["shared state"],
        "risk": ["stale replay"],
    })
    candidate = canonical_problem_signature({
        "topology": ["stale replay"],
        "risk": ["shared state"],
    })
    assert structural_similarity(query, candidate) == 0.0


def test_signature_normalization_duplicates_fail_closed():
    with pytest.raises(MethodRecordError, match="normalized duplicates"):
        canonical_problem_signature({
            "topology": ["Shared State", "shared state"],
            "risk": ["stale replay"],
        })
