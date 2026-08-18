from pathlib import Path

import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_browser_terminal_input_is_chunked_to_server_frame_budget():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    # terminal_gateway.py builds this HTML through an f-string template, so the
    # constant appears in SOURCE as the literal Python placeholder, not its
    # evaluated number -- assert on the source-level text, and separately that
    # the placeholder really is the shared constant (not a duplicated literal).
    assert "const maxInputFrameBytes={_PTY_INPUT_FRAME_MAX_BYTES};" in source
    assert gateway._PTY_INPUT_FRAME_MAX_BYTES == 65_536
    assert "offset+=maxInputFrameBytes" in source
    assert "encoded.slice(offset,offset+maxInputFrameBytes)" in source
    assert "ws.send(new TextEncoder().encode(data))" not in source
