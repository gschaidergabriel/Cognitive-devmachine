import json

from clayverse.terminal_hooks import HOOK_CONTEXT_MAX_CHARS, _bounded_hook_context


def test_hook_compacts_method_context_without_erasing_unknown_or_receipts():
    method = {
        "memory_id": "method:1",
        "kind": "framework",
        "subject": "causal triage",
        "goal_shape": "diagnose_repair",
        "problem_signature": {"goal_shape": "diagnose_repair", "facets": ["evidence_gap"], "resource_shapes": ["file"]},
        "preconditions": ["p" * 500] * 8,
        "method_steps": ["s" * 800] * 8,
        "invariants": ["i" * 500] * 8,
        "expected_observations": ["o" * 500] * 8,
        "falsifiers": ["f" * 500] * 8,
        "failure_modes": ["m" * 500] * 8,
        "scope_limits": ["l" * 500] * 8,
        "source_episode_ids": [f"episode:{i}" for i in range(8)],
        "supporting_memory_ids": [f"memory:{i}" for i in range(8)],
        "counterexample_memory_ids": [f"counter:{i}" for i in range(8)],
        "provenance": {"source": "x" * 1000},
        "calibration": 0.8,
        "structural_score": 1.0,
        "truth_authority": False,
        "effect_authority": False,
    }
    context = {
        "own_recent": [{"content": "r" * 3000}] * 12,
        "cross_session_collision": [{"content": "c" * 3000}] * 5,
        "durable_memory": [{"value": "legacy-duplicate" * 1000}],
        "evidence_context": [{"memory_id": f"fact:{i}", "value": "e" * 3000} for i in range(12)],
        "method_context": [dict(method, memory_id=f"method:{i}") for i in range(5)],
        "unknowns": ["FACT STILL UNKNOWN " + "u" * 5000],
        "counterevidence": [f"counter:{i}" for i in range(100)],
        "retrieval_receipt": {"status": "UNKNOWN", "truth_authority": False, "effect_authority": False},
        "method_retrieval_receipt": {"method_status": "PRESENT", "fact_status": "UNKNOWN", "truth_authority": False, "effect_authority": False},
    }
    result = {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn:1",
        "episode_id": "episode:1",
        "causal_id": "causal:1",
        "generation": 1,
        "resources": ["file:broken.py"],
        "workspace": {"salience": 0.9, "alternatives": []},
        "needle": {},
        "hyperpositions": [],
        "context": context,
    }
    rendered = _bounded_hook_context(result)
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    payload = json.loads(rendered.split("\n", 1)[1])
    hook_context = payload["context"]
    assert "durable_memory" not in hook_context
    assert hook_context["retrieval_receipt"]["status"] == "UNKNOWN"
    assert hook_context["method_retrieval_receipt"]["method_status"] == "PRESENT"
    assert hook_context["unknowns"]
    assert hook_context["method_context"]
    assert hook_context["method_context"][0]["truth_authority"] is False
    assert hook_context["method_context"][0]["effect_authority"] is False
