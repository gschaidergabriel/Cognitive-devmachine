import json
import time

import pytest

from clayverse.method_transfer import MethodTransfer
from clayverse.retrieval import EvidenceMicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _world(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    sid = db.ensure_session("gabriel", "terminal-gabriel")
    generation = db.session_generation(sid)
    return db, sid, generation


def _signature():
    return {
        "intent": ["diagnose"],
        "system_shape": ["concurrent"],
        "failure_shape": ["replay_identity"],
        "resources": ["database"],
        "constraints": ["replay_safe", "bounded"],
        "goal_shape": ["diagnose"],
    }


def _method(*, signature=None, support=3, calibration=0.95, status="PROMOTED"):
    return {
        "problem_signature": signature or _signature(),
        "preconditions": ["capture exact request identity"],
        "goal_shape": ["diagnose"],
        "method_steps": ["freeze identity", "perturb one causal dimension", "compare outcome"],
        "invariants": ["do not widen authority"],
        "expected_observations": ["mismatched replay is rejected"],
        "falsifiers": ["mismatched replay is served"],
        "failure_modes": ["hidden identity dimension"],
        "scope_limits": ["causal replay systems"],
        "source_episode_ids": ["episode:source-a", "episode:source-b"],
        "supporting_memory_ids": ["evidence:a", "evidence:b"],
        "counterexample_memory_ids": [],
        "provenance": {"source": "test-fixture", "truth_authority": False},
        "abstraction_version": 1,
        "support_count": support,
        "success_count": max(0, support - 1),
        "failure_count": 1 if support > 1 else 0,
        "calibration": calibration,
        "last_validated_at": 1.0,
        "status": status,
    }


def _add(db, memory_id, kind, subject, value, *, user_id=None):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            memory_id,
            kind,
            subject,
            json.dumps(value, ensure_ascii=False, sort_keys=True),
            None,
            user_id,
            time.time(),
            json.dumps({"source": "test"}, sort_keys=True),
        ),
    )


def _retrieve(mt, sid, generation, *, query, causal_id, evidence_status="UNKNOWN"):
    return mt.retrieve(
        query=query,
        evidence_status=evidence_status,
        user_id="gabriel",
        session_id=sid,
        turn_id=f"turn:{causal_id}",
        episode_id=f"episode:{causal_id}",
        causal_id=causal_id,
        generation=generation,
        resource_refs=[],
    )


def test_known_evidence_without_method_intent_does_not_trigger(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:known", "framework", "not needed", _method())
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="What checksum is recorded for artifact x?",
        causal_id="known",
        evidence_status="PRESENT",
    )
    assert result["items"] == []
    assert result["receipt"]["status"] == "NOT_TRIGGERED"
    assert result["receipt"]["truth_authority"] is False


def test_unknown_can_supply_method_without_truth_authority(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:transfer", "framework", "causal aperture", _method())
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="Investigate a parallel duplicate sqlite replay with bounded idempotent handling",
        causal_id="unknown",
    )
    assert result["receipt"]["status"] == "METHOD_PRESENT"
    assert result["receipt"]["trigger"] == "EVIDENCE_UNKNOWN"
    assert result["receipt"]["truth_authority"] is False
    assert result["items"][0]["method_id"] == "method:transfer"
    assert result["items"][0]["truth_authority"] is False
    assert result["items"][0]["effect_authority"] is False


def test_single_success_cannot_become_active_method(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:single", "framework", "one anecdote", _method(support=1))
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="Investigate a parallel duplicate sqlite replay with bounded idempotent handling",
        causal_id="single",
    )
    assert result["items"] == []
    assert result["receipt"]["status"] == "NO_METHOD"
    assert result["receipt"]["malformed_rejected"] == 1


def test_verified_counterexample_can_hard_block_framework(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:block", "framework", "candidate method", _method())
    _add(
        db,
        "counter:block",
        "counterexample",
        "known failure",
        {
            "problem_signature": _signature(),
            "status": "VERIFIED",
            "severity": 1.0,
            "method_ids": ["method:block"],
        },
    )
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="Investigate a parallel duplicate sqlite replay with bounded idempotent handling",
        causal_id="blocked",
    )
    assert result["items"] == []
    assert result["receipt"]["status"] == "NO_METHOD"


def test_method_replay_is_identity_bound_and_query_drift_fails_closed(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:replay", "framework", "replay method", _method())
    mt = MethodTransfer(db)
    query = "Investigate a parallel duplicate sqlite replay with bounded idempotent handling"
    first = _retrieve(mt, sid, generation, query=query, causal_id="replay")
    replay = _retrieve(mt, sid, generation, query=query, causal_id="replay")
    assert first["items"] == replay["items"]
    assert replay["receipt"]["replayed"] is True
    with pytest.raises(StaleGeneration):
        _retrieve(
            mt, sid, generation,
            query="Investigate a parallel timeout network stream",
            causal_id="replay",
        )


def test_other_user_private_method_is_not_visible(tmp_path):
    db, sid, generation = _world(tmp_path)
    _add(db, "method:andreas", "framework", "private method", _method(), user_id="andreas")
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="Investigate a parallel duplicate sqlite replay with bounded idempotent handling",
        causal_id="privacy",
    )
    assert result["items"] == []


def test_stage_a_scores_method_memory_as_nonservable(tmp_path):
    db, _, _ = _world(tmp_path)
    retriever = EvidenceMicroClayRetrieval(db)
    row = {
        "memory_id": "method:evidence-fence",
        "kind": "framework",
        "subject": "sqlite replay",
        "value": "sqlite replay diagnose parallel duplicate",
        "ts": time.time(),
        "provenance": "{}",
    }
    candidate = retriever._score_candidate(
        row,
        {"sqlite", "replay", "diagnose", "parallel"},
        time.time(),
        {},
    )
    assert candidate.baseline_score == 0.0
    assert candidate.adaptive_score == 0.0
    assert candidate.entry_keys == ()


def test_structural_transfer_beats_lexical_decoy_unusual_experiment(tmp_path):
    """ONE unusual GO experiment: invert lexical lure against structural identity."""
    db, sid, generation = _world(tmp_path)
    _add(
        db,
        "method:structural",
        "framework",
        "aurora aperture",
        _method(),
    )
    _add(
        db,
        "method:lexical-decoy",
        "framework",
        "investigate parallel duplicate sqlite replay bounded idempotent strategy",
        _method(
            signature={
                "intent": ["design"],
                "system_shape": ["streaming"],
                "failure_shape": ["timeout_latency"],
                "resources": ["network"],
                "constraints": ["no_side_effect"],
                "goal_shape": ["design"],
            }
        ),
    )
    result = _retrieve(
        MethodTransfer(db), sid, generation,
        query="Investigate a parallel duplicate sqlite replay with bounded idempotent handling",
        causal_id="lexical-inversion",
    )
    ids = [item["method_id"] for item in result["items"]]
    assert ids == ["method:structural"]
    assert "method:lexical-decoy" not in ids
