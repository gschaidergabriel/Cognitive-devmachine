import clayverse.service as service
import clayverse.terminal_gateway as gateway


def test_uvicorn_transport_bound_matches_pty_input_contract():
    options = service._uvicorn_options(host="127.0.0.1", port=3000)

    assert options["host"] == "127.0.0.1"
    assert options["port"] == 3000
    assert options["workers"] == 1
    assert options["access_log"] is False
    assert options["ws"] == "websockets"
    assert options["ws_max_size"] == gateway._PTY_INPUT_FRAME_MAX_BYTES == 65_536
    assert options["ws_max_queue"] == service._WS_MAX_QUEUE == 8
    assert options["ws_per_message_deflate"] is False
