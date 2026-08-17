import json

import pytest

from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def test_bound_world_never_returns_payload_above_declared_limit():
    max_chars = 1_000
    world = {
        "own_recent": [
            {"role": "user", "content": "X" * 5_000}
            for _ in range(4)
        ],
        "cross_session_collision": [],
        "durable_memory": [],
        "retrieval_receipt": {
            "status": "PRESENT",
            "selected_count": 0,
            "truth_authority": False,
            "effect_authority": False,
        },
    }

    try:
        packed = TurnLifecycle._bound_world(world, max_chars=max_chars)
    except TurnLifecycleError:
        return

    rendered = json.dumps(packed, ensure_ascii=False, sort_keys=True, default=str)
    assert len(rendered) <= max_chars, (
        "_bound_world returned a payload larger than its declared max_chars "
        f"contract: {len(rendered)} > {max_chars}"
    )
