import clayverse.service as service
import clayverse.terminal_gateway as gateway


def test_terminal_websocket_transport_is_pinned_and_bounded():
    options = service._uvicorn_websocket_options()

    assert options == {
        "ws": "websockets",
        "ws_max_size": gateway._PTY_INPUT_FRAME_MAX_BYTES,
        "ws_max_queue": 8,
        "ws_per_message_deflate": False,
    }
    assert options["ws_max_size"] == 65_536
