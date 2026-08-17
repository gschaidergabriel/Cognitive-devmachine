from pathlib import Path

import pytest

import clayverse.service as service
import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_control_messages_are_bounded_json_objects():
    assert gateway._decode_json_object(
        '{"type":"resize"}', name="control", max_chars=gateway._CONTROL_MESSAGE_MAX_CHARS
    ) == {"type": "resize"}
    with pytest.raises(ValueError, match="exceeds bound"):
        gateway._decode_json_object(
            "x" * (gateway._CONTROL_MESSAGE_MAX_CHARS + 1),
            name="control",
            max_chars=gateway._CONTROL_MESSAGE_MAX_CHARS,
        )
    with pytest.raises(ValueError, match="must be an object"):
        gateway._decode_json_object(
            "[]", name="control", max_chars=gateway._CONTROL_MESSAGE_MAX_CHARS
        )


def test_auth_token_shape_and_size_fail_closed():
    assert gateway._auth_token({"token": "abc"}) == "abc"
    with pytest.raises(Exception, match="token shape"):
        gateway._auth_token({"token": ["not", "text"]})
    with pytest.raises(Exception, match="token shape"):
        gateway._auth_token({"token": "x" * (gateway._AUTH_TOKEN_MAX_CHARS + 1)})


def test_terminal_dimensions_require_json_integers_before_clamp():
    assert gateway._terminal_dimensions({"rows": 24, "cols": 80}) == (24, 80)
    with pytest.raises(ValueError, match="rows"):
        gateway._terminal_dimensions({"rows": True, "cols": 80})
    with pytest.raises(ValueError, match="cols"):
        gateway._terminal_dimensions({"rows": 24, "cols": "80"})


def test_pty_input_frame_is_hard_bounded():
    payload = b"x" * gateway._PTY_INPUT_FRAME_MAX_BYTES
    assert gateway._bounded_pty_input(payload) is payload
    with pytest.raises(ValueError, match="exceeds bound"):
        gateway._bounded_pty_input(payload + b"x")


def test_gateway_source_handles_disconnect_and_rejects_unknown_text_control():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert 'message.get("type") == "websocket.disconnect"' in source
    assert '_bounded_pty_input(message["bytes"])' in source
    assert "unsupported terminal control message" in source


def test_uvicorn_transport_bound_matches_pty_ingress_bound():
    kwargs = service._uvicorn_run_kwargs("127.0.0.1", 3000)
    assert kwargs["ws_max_size"] == service._WS_MAX_MESSAGE_BYTES
    assert kwargs["ws_max_size"] == gateway._PTY_INPUT_FRAME_MAX_BYTES
