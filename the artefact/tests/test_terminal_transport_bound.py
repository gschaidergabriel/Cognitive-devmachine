from pathlib import Path

import clayverse.service as service
import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_uvicorn_transport_limit_matches_terminal_ingress_bound():
    kwargs = service._uvicorn_run_kwargs("127.0.0.1", 3000)
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 3000
    assert kwargs["workers"] == 1
    assert kwargs["access_log"] is False
    assert kwargs["ws_max_size"] == 65_536
    assert kwargs["ws_max_size"] == gateway._PTY_INPUT_FRAME_MAX_BYTES
    assert kwargs["ws_max_size"] >= gateway._AUTH_MESSAGE_MAX_CHARS


def test_service_main_uses_the_bounded_uvicorn_settings():
    source = (ROOT / "clayverse" / "service.py").read_text()
    assert "uvicorn.run(app, **_uvicorn_run_kwargs(host, port))" in source
    assert '"ws_max_size": _WS_MAX_MESSAGE_BYTES' in source
