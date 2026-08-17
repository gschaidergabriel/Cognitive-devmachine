import time

import pytest

from clayverse.method_memory import MethodMemory, MethodMemoryError
from clayverse.store import UnifiedDB


def _record(signature, *, status="PROMOTED", support=2, episodes=None, counters=None, calibration=0.8, receipt="promotion-1"):
    value = {
        "problem_signature": signature,
        "preconditions": ["bounded input"],
        "goal_shape": "diagnose",
        "method_steps": ["generate competing mechanisms", "run discriminator"],
        "invariants": ["do not mint truth"],
        "expected_observations": ["one mechanism separates"],
        "falsifiers": ["both mechanisms predict same observation"],
        "failure_modes": ["proxy overfit"],
        "scope_limits": ["requires observable discriminator"],
        "source_episode_ids": episodes or ["episode-a", "episode-b"],
        "supporting_memory_ids": ["evidence-a", "evidence-b"],
        "counterexample_memory_ids": counters or [],
        "provenance": {"source": "test", "complete": True},
        "abstraction_version": 1,
        "support_count": support,
        "success_count": 2,
        "failure_count": 0,
        "calibration": calibration,
        "last_validated_at": time.time(),
        "status": status,
        "promotion_receipt_id": receipt,
    }
    if receipt is None:
        value.pop("promotion_receipt_id")
    return value


def test_structural_method_retrieval_does_not_depend_on_lexical_topic(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        mm = MethodMemory(db)
        signature = {
            "goal": "diagnose",
            "uncertainty": "unknown",
            "mechanism": "competing-hypotheses",
            "evidence_shape": "discriminator",
        }
        framework_id = mm.admit(
            kind="framework",
            name="mechanism discriminator",
            record=_record(signature),
            user_id="gabriel",
        )
        hit = mm.retrieve(problem_signature=signature, user_id="gabriel")
        assert [item["memory_id"] for item in hit["methods"]] == [framework_id]
        assert hit["receipt"]["structural_only"] is True
        assert all(item["truth_authority"] is False for item in hit["methods"])

        miss = mm.retrieve(
            problem_signature={
                "goal": "summarize",
                "uncertainty": "known",
                "mechanism": "single-description",
                "evidence_shape": "complete",
            },
            user_id="gabriel",
        )
        assert miss["methods"] == []
        assert miss["receipt"]["status"] == "UNKNOWN"
    finally:
        db.close()


def test_candidates_are_not_served_and_single_success_cannot_promote(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        mm = MethodMemory(db)
        signature = {"goal": "diagnose", "uncertainty": "unknown"}
        mm.admit(
            kind="framework_candidate",
            name="candidate only",
            record=_record(signature, status="CANDIDATE", support=0, episodes=["episode-c"], receipt=None),
            user_id="gabriel",
        )
        assert mm.retrieve(problem_signature=signature, user_id="gabriel")["methods"] == []

        with pytest.raises(MethodMemoryError, match="two source episodes|cross-instance"):
            mm.admit(
                kind="framework",
                name="single anecdote",
                record=_record(signature, support=1, episodes=["episode-one"]),
                user_id="gabriel",
            )
    finally:
        db.close()


def test_malformed_records_and_privacy_fail_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        db.ensure_user("andreas", "Andreas")
        mm = MethodMemory(db)
        signature = {"goal": "diagnose", "uncertainty": "unknown"}
        mm.admit(kind="framework", name="private", record=_record(signature), user_id="gabriel")
        db.add_memory("framework", "malformed", "{}", None, "gabriel", {"source": "test"})

        own = mm.retrieve(problem_signature=signature, user_id="gabriel")
        assert own["receipt"]["malformed_rejected_count"] == 1
        other = mm.retrieve(problem_signature=signature, user_id="andreas")
        assert other["methods"] == []
    finally:
        db.close()


def test_matching_linked_counterexample_blocks_framework(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        mm = MethodMemory(db)
        signature = {
            "goal": "diagnose",
            "uncertainty": "unknown",
            "mechanism": "competing-hypotheses",
        }
        counter_id = mm.admit(
            kind="counterexample",
            name="known counterexample",
            record=_record(signature, calibration=0.9),
            user_id="gabriel",
        )
        blocked_id = mm.admit(
            kind="framework",
            name="blocked framework",
            record=_record(signature, counters=[counter_id], receipt="promotion-2"),
            user_id="gabriel",
        )
        result = mm.retrieve(problem_signature=signature, user_id="gabriel")
        assert blocked_id not in [item["memory_id"] for item in result["methods"]]
        assert counter_id in [item["memory_id"] for item in result["counterevidence"]]
        assert result["receipt"]["blocked_count"] >= 1
    finally:
        db.close()
