import inspect

import uvicorn

import clayverse.service as service
import clayverse.terminal_gateway as gateway


def test_uvicorn_websocket_transport_is_bounded_before_asgi():
    options = service._uvicorn_transport_config("127.0.0.1", 3000)

    assert options["host"] == "127.0.0.1"
    assert options["port"] == 3000
    assert options["workers"] == 1
    assert options["access_log"] is False
    assert options["ws"] == "websockets"
    assert options["ws_max_size"] == gateway._PTY_INPUT_FRAME_MAX_BYTES
    assert options["ws_max_size"] >= gateway._AUTH_MESSAGE_MAX_CHARS
    assert 1 <= options["ws_max_queue"] <= 8
    assert options["ws_per_message_deflate"] is False


def test_pinned_uvicorn_exposes_required_transport_controls():
    parameters = inspect.signature(uvicorn.run).parameters
    for required in ("ws", "ws_max_size", "ws_max_queue", "ws_per_message_deflate"):
        assert required in parameters
