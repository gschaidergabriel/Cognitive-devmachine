import json
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


def test_uncompactable_context_never_spills_to_file_and_declares_what_it_dropped():
    """Die geschuetzte Eigenschaft ist: NICHTS wird in eine Datei ausgelagert.

    Frueher war der Mechanismus dafuer ein harter Abbruch. Der hat aber den
    Menschen ausgesperrt: bei gewachsenem Kontext kam kein Prompt mehr durch,
    und die Sitzung war tot. Zwischen "unbegrenzt ausliefern" und "gar nichts"
    liegt "weniger, und es steht dabei".

    Der Test prueft deshalb die Eigenschaft, nicht mehr den Mechanismus:
    es bleibt inline, es bleibt in der Huelle, und was fehlt, ist BENANNT --
    stille Kuerzung waere schlimmer als die Sperre, weil das Modell dann mit
    einem Loch arbeitet, von dem es nichts weiss.
    """
    huge_resource = "resource:" + ("r" * 12_000)
    text = _bounded_hook_context(_result("short", resources=[huge_resource]))

    assert len(text) <= HOOK_CONTEXT_MAX_CHARS
    nutzlast = json.loads(text[text.index("{"):])
    assert nutzlast["gekuerzt"]["entfernt"], "was entfernt wurde, muss benannt sein"
    assert "r" * 500 not in text, "der riesige Verweis darf nicht ungekuerzt mitfahren"


def test_minimal_envelope_still_fails_closed_when_the_budget_itself_is_wrong():
    """Wenn selbst die Notfassung nicht passt, ist die Grenze falsch gesetzt --
    das ist ein echter Fehler und muss weiterhin hart abbrechen."""
    with pytest.raises(TerminalHookError, match="budget is wrong"):
        _bounded_hook_context(_result("short"), limit=10)
