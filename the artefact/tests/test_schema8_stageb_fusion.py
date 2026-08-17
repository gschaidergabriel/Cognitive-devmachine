from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.method_stageb import (
    AdmittedMethodRetriever,
    MethodRetrievalIdentityError,
    ProblemSignatureAdmissionError,
    QUERY_ADMISSION_VERSION,
    QUERY_SCHEMA,
)
from clayverse.method_validation import CandidateValidation, MethodValidationError
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid


def _source_episode(db: UnifiedDB, sid: str, label: str):
    turn_id = db.append_turn(sid, "gabriel", "user", label)
    episode_id = str(uuid.uuid4()); causal_id = str(uuid.uuid4()); now = time.time()
    db.db.execute("INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)", (episode_id, sid, now, turn_id, 1.0, "[]", "respond", "COMPLETED"))
    db.db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)", (causal_id, episode_id, None, turn_id, "source-outcome", 0.0, 1, now))
    return turn_id, episode_id


def _active(db: UnifiedDB, sid: str, query: str):
    turn_id = db.append_turn(sid, "gabriel", "user", query)
    episode_id = str(uuid.uuid4()); causal_id = str(uuid.uuid4()); generation = db.entity_generation(); now = time.time()
    db.db.execute("INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)", (episode_id, sid, now, turn_id, 1.0, "[]", None, "OPEN"))
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (sid, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, now),
    )
    return turn_id, episode_id, causal_id, generation


def _candidate_record(source_episode_ids, support_memory_id):
    return {
        "problem_signature": {"goal": ["diagnose"], "mechanism": ["causal_boundary"]},
        "preconditions": ["a bounded dependency exists"], "goal_shape": "diagnose",
        "method_steps": ["isolate dependency", "run bounded falsifier"],
        "invariants": ["facts remain unknown until evidence arrives"],
        "expected_observations": ["failure follows the isolated dependency"],
        "falsifiers": ["failure persists after dependency removal"],
        "failure_modes": ["surface similarity without causal equivalence"],
        "scope_limits": ["diagnostic method only"], "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": [support_memory_id], "counterexample_memory_ids": [],
        "abstraction_version": "1",
        # Candidate counters are descriptive claims only. Promotion overwrites them from held-out receipts.
        "support_count": 2, "success_count": 2, "failure_count": 0, "calibration": 1.0,
        "last_validated_at": None, "status": "CANDIDATE",
    }


def _candidate(db: UnifiedDB, sid: str):
    turn1, ep1 = _source_episode(db, sid, "abstraction source one")
    _, ep2 = _source_episode(db, sid, "abstraction source two")
    support_id = db.add_memory("fact", "validated-support", "bounded causal observation", turn1, "gabriel", {"source": "test"})
    candidate_id = db.add_method_memory(
        "framework_candidate", "causal-boundary-diagnosis", _candidate_record([ep1, ep2], support_id),
        turn1, "gabriel", {"source": "test-abstraction"},
    )
    return candidate_id, {ep1, ep2}


def _finalize_external_result(
    db: UnifiedDB,
    sid: str,
    candidate_id: str,
    *,
    success: bool,
    falsifier_checked: bool,
    outcome_ok: bool | None = None,
):
    turn_id, episode_id, causal_id, generation = _active(db, sid, "held-out validation case")
    validator = CandidateValidation(db)
    use_id = validator.begin(
        candidate_memory_id=candidate_id, user_id="gabriel", session_id=sid, turn_id=turn_id,
        episode_id=episode_id, causal_id=causal_id, generation=generation, evidence_status="UNKNOWN",
        problem_signature={"goal": ["diagnose"], "mechanism": ["causal_boundary"]},
        evaluation_mode="HELD_OUT", falsifier_checked=falsifier_checked,
    )
    status = "VERIFIED" if success else "FAILED"
    payload_ok = success if outcome_ok is None else bool(outcome_ok)
    payload = json.dumps({"ok": payload_ok}, sort_keys=True)
    effect_id = str(uuid.uuid4()); now = time.time()
    outcome_hash = hashlib.sha256(f"{status}:{payload}:{causal_id}".encode()).hexdigest()
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (effect_id, episode_id, "gabriel", "entityos.exec", "{}", None, generation, status, payload, now, now),
    )
    db.db.execute("UPDATE workspace_episodes SET selected='respond',state='COMPLETED' WHERE episode_id=?", (episode_id,))
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,1,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, 1.0 if success else -1.0, now),
    )
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (sid,))
    validation_id = validator.finalize(candidate_use_receipt_id=use_id)
    return episode_id, validation_id


