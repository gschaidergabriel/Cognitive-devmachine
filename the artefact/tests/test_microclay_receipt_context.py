import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import _bounded_hook_context
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject="topic:test", user_id="gabriel", ts=100.0):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def test_product_turn_preserves_present_and_unknown_retrieval_receipts(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "orchid", "orchid launch code")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        present = life.begin("where is the orchid launch code")
        receipt = present["context"]["retrieval_receipt"]
        assert receipt["status"] == "PRESENT"
        assert receipt["selected_count"] == 1
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
        life.abort("test-present-complete")

        unknown = life.begin("quantum pineapple")
        receipt = unknown["context"]["retrieval_receipt"]
        assert receipt["status"] == "UNKNOWN"
        assert receipt["selected_count"] == 0
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
        life.abort("test-unknown-complete")
    finally:
        db.close()


def test_bound_world_rejects_malformed_or_non_compact_receipt():
    base = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
    }
    with pytest.raises(TurnLifecycleError, match="must be an object"):
        TurnLifecycle._bound_world(base)
    with pytest.raises(TurnLifecycleError, match="must be an object"):
        TurnLifecycle._bound_world({**base, "retrieval_receipt": []})
    with pytest.raises(TurnLifecycleError, match="keys must be strings"):
        TurnLifecycle._bound_world({**base, "retrieval_receipt": {1: "not-canonical"}})
    with pytest.raises(TurnLifecycleError, match="values must be scalar"):
        TurnLifecycle._bound_world({**base, "retrieval_receipt": {"nested": {"not": "compact"}}})
    with pytest.raises(TurnLifecycleError, match="not canonical JSON"):
        TurnLifecycle._bound_world({**base, "retrieval_receipt": {"score": float("nan")}})
    with pytest.raises(TurnLifecycleError, match="compact context bound"):
        TurnLifecycle._bound_world({**base, "retrieval_receipt": {"status": "x" * 5_000}})


def test_terminal_hook_keeps_bound_retrieval_receipt_unchanged():
    receipt = {
        "retrieval_id": "retrieval-1",
        "policy_version": 1,
        "mode": "SHADOW",
        "query_sha256": "a" * 64,
        "candidate_count": 2,
        "selected_count": 1,
        "chars_selected": 19,
        "status": "PRESENT",
        "shadow_differs": False,
        "truth_authority": False,
        "effect_authority": False,
        "outcome_learning_applied": 0,
    }
    context = TurnLifecycle._bound_world(
        {
            "own_recent": [{"role": "user", "content": "orchid"}],
            "cross_session_collision": [],
            "durable_memory": [{"memory_id": "orchid", "value": "orchid launch code"}],
            "retrieval_receipt": receipt,
        }
    )
    result = {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn-1",
        "episode_id": "episode-1",
        "causal_id": "causal-1",
        "generation": 1,
        "resources": [],
        "workspace": {"salience": 0.5, "alternatives": []},
        "needle": {},
        "hyperpositions": [],
        "context": context,
    }
    rendered = _bounded_hook_context(result)
    payload = json.loads(rendered.split("\n", 1)[1])
    assert payload["context"]["retrieval_receipt"] == receipt
