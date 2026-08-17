from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_memory import METHOD_SCHEMA, MethodMemoryManager, MethodRecordError
from clayverse.method_stage_b import StageBShadowRetrieval
from clayverse.problem_signature import ProblemSignatureAdmission
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gs = db.ensure_session("gabriel", "clayverse-gabriel")
    ans = db.ensure_session("andreas", "clayverse-andreas")
    return db, gs, ans


def _completed_episode(db, session_id: str, episode_id: str):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        ("causal:" + episode_id, episode_id, None, None, "outcome:" + episode_id, 1.0, 1, time.time()),
    )


def _active_turn(db, user_id: str, session_id: str, content: str = "novel unresolved task", resources=()):
    turn_id = db.append_turn(session_id, user_id, "user", content, resources=resources)
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, user_id, turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return turn_id, episode_id, causal_id, generation


def _payload(*, name: str, signature, episodes, status: str, counters=()):
    return {
        "schema": METHOD_SCHEMA,
        "name": name,
        "problem_signature": signature,
        "preconditions": ["canonical state is available"],
        "goal_shape": "recover a valid decision path",
        "method_steps": ["enumerate alternatives", "derive a discriminator", "test the smallest falsifier"],
        "invariants": ["direct evidence outranks analogy"],
        "expected_observations": ["mechanisms separate under bounded intervention"],
        "falsifiers": ["structural preconditions do not hold"],
        "failure_modes": ["surface similarity hides different structure"],
        "scope_limits": ["method memory cannot establish facts or effects"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": list(counters),
        "abstraction_version": 1,
        "support_count": len(episodes),
        "success_count": len(episodes),
        "failure_count": 0,
        "calibration": 0.8,
        "last_validated_at": 0.0 if status == "CANDIDATE" else time.time(),
        "status": status,
    }


def _safe_evaluation(held_out):
    return {
        "held_out_episode_ids": list(held_out),
        "counterexample_search_performed": True,
        "memorization_only_rejected": True,
        "contamination_detected": False,
        "stale_state_detected": False,
        "privacy_leakage_detected": False,
        "authority_leakage_detected": False,
        "evaluator": "bounded-regression",
        "evaluated_at": time.time(),
    }


def _promoted_framework(db, session_id: str, *, counters=()):
    _completed_episode(db, session_id, "source:a")
    _completed_episode(db, session_id, "heldout:b")
    manager = MethodMemoryManager(db)
    signature = {"goal": ["recover"], "mechanism": ["stateful", "provenance"]}
    candidate_id = manager.admit(
        kind="framework_candidate",
        payload=_payload(name="recovery framework candidate", signature=signature, episodes=["source:a"], status="CANDIDATE"),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    result = manager.promote(
        candidate_memory_id=candidate_id,
        target_kind="framework",
        promoted_payload=_payload(
            name="recovery framework",
            signature=signature,
            episodes=["source:a", "heldout:b"],
            status="PROMOTED",
            counters=counters,
        ),
        evaluation=_safe_evaluation(["heldout:b"]),
        user_id="gabriel",
        provenance={"source": "test-promotion"},
    )
    return result, signature


def test_normal_admission_cannot_mint_active_framework(tmp_path):
    db, gs, _ = _db(tmp_path)
    _completed_episode(db, gs, "source:a")
    _completed_episode(db, gs, "heldout:b")
    with pytest.raises(MethodRecordError, match="dedicated lifecycle"):
        MethodMemoryManager(db).admit(
            kind="framework",
            payload=_payload(
                name="forged active framework",
                signature={"goal": ["recover"], "mechanism": ["stateful"]},
                episodes=["source:a", "heldout:b"],
                status="PROMOTED",
            ),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "forgery"},
        )


def test_promotion_requires_held_out_safety_evidence(tmp_path):
    db, gs, _ = _db(tmp_path)
    _completed_episode(db, gs, "source:a")
    _completed_episode(db, gs, "heldout:b")
    manager = MethodMemoryManager(db)
    signature = {"goal": ["recover"], "mechanism": ["stateful"]}
    candidate_id = manager.admit(
        kind="framework_candidate",
        payload=_payload(name="candidate", signature=signature, episodes=["source:a"], status="CANDIDATE"),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    bad = _safe_evaluation(["heldout:b"])
    bad["privacy_leakage_detected"] = True
    with pytest.raises(MethodRecordError, match="privacy_leakage_detected must be false"):
        manager.promote(
            candidate_memory_id=candidate_id,
            target_kind="framework",
            promoted_payload=_payload(
                name="framework",
                signature=signature,
                episodes=["source:a", "heldout:b"],
                status="PROMOTED",
            ),
            evaluation=bad,
            user_id="gabriel",
            provenance={"source": "test"},
        )


def test_promoted_method_is_receipt_bound(tmp_path):
    db, gs, _ = _db(tmp_path)
    result, _ = _promoted_framework(db, gs)
    row = MethodMemoryManager(db).row_by_id(result["promoted_memory_id"], "gabriel")
    record = MethodMemoryManager(db).decode_row(row)
    provenance = __import__("json").loads(row["provenance"])
    assert record.status == "PROMOTED"
    assert provenance["promotion_receipt_id"] == result["promotion_receipt_id"]
    assert provenance["truth_authority"] is False
    assert provenance["effect_authority"] is False


def test_stage_b_without_admitted_signature_is_not_served(tmp_path):
    db, gs, _ = _db(tmp_path)
    _promoted_framework(db, gs)
    turn_id, episode_id, causal_id, generation = _active_turn(db, "gabriel", gs)
    result = StageBShadowRetrieval(db).retrieve_shadow(
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        signature_receipt_id=None,
        resource_refs=[],
    )
    assert result["method_context"] == []
    assert result["shadow_method_context"] == []
    assert result["receipt"]["signature_status"] == "MISSING_NOT_SERVED"
    assert result["fact_status"] == "UNKNOWN"


def test_admitted_signature_yields_shadow_only_and_replays(tmp_path):
    db, gs, _ = _db(tmp_path)
    promoted, signature = _promoted_framework(db, gs)
    turn_id, episode_id, causal_id, generation = _active_turn(
        db, "gabriel", gs, resources=("path:/tmp/input",)
    )
    admitted = ProblemSignatureAdmission(db).admit(
        problem_signature=signature,
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        resource_refs=["path:/tmp/input"],
        source="EXPLICIT_STRUCTURED",
        provenance={"source": "test"},
    )
    stage_b = StageBShadowRetrieval(db)
    first = stage_b.retrieve_shadow(
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        signature_receipt_id=admitted["memory_id"],
        resource_refs=["path:/tmp/input"],
        limit=4,
        budget_chars=12000,
    )
    assert first["method_context"] == []
    assert [item["memory_id"] for item in first["shadow_method_context"]] == [promoted["promoted_memory_id"]]
    assert first["receipt"]["served"] is False
    assert first["receipt"]["fact_status_unchanged"] == "UNKNOWN"
    second = stage_b.retrieve_shadow(
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        signature_receipt_id=admitted["memory_id"],
        resource_refs=["path:/tmp/input"],
        limit=4,
        budget_chars=12000,
    )
    assert second["receipt"]["replayed"] is True
    assert second["receipt"]["request_identity_sha256"] == first["receipt"]["request_identity_sha256"]


def test_stage_b_replay_identity_binds_budget_and_resources(tmp_path):
    db, gs, _ = _db(tmp_path)
    _, signature = _promoted_framework(db, gs)
    turn_id, episode_id, causal_id, generation = _active_turn(db, "gabriel", gs)
    admitted = ProblemSignatureAdmission(db).admit(
        problem_signature=signature,
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        resource_refs=[],
        source="VALIDATED_ABSTRACTION",
        provenance={"source": "test"},
    )
    stage_b = StageBShadowRetrieval(db)
    stage_b.retrieve_shadow(
        user_id="gabriel", session_id=gs, turn_id=turn_id, episode_id=episode_id,
        causal_id=causal_id, generation=generation, evidence_status="UNKNOWN",
        signature_receipt_id=admitted["memory_id"], resource_refs=[], budget_chars=12000,
    )
    with pytest.raises(MethodRecordError, match="replay request identity mismatch"):
        stage_b.retrieve_shadow(
            user_id="gabriel", session_id=gs, turn_id=turn_id, episode_id=episode_id,
            causal_id=causal_id, generation=generation, evidence_status="UNKNOWN",
            signature_receipt_id=admitted["memory_id"], resource_refs=[], budget_chars=9000,
        )
    with pytest.raises(MethodRecordError, match="resource refs diverge"):
        stage_b.retrieve_shadow(
            user_id="gabriel", session_id=gs, turn_id=turn_id, episode_id=episode_id,
            causal_id=causal_id, generation=generation, evidence_status="UNKNOWN",
            signature_receipt_id=admitted["memory_id"], resource_refs=["path:/different"], budget_chars=12000,
        )


def test_linked_counterexample_blocks_shadow_transfer(tmp_path):
    db, gs, _ = _db(tmp_path)
    _completed_episode(db, gs, "counter:c")
    manager = MethodMemoryManager(db)
    signature = {"goal": ["recover"], "mechanism": ["stateful", "provenance"]}
    counter_id = manager.admit(
        kind="counterexample",
        payload=_payload(name="known failure", signature=signature, episodes=["counter:c"], status="PROMOTED"),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "counter-test"},
    )
    promoted, _ = _promoted_framework(db, gs, counters=[counter_id])
    turn_id, episode_id, causal_id, generation = _active_turn(db, "gabriel", gs)
    admitted = ProblemSignatureAdmission(db).admit(
        problem_signature=signature,
        user_id="gabriel", session_id=gs, turn_id=turn_id, episode_id=episode_id,
        causal_id=causal_id, generation=generation, resource_refs=[],
        source="EXPLICIT_STRUCTURED", provenance={"source": "test"},
    )
    result = StageBShadowRetrieval(db).retrieve_shadow(
        user_id="gabriel", session_id=gs, turn_id=turn_id, episode_id=episode_id,
        causal_id=causal_id, generation=generation, evidence_status="UNKNOWN",
        signature_receipt_id=admitted["memory_id"], resource_refs=[],
    )
    assert promoted["promoted_memory_id"] not in [item["memory_id"] for item in result["shadow_method_context"]]
    assert counter_id in [item["memory_id"] for item in result["shadow_counterevidence"]]
