import time
import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import MethodMemoryManager, MethodMemoryValidationError
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _episode(db, user_id, label, *, state="COMPLETED", reentered=True):
    session_id = f"session:{user_id}"
    turn_id = db.append_turn(session_id, user_id, "user", label)
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, state),
    )
    if reentered:
        db.db.execute(
            "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), episode_id, None, turn_id, "test-outcome", 1.0, 1, time.time()),
        )
    return turn_id, episode_id


def candidate_record(episodes, **overrides):
    value = {
        "problem_signature": {
            "goal": ["identify causal fault"],
            "constraint_shape": ["partial observability"],
            "evidence_shape": ["competing explanations"],
        },
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": "separate competing causal mechanisms",
        "method_steps": ["generate alternatives", "derive discriminating predictions", "run cheapest falsifier"],
        "invariants": ["unknown facts remain unknown"],
        "expected_observations": ["one intervention separates predictions"],
        "falsifiers": ["candidate predictions remain indistinguishable"],
        "failure_modes": ["proxy metric is not causally diagnostic"],
        "scope_limits": ["not for settled factual lookup"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.75,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }
    value.update(overrides)
    return value


def _candidate(db, episodes, *, user_id="gabriel", supporting=()):
    return MethodMemoryManager(db).admit(
        "framework_candidate",
        "causal discrimination",
        candidate_record(episodes, supporting_memory_ids=list(supporting)),
        None,
        user_id,
        {"source": "episode_abstraction", "extractor": "test"},
    )


def test_promotion_transaction_binds_terminal_causal_episodes_evidence_and_receipt(tmp_path):
    db = _db(tmp_path)
    try:
        _, e1 = _episode(db, "gabriel", "source one")
        _, e2 = _episode(db, "gabriel", "source two")
        evidence_a = db.add_memory("fact", "evidence", "A", None, "gabriel", {"source": "test"})
        evidence_b = db.add_memory("fact", "evidence", "B", None, "gabriel", {"source": "test"})
        manager = MethodMemoryManager(db)
        candidate_id = _candidate(db, [e1, e2], supporting=[evidence_a, evidence_b])

        result = manager.promote(
            candidate_id,
            evaluation="held-out transfer succeeded on a second terminal source episode",
            provenance={"source": "held_out_eval", "evaluator": "test"},
        )
        receipt = db.method_memory(result["receipt_memory_id"])
        promoted = db.method_memory(result["promoted_memory_id"])
        assert receipt["value"]["action"] == "PROMOTE"
        assert receipt["value"]["method_memory_id"] == candidate_id
        assert promoted["kind"] == "framework"
        assert promoted["value"]["status"] == "PROMOTED"
        assert promoted["provenance"]["promotion_source_memory_id"] == candidate_id
        assert promoted["provenance"]["promotion_receipt_id"] == result["receipt_memory_id"]

        row_count = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="already has a promotion receipt"):
            manager.promote(
                candidate_id,
                evaluation="duplicate promotion attempt",
                provenance={"source": "held_out_eval", "evaluator": "test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == row_count
    finally:
        db.close()


def test_open_source_episode_cannot_promote(tmp_path):
    db = _db(tmp_path)
    try:
        _, e1 = _episode(db, "gabriel", "terminal source")
        _, e2 = _episode(db, "gabriel", "open source", state="OPEN", reentered=False)
        candidate_id = _candidate(db, [e1, e2])
        with pytest.raises(MethodMemoryValidationError, match="must be terminal"):
            MethodMemoryManager(db).promote(
                candidate_id,
                evaluation="must reject open evidence",
                provenance={"source": "test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0
    finally:
        db.close()


def test_terminal_but_not_reentered_source_episode_cannot_promote(tmp_path):
    db = _db(tmp_path)
    try:
        _, e1 = _episode(db, "gabriel", "source one")
        _, e2 = _episode(db, "gabriel", "not reentered", state="COMPLETED", reentered=False)
        candidate_id = _candidate(db, [e1, e2])
        with pytest.raises(MethodMemoryValidationError, match="causally re-entered"):
            MethodMemoryManager(db).promote(
                candidate_id,
                evaluation="must reject non-reentered evidence",
                provenance={"source": "test"},
            )
    finally:
        db.close()


def test_cross_user_source_episode_cannot_promote(tmp_path):
    db = _db(tmp_path)
    try:
        _, e1 = _episode(db, "gabriel", "gabriel source")
        _, e2 = _episode(db, "andreas", "andreas source")
        candidate_id = _candidate(db, [e1, e2], user_id="gabriel")
        with pytest.raises(MethodMemoryValidationError, match="crosses user boundary"):
            MethodMemoryManager(db).promote(
                candidate_id,
                evaluation="must not cross user perspective boundary",
                provenance={"source": "test"},
            )
    finally:
        db.close()


def test_promotion_missing_episode_rolls_back_without_receipt_or_framework(tmp_path):
    db = _db(tmp_path)
    try:
        _, e1 = _episode(db, "gabriel", "source one")
        candidate_id = _candidate(db, [e1, "episode:missing"])
        before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="episode evidence is incomplete"):
            MethodMemoryManager(db).promote(
                candidate_id,
                evaluation="must not promote with a missing source episode",
                provenance={"source": "held_out_eval", "evaluator": "test"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
        assert db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework','heuristic')"
        ).fetchone()[0] == 0
    finally:
        db.close()