def _finalize_external_success(db: UnifiedDB, sid: str, candidate_id: str, *, falsifier_checked: bool):
    return _finalize_external_result(
        db, sid, candidate_id, success=True, falsifier_checked=falsifier_checked
    )


def _promoted_method(db: UnifiedDB, sid: str):
    candidate_id, source_ids = _candidate(db, sid)
    heldout1, _ = _finalize_external_success(db, sid, candidate_id, falsifier_checked=True)
    heldout2, _ = _finalize_external_success(db, sid, candidate_id, falsifier_checked=False)
    assert heldout1 not in source_ids and heldout2 not in source_ids
    promoted = db.promote_method_memory(candidate_id, evaluation="two held-out causal validations support transfer", provenance={"source": "test-promotion"})
    return promoted["promoted_memory_id"]


def _problem_query(turn_id, episode_id, causal_id, generation, *, source="structured_hook_v1"):
    return {
        "schema": QUERY_SCHEMA,
        "problem_signature": {"goal": ["diagnose"], "mechanism": ["causal_boundary"]},
        "goal_shape": "diagnose",
        "provenance": {"source": source, "turn_id": turn_id, "episode_id": episode_id,
                       "causal_id": causal_id, "generation": generation, "admission_version": QUERY_ADMISSION_VERSION},
    }


