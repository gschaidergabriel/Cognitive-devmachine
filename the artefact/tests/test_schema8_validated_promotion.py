from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.method_validation import CandidateValidation
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid


def _formation_episode(db: UnifiedDB, sid: str, label: str):
    turn_id = db.append_turn(sid, "gabriel", "user", label)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, sid, now, turn_id, 1.0, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, None, turn_id, f"formation:{episode_id}", 0.0, 1, now),
    )
    return turn_id, episode_id


def _candidate(db: UnifiedDB, sid: str):
    turn1, ep1 = _formation_episode(db, sid, "formation one")
    _, ep2 = _formation_episode(db, sid, "formation two")
    support_id = db.add_memory(
        "fact", "support", "formation evidence", turn1, "gabriel", {"source": "validated-promotion-test"}
    )
    candidate = {
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
        "source_episode_ids": [ep1, ep2],
        "supporting_memory_ids": [support_id],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        # Deliberately caller supplied. Promotion must not trust these counters.
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 1.0,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }
    candidate_id = db.add_method_memory(
        "framework_candidate",
        "causal-boundary-diagnosis",
        candidate,
        turn1,
        "gabriel",
        {"source": "validated-promotion-test"},
    )
    return candidate_id, candidate


def _validate_once(
    db: UnifiedDB,
    sid: str,
    candidate_id: str,
    signature: dict,
    *,
    success: bool,
    falsifier_checked: bool,
    evaluation_mode: str = "HELD_OUT",
):
    generation = db.entity_generation()
    turn_id = db.append_turn(sid, "gabriel", "user", "held-out validation")
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, sid, now, turn_id, 1.0, "[]", "validate", "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,started_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (sid, "gabriel", turn_id, episode_id, causal_id, generation, "[]", now),
    )
    validator = CandidateValidation(db)
    use_id = validator.begin(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=sid,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature=signature,
        evaluation_mode=evaluation_mode,
        falsifier_checked=falsifier_checked,
    )

    status = "VERIFIED" if success else "FAILED"
    outcome = {"ok": bool(success), "validation": True}
    effect_id = db.record_effect(
        episode_id,
        "gabriel",
        "entityos.exec",
        "validation:bounded",
        generation,
        status,
        argv=["validate"],
        outcome=outcome,
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            causal_id,
            episode_id,
            effect_id,
            turn_id,
            f"validation:{causal_id}",
            1.0 if success else -1.0,
            1,
            time.time(),
        ),
    )
    db.db.execute("UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=?", (episode_id,))
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (sid,))
    receipt_id = validator.finalize(candidate_use_receipt_id=use_id)
    return episode_id, receipt_id


def test_caller_counters_without_validation_cannot_promote(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, _ = _candidate(db, sid)
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="held-out causal outcome receipts"):
            db.promote_method_memory(
                candidate_id,
                evaluation="caller counters are not validation",
                provenance={"source": "test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    finally:
        db.close()


def test_two_true_heldout_successes_promote_and_bind_receipts(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, candidate = _candidate(db, sid)
        _, receipt1 = _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=True, falsifier_checked=True
        )
        _, receipt2 = _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=True, falsifier_checked=False
        )
        result = db.promote_method_memory(
            candidate_id,
            evaluation="two disjoint held-out causal successes",
            provenance={"source": "held-out promotion"},
        )
        promoted = db.method_memory(result["promoted_memory_id"])
        assert promoted["kind"] == "framework"
        assert promoted["value"]["status"] == "PROMOTED"
        assert promoted["value"]["support_count"] == 2
        assert promoted["value"]["success_count"] == 2
        assert promoted["value"]["failure_count"] == 0
        assert promoted["value"]["calibration"] == 1.0
        assert promoted["provenance"]["validation_receipt_ids"] == [receipt1, receipt2]
        assert len(promoted["provenance"]["validation_evidence_sha256"]) == 64
        # Read-time lineage validation must also succeed after reopen.
        promoted_id = result["promoted_memory_id"]
        db.close()
        db = UnifiedDB(tmp_path / "u.db")
        assert db.method_memory(promoted_id)["value"]["success_count"] == 2
    finally:
        db.close()


def test_one_success_one_failure_is_not_reusable_transfer(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, candidate = _candidate(db, sid)
        _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=True, falsifier_checked=True
        )
        _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=False, falsifier_checked=False
        )
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="held-out causal outcome receipts"):
            db.promote_method_memory(
                candidate_id,
                evaluation="one anecdotal success is insufficient",
                provenance={"source": "test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
        assert db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('framework','heuristic')"
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_shadow_or_in_sample_validation_cannot_promote(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, candidate = _candidate(db, sid)
        _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=True,
            falsifier_checked=True, evaluation_mode="SHADOW"
        )
        _validate_once(
            db, sid, candidate_id, candidate["problem_signature"], success=True,
            falsifier_checked=False, evaluation_mode="SHADOW"
        )
        with pytest.raises(MethodMemoryValidationError, match="held-out causal outcome receipts"):
            db.promote_method_memory(
                candidate_id, evaluation="shadow is not held out", provenance={"source": "test"}
            )
    finally:
        db.close()
