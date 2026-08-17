import json
import time

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def promoted(signature, subject):
    return {
        "status": "PROMOTED", "problem_signature": signature, "goal_shape": signature["goal_shape"],
        "preconditions": ["failure observed"], "method_steps": ["partition observations", "run discriminator"],
        "invariants": ["preserve factual unknown"], "expected_observations": ["ranking changes after evidence"],
        "falsifiers": ["counter-test reverses ranking"], "failure_modes": ["wrong structure"],
        "scope_limits": ["bounded diagnosis"],
        "source_episode_ids": [f"episode:{subject}:a", f"episode:{subject}:b"],
        "supporting_memory_ids": [], "counterexample_memory_ids": [],
        "provenance": {"source": "route-policy-test"}, "abstraction_version": "v1",
        "support_count": 2, "success_count": 2, "failure_count": 0,
        "calibration": 0.8, "last_validated_at": time.time(),
    }


def test_verified_negative_outcome_changes_shadow_not_served_ranking(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        signature = {"goal_shape": "diagnose_repair", "facets": ["evidence_gap", "failure_observed"], "resource_shapes": ["file"]}
        for subject in ("alpha frame", "beta frame"):
            db.add_memory("framework", subject, json.dumps(promoted(signature, subject), sort_keys=True), None, "gabriel", {"test": True})
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("diagnose file:broken.py failure")
        receipt_a = first["context"]["method_retrieval_receipt"]
        served = receipt_a["selected_method_ids"]
        assert len(served) == 2
        assert receipt_a["shadow_method_ids"] == served
        assert receipt_a["learned_routing_active"] is False

        effect_id = db.record_effect(
            first["episode_id"], "gabriel", "test_effect", "bounded-test-target",
            first["generation"], "FAILED", outcome={"ok": False})
        db.db.execute(
            "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
            (first["causal_id"], first["episode_id"], effect_id, first["turn_id"],
             "negative-outcome", -1.0, 1, time.time()))

        second = life.begin("diagnose file:broken.py failure")
        receipt_b = second["context"]["method_retrieval_receipt"]
        assert receipt_b["selected_method_ids"] == served
        assert receipt_b["shadow_method_ids"] != served
        assert receipt_b["shadow_method_ids"][0] == served[1]
        assert receipt_b["learned_routing_active"] is False
        assert receipt_b["outcome_learning_applied"] == 1
        assert second["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        capitals = {
            row["entry_key"]: float(row["capital"])
            for row in db.db.execute("SELECT entry_key,capital FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'method:%'").fetchall()
        }
        assert any(key.startswith(f"method:id:{served[0]}") and value < 0 for key, value in capitals.items())
        assert not any(key.startswith(f"method:id:{served[1]}") and value != 0 for key, value in capitals.items())
        life.abort("test-end")
    finally:
        db.close()
