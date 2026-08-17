from __future__ import annotations

import hashlib
import json
import time

import pytest

from clayverse.method_memory import MethodMemory
from clayverse.method_validation import CandidateValidation, MethodValidationError, derive_promotion_stats
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, session_id, db.session_generation(session_id)


def _episode(db, session_id, label, ordinal):
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (turn_id, session_id, "gabriel", ordinal, time.time(), "user", label, "[]", "[]", json.dumps({"source": "authority-edge"})),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _activate(db, session_id, generation, identity):
    turn_id, episode_id, causal_id = identity
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )


def _effect(db, session_id, generation, identity, *, status="VERIFIED", keep_active=False):
    turn_id, episode_id, causal_id = identity
    effect_id = f"effect:{episode_id}"
    outcome_hash = hashlib.sha256(f"{episode_id}:{status}".encode()).hexdigest()
    credit = 1.0 if status == "VERIFIED" else 0.0
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            "gabriel",
            "entityos.exec",
            json.dumps({"audit": "authority-edge"}),
            None,
            generation,
            status,
            json.dumps({"audit": "authority-edge", "ok": status == "VERIFIED"}),
            time.time(),
            time.time(),
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, credit, 1, time.time()),
    )
    if not keep_active:
        db.db.execute("UPDATE workspace_episodes SET selected='request_effect',state='COMPLETED' WHERE episode_id=?", (episode_id,))
        db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    return effect_id


def _candidate(db, episode_ids):
    record = {
        "problem_signature": {"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        "preconditions": ["canonical state is available"],
        "goal_shape": ["separate competing mechanisms"],
        "method_steps": ["enumerate alternatives", "test cheapest falsifier"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["held-out evidence discriminates the method"],
        "falsifiers": ["candidate fails objective held-out criterion"],
        "failure_modes": ["execution success is mistaken for method success"],
        "scope_limits": ["method does not create facts"],
        "source_episode_ids": list(episode_ids),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        "support_count": len(episode_ids),
        "success_count": 0,
        "failure_count": 0,
        "calibration": 0.0,
        "last_validated_at": 0.0,
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }
    return MethodMemory(db).admit(
        kind="framework_candidate",
        subject="authority edge candidate",
        record=record,
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "authority-edge"},
    )


def _begin(validator, candidate_id, session_id, generation, identity, *, mode="HELD_OUT"):
    return validator.begin(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=session_id,
        turn_id=identity[0],
        episode_id=identity[1],
        causal_id=identity[2],
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        evaluation_mode=mode,
        falsifier_checked=True,
    )


def test_candidate_use_retry_is_idempotent_despite_new_wall_clock_time(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _episode(db, session_id, "a", 1)
    b = _episode(db, session_id, "b", 2)
    candidate_id = _candidate(db, [a[1], b[1]])
    _activate(db, session_id, generation, a)
    validator = CandidateValidation(db)
    first = _begin(validator, candidate_id, session_id, generation, a)
    time.sleep(0.002)
    second = _begin(validator, candidate_id, session_id, generation, a)
    assert second == first


def test_candidate_use_must_be_bound_before_any_effect_is_persisted(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _episode(db, session_id, "a", 1)
    b = _episode(db, session_id, "b", 2)
    candidate_id = _candidate(db, [a[1], b[1]])
    _activate(db, session_id, generation, a)
    _effect(db, session_id, generation, a, keep_active=True)
    with pytest.raises(MethodValidationError):
        _begin(CandidateValidation(db), candidate_id, session_id, generation, a)


def test_shadow_receipts_cannot_supply_positive_promotion_statistics(tmp_path):
    db, session_id, generation = _db(tmp_path)
    identities = [_episode(db, session_id, "a", 1), _episode(db, session_id, "b", 2)]
    candidate_id = _candidate(db, [item[1] for item in identities])
    validator = CandidateValidation(db)
    for identity in identities:
        _activate(db, session_id, generation, identity)
        use_id = _begin(validator, candidate_id, session_id, generation, identity, mode="SHADOW")
        _effect(db, session_id, generation, identity)
        validator.finalize(candidate_use_receipt_id=use_id)
    row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (candidate_id,)).fetchone()
    with pytest.raises(MethodValidationError):
        derive_promotion_stats(db.db, candidate_id, json.loads(row["value"]), "gabriel")


def test_validation_instances_must_not_be_the_candidate_source_episodes(tmp_path):
    db, session_id, generation = _db(tmp_path)
    identities = [_episode(db, session_id, "a", 1), _episode(db, session_id, "b", 2)]
    candidate_id = _candidate(db, [item[1] for item in identities])
    validator = CandidateValidation(db)
    for identity in identities:
        _activate(db, session_id, generation, identity)
        use_id = _begin(validator, candidate_id, session_id, generation, identity, mode="HELD_OUT")
        _effect(db, session_id, generation, identity)
        validator.finalize(candidate_use_receipt_id=use_id)
    row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (candidate_id,)).fetchone()
    with pytest.raises(MethodValidationError):
        derive_promotion_stats(db.db, candidate_id, json.loads(row["value"]), "gabriel")


def test_candidate_payload_drift_after_use_registration_invalidates_validation(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _episode(db, session_id, "a", 1)
    b = _episode(db, session_id, "b", 2)
    candidate_id = _candidate(db, [a[1], b[1]])
    _activate(db, session_id, generation, a)
    validator = CandidateValidation(db)
    use_id = _begin(validator, candidate_id, session_id, generation, a)

    row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (candidate_id,)).fetchone()
    mutated = json.loads(row["value"])
    mutated["method_steps"] = list(mutated["method_steps"]) + ["post-registration mutation"]
    db.db.execute(
        "UPDATE durable_memory SET value=? WHERE memory_id=?",
        (json.dumps(mutated, sort_keys=True, separators=(",", ":")), candidate_id),
    )
    _effect(db, session_id, generation, a)
    with pytest.raises(MethodValidationError):
        validator.finalize(candidate_use_receipt_id=use_id)
