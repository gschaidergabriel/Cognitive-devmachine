import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.retrieval import WorldAssembler
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def test_product_unknown_persists_signature_required_stage_b_without_serving(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("unseen mechanism without matching factual evidence")
        context = turn["context"]

        assert context["retrieval_receipt"]["status"] == "UNKNOWN"
        assert context["durable_memory"] == []
        assert context["method_context"] == []
        assert context["counterevidence"] == []
        assert context["method_receipt"]["status"] == "SIGNATURE_REQUIRED"
        assert context["method_receipt"]["triggered"] is False
        assert context["method_receipt"]["factual_status_unchanged"] == "UNKNOWN"
        assert context["method_receipt"]["truth_authority"] is False
        assert context["method_receipt"]["effect_authority"] is False
        assert context["method_receipt"]["selected_method_ids_count"] == 0
        assert context["method_receipt"]["counterevidence_ids_count"] == 0
        assert context["unknowns"][0]["status"] == "FACT_UNKNOWN"

        persisted = db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory "
            "WHERE source_turn_id=? AND kind='method_receipt'",
            (turn["turn_id"],),
        ).fetchone()
        assert persisted is not None
        payload = json.loads(persisted["value"])
        assert payload["receipt"]["status"] == "SIGNATURE_REQUIRED"
        assert payload["receipt"]["selected_method_ids"] == []
        assert payload["receipt"]["counterevidence_ids"] == []
        assert payload["receipt"]["factual_status_unchanged"] == "UNKNOWN"
        assert json.loads(persisted["provenance"])["source"] == "method_stage_b:v2"
        life.abort("stageab-test-complete")
    finally:
        db.close()


def test_same_causal_signature_addition_after_signature_required_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("unseen mechanism without matching factual evidence")
        with pytest.raises(StaleGeneration, match="method_retrieval_identity"):
            life.world.assemble(
                "session:gabriel",
                [],
                query="unseen mechanism without matching factual evidence",
                problem_signature={"goal_shape": ["diagnose"], "evidence_state": ["unknown"]},
                turn_id=turn["turn_id"],
                episode_id=turn["episode_id"],
                causal_id=turn["causal_id"],
                generation=turn["generation"],
            )
        life.abort("stageab-test-complete")
    finally:
        db.close()


def test_method_receipt_context_projection_is_scalar_and_binds_id_lists():
    projected = WorldAssembler._context_method_receipt({
        "receipt_schema": "clayverse-stage-b-method-use/v2",
        "policy_version": 2,
        "status": "METHOD_PRESENT",
        "selected_method_ids": ["method-a", "method-b"],
        "counterevidence_ids": ["counter-a"],
        "factual_status_unchanged": "UNKNOWN",
        "truth_authority": False,
        "effect_authority": False,
    })
    assert projected["selected_method_ids_count"] == 2
    assert projected["counterevidence_ids_count"] == 1
    assert len(projected["selected_method_ids_sha256"]) == 64
    assert len(projected["counterevidence_ids_sha256"]) == 64
    assert all(isinstance(value, (str, int, float, bool, type(None))) for value in projected.values())

    with pytest.raises(StaleGeneration, match="method_retrieval_receipt"):
        WorldAssembler._context_method_receipt({"status": "METHOD_PRESENT", "nested": {"bad": True}})
