import time

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.store import UnifiedDB


def candidate_record(**overrides):
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
        "source_episode_ids": ["episode:a", "episode:b"],
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


def add_episode(db, user_id, episode_id, *, state="COMPLETED", reentered=True):
    session_id = db.ensure_session(user_id, f"clayverse-{user_id}")
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", None, state),
    )
    if reentered:
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (f"causal:{episode_id}", episode_id, None, None, f"hash:{episode_id}", 0.0, 1, time.time()),
        )
    return session_id


def make_db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    return db


def admit_candidate(db, *, episodes=None, supports=None, counters=None, user_id="gabriel"):
    return db.add_method_memory(
        "framework_candidate",
        "causal discrimination",
        candidate_record(
            source_episode_ids=episodes or ["episode:a", "episode:b"],
            supporting_memory_ids=supports or [],
            counterexample_memory_ids=counters or [],
        ),
        None,
        user_id,
        {"source": "episode_abstraction", "extractor": "test"},
    )


def count_promoted_rows(db):
    return db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework','heuristic')"
    ).fetchone()[0]


def promote(db, candidate_id):
    return db.promote_method_memory(
        candidate_id,
        evaluation="held-out transfer succeeded on a second source episode",
        provenance={"source": "held_out_eval", "evaluator": "test"},
    )


def test_promotion_binds_terminal_causal_session_and_receipt(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "gabriel", "episode:b", state="ABORTED", reentered=True)
        evidence_a = db.add_memory("fact", "evidence", "A", None, "gabriel", {"source": "test"})
        evidence_b = db.add_memory("fact", "evidence", "B", None, None, {"source": "test"})
        candidate_id = admit_candidate(db, supports=[evidence_a, evidence_b])

        result = promote(db, candidate_id)
        receipt = db.method_memory(result["receipt_memory_id"])
        promoted = db.method_memory(result["promoted_memory_id"])

        assert receipt["value"]["action"] == "PROMOTE"
        assert receipt["value"]["method_memory_id"] == candidate_id
        assert receipt["provenance"]["promotion_transaction_version"] == 2
        assert receipt["provenance"]["promotion_source_user_id"] == "gabriel"
        assert receipt["provenance"]["promotion_source_session_id"] == "session:gabriel"
        assert receipt["provenance"]["promotion_sources_terminal_causal"] is True
        assert promoted["kind"] == "framework"
        assert promoted["value"]["status"] == "PROMOTED"
        assert promoted["provenance"]["promotion_source_memory_id"] == candidate_id
        assert promoted["provenance"]["promotion_receipt_id"] == result["receipt_memory_id"]

        row_count = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
        with pytest.raises(MethodMemoryValidationError, match="already has a promotion receipt"):
            promote(db, candidate_id)
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == row_count
    finally:
        db.close()


@pytest.mark.parametrize("state", ["OPEN", "SELECTED"])
def test_nonterminal_source_episode_fails_before_receipt(tmp_path, state):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "gabriel", "episode:b", state=state, reentered=True)
        candidate_id = admit_candidate(db)
        before = count_promoted_rows(db)
        with pytest.raises(MethodMemoryValidationError, match="not terminal"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == before == 0
    finally:
        db.close()


def test_terminal_source_without_causal_reentry_fails_before_receipt(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "gabriel", "episode:b", state="ABORTED", reentered=False)
        candidate_id = admit_candidate(db)
        with pytest.raises(MethodMemoryValidationError, match="lacks causal re-entry"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == 0
    finally:
        db.close()


def test_cross_user_source_episode_fails_before_receipt(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "andreas", "episode:b", state="COMPLETED", reentered=True)
        candidate_id = admit_candidate(db)
        with pytest.raises(MethodMemoryValidationError, match="canonical session"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == 0
    finally:
        db.close()


def test_cross_user_supporting_memory_fails_before_receipt(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "gabriel", "episode:b", state="COMPLETED", reentered=True)
        foreign = db.add_memory("fact", "foreign", "private", None, "andreas", {"source": "test"})
        candidate_id = admit_candidate(db, supports=[foreign])
        with pytest.raises(MethodMemoryValidationError, match="memory crosses user scope"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == 0
    finally:
        db.close()


def test_counterexample_reference_must_be_negative_method_evidence(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        add_episode(db, "gabriel", "episode:b", state="COMPLETED", reentered=True)
        wrong_kind = db.add_memory("fact", "not-counterexample", "plain fact", None, "gabriel", {"source": "test"})
        candidate_id = admit_candidate(db, counters=[wrong_kind])
        with pytest.raises(MethodMemoryValidationError, match="not negative method evidence"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == 0
    finally:
        db.close()


def test_missing_source_episode_rolls_back_without_receipt(tmp_path):
    db = make_db(tmp_path)
    try:
        add_episode(db, "gabriel", "episode:a", state="COMPLETED", reentered=True)
        candidate_id = admit_candidate(db, episodes=["episode:a", "episode:missing"])
        with pytest.raises(MethodMemoryValidationError, match="episode evidence is incomplete"):
            promote(db, candidate_id)
        assert count_promoted_rows(db) == 0
    finally:
        db.close()