def test_schema8_keeps_method_records_in_durable_memory_only(tmp_path):
    db, _ = _db(tmp_path)
    try:
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "8"
        tables = {row["name"] for row in db.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "method_use_receipts" in tables and "method_records" not in tables
        assert "limit_items" in {row["name"] for row in db.db.execute("PRAGMA table_info(retrieval_episodes)").fetchall()}
    finally: db.close()


def test_reserved_method_kinds_require_canonical_admission(tmp_path):
    db, _ = _db(tmp_path)
    try:
        with pytest.raises(MethodMemoryValidationError, match="reserved method-memory kind"):
            db.add_memory("framework_candidate", "bypass", "{}", None, "gabriel", {"source": "bypass"})
        with pytest.raises(sqlite3.DatabaseError):
            db.db.execute("INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), "framework_candidate", "raw", "{}", None, "gabriel", time.time(), json.dumps({"source": "raw"})))
    finally: db.close()


def test_promotion_stats_come_from_distinct_heldout_receipts_not_candidate_claims(tmp_path):
    db, sid = _db(tmp_path)
    try:
        promoted_id = _promoted_method(db, sid); promoted = db.method_memory(promoted_id)
        assert promoted["kind"] == "framework" and promoted["value"]["status"] == "PROMOTED"
        assert promoted["value"]["support_count"] == 2 and promoted["value"]["success_count"] == 2
        assert len(promoted["provenance"]["validation_receipt_ids"]) == 2
        assert len(promoted["provenance"]["validation_evidence_sha256"]) == 64
    finally: db.close()


def test_one_success_one_failure_cannot_promote_reusable_method(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, _ = _candidate(db, sid)
        _finalize_external_result(db, sid, candidate_id, success=True, falsifier_checked=True)
        _finalize_external_result(db, sid, candidate_id, success=False, falsifier_checked=False)
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="held-out causal validation receipts"):
            db.promote_method_memory(
                candidate_id,
                evaluation="one anecdotal success is insufficient transfer evidence",
                provenance={"source": "anti-anecdote-test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind IN ('framework','heuristic')").fetchone()[0] == 0
    finally: db.close()


def test_verified_positive_credit_requires_outcome_ok_true(tmp_path):
    db, sid = _db(tmp_path)
    try:
        candidate_id, _ = _candidate(db, sid)
        before = db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt' AND subject LIKE ?",
            (f"candidate_validation:{candidate_id}:%",),
        ).fetchone()[0]
        with pytest.raises(MethodValidationError, match="outcome ok=true"):
            _finalize_external_result(
                db, sid, candidate_id, success=True, falsifier_checked=True, outcome_ok=False
            )
        after = db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt' AND subject LIKE ?",
            (f"candidate_validation:{candidate_id}:%",),
        ).fetchone()[0]
        assert after == before == 0
    finally: db.close()


def test_stage_b_preserves_fact_unknown_and_replays_exact_request(tmp_path):
    db, sid = _db(tmp_path)
    try:
        promoted_id = _promoted_method(db, sid)
        turn_id, episode_id, causal_id, generation = _active(db, sid, "new unknown diagnostic problem")
        query = _problem_query(turn_id, episode_id, causal_id, generation); stage_b = AdmittedMethodRetriever(db)
        result = stage_b.retrieve(problem_query=query, user_id="gabriel", session_id=sid, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation, fact_status="UNKNOWN",
            resource_refs=["repo:clayverse"], limit=4, budget_chars=24_000)
        assert [item["memory_id"] for item in result["items"]] == [promoted_id]
        assert result["receipt"]["fact_status"] == "UNKNOWN" and result["receipt"]["truth_authority"] is False
        assert result["receipt"]["effect_authority"] is False and result["receipt"]["served"] is False
        replay = stage_b.retrieve(problem_query=query, user_id="gabriel", session_id=sid, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation, fact_status="UNKNOWN",
            resource_refs=["repo:clayverse"], limit=4, budget_chars=24_000)
        assert replay["receipt"]["replayed"] is True
        with pytest.raises(MethodRetrievalIdentityError, match="method_retrieval_identity"):
            stage_b.retrieve(problem_query=query, user_id="gabriel", session_id=sid, turn_id=turn_id,
                episode_id=episode_id, causal_id=causal_id, generation=generation, fact_status="UNKNOWN",
                resource_refs=["repo:clayverse"], limit=4, budget_chars=12_000)
    finally: db.close()


def test_raw_prompt_source_cannot_become_stage_b_signature_authority(tmp_path):
    db, sid = _db(tmp_path)
    try:
        turn_id, episode_id, causal_id, generation = _active(db, sid, "surface words")
        with pytest.raises(ProblemSignatureAdmissionError, match="raw-prompt lexical derivation"):
            AdmittedMethodRetriever(db).retrieve(problem_query=_problem_query(turn_id, episode_id, causal_id, generation, source="raw_prompt"),
                user_id="gabriel", session_id=sid, turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation, fact_status="UNKNOWN")
    finally: db.close()


def test_demotion_suppresses_new_turn_without_rewriting_old_replay(tmp_path):
    db, sid = _db(tmp_path)
    try:
        promoted_id = _promoted_method(db, sid); t1, e1, c1, g1 = _active(db, sid, "first unknown"); stage_b = AdmittedMethodRetriever(db)
        first = stage_b.retrieve(problem_query=_problem_query(t1, e1, c1, g1), user_id="gabriel", session_id=sid,
            turn_id=t1, episode_id=e1, causal_id=c1, generation=g1, fact_status="UNKNOWN")
        assert [item["memory_id"] for item in first["items"]] == [promoted_id]
        db.db.execute("DELETE FROM active_turns WHERE session_id=?", (sid,))
        db.transition_method_memory(promoted_id, action="DEMOTE", evaluation="held-out transfer failed", provenance={"source": "test-demotion"})
        t2, e2, c2, g2 = _active(db, sid, "second unknown")
        second = stage_b.retrieve(problem_query=_problem_query(t2, e2, c2, g2), user_id="gabriel", session_id=sid,
            turn_id=t2, episode_id=e2, causal_id=c2, generation=g2, fact_status="UNKNOWN")
        assert second["items"] == []
    finally: db.close()
