from __future__ import annotations

import json

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError, validate_method_record
from clayverse.store import UnifiedDB


def _payload(
    *,
    name: str,
    signature: dict[str, list[str]],
    status: str = "PROMOTED",
    source_episode_ids: list[str] | None = None,
    support_count: int = 2,
    success_count: int = 2,
    failure_count: int = 0,
    counterexample_memory_ids: list[str] | None = None,
) -> dict:
    return {
        "schema": "clayverse.method/v1",
        "name": name,
        "problem_signature": signature,
        "preconditions": ["the observed problem satisfies the declared structural facets"],
        "goal_shape": "identify a bounded discriminator before committing to a solution",
        "method_steps": [
            "enumerate competing mechanisms",
            "choose the cheapest observation that separates them",
            "preserve the losing mechanism as counterevidence",
        ],
        "invariants": ["analogy never upgrades an unknown fact to known"],
        "expected_observations": ["one discriminator separates at least two mechanisms"],
        "falsifiers": ["the discriminator predicts the same outcome under every candidate mechanism"],
        "failure_modes": ["surface similarity is mistaken for structural similarity"],
        "scope_limits": ["do not use when the structural preconditions are absent"],
        "source_episode_ids": source_episode_ids or ["episode:a", "episode:b"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": counterexample_memory_ids or [],
        "abstraction_version": 1,
        "support_count": support_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "calibration": 0.75,
        "last_validated_at": 1_786_927_000.0,
        "status": status,
    }


def _db(tmp_path) -> UnifiedDB:
    return UnifiedDB(tmp_path / "clayverse.db")


def _ensure_session(db: UnifiedDB, user_id: str) -> str:
    db.ensure_user(user_id, user_id.title())
    return db.ensure_session(user_id, f"clayverse-{user_id}")


def _seed_episodes(db: UnifiedDB, user_id: str, episode_ids: list[str]) -> None:
    session_id = _ensure_session(db, user_id)
    for index, episode_id in enumerate(episode_ids):
        ts = float(index + 1)
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, session_id, ts, None, 0.5, "[]", "respond", "COMPLETED"),
        )
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (f"causal:{episode_id}", episode_id, None, None, f"outcome:{episode_id}", 0.0, 1, ts),
        )


def _seed_open_episode(db: UnifiedDB, user_id: str, episode_id: str) -> None:
    session_id = _ensure_session(db, user_id)
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, 1.0, None, 0.5, "[]", None, "OPEN"),
    )


def test_single_episode_cannot_promote_reusable_framework():
    payload = _payload(
        name="single anecdote",
        signature={"topology": ["shared state"], "risk": ["stale replay"]},
        source_episode_ids=["episode:only"],
        support_count=1,
        success_count=1,
    )
    with pytest.raises(MethodRecordError, match="single episode"):
        validate_method_record("framework", payload)


