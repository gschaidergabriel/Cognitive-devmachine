import pytest

from clayverse.terminal_hooks import (
    HOOK_CONTEXT_MAX_CHARS,
    TerminalHookError,
    _bounded_hook_context,
)


def _result(content: str, resources=None):
    return {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn-1",
        "episode_id": "episode-1",
        "causal_id": "causal-1",
        "generation": 1,
        "resources": resources or [],
        "workspace": {
            "salience": 0.5,
            "alternatives": [
                {"id": "respond", "kind": "reason"},
                {"id": "request_effect", "kind": "effect_intent"},
                {"id": "defer_effect", "kind": "no_effect"},
            ],
        },
        "context": {
            "own_recent": [{"role": "user", "content": content}],
            "cross_session_collision": [],
            "durable_memory": [],
        },
    }


def test_large_canonical_context_is_compacted_below_inline_envelope():
    rendered = _bounded_hook_context(_result("x" * 10_500))
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    assert HOOK_CONTEXT_MAX_CHARS < 10_000
    assert rendered.startswith("ClayVerse canonical context snapshot")
    assert "…" in rendered


def test_envelope_counts_prefix_not_only_json_payload():
    rendered = _bounded_hook_context(_result("short"))
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    assert rendered.endswith("}")


def test_uncompactable_context_fails_closed_instead_of_spilling_to_file():
    huge_resource = "resource:" + ("r" * 12_000)
    with pytest.raises(TerminalHookError, match="safe inline hook envelope"):
        _bounded_hook_context(_result("short", resources=[huge_resource]))
