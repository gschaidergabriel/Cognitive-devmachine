from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid


def _source_episode(db: UnifiedDB, sid: str, label: str, *, credit: float = 0.0):
    turn_id = db.append_turn(sid, "gabriel", "user", label)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, sid, now, turn_id, 1.0, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, None, turn_id, "source-outcome", float(credit), 1, now),
    )
    return turn_id, episode_id


def _candidate_record(source_episode_ids, support_memory_id, *, success_count: int):
    failure_count = 2 - success_count
    return {
        "problem_signature": {
            "goal": ["diagnose"],
            "mechanism": ["causal_boundary"],
        },
        "preconditions": ["a bounded dependency exists"],
        "goal_shape": "diagnose",
        "method_steps": ["isolate dependency", "run bounded falsifier"],
        "invariants": ["facts remain unknown until evidence arrives"],
        "expected_observations": ["failure follows the isolated dependency"],
        "falsifiers": ["failure persists after dependency removal"],
        "failure_modes": ["surface similarity without causal equivalence"],
        "scope_limits": ["diagnostic method only"],
        "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": [support_memory_id],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        # Deliberately caller-supplied counters. These are not validation authority.
        "support_count": 2,
        "success_count": success_count,
        "failure_count": failure_count,
        "calibration": success_count / 2.0,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }


def _candidate(db: UnifiedDB, sid: str, *, success_count: int):
    turn1, ep1 = _source_episode(db, sid, "formation one", credit=0.0)
    _, ep2 = _source_episode(db, sid, "formation two", credit=0.0)
    support_id = db.add_memory(
        "fact", "support", "formation evidence", turn1, "gabriel", {"source": "promotion-authority-gate"}
    )
    candidate_id = db.add_method_memory(
        "framework_candidate",
        "causal-boundary-diagnosis",
        _candidate_record([ep1, ep2], support_id, success_count=success_count),
        turn1,
        "gabriel",
        {"source": "promotion-authority-gate"},
    )
    return candidate_id


def _assert_no_positive_promotion_rows(db: UnifiedDB, before: int):
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('framework','heuristic')"
    ).fetchone()[0] == 0


def test_terminal_reentry_plus_caller_success_counters_cannot_authorize_promotion(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id = _candidate(db, sid, success_count=2)
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError):
            db.promote_method_memory(
                candidate_id,
                evaluation="caller text is not held-out validation evidence",
                provenance={"source": "promotion-authority-gate"},
            )
        _assert_no_positive_promotion_rows(db, before)
    finally:
        db.close()


def test_one_claimed_success_is_not_reusable_transfer_evidence(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id = _candidate(db, sid, success_count=1)
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError):
            db.promote_method_memory(
                candidate_id,
                evaluation="one claimed success cannot promote reusable method",
                provenance={"source": "promotion-authority-gate"},
            )
        _assert_no_positive_promotion_rows(db, before)
    finally:
        db.close()
