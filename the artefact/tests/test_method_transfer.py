import json
import time

from clayverse.identity import IdentityRouter
from clayverse.method_transfer import MethodTransfer
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def promoted(signature, steps):
    return {
        "status": "PROMOTED",
        "problem_signature": signature,
        "goal_shape": signature["goal_shape"],
        "preconditions": ["failure observed"],
        "method_steps": steps,
        "invariants": ["evidence remains evidence"],
        "expected_observations": ["discriminator changes the hypothesis ranking"],
        "falsifiers": ["discriminator contradicts method"],
        "failure_modes": ["wrong structural class"],
        "scope_limits": ["bounded diagnosis"],
        "source_episode_ids": ["episode:source-a", "episode:source-b"],
        "supporting_memory_ids": ["memory:support"],
        "counterexample_memory_ids": [],
        "provenance": {"source": "validated-transfer-test"},
        "support_count": 3,
        "success_count": 2,
        "failure_count": 1,
        "calibration": 0.8,
        "abstraction_version": "v1",
        "last_validated_at": time.time(),
    }


def add_method(db, kind, subject, record):
    return db.add_memory(kind, subject, json.dumps(record, sort_keys=True), None, "gabriel", {"test": True})


def real_turn(db, content):
    return db.append_turn("session:gabriel", "gabriel", "user", content)


def test_structural_transfer_preserves_unknown_and_is_receipt_bound(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        correct = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap", "failure_observed"], "resource_shapes": ["file"]}
        wrong = {"goal_shape": "plan", "facets": ["open_problem"], "resource_shapes": ["file"]}
        correct_id = add_method(db, "framework", "causal aperture triage", promoted(correct, ["partition observations", "run discriminator"]))
        wrong_id = add_method(db, "framework", "matching words", promoted(wrong, ["diagnose repair file failure"]))
        turn_id = real_turn(db, "diagnose file failure")
        organ = MethodTransfer(db)
        args = dict(
            query="diagnose file failure", signature=correct, evidence_status="UNKNOWN",
            user_id="gabriel", session_id="session:gabriel", turn_id=turn_id,
            episode_id="episode:new", causal_id="causal:new", generation=db.entity_generation(),
        )
        result = organ.retrieve(**args)
        assert result["fact_status"] == "UNKNOWN"
        assert result["receipt"]["fact_status_unchanged"] is True
        assert result["receipt"]["learned_routing_active"] is False
        assert result["receipt"]["turn_id"] == turn_id
        assert result["items"][0]["memory_id"] == correct_id
        assert wrong_id not in {item["memory_id"] for item in result["items"]}
        first_receipt_id = result["receipt"]["use_receipt_memory_id"]
        replay = organ.retrieve(**args)
        assert replay["receipt"]["use_receipt_memory_id"] == first_receipt_id
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'").fetchone()[0] == 1
    finally:
        db.close()


def test_direct_single_instance_promoted_record_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        signature = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap"], "resource_shapes": []}
        record = promoted(signature, ["run discriminator"])
        record["source_episode_ids"] = ["episode:one"]
        record["support_count"] = 1
        add_method(db, "framework", "one anecdote", record)
        turn_id = real_turn(db, "diagnose unknown")
        result = MethodTransfer(db).retrieve(
            query="diagnose unknown", signature=signature, evidence_status="UNKNOWN",
            user_id="gabriel", session_id="session:gabriel", turn_id=turn_id,
            episode_id="episode:single", causal_id="causal:single", generation=db.entity_generation(),
        )
        assert result["items"] == []
        assert result["method_status"] == "UNKNOWN"
        assert result["receipt"]["malformed_rejected"] == 1
    finally:
        db.close()


def test_real_turn_context_keeps_method_memory_out_of_evidence(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        signature = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap", "failure_observed"], "resource_shapes": ["file"]}
        method_id = add_method(db, "framework", "causal aperture triage", promoted(signature, ["partition observations", "run discriminator"]))
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("diagnose file:broken.py failure")
        context = result["context"]
        assert context["retrieval_receipt"]["status"] == "UNKNOWN"
        assert context["method_retrieval_receipt"]["fact_status"] == "UNKNOWN"
        assert context["method_retrieval_receipt"]["method_status"] == "PRESENT"
        assert context["method_retrieval_receipt"]["causal_id"] == result["causal_id"]
        assert context["method_retrieval_receipt"]["generation"] == result["generation"]
        assert context["method_retrieval_receipt"]["learned_routing_active"] is False
        assert context["durable_memory"] == context["evidence_context"] == []
        assert [item["memory_id"] for item in context["method_context"]] == [method_id]
        assert context["method_context"][0]["truth_authority"] is False
        assert context["method_context"][0]["effect_authority"] is False
        receipt_id = context["method_retrieval_receipt"]["use_receipt_memory_id"]
        persisted = db.db.execute("SELECT kind,source_turn_id FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
        assert persisted["kind"] == "method_receipt"
        assert persisted["source_turn_id"] == result["turn_id"]
        life.abort("test-end")
    finally:
        db.close()
