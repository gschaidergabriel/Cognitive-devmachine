from __future__ import annotations

import time

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.store import UnifiedDB


def _record(source_episode_ids, supporting_memory_ids):
    return {
        "problem_signature": {"goal": ["verify"], "mechanism": ["privacy"]},
        "preconditions": ["canonical user scope is known"],
        "goal_shape": ["preserve access boundary"],
        "method_steps": ["check source ownership", "deny divergent provenance"],
        "invariants": ["method retrieval cannot widen user scope"],
        "expected_observations": ["cross-user admission is rejected"],
        "falsifiers": ["explicit future declassification contract exists"],
        "failure_modes": ["generic abstraction masks private source provenance"],
        "scope_limits": ["v1 is user-scoped only"],
        "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": list(supporting_memory_ids),
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.8,
        "last_validated_at": time.time(),
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }


def _setup(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gs = db.ensure_session("gabriel", "clayverse-gabriel")
    ans = db.ensure_session("andreas", "clayverse-andreas")
    return db, gs, ans


def _episode(db, session_id, episode_id):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", "COMPLETED"),
    )


def test_cross_user_source_episode_is_rejected(tmp_path):
    db, gs, ans = _setup(tmp_path)
    _episode(db, gs, "g:one")
    _episode(db, ans, "a:one")
    support_a = db.add_memory("fact", "gabriel", "support-a", None, "gabriel", {"source": "test"})
    support_b = db.add_memory("fact", "gabriel", "support-b", None, "gabriel", {"source": "test"})
    with pytest.raises(MethodRecordError, match="canonical user/session scope"):
        MethodMemory(db).admit(
            kind="framework_candidate",
            subject="privacy framework candidate",
            record=_record(["g:one", "a:one"], [support_a, support_b]),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "privacy-regression"},
        )


def test_cross_user_support_memory_is_rejected(tmp_path):
    db, gs, _ = _setup(tmp_path)
    _episode(db, gs, "g:one")
    _episode(db, gs, "g:two")
    own = db.add_memory("fact", "gabriel", "support-own", None, "gabriel", {"source": "test"})
    other = db.add_memory("fact", "andreas", "support-other", None, "andreas", {"source": "test"})
    with pytest.raises(MethodRecordError, match="cross-user referenced memory denied"):
        MethodMemory(db).admit(
            kind="framework_candidate",
            subject="privacy framework candidate",
            record=_record(["g:one", "g:two"], [own, other]),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "privacy-regression"},
        )


def test_unscoped_global_method_candidate_admission_is_rejected(tmp_path):
    db, gs, _ = _setup(tmp_path)
    _episode(db, gs, "g:one")
    _episode(db, gs, "g:two")
    support_a = db.add_memory("fact", "gabriel", "support-a", None, "gabriel", {"source": "test"})
    support_b = db.add_memory("fact", "gabriel", "support-b", None, "gabriel", {"source": "test"})
    with pytest.raises(MethodRecordError, match="explicit canonical user scope"):
        MethodMemory(db).admit(
            kind="framework_candidate",
            subject="unsafe global framework candidate",
            record=_record(["g:one", "g:two"], [support_a, support_b]),
            source_turn_id=None,
            user_id=None,
            provenance={"source": "privacy-regression"},
        )
