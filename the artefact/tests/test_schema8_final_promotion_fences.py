from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.method_validation import CandidateValidation
from clayverse.store import UnifiedDB


def _db(tmp_path):
    path = tmp_path / "u.db"
    db = UnifiedDB(path)
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid, path


def _source_episode(db: UnifiedDB, sid: str, label: str):
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
        (causal_id, episode_id, None, turn_id, "formation-outcome", 0.0, 1, now),
    )
    return turn_id, episode_id


def _active(db: UnifiedDB, sid: str, query: str):
    turn_id = db.append_turn(sid, "gabriel", "user", query)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    generation = db.entity_generation()
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, sid, now, turn_id, 1.0, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (sid, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, now),
    )
    return turn_id, episode_id, causal_id, generation


def _candidate_record(source_episode_ids, support_memory_id):
    return {
        "problem_signature": {"goal": ["diagnose"], "mechanism": ["causal_boundary"]},
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
        # Descriptive candidate counters are never promotion authority.
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 1.0,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }


def _candidate(db: UnifiedDB, sid: str, *, support_memory_id: str | None = None):
    turn1, ep1 = _source_episode(db, sid, "formation one")
    _, ep2 = _source_episode(db, sid, "formation two")
    if support_memory_id is None:
        support_memory_id = db.add_memory(
            "fact", "validated-support", "bounded observation", turn1, "gabriel", {"source": "test"}
        )
    candidate_id = db.add_method_memory(
        "framework_candidate",
        "causal-boundary-diagnosis",
        _candidate_record([ep1, ep2], support_memory_id),
        turn1,
        "gabriel",
        {"source": "test-abstraction"},
    )
    return candidate_id


def _finalize_validation(
    db: UnifiedDB,
    sid: str,
    candidate_id: str,
    *,
    classification: str,
    falsifier_checked: bool,
    evaluation_mode: str = "HELD_OUT",
):
    turn_id, episode_id, causal_id, generation = _active(db, sid, "held-out validation case")
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
        problem_signature={"goal": ["diagnose"], "mechanism": ["causal_boundary"]},
        evaluation_mode=evaluation_mode,
        falsifier_checked=falsifier_checked,
    )
    now = time.time()
    effect_id = str(uuid.uuid4())
    status = "VERIFIED" if classification == "SUCCESS" else "FAILED"
    credit = 1.0 if classification == "SUCCESS" else -1.0
    outcome_hash = hashlib.sha256(f"{classification}:{causal_id}".encode()).hexdigest()
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (effect_id, episode_id, "gabriel", "entityos.exec", "{}", None, generation, status, "{}", now, now),
    )
    db.db.execute(
        "UPDATE workspace_episodes SET selected='respond',state='COMPLETED' WHERE episode_id=?",
        (episode_id,),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,1,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, credit, now),
    )
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (sid,))
    return validator.finalize(candidate_use_receipt_id=use_id)


def _promoted(db: UnifiedDB, sid: str):
    candidate_id = _candidate(db, sid)
    _finalize_validation(db, sid, candidate_id, classification="SUCCESS", falsifier_checked=True)
    _finalize_validation(db, sid, candidate_id, classification="SUCCESS", falsifier_checked=False)
    result = db.promote_method_memory(
        candidate_id,
        evaluation="two positive held-out causal validations",
        provenance={"source": "test-promotion"},
    )
    return candidate_id, result


def test_one_success_plus_one_failure_cannot_promote_reusable_method(tmp_path):
    db, sid, _ = _db(tmp_path)
    try:
        candidate_id = _candidate(db, sid)
        _finalize_validation(db, sid, candidate_id, classification="SUCCESS", falsifier_checked=True)
        _finalize_validation(db, sid, candidate_id, classification="FAILURE", falsifier_checked=False)
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="two validated successes"):
            db.promote_method_memory(
                candidate_id,
                evaluation="one anecdotal success must not mint reusable method",
                provenance={"source": "anti-anecdote-gate"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0
    finally:
        db.close()


def test_shadow_history_does_not_count_or_poison_later_true_heldout_transfer(tmp_path):
    db, sid, _ = _db(tmp_path)
    try:
        candidate_id = _candidate(db, sid)
        shadow_receipt = _finalize_validation(
            db,
            sid,
            candidate_id,
            classification="SUCCESS",
            falsifier_checked=True,
            evaluation_mode="SHADOW",
        )
        heldout_one = _finalize_validation(
            db,
            sid,
            candidate_id,
            classification="SUCCESS",
            falsifier_checked=True,
        )
        heldout_two = _finalize_validation(
            db,
            sid,
            candidate_id,
            classification="SUCCESS",
            falsifier_checked=False,
        )
        result = db.promote_method_memory(
            candidate_id,
            evaluation="shadow history is audit-only; two later held-out successes authorize transfer",
            provenance={"source": "shadow-to-heldout-gate"},
        )
        promoted = db.method_memory(result["promoted_memory_id"])
        assert promoted["value"]["support_count"] == 2
        assert promoted["value"]["success_count"] == 2
        assert promoted["value"]["failure_count"] == 0
        receipt = db.method_memory(result["receipt_memory_id"])
        assert receipt["value"]["validation_receipt_ids"] == [heldout_one, heldout_two]
        assert shadow_receipt not in receipt["value"]["validation_receipt_ids"]
    finally:
        db.close()


def test_method_memory_cannot_recursively_serve_as_support_for_promotion(tmp_path):
    db, sid, _ = _db(tmp_path)
    try:
        seed_candidate_id = _candidate(db, sid)
        candidate_id = _candidate(db, sid, support_memory_id=seed_candidate_id)
        with pytest.raises(MethodMemoryValidationError, match="supporting evidence cannot be method memory"):
            db.promote_method_memory(
                candidate_id,
                evaluation="method memory must not self-reinforce as evidence",
                provenance={"source": "recursive-support-gate"},
            )
    finally:
        db.close()


def test_reopen_rejects_promote_receipt_whose_source_sets_drift_from_promoted_payload(tmp_path):
    db, sid, path = _db(tmp_path)
    candidate_id, result = _promoted(db, sid)
    receipt_id = result["receipt_memory_id"]
    promoted_id = result["promoted_memory_id"]
    promoted = db.method_memory(promoted_id)
    expected_sources = list(promoted["value"]["source_episode_ids"])
    db.close()

    # Simulate out-of-band durable corruption that bypasses normal immutable triggers.
    raw = sqlite3.connect(path)
    try:
        raw.execute("DROP TRIGGER durable_method_memory_immutable")
        row = raw.execute("SELECT value FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
        payload = json.loads(row[0])
        payload["source_episode_ids"] = ["episode:tampered-source"]
        raw.execute(
            "UPDATE durable_memory SET value=? WHERE memory_id=?",
            (json.dumps(payload, sort_keys=True, separators=(",", ":")), receipt_id),
        )
        raw.commit()
    finally:
        raw.close()

    with pytest.raises(MethodMemoryValidationError, match="promotion receipt source/support/counterexample drift"):
        UnifiedDB(path)

    # Sanity: the corruption changed only lifecycle lineage, not the promoted payload itself.
    raw = sqlite3.connect(path)
    try:
        promoted_payload = json.loads(raw.execute("SELECT value FROM durable_memory WHERE memory_id=?", (promoted_id,)).fetchone()[0])
        assert promoted_payload["source_episode_ids"] == expected_sources
        assert raw.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id=?", (candidate_id,)).fetchone()[0] == 1
    finally:
        raw.close()
