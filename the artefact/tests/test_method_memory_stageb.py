import json
import time
import uuid

import pytest

from clayverse.method_memory import METHOD_SCHEMA, MethodMemoryRetriever
from clayverse.store import UnifiedDB


def _episode(db, session_id, user_id, label):
    turn_id = db.append_turn(session_id, user_id, "user", label)
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "SELECTED"),
    )
    return episode_id


def _promoted(signature, source_episode_ids, *, calibration=0.7, support_count=3):
    return {
        "schema": METHOD_SCHEMA,
        "status": "PROMOTED",
        "problem_signature": {"task_shape": list(signature)},
        "preconditions": ["bounded inputs"],
        "goal_shape": list(signature),
        "method_steps": ["generate competing mechanisms", "run discriminator"],
        "invariants": ["do not mint factual truth"],
        "expected_observations": ["one mechanism separates"],
        "falsifiers": ["discriminator does not separate"],
        "failure_modes": ["proxy match"],
        "scope_limits": ["method guidance only"],
        "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": 1,
        "support_count": support_count,
        "success_count": 2,
        "failure_count": 1,
        "calibration": calibration,
        "last_validated_at": "2026-08-17T00:00:00Z",
    }


def _candidate(signature):
    return {
        "schema": METHOD_SCHEMA,
        "status": "CANDIDATE",
        "problem_signature": {"task_shape": list(signature)},
    }


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, session_id


def test_method_memory_is_canonical_but_separate_from_fact_memory(tmp_path):
    db, _ = _db(tmp_path)
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "diagnostic loop",
            _candidate(["diagnose", "validate"]),
            "gabriel",
            {"source": "test"},
        )
        assert db.db.execute("SELECT COUNT(*) FROM method_memory").fetchone()[0] == 1
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == 0
        receipt = db.db.execute("SELECT action FROM method_receipts WHERE memory_id=?", (mid,)).fetchone()
        assert receipt[0] == "CREATE"
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "8"
    finally:
        db.close()


