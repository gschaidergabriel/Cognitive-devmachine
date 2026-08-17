import json

import pytest

from clayverse.inference_protocol import InferenceProtocolError, parse_claude_decision


def encode(text="ok", effect=None):
    return json.dumps({"text": text, "effect": effect})


def test_normal_response_has_no_effect():
    assert parse_claude_decision(encode()) == {"text": "ok", "selection": "respond", "effect": None}


def test_entityos_intent_is_bounded_and_selected():
    decision = parse_claude_decision(encode(effect={
        "capability": "entityos.exec",
        "target": "status probe",
        "argv": ["status", "--json"],
    }))
    assert decision["selection"] == "request_effect"
    assert decision["effect"] == {
        "capability": "entityos.exec",
        "target": "status probe",
        "argv": ["status", "--json"],
    }


@pytest.mark.parametrize("effect", [
    {"capability": "process.exec", "target": "forbidden", "argv": ["/bin/echo", "x"]},
    {"capability": "entityos.exec", "target": "missing argv", "argv": []},
    {"capability": "entityos.exec", "target": "nul", "argv": ["bad\x00arg"]},
    {"capability": "state.noop", "target": "noop", "argv": ["unexpected"]},
])
def test_forbidden_or_malformed_effects_fail_closed(effect):
    with pytest.raises(InferenceProtocolError):
        parse_claude_decision(encode(effect=effect))


def test_unknown_fields_and_non_json_fail_closed():
    with pytest.raises(InferenceProtocolError):
        parse_claude_decision(json.dumps({"text": "x", "effect": None, "extra": True}))
    with pytest.raises(InferenceProtocolError):
        parse_claude_decision("not-json")
