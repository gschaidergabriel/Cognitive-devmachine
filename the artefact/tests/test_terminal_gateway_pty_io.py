from pathlib import Path

import pytest

import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_write_pty_all_retries_partial_writes(monkeypatch):
    payload = b"0123456789abcdef"
    observed = bytearray()

    def partial_write(_fd, data):
        chunk = bytes(data[:3])
        observed.extend(chunk)
        return len(chunk)

    monkeypatch.setattr(gateway.os, "write", partial_write)
    gateway._write_pty_all(7, payload)
    assert bytes(observed) == payload


def test_write_pty_all_fails_if_kernel_makes_no_progress(monkeypatch):
    monkeypatch.setattr(gateway.os, "write", lambda _fd, _data: 0)
    with pytest.raises(OSError, match="made no progress"):
        gateway._write_pty_all(7, b"input")


def test_websocket_input_moves_blocking_complete_write_off_event_loop():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert 'await asyncio.to_thread(_write_pty_all, attach_fd, message["bytes"])' in source
    assert 'os.write(attach_fd, message["bytes"])' not in source
