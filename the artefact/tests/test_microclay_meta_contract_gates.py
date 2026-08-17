from __future__ import annotations

import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _promoted_framework(*, problem_signature=None):
    return {
        "problem_signature": problem_signature or ["dependency boundary", "bounded diagnosis"],
        "preconditions": ["a dependency boundary exists"],
        "goal_shape": ["localize a causal bottleneck without inventing a fact"],
        "method_steps": ["isolate the boundary", "run a bounded falsifier"],
        "invariants": ["fact status remains UNKNOWN until evidence arrives"],
        "expected_observations": ["the failure follows the isolated dependency when causal"],
        "falsifiers": ["the failure persists after dependency removal"],
        "failure_modes": ["surface similarity without causal equivalence"],
        "scope_limits": ["method context is not factual evidence"],
        "source_episode_ids": ["episode:validated:1"],
        "supporting_memory_ids": ["memory:validated:1"],
        "counterexample_memory_ids": ["memory:counterexample:1"],
        "abstraction_version": 1,
        "support_count": 3,
        "success_count": 2,
        "failure_count": 1,
        "calibration": 0.67,
        "last_validated_at": "2026-08-17T00:00:00Z",
        "status": "PROMOTED",
        # Compatibility alias used by the current #404 implementation.  The test below
        # intentionally requires the canonical full contract as well.
        "lifecycle_status": "PROMOTED",
    }


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid


def _add_method(db: UnifiedDB, record: dict, *, subject="dependency-isolation"):
    return db.add_memory(
        "framework",
        subject,
        "validated reusable diagnostic method",
        None,
        "gabriel",
        {"method_record": record},
    )


def test_product_turn_context_surfaces_fact_unknown_and_method_context(tmp_path):
    """The real hook path, not a direct WorldAssembler call, must deliver Stage B to Claude."""
    db, sid = _db(tmp_path)
    try:
        method_id = _add_method(
            db,
            _promoted_framework(problem_signature=["sensor timeout dependency", "bounded diagnosis"]),
        )
        result = TurnLifecycle(db, "gabriel", sid).begin("sensor timeout dependency")
        context = result["context"]

        assert context["retrieval_receipt"]["status"] == "UNKNOWN"
        assert context["unknowns"] == [pytest.helpers.anything] if False else context["unknowns"]
        assert context["unknowns"][0]["status"] == "FACT_UNKNOWN"
        assert context["unknowns"][0]["method_present"] is True
        assert [item["memory_id"] for item in context["method_context"]] == [method_id]
        assert context["durable_memory"] == []
    finally:
        db.close()


def test_promoted_method_requires_complete_contract_envelope(tmp_path):
    """A method is not ACTIVE merely because a few convenient fields and PROMOTED text exist."""
    db, sid = _db(tmp_path)
    try:
        incomplete = {
            "problem_signature": ["sensor timeout dependency"],
            "preconditions": ["dependency exists"],
            "method_steps": ["isolate dependency"],
            "falsifiers": ["failure persists after isolation"],
            "scope_limits": ["not factual evidence"],
            "lifecycle_status": "PROMOTED",
        }
        _add_method(db, incomplete)
        micro = MicroClayRetrieval(db)
        turn_id = db.append_turn(sid, "gabriel", "user", "sensor timeout dependency")

        with pytest.raises(ValueError, match="goal_shape|invariants|expected_observations|source_episode_ids|support_count|calibration|status"):
            micro.retrieve_methods(
                query="sensor timeout dependency",
                user_id="gabriel",
                turn_id=turn_id,
            )
    finally:
        db.close()


def test_structurally_similar_lexically_dissimilar_problem_retrieves_framework(tmp_path):
    """Contract test: structural transfer must not require token overlap with the saved signature."""
    db, sid = _db(tmp_path)
    try:
        method_id = _add_method(
            db,
            _promoted_framework(
                problem_signature=[
                    "upstream dependency controls downstream availability",
                    "intervention isolates one causal boundary",
                    "partial observability with competing causes",
                ]
            ),
            subject="causal-boundary-isolation",
        )
        micro = MicroClayRetrieval(db)
        query = "The lamp flickers only after the shared feeder is loaded; what diagnostic strategy should I use?"
        turn_id = db.append_turn(sid, "gabriel", "user", query)

        result = micro.retrieve_methods(query=query, user_id="gabriel", turn_id=turn_id)

        assert result["receipt"]["status"] == "METHOD_PRESENT"
        assert [item["memory_id"] for item in result["items"]] == [method_id]
        assert result["items"][0]["truth_authority"] is False
    finally:
        db.close()
