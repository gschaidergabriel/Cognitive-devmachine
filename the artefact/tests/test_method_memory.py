import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import (
    MethodMemoryError,
    MethodMemoryStore,
    MethodQuery,
    STAGE_A_METHOD_SEPARATION_META_KEY,
    STAGE_A_METHOD_SEPARATION_VERSION,
    validate_method_envelope,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _admit_stage_a_method_separation(db):
    """Test-only simulation of the future integrated Stage-A exclusion gate."""
    db.db.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (STAGE_A_METHOD_SEPARATION_META_KEY, STAGE_A_METHOD_SEPARATION_VERSION),
    )


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


def _seed_validated_method(
    db,
    memory_id,
    *,
    kind="framework",
    subject="method:test",
    envelope=None,
    user_id="gabriel",
):
    """Test-only seed standing in for a future causal promotion/admission gate."""
    value = validate_method_envelope(kind, envelope or _envelope())
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            memory_id,
            kind,
            subject,
            json.dumps(value, sort_keys=True, separators=(",", ":")),
            None,
            user_id,
            1.0,
            json.dumps({"source": "test-only-pre-admitted-method"}, sort_keys=True),
        ),
    )
    return memory_id


def test_promoted_method_envelope_fails_closed_without_multi_episode_support():
    with pytest.raises(MethodMemoryError, match="at least two source episodes"):
        validate_method_envelope(
            "framework",
            _envelope(source_episodes=["episode:a"], support_count=1),
        )


