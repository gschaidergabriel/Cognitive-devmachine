from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.store import UnifiedDB


def _terminal_reentered_episode(db: UnifiedDB, session_id: str, episode_id: str) -> None:
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "causal:" + uuid.uuid4().hex,
            episode_id,
            None,
            None,
            "ordinary-completion:" + episode_id,
            0.0,
            1,
            time.time(),
        ),
    )


def test_promotion_requires_durable_method_validation_receipts(tmp_path):
    """Terminal causal re-entry and caller counters are not promotion evidence.

    This regression is intentionally a merge gate for issue #425. Normal Claude/turn
    completion can produce reentered=1 with credit=0.0, so two such episodes must not be
    sufficient to mint a reusable positive framework even when the candidate payload
    claims success_count=2 and calibration=1.0. Promotion remains fail-closed until a
    canonical validation-receipt path proves that this exact candidate was evaluated on
    distinct held-out/cross-instance causal cases and derives the counters/calibration.
    """
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    _terminal_reentered_episode(db, session_id, "validation-src:a")
    _terminal_reentered_episode(db, session_id, "validation-src:b")

    support_ids = [
        db.add_memory("fact", "support-a", "a", None, "gabriel", {"source": "test"}),
        db.add_memory("fact", "support-b", "b", None, "gabriel", {"source": "test"}),
    ]
    candidate = {
        "problem_signature": {"goal": ["recover"], "mechanism": ["stateful", "causal"]},
        "preconditions": ["canonical state is available"],
        "goal_shape": ["restore a valid decision path"],
        "method_steps": ["enumerate alternatives", "test discriminating intervention"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["held-out outcome distinguishes the method"],
        "falsifiers": ["candidate does not improve held-out outcome"],
        "failure_modes": ["ordinary completion is mistaken for method success"],
        "scope_limits": ["method is not factual truth"],
        "source_episode_ids": ["validation-src:a", "validation-src:b"],
        "supporting_memory_ids": support_ids,
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 1.0,
        "last_validated_at": time.time(),
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }
    methods = MethodMemory(db)
    candidate_id = methods.admit(
        kind="framework_candidate",
        subject="held-out validation required",
        record=candidate,
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "candidate-abstraction"},
    )

    before_positive = db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='framework'"
    ).fetchone()[0]
    before_receipts = db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'"
    ).fetchone()[0]

    with pytest.raises(MethodRecordError):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="caller claims success but no method-validation receipts exist",
            user_id="gabriel",
            provenance={"source": "promotion-validation-regression"},
        )

    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='framework'"
    ).fetchone()[0] == before_positive
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'"
    ).fetchone()[0] == before_receipts
