from __future__ import annotations

import hashlib
import json
import time
import uuid

import pytest

from clayverse.method_memory import MethodMemory
from clayverse.method_validation import (
    CandidateValidation,
    MethodValidationError,
    derive_promotion_stats,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.session_generation(session_id)
    return db, session_id, generation


def _make_episode(db, session_id, generation, label, ordinal):
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            turn_id,
            session_id,
            "gabriel",
            ordinal,
            time.time(),
            "user",
            f"validation {label}",
            "[]",
            "[]",
            json.dumps({"source": "validation-test"}),
        ),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _activate(db, session_id, generation, turn_id, episode_id, causal_id):
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )


def _finish_external(db, *, session_id, generation, turn_id, episode_id, causal_id, status):
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
            json.dumps({"audit": "test"}),
            None,
            generation,
            status,
            json.dumps({"audit": "test", "ok": status == "VERIFIED"}),
            time.time(),
            time.time(),
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, credit, 1, time.time()),
    )
    db.db.execute(
        "UPDATE workspace_episodes SET selected='request_effect',state='COMPLETED' WHERE episode_id=?",
        (episode_id,),
    )
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))


def _candidate_record(episodes):
    return {
        "problem_signature": {"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        "preconditions": ["canonical state is available"],
        "goal_shape": ["separate competing mechanisms"],
        "method_steps": ["enumerate alternatives", "test cheapest falsifier"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["one mechanism separates"],
        "falsifiers": ["structural preconditions fail"],
        "failure_modes": ["surface similarity hides causal mismatch"],
        "scope_limits": ["method does not create facts"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        # Deliberately caller-asserted nonsense: promotion statistics must ignore this.
        "support_count": 99,
        "success_count": 99,
        "failure_count": 0,
        "calibration": 0.99,
        "last_validated_at": 0.0,
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }


def _admit_candidate(db, episodes):
    return MethodMemory(db).admit(
        kind="framework_candidate",
        subject="effect-bound causal discriminator",
        record=_candidate_record(episodes),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "candidate-validation-test"},
    )


def test_effect_bound_validation_derives_counts_instead_of_trusting_candidate(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _make_episode(db, session_id, generation, "a", 1)
    b = _make_episode(db, session_id, generation, "b", 2)
    candidate_id = _admit_candidate(db, [a[1], b[1]])
    validator = CandidateValidation(db)

    use_ids = []
    for index, identity in enumerate((a, b)):
        turn_id, episode_id, causal_id = identity
        _activate(db, session_id, generation, turn_id, episode_id, causal_id)
        use_ids.append(
            validator.begin(
                candidate_memory_id=candidate_id,
                user_id="gabriel",
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
                evidence_status="UNKNOWN",
                problem_signature={"goal": ["verify"], "mechanism": ["causal", "provenance"]},
                evaluation_mode="HELD_OUT",
                falsifier_checked=index == 1,
            )
        )
        _finish_external(
            db,
            session_id=session_id,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            status="VERIFIED" if index == 0 else "FAILED",
        )

    validation_ids = [validator.finalize(candidate_use_receipt_id=rid) for rid in use_ids]
    candidate_row = db.db.execute(
        "SELECT value FROM durable_memory WHERE memory_id=?",
        (candidate_id,),
    ).fetchone()
    stats = derive_promotion_stats(db.db, candidate_id, json.loads(candidate_row["value"]), "gabriel")
    assert stats["support_count"] == 2
    assert stats["success_count"] == 1
    assert stats["failure_count"] == 1
    assert stats["calibration"] == 0.5
    assert stats["validation_receipt_ids"] == validation_ids
    assert len(stats["validation_evidence_sha256"]) == 64


def test_normal_claude_completion_is_not_candidate_validation_reward(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _make_episode(db, session_id, generation, "a", 1)
    b = _make_episode(db, session_id, generation, "b", 2)
    candidate_id = _admit_candidate(db, [a[1], b[1]])
    validator = CandidateValidation(db)
    _activate(db, session_id, generation, *a)
    use_id = validator.begin(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=session_id,
        turn_id=a[0],
        episode_id=a[1],
        causal_id=a[2],
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["verify"]},
        evaluation_mode="SHADOW",
        falsifier_checked=False,
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (a[2], a[1], None, a[0], hashlib.sha256(b"claude").hexdigest(), 0.0, 1, time.time()),
    )
    db.db.execute("UPDATE workspace_episodes SET selected='respond',state='COMPLETED' WHERE episode_id=?", (a[1],))
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    with pytest.raises(MethodValidationError, match="no external causal effect outcome"):
        validator.finalize(candidate_use_receipt_id=use_id)


def test_validation_use_must_be_registered_on_exact_active_causal_identity(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _make_episode(db, session_id, generation, "a", 1)
    b = _make_episode(db, session_id, generation, "b", 2)
    candidate_id = _admit_candidate(db, [a[1], b[1]])
    _activate(db, session_id, generation, *a)
    with pytest.raises(MethodValidationError, match="exact active causal instance"):
        CandidateValidation(db).begin(
            candidate_memory_id=candidate_id,
            user_id="gabriel",
            session_id=session_id,
            turn_id=a[0],
            episode_id=a[1],
            causal_id="causal:forged",
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["verify"]},
            evaluation_mode="HELD_OUT",
            falsifier_checked=True,
        )
