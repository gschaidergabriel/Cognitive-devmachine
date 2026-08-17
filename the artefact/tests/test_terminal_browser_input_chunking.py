from pathlib import Path

import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_browser_terminal_input_is_chunked_to_server_frame_budget():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert f"const maxInputFrameBytes={gateway._PTY_INPUT_FRAME_MAX_BYTES};" in source
    assert "offset+=maxInputFrameBytes" in source
    assert "encoded.slice(offset,offset+maxInputFrameBytes)" in source
    assert "ws.send(new TextEncoder().encode(data))" not in source