def test_current_main_gate_blocks_method_persistence_and_preview(tmp_path):
    db = _db(tmp_path)
    try:
        _episode(db, "episode:a")
        store = MethodMemoryStore(db)
        candidate = _envelope(status="CANDIDATE", source_episodes=["episode:a"], support_count=1)
        with pytest.raises(MethodMemoryError, match="Stage-A method-kind separation"):
            store.add_candidate(
                kind="framework_candidate",
                subject="method:blocked-before-separation",
                envelope=candidate,
                user_id="gabriel",
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework_candidate'").fetchone()[0] == 0
        with pytest.raises(MethodMemoryError, match="Stage-A method-kind separation"):
            store.preview_stage_b(
                query=MethodQuery.build(problem_signature=["x"], goal_shape="y"),
                user_id="gabriel",
                fact_status="UNKNOWN",
            )
    finally:
        db.close()


def test_product_write_boundary_cannot_mint_promoted_method(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        with pytest.raises(MethodMemoryError, match="candidates only"):
            store.add_candidate(
                kind="framework",
                subject="method:forged-promotion",
                envelope=_envelope(),
                user_id="gabriel",
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0
    finally:
        db.close()


def test_candidate_is_durable_after_explicit_stage_a_separation_but_not_previewed_as_promoted(tmp_path):
    db = _db(tmp_path)
    try:
        _episode(db, "episode:a")
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        candidate = _envelope(status="CANDIDATE", source_episodes=["episode:a"], support_count=1)
        memory_id = store.add_candidate(
            kind="framework_candidate",
            subject="method:candidate",
            envelope=candidate,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        row = db.db.execute("SELECT kind,provenance FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        assert row["kind"] == "framework_candidate"
        provenance = json.loads(row["provenance"])
        assert provenance["promotion_authority"] is False
        assert provenance["truth_authority"] is False
        assert provenance["effect_authority"] is False

        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=candidate["problem_signature"], goal_shape=candidate["goal_shape"]),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert result["method_status"] == "UNKNOWN"
        assert result["method_candidates"] == []
        assert result["serve_authorized"] is False
        assert result["receipt_bound"] is False
    finally:
        db.close()


def test_candidate_source_episode_cannot_cross_user_boundary(tmp_path):
    db = _db(tmp_path)
    try:
        _episode(db, "episode:andreas", session_id="session:andreas")
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        candidate = _envelope(status="CANDIDATE", source_episodes=["episode:andreas"], support_count=1)
        with pytest.raises(MethodMemoryError, match="crosses user boundary"):
            store.add_candidate(
                kind="framework_candidate",
                subject="method:cross-user",
                envelope=candidate,
                user_id="gabriel",
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework_candidate'").fetchone()[0] == 0
    finally:
        db.close()


def test_fact_unknown_can_preview_method_without_becoming_fact_present_or_serving_it(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        _seed_validated_method(db, "framework:causal", subject="method:causal-discriminator", envelope=envelope)
        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=envelope["problem_signature"], goal_shape=envelope["goal_shape"]),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert result["method_status"] == "PRESENT"
        assert len(result["method_candidates"]) == 1
        assert result["serve_authorized"] is False
        assert result["receipt_bound"] is False
        assert result["truth_authority"] is False
        assert result["effect_authority"] is False
    finally:
        db.close()


def test_structural_match_beats_surface_lexical_similarity(tmp_path):
    """The GO macro-cycle's single bounded STRUCTURAL_LEXICAL_INVERSION case."""
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
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
        correct_id = _seed_validated_method(db, "framework:lantern", subject="method:lantern", envelope=correct)
        _seed_validated_method(
            db,
            "framework:lexical-lure",
            subject="database lock timeout stale retry",
            envelope=misleading,
        )

        _surface_prompt = "database lock timeout after stale retry"
        result = store.preview_stage_b(
            query=MethodQuery.build(
                problem_signature=["single authority", "stale generation fence", "resource contention"],
                goal_shape="preserve one admitted winner",
            ),
            user_id="gabriel",
            fact_status="UNKNOWN",
            out_of_distribution=True,
        )
        assert _surface_prompt not in json.dumps(result)
        assert [item["memory_id"] for item in result["method_candidates"]] == [correct_id]
        assert result["serve_authorized"] is False
    finally:
        db.close()


def test_linked_matching_counterexample_blocks_framework(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        counter = _envelope(
            name="Lease-free replicated exception",
            signature=["resource contention", "single authority", "stale generation fence"],
            goal="preserve one admitted winner",
            status="PROMOTED",
            calibration=0.9,
        )
        counter_id = _seed_validated_method(
            db,
            "counterexample:lease-free",
            kind="counterexample",
            subject="counterexample:lease-free",
            envelope=counter,
        )
        framework = _envelope(counterexamples=[counter_id])
        framework["problem_signature"] = ["resource contention", "single authority", "stale generation fence"]
        framework["goal_shape"] = "preserve one admitted winner"
        _seed_validated_method(db, "framework:blocked", subject="method:blocked", envelope=framework)
        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=framework["problem_signature"], goal_shape=framework["goal_shape"]),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["method_candidates"] == []
        assert result["method_status"] == "UNKNOWN"
        assert [item["memory_id"] for item in result["counterevidence"]] == [counter_id]
    finally:
        db.close()


def test_present_fact_does_not_enter_analogy_preview_without_bounded_trigger(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        _seed_validated_method(db, "framework:not-needed", envelope=envelope)
        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=envelope["problem_signature"], goal_shape=envelope["goal_shape"]),
            user_id="gabriel",
            fact_status="PRESENT",
        )
        assert result["method_status"] == "NOT_ENTERED"
        assert result["method_candidates"] == []
        assert result["serve_authorized"] is False
    finally:
        db.close()


def test_method_preview_does_not_broaden_user_boundary(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        _seed_validated_method(db, "framework:gabriel-private", envelope=envelope, user_id="gabriel")
        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=envelope["problem_signature"], goal_shape=envelope["goal_shape"]),
            user_id="andreas",
            fact_status="UNKNOWN",
        )
        assert result["method_candidates"] == []
    finally:
        db.close()


def test_unscoped_global_method_is_not_previewed_before_privacy_admission_exists(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        store = MethodMemoryStore(db)
        envelope = _envelope()
        _seed_validated_method(db, "framework:global-unadmitted", envelope=envelope, user_id=None)
        result = store.preview_stage_b(
            query=MethodQuery.build(problem_signature=envelope["problem_signature"], goal_shape=envelope["goal_shape"]),
            user_id="gabriel",
            fact_status="UNKNOWN",
        )
        assert result["method_candidates"] == []
    finally:
        db.close()


def test_malformed_persisted_method_fails_closed_in_preview(tmp_path):
    db = _db(tmp_path)
    try:
        _prepare_episodes(db)
        _admit_stage_a_method_separation(db)
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("bad", "framework", "method:bad", "{}", None, "gabriel", 1.0, "{}"),
        )
        store = MethodMemoryStore(db)
        with pytest.raises(MethodMemoryError, match="shape mismatch"):
            store.preview_stage_b(
                query=MethodQuery.build(problem_signature=["hidden competing mechanisms"], goal_shape="diagnose causal mechanism"),
                user_id="gabriel",
                fact_status="UNKNOWN",
            )
    finally:
        db.close()
