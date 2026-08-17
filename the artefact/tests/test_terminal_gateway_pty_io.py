from pathlib import Path

import pytest

import clayverse.terminal_gateway as gateway


ROOT = Path(__file__).resolve().parents[1]


def test_write_pty_all_retries_partial_writes(monkeypatch):
    payload = b"0123456789abcdef"
    observed = bytearray()

    monkeypatch.setattr(gateway.time, "time", lambda: 100.0)

    def partial_write(_fd, data):
        chunk = bytes(data[:3])
        observed.extend(chunk)
        return len(chunk)

    monkeypatch.setattr(gateway.os, "write", partial_write)
    gateway._write_pty_all(7, payload, 110.0)
    assert bytes(observed) == payload


def test_write_pty_all_fails_if_kernel_makes_no_progress(monkeypatch):
    monkeypatch.setattr(gateway.time, "time", lambda: 100.0)
    monkeypatch.setattr(gateway.os, "write", lambda _fd, _data: 0)
    with pytest.raises(OSError, match="made no progress"):
        gateway._write_pty_all(7, b"input", 110.0)


def test_write_pty_all_stops_partial_continuation_when_lease_expires(monkeypatch):
    payload = b"0123456789abcdef"
    observed = bytearray()
    clock = [100.0]

    monkeypatch.setattr(gateway.time, "time", lambda: clock[0])

    def expiring_partial_write(_fd, data):
        chunk = bytes(data[:3])
        observed.extend(chunk)
        clock[0] = 111.0
        return len(chunk)

    monkeypatch.setattr(gateway.os, "write", expiring_partial_write)
    with pytest.raises(gateway.AuthenticationError, match="expired"):
        gateway._write_pty_all(7, payload, 110.0)
    assert bytes(observed) == payload[:3]


def test_write_pty_all_rejects_already_expired_frame_before_kernel_write(monkeypatch):
    writes = []
    monkeypatch.setattr(gateway.time, "time", lambda: 111.0)
    monkeypatch.setattr(gateway.os, "write", lambda _fd, data: writes.append(bytes(data)) or len(data))
    with pytest.raises(gateway.AuthenticationError, match="expired"):
        gateway._write_pty_all(7, b"input", 110.0)
    assert writes == []


def test_websocket_input_moves_deadline_bound_complete_write_off_event_loop():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "frame_auth_deadline = auth_expires_at" in source
    assert "_write_pty_all," in source
    assert "frame_auth_deadline," in source
    assert 'os.write(attach_fd, message["bytes"])' not in source
