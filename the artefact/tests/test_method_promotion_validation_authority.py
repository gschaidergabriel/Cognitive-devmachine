from __future__ import annotations

import time

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, session_id


def _terminal_reentered_episode(db, session_id, episode_id, *, credit):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "causal:" + episode_id,
            episode_id,
            None,
            None,
            "unbound-outcome:" + episode_id,
            float(credit),
            1,
            time.time(),
        ),
    )


def _candidate_record(episode_ids, support_ids):
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
        "source_episode_ids": list(episode_ids),
        "supporting_memory_ids": list(support_ids),
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        # Deliberately optimistic caller payload. These values are not promotion evidence.
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.95,
        "last_validated_at": time.time(),
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }


def _admit_candidate(db, session_id, *, credits):
    episode_ids = []
    for index, credit in enumerate(credits):
        episode_id = f"src:{index}"
        _terminal_reentered_episode(db, session_id, episode_id, credit=credit)
        episode_ids.append(episode_id)
    support_ids = [
        db.add_memory("fact", "support", "a", None, "gabriel", {"source": "validation-authority-regression"}),
        db.add_memory("fact", "support", "b", None, "gabriel", {"source": "validation-authority-regression"}),
    ]
    methods = MethodMemory(db)
    candidate_id = methods.admit(
        kind="framework_candidate",
        subject="candidate requiring held-out validation",
        record=_candidate_record(episode_ids, support_ids),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "validation-authority-regression"},
    )
    return methods, candidate_id


def _assert_promotion_fails_without_partial_write(db, methods, candidate_id):
    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
    with pytest.raises(MethodRecordError, match="validation"):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="caller text is not a validation receipt",
            user_id="gabriel",
            provenance={"source": "validation-authority-regression"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework','heuristic')"
    ).fetchone()[0] == 0


def test_terminal_reentry_with_zero_credit_is_not_method_validation(tmp_path):
    """Normal causal re-entry proves continuity, not reusable-method success."""
    db, session_id = _db(tmp_path)
    methods, candidate_id = _admit_candidate(db, session_id, credits=[0.0, 0.0])
    _assert_promotion_fails_without_partial_write(db, methods, candidate_id)


def test_unbound_positive_causal_credit_is_not_method_validation(tmp_path):
    """Even positive causal utility cannot be attached to a method after the outcome.

    Promotion requires a durable pre-bound validation request/result lineage proving this
    exact candidate was the evaluated method on the held-out/controlled causal instance.
    """
    db, session_id = _db(tmp_path)
    methods, candidate_id = _admit_candidate(db, session_id, credits=[1.0, 1.0])
    _assert_promotion_fails_without_partial_write(db, methods, candidate_id)
