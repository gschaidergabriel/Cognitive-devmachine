from __future__ import annotations

import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import _HOOK_CONTEXT_PREFIX, _bounded_hook_context
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


def test_product_turn_preserves_present_and_unknown_receipts(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "orchid-memory", "orchid launch code")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        present = life.begin("where is the orchid launch code")
        receipt = present["context"]["retrieval_receipt"]
        assert receipt["status"] == "PRESENT"
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
        life.abort("test-present")

        unknown = life.begin("quantum pineapple")
        receipt = unknown["context"]["retrieval_receipt"]
        assert receipt["status"] == "UNKNOWN"
        assert receipt["truth_authority"] is False
        assert receipt["effect_authority"] is False
        life.abort("test-unknown")
    finally:
        db.close()


def test_bound_world_keeps_receipt_inside_budget_accounting():
    receipt = {
        "status": "PRESENT",
        "mode": "SHADOW",
        "truth_authority": False,
        "effect_authority": False,
        "selected_count": 1,
    }
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [{"memory_id": str(i), "value": "x" * 500} for i in range(20)],
        "retrieval_receipt": receipt,
    }
    bounded = TurnLifecycle._bound_world(world, max_chars=1000)
    assert bounded["retrieval_receipt"] == receipt
    assert len(json.dumps(bounded, ensure_ascii=False, sort_keys=True, default=str)) <= 1000


@pytest.mark.parametrize("bad", [None, [], "receipt", 1])
def test_bound_world_fails_closed_on_missing_or_malformed_receipt(bad):
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
    }
    if bad is not None:
        world["retrieval_receipt"] = bad
    with pytest.raises(TurnLifecycleError, match="retrieval receipt"):
        TurnLifecycle._bound_world(world)


def test_terminal_hook_context_keeps_bound_receipt_unchanged():
    receipt = {
        "status": "UNKNOWN",
        "mode": "SHADOW",
        "truth_authority": False,
        "effect_authority": False,
        "selected_count": 0,
    }
    result = {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn",
        "episode_id": "episode",
        "causal_id": "causal",
        "generation": 1,
        "resources": [],
        "workspace": {"salience": 0.1, "alternatives": []},
        "needle": {},
        "hyperpositions": [],
        "context": {
            "own_recent": [],
            "cross_session_collision": [],
            "durable_memory": [],
            "retrieval_receipt": receipt,
        },
    }
    rendered = _bounded_hook_context(result)
    compact = json.loads(rendered.removeprefix(_HOOK_CONTEXT_PREFIX))
    assert compact["context"]["retrieval_receipt"] == receipt