def test_fabricated_source_episode_ids_fail_closed_at_admission(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a"])
        methods = MethodMemory(db)
        payload = _payload(
            name="forged provenance",
            signature={"topology": ["shared state"], "risk": ["stale replay"]},
            source_episode_ids=["episode:a", "episode:invented"],
        )
        with pytest.raises(MethodRecordError, match="unknown source_episode_ids"):
            methods.admit(
                kind="framework",
                payload=payload,
                source_turn_id=None,
                user_id="gabriel",
                provenance={"source": "test"},
            )
    finally:
        db.close()


def test_open_episode_cannot_be_used_as_promotion_evidence(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a"])
        _seed_open_episode(db, "gabriel", "episode:open")
        methods = MethodMemory(db)
        payload = _payload(
            name="open provenance",
            signature={"topology": ["shared state"], "risk": ["stale replay"]},
            source_episode_ids=["episode:a", "episode:open"],
        )
        with pytest.raises(MethodRecordError, match="terminal causally re-entered"):
            methods.admit(
                kind="framework",
                payload=payload,
                source_turn_id=None,
                user_id="gabriel",
                provenance={"source": "test"},
            )
    finally:
        db.close()


def test_candidate_can_be_stored_but_is_not_stage_b_served(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:only"])
        methods = MethodMemory(db)
        payload = _payload(
            name="candidate only",
            signature={"topology": ["shared state"], "risk": ["stale replay"]},
            status="CANDIDATE",
            source_episode_ids=["episode:only"],
            support_count=1,
            success_count=1,
        )
        memory_id = methods.admit(
            kind="framework_candidate",
            payload=payload,
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        assert memory_id
        result = methods.retrieve_stage_b(
            evidence_status="UNKNOWN",
            problem_signature={"topology": ["shared state"], "risk": ["stale replay"]},
            user_id="gabriel",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert result["method_context"] == []
        assert result["receipt"]["served"] is False
    finally:
        db.close()


def test_unknown_fact_remains_unknown_when_method_context_is_present(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        signature = {
            "topology": ["shared mutable state"],
            "risk": ["stale replay"],
            "goal": ["separate competing mechanisms"],
        }
        methods.admit(
            kind="framework",
            payload=_payload(name="causal discriminator", signature=signature),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = methods.retrieve_stage_b(
            evidence_status="UNKNOWN",
            problem_signature=signature,
            user_id="gabriel",
        )
        assert result["fact_status"] == "UNKNOWN"
        assert [item["name"] for item in result["method_context"]] == ["causal discriminator"]
        assert result["method_context"][0]["truth_authority"] is False
        assert result["receipt"]["truth_authority"] is False
        assert result["receipt"]["served"] is False
    finally:
        db.close()


def test_present_evidence_does_not_trigger_stage_b_by_default(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        signature = {"topology": ["shared state"], "risk": ["stale replay"]}
        methods.admit(
            kind="framework",
            payload=_payload(name="not needed", signature=signature),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = methods.retrieve_stage_b(
            evidence_status="PRESENT",
            problem_signature=signature,
            user_id="gabriel",
        )
        assert result["fact_status"] == "PRESENT"
        assert result["method_context"] == []
        assert result["receipt"]["trigger"] is None
    finally:
        db.close()


def test_structural_match_beats_surface_lexical_decoy_regression(tmp_path):
    """Regression of GO unusual experiment STRUCTURAL_LEXICAL_DECOY_INVERSION."""
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        methods.admit(
            kind="framework",
            payload=_payload(
                name="generic invariant discriminator",
                signature={
                    "topology": ["shared mutable state"],
                    "failure": ["aba stale generation"],
                    "goal": ["prove one live generation"],
                },
            ),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        methods.admit(
            kind="framework",
            payload=_payload(
                name="shared mutable state ABA stale generation one live generation",
                signature={
                    "topology": ["independent immutable snapshots"],
                    "failure": ["format mismatch"],
                    "goal": ["pretty print output"],
                },
            ),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = methods.retrieve_stage_b(
            evidence_status="UNKNOWN",
            problem_signature={
                "topology": ["shared mutable state"],
                "failure": ["aba stale generation"],
                "goal": ["prove one live generation"],
            },
            user_id="gabriel",
        )
        assert [item["name"] for item in result["method_context"]] == ["generic invariant discriminator"]
    finally:
        db.close()


def test_matching_linked_counterexample_blocks_framework(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        signature = {
            "topology": ["shared mutable state"],
            "risk": ["stale replay"],
            "goal": ["safe retry"],
        }
        counter_id = methods.admit(
            kind="counterexample",
            payload=_payload(name="unsafe retry counterexample", signature=signature),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        methods.admit(
            kind="framework",
            payload=_payload(
                name="retry framework",
                signature=signature,
                counterexample_memory_ids=[counter_id],
            ),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )
        result = methods.retrieve_stage_b(
            evidence_status="UNKNOWN",
            problem_signature=signature,
            user_id="gabriel",
        )
        assert result["method_context"] == []
        assert [item["memory_id"] for item in result["counterevidence"]] == [counter_id]
    finally:
        db.close()


def test_counterexample_link_must_reference_counter_kind(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        evidence_id = db.add_memory(
            "fact", "x", "supporting fact", None, "gabriel", {"source": "test"}
        )
        payload = _payload(
            name="bad counter link",
            signature={"topology": ["shared state"], "risk": ["stale replay"]},
            counterexample_memory_ids=[evidence_id],
        )
        with pytest.raises(MethodRecordError, match="counterexample link has wrong kind"):
            methods.admit(
                kind="framework",
                payload=payload,
                source_turn_id=None,
                user_id="gabriel",
                provenance={"source": "test"},
            )
    finally:
        db.close()


def test_malformed_promoted_method_fails_closed_during_stage_b(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "gabriel", ["episode:a", "episode:b"])
        methods = MethodMemory(db)
        db.add_memory(
            "framework",
            "malformed",
            json.dumps({"schema": "clayverse.method/v1", "status": "PROMOTED"}),
            None,
            "gabriel",
            {"source": "test-direct-corruption"},
        )
        with pytest.raises(MethodRecordError):
            methods.retrieve_stage_b(
                evidence_status="UNKNOWN",
                problem_signature={"topology": ["shared state"], "risk": ["stale replay"]},
                user_id="gabriel",
            )
    finally:
        db.close()


def test_method_retrieval_does_not_broaden_user_scope(tmp_path):
    db = _db(tmp_path)
    try:
        _seed_episodes(db, "andreas", ["episode:andreas:a", "episode:andreas:b"])
        methods = MethodMemory(db)
        methods.admit(
            kind="framework",
            payload=_payload(
                name="andreas private method",
                signature={"topology": ["shared state"], "risk": ["stale replay"]},
                source_episode_ids=["episode:andreas:a", "episode:andreas:b"],
            ),
            source_turn_id=None,
            user_id="andreas",
            provenance={"source": "test"},
        )
        result = methods.retrieve_stage_b(
            evidence_status="UNKNOWN",
            problem_signature={"topology": ["shared state"], "risk": ["stale replay"]},
            user_id="gabriel",
        )
        assert result["method_context"] == []
    finally:
        db.close()
