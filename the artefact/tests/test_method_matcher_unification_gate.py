from __future__ import annotations

import pytest

from clayverse.method_memory import MethodRecordError, canonical_problem_signature, structural_score
from clayverse.method_stage_b import StageBMethodRetrieval


def test_normalized_duplicate_signature_values_fail_closed():
    with pytest.raises(MethodRecordError):
        canonical_problem_signature({
            "topology": ["Shared State", "shared state"],
            "risk": ["stale replay"],
        })


def test_structural_facets_have_one_symmetric_similarity_law_not_privileged_goal_weights():
    query = canonical_problem_signature({
        "goal": ["recover"],
        "topology": ["shared state"],
    })
    candidate = canonical_problem_signature({
        "goal": ["recover"],
        "topology": ["independent state"],
    })
    # Exactly one of two equally structural facets matches. A special goal/mechanism
    # weight would return 2/3 and silently create a second matcher semantics.
    assert structural_score(query, candidate) == pytest.approx(0.5)
    assert structural_score(candidate, query) == pytest.approx(0.5)


def test_matcher_semantic_change_advances_stage_b_replay_policy_identity():
    # Stage-B v2 receipts were defined before the canonical matcher fusion. Replaying
    # them under a changed matcher law without a policy/version bump would make the same
    # request identity resolve under different semantics.
    assert StageBMethodRetrieval.POLICY_VERSION > 2
