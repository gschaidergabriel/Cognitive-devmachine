import json
import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_admission import MethodAdmission, MethodAdmissionError
from clayverse.method_transfer import MethodTransfer
from clayverse.store import UnifiedDB


def candidate(signature):
    return {
        "problem_signature": signature, "goal_shape": signature["goal_shape"],
        "method_steps": ["partition observations", "run discriminator"],
        "falsifiers": ["counter-test reverses ranking"],
        "source_episode_ids": ["episode:source-a"],
        "provenance": {"source": "episode abstraction"},
    }


def promoted(signature):
    return {
        "problem_signature": signature, "goal_shape": signature["goal_shape"],
        "preconditions": ["failure observed"],
        "method_steps": ["partition observations", "run discriminator"],
        "invariants": ["preserve factual unknown"],
        "expected_observations": ["hypothesis ranking changes"],
        "falsifiers": ["counter-test reverses ranking"], "failure_modes": ["wrong structure"],
        "scope_limits": ["bounded diagnosis"],
        "source_episode_ids": ["episode:source-a", "episode:source-b"],
        "supporting_memory_ids": ["memory:support-a", "memory:support-b"],
        "counterexample_memory_ids": [], "provenance": {"source": "external validation"},
        "abstraction_version": "v1", "support_count": 2, "success_count": 2, "failure_count": 0,
        "calibration": 0.8, "last_validated_at": time.time(),
    }


def validation(validated_by="external_replay_gate"):
    return {
        "source_provenance_complete": True, "counterexample_search_performed": True,
        "held_out_or_cross_instance_passed": True, "contamination_increase": False,
        "stale_state_use": False, "privacy_leakage": False, "authority_leakage": False,
        "validated_by": validated_by, "validation_episode_ids": ["validation:a", "validation:b"],
    }


def test_external_gate_rejects_single_instance_and_self_promotion(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        gate = MethodAdmission(db)
        sig = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap"], "resource_shapes": ["file"]}
        candidate_id = gate.create_candidate(
            kind="framework_candidate", subject="triage", record=candidate(sig), source_turn_id=None,
            user_id="gabriel", session_id="session:gabriel", generation=db.entity_generation(), provenance={"test": True})
        turn_id = db.append_turn("session:gabriel", "gabriel", "user", "promotion validation")
        one = promoted(sig); one["source_episode_ids"] = ["episode:only"]; one["support_count"] = 1
        with pytest.raises(MethodAdmissionError, match="single-instance|promoted record invalid"):
            gate.promote(candidate_memory_id=candidate_id, promoted_record=one, validation=validation(),
                         user_id="gabriel", session_id="session:gabriel", turn_id=turn_id,
                         episode_id="episode:p", causal_id="causal:p", generation=db.entity_generation())
        with pytest.raises(MethodAdmissionError, match="self-promotion"):
            gate.promote(candidate_memory_id=candidate_id, promoted_record=promoted(sig), validation=validation("microclay"),
                         user_id="gabriel", session_id="session:gabriel", turn_id=turn_id,
                         episode_id="episode:p", causal_id="causal:p", generation=db.entity_generation())
    finally:
        db.close()


def test_promote_then_demote_is_append_only_and_blocks_transfer(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        gate = MethodAdmission(db)
        sig = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap"], "resource_shapes": ["file"]}
        candidate_id = gate.create_candidate(
            kind="framework_candidate", subject="triage", record=candidate(sig), source_turn_id=None,
            user_id="gabriel", session_id="session:gabriel", generation=db.entity_generation(), provenance={"test": True})
        pturn = db.append_turn("session:gabriel", "gabriel", "user", "promotion validation")
        promoted_result = gate.promote(
            candidate_memory_id=candidate_id, promoted_record=promoted(sig), validation=validation(),
            user_id="gabriel", session_id="session:gabriel", turn_id=pturn,
            episode_id="episode:p", causal_id="causal:p", generation=db.entity_generation())
        method_id = promoted_result["promoted_memory_id"]
        use_a = db.append_turn("session:gabriel", "gabriel", "user", "diagnose unknown file")
        before = MethodTransfer(db).retrieve(
            query="diagnose unknown file", signature=sig, evidence_status="UNKNOWN",
            user_id="gabriel", session_id="session:gabriel", turn_id=use_a,
            episode_id="episode:a", causal_id="causal:a", generation=db.entity_generation())
        assert [item["memory_id"] for item in before["items"]] == [method_id]
        counter_id = db.add_memory(
            "counterexample", "triage counter",
            json.dumps({"problem_signature": sig, "targets": [method_id]}, sort_keys=True),
            None, "gabriel", {"test": True})
        dturn = db.append_turn("session:gabriel", "gabriel", "user", "demote method")
        gate.change_state(
            method_memory_id=method_id, action="DEMOTE", reason="counterexample invalidated scope",
            counterexample_memory_ids=[counter_id], user_id="gabriel", session_id="session:gabriel",
            turn_id=dturn, episode_id="episode:d", causal_id="causal:d", generation=db.entity_generation())
        use_b = db.append_turn("session:gabriel", "gabriel", "user", "diagnose unknown file again")
        after = MethodTransfer(db).retrieve(
            query="diagnose unknown file", signature=sig, evidence_status="UNKNOWN",
            user_id="gabriel", session_id="session:gabriel", turn_id=use_b,
            episode_id="episode:b", causal_id="causal:b", generation=db.entity_generation())
        assert after["items"] == []
        assert after["receipt"]["state_blocked"] == 1
        assert db.db.execute("SELECT 1 FROM durable_memory WHERE memory_id=?", (method_id,)).fetchone() is not None
    finally:
        db.close()
