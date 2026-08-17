import json

import pytest

from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _serialized_chars(value):
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))


def test_receipt_dominating_world_budget_fails_closed():
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
        "retrieval_receipt": {
            "probe": "R" * 1800,
            "status": "PRESENT",
            "truth_authority": False,
        },
    }
    with pytest.raises(TurnLifecycleError, match="world context exceeds bound after safe trimming"):
        TurnLifecycle._bound_world(world, max_chars=1000)


def test_world_with_compact_receipt_stays_inside_bound():
    world = {
        "own_recent": [{"content": "recent"}],
        "cross_session_collision": [],
        "durable_memory": [{"value": "x" * 500}, {"value": "y" * 500}],
        "retrieval_receipt": {
            "status": "PRESENT",
            "selected_count": 1,
            "truth_authority": False,
            "effect_authority": False,
        },
    }
    packed = TurnLifecycle._bound_world(world, max_chars=800)
    assert packed["retrieval_receipt"] == world["retrieval_receipt"]
    assert _serialized_chars(packed) <= 800
