import uvicorn

from clayverse.service import _uvicorn_websocket_kwargs
from clayverse.terminal_gateway import _PTY_INPUT_FRAME_MAX_BYTES


async def _noop_asgi(scope, receive, send):
    return None


def test_service_binds_transport_before_asgi_delivery():
    kwargs = _uvicorn_websocket_kwargs()
    assert kwargs == {
        "ws": "websockets",
        "ws_max_size": _PTY_INPUT_FRAME_MAX_BYTES,
        "ws_max_queue": 4,
        "ws_per_message_deflate": False,
    }

    config = uvicorn.Config(_noop_asgi, **kwargs)
    assert config.ws == "websockets"
    assert config.ws_max_size == _PTY_INPUT_FRAME_MAX_BYTES
    assert config.ws_max_queue == 4
    assert config.ws_per_message_deflate is False
