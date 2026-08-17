from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def test_context_packing_preserves_authority_receipts():
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
        "retrieval_receipt": {"status": "UNKNOWN", "truth_authority": False},
        "method_receipt": {
            "stage": "B",
            "status": "UNADMITTED",
            "served": False,
            "raw_prompt_authority": False,
        },
    }

    packed = TurnLifecycle._bound_world(world, max_chars=10_000)

    assert packed["retrieval_receipt"] == world["retrieval_receipt"]
    assert packed["method_receipt"] == world["method_receipt"]


def test_raw_prompt_cannot_admit_stage_b_method_routing(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin(
            "Use a framework heuristic analogy transfer method to solve this unknown problem"
        )
        context = result["context"]
        receipt = context["method_receipt"]

        assert receipt["stage"] == "B"
        assert receipt["status"] == "UNADMITTED"
        assert receipt["served"] is False
        assert receipt["raw_prompt_authority"] is False
        assert receipt["truth_authority"] is False
        assert receipt["reason"] == "independent_structured_problem_signature_required"
        assert "method_context" not in context

        life.abort("test-end")
    finally:
        db.close()
