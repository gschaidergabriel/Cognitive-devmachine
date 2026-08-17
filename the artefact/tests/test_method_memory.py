import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import (
    MethodMemoryError,
    MethodMemoryStore,
    MethodQuery,
    validate_method_envelope,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _episode(db, episode_id, *, session_id="session:gabriel"):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, 1.0, None, 0.5, "[]", None, "SELECTED"),
    )


def _envelope(
    *,
    name="Invariant-guided discriminator",
    signature=None,
    goal="diagnose causal mechanism",
    status="PROMOTED",
    source_episodes=None,
    counterexamples=None,
    support_count=2,
    calibration=0.8,
):
    return {
        "name": name,
        "problem_signature": signature or ["hidden competing mechanisms", "observable discriminating intervention"],
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": goal,
        "method_steps": ["state competing mechanisms", "derive divergent predictions", "run cheapest discriminator"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["candidate mechanisms predict different outcomes"],
        "falsifiers": ["all candidates predict the same admitted observation"],
        "failure_modes": ["proxy metric does not discriminate the mechanisms"],
        "scope_limits": ["does not establish facts without admitted evidence"],
        "source_episode_ids": source_episodes or ["episode:a", "episode:b"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": counterexamples or [],
        "abstraction_version": 1,
        "support_count": support_count,
        "success_count": 2 if status == "PROMOTED" else 1,
        "failure_count": 0,
        "calibration": calibration,
        "last_validated_at": 1.0,
        "status": status,
    }


def _prepare_episodes(db):
    _episode(db, "episode:a")
    _episode(db, "episode:b")


def test_promoted_method_envelope_fails_closed_without_cross_instance_support():
    with pytest.raises(MethodMemoryError, match="at least two source episodes"):
        validate_method_envelope(
            "framework",
            _envelope(source_episodes=["episode:a"], support_count=1),
        )


def test_candidate_is_durable_but_never_served_as_promoted_method(tmp_path):
    db = _db(tmp_path)
    try:
        _episode(db, "episode:a")
        store = MethodMemoryStore(db)
        candidate = _envelope(
            status="CANDIDATE",
            source_episodes=["episode:a"],
            support_count=1,
        )
        memory_id = store.add_method(
            kind="framework_candidate",
            subject="method:candidate",
            envelope=candidate,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        assert db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()[0] == "framework_candidate"
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=candidate["problem_signature"],
                goal_shape=candidate["goal_shape"],
            ),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert result["method_status"] == "UNKNOWN"
        assert result["method_context"] == []
    finally:
        db.close()


def test_fact_unknown_can_get_method_without_becoming_fact_present(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        store.add_method(
            kind="framework",
            subject="method:causal-discriminator",
            envelope=envelope,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=envelope["problem_signature"],
                goal_shape=envelope["goal_shape"],
            ),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert result["method_status"] == "PRESENT"
        assert len(result["method_context"]) == 1
        assert result["truth_authority"] is False
        assert result["effect_authority"] is False
    finally:
        db.close()


def test_structural_match_beats_surface_lexical_similarity(tmp_path):
    """Bounded lexical-inversion discriminator for analogical transfer.

    The correct framework name/subject deliberately share no surface vocabulary with
    the novel problem wording. A misleading framework sounds similar at the surface
    but has a different structural signature. Stage-B must use the explicit structure.
    """
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        store = MethodMemoryStore(db)
        correct = _envelope(
            name="Lantern bridge",
            signature=["resource contention", "single authority", "stale generation fence"],
            goal="preserve one admitted winner",
            calibration=0.77,
        )
        misleading = _envelope(
            name="Database lock timeout recovery",
            signature=["capacity exhaustion", "retry with exponential backoff"],
            goal="restore throughput",
            calibration=0.99,
        )
        correct_id = store.add_method(
            kind="framework",
            subject="method:lantern",
            envelope=correct,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        store.add_method(
            kind="framework",
            subject="database lock timeout stale retry",
            envelope=misleading,
            user_id="gabriel",
            provenance={"source": "test"},
        )

        # Surface wording intentionally resembles the misleading record, while the
        # admitted structural signature represents the actual novel problem.
        _surface_prompt = "database lock timeout after stale retry"
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=["single authority", "stale generation fence", "resource contention"],
                goal_shape="preserve one admitted winner",
            ),
            user_id="gabriel",
            fact_status="UNKNOWN",
            out_of_distribution=True,
        )
        assert _surface_prompt not in json.dumps(result)
        assert [item["memory_id"] for item in result["method_context"]] == [correct_id]
    finally:
        db.close()


def test_linked_matching_counterexample_blocks_framework(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        store = MethodMemoryStore(db)
        counter = _envelope(
            name="Lease-free replicated exception",
            signature=["resource contention", "single authority", "stale generation fence"],
            goal="preserve one admitted winner",
            status="PROMOTED",
            calibration=0.9,
        )
        counter_id = store.add_method(
            kind="counterexample",
            subject="counterexample:lease-free",
            envelope=counter,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        framework = _envelope(counterexamples=[counter_id])
        framework["problem_signature"] = ["resource contention", "single authority", "stale generation fence"]
        framework["goal_shape"] = "preserve one admitted winner"
        store.add_method(
            kind="framework",
            subject="method:blocked",
            envelope=framework,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=framework["problem_signature"],
                goal_shape=framework["goal_shape"],
            ),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["method_context"] == []
        assert result["method_status"] == "UNKNOWN"
        assert [item["memory_id"] for item in result["counterevidence"]] == [counter_id]
    finally:
        db.close()


def test_present_fact_does_not_enter_analogy_without_bounded_trigger(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        store.add_method(
            kind="framework",
            subject="method:not-needed",
            envelope=envelope,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=envelope["problem_signature"],
                goal_shape=envelope["goal_shape"],
            ),
            user_id="gabriel",
            fact_status="PRESENT",
        )
        assert result["method_status"] == "NOT_ENTERED"
        assert result["method_context"] == []
    finally:
        db.close()


def test_method_retrieval_does_not_broaden_user_boundary(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        store.add_method(
            kind="framework",
            subject="method:gabriel-private",
            envelope=envelope,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = store.retrieve_stage_b(
            query=MethodQuery.build(
                problem_signature=envelope["problem_signature"],
                goal_shape=envelope["goal_shape"],
            ),
            user_id="andreas",
            fact_status="UNKNOWN",
        )
        assert result["method_context"] == []
    finally:
        db.close()


def test_malformed_persisted_method_fails_closed_at_retrieval(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("bad", "framework", "method:bad", "{}", None, "gabriel", 1.0, "{}"),
        )
        store = MethodMemoryStore(db)
        with pytest.raises(MethodMemoryError, match="shape mismatch"):
            store.retrieve_stage_b(
                query=MethodQuery.build(
                    problem_signature=["hidden competing mechanisms"],
                    goal_shape="diagnose causal mechanism",
                ),
                user_id="gabriel",
                fact_status="UNKNOWN",
            )
    finally:
        db.close()