def test_single_episode_candidate_cannot_be_served_or_directly_minted_as_framework(tmp_path):
    db, _ = _db(tmp_path)
    try:
        candidate_id = db.add_method_memory(
            "framework_candidate",
            "single anecdote",
            _candidate(["diagnose"]),
            "gabriel",
            {"source": "test"},
        )
        with pytest.raises(PermissionError):
            db.add_method_memory(
                "framework",
                "bypass",
                _promoted(["diagnose"], ["a", "b"]),
                "gabriel",
                {"source": "test"},
            )
        result = MethodMemoryRetriever(db).retrieve(
            query="What mechanism caused this failure?",
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert candidate_id not in [item["memory_id"] for item in result["items"]]
        assert result["fact_status"] == "UNKNOWN"
    finally:
        db.close()


def test_promotion_requires_two_real_source_episodes_and_is_receipted(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        candidate_id = db.add_method_memory(
            "framework_candidate",
            "cross-instance discriminator",
            _candidate(["diagnose", "validate"]),
            "gabriel",
            {"source": "test"},
        )
        e1 = _episode(db, session_id, "gabriel", "case one")
        e2 = _episode(db, session_id, "gabriel", "case two")
        payload = _promoted(["diagnose", "validate"], [e1, e2])
        db.promote_method_memory(candidate_id, "framework", payload, {"source": "promotion-test"})
        row = db.db.execute("SELECT kind,value FROM method_memory WHERE memory_id=?", (candidate_id,)).fetchone()
        assert row["kind"] == "framework"
        assert json.loads(row["value"])["status"] == "PROMOTED"
        assert db.db.execute("SELECT COUNT(*) FROM method_receipts WHERE memory_id=? AND action='PROMOTE'", (candidate_id,)).fetchone()[0] == 1
    finally:
        db.close()


def test_fact_unknown_plus_method_present_never_becomes_fact_present(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "mechanism discriminator",
            _candidate(["diagnose", "validate"]),
            "gabriel",
            {"source": "test"},
        )
        e1 = _episode(db, session_id, "gabriel", "case one")
        e2 = _episode(db, session_id, "gabriel", "case two")
        db.promote_method_memory(mid, "framework", _promoted(["diagnose", "validate"], [e1, e2]), {"source": "test"})
        result = MethodMemoryRetriever(db).retrieve(
            query="What mechanism explains this unfamiliar failure, and how can I test it?",
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["method_status"] == "PRESENT"
        assert result["fact_status"] == "UNKNOWN"
        assert result["items"][0]["truth_authority"] is False
        assert result["items"][0]["effect_authority"] is False
        assert result["policy_mode"] == "SHADOW"
    finally:
        db.close()


def test_counterexample_blocks_matching_framework(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "mechanism discriminator",
            _candidate(["diagnose", "validate"]),
            "gabriel",
            {"source": "test"},
        )
        e1 = _episode(db, session_id, "gabriel", "case one")
        e2 = _episode(db, session_id, "gabriel", "case two")
        db.promote_method_memory(mid, "framework", _promoted(["diagnose", "validate"], [e1, e2]), {"source": "test"})
        db.add_method_memory(
            "counterexample",
            "known boundary",
            {
                "schema": METHOD_SCHEMA,
                "status": "PROMOTED",
                "problem_signature": {"task_shape": ["diagnose", "validate"]},
                "blocks_method_ids": [mid],
            },
            "gabriel",
            {"source": "counterexample-test"},
        )
        result = MethodMemoryRetriever(db).retrieve(
            query="Why did this mechanism fail; verify the cause",
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["method_status"] == "UNKNOWN"
        assert result["counterevidence"]
    finally:
        db.close()


def test_demoted_method_stops_serving_without_deleting_receipt_history(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "recovery method",
            _candidate(["recovery", "validate"]),
            "gabriel",
            {"source": "test"},
        )
        e1 = _episode(db, session_id, "gabriel", "case one")
        e2 = _episode(db, session_id, "gabriel", "case two")
        db.promote_method_memory(mid, "framework", _promoted(["recovery", "validate"], [e1, e2]), {"source": "test"})
        db.demote_method_memory(mid, "counterevidence accumulated")
        result = MethodMemoryRetriever(db).retrieve(
            query="How do we recover after a crash and verify the restart?",
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert mid not in [item["memory_id"] for item in result["items"]]
        assert db.db.execute("SELECT COUNT(*) FROM method_receipts WHERE memory_id=? AND action='DEMOTE'", (mid,)).fetchone()[0] == 1
    finally:
        db.close()


def test_structural_match_beats_lexical_decoy_regression_only(tmp_path):
    # Regression-only rerun of the GO's one unusual ANALOGICAL_LEXICAL_DECOY experiment.
    db, session_id = _db(tmp_path)
    try:
        e1 = _episode(db, session_id, "gabriel", "case one")
        e2 = _episode(db, session_id, "gabriel", "case two")
        correct = db.add_method_memory("framework_candidate", "lease-epoch discriminator", _candidate(["diagnose", "validate"]), "gabriel", {"source": "test"})
        decoy = db.add_method_memory("framework_candidate", "mechanism unfamiliar failure cause experiment test", _candidate(["plan", "optimize"]), "gabriel", {"source": "test"})
        db.promote_method_memory(correct, "framework", _promoted(["diagnose", "validate"], [e1, e2], calibration=0.72), {"source": "test"})
        db.promote_method_memory(decoy, "framework", _promoted(["plan", "optimize"], [e1, e2], calibration=0.99), {"source": "test"})
        result = MethodMemoryRetriever(db).retrieve(
            query="What mechanism explains this unfamiliar failure, and which experiment would separate the cause?",
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert [item["memory_id"] for item in result["items"]] == [correct]
        assert decoy not in [item["memory_id"] for item in result["items"]]
        assert result["fact_status"] == "UNKNOWN"
    finally:
        db.close()
