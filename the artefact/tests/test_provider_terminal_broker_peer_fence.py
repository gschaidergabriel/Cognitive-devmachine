import os
import struct

import pytest

from clayverse.provider_terminal_broker import ProviderTerminalBroker, ProviderTerminalBrokerError


class _FakeEngine:
    def ingest(self, clerk_subject, content, *, resources=None):
        return {
            "user_id": "gabriel",
            "session_id": "session:gabriel",
            "turn_id": "turn-1",
            "assistant_turn_id": "turn-2",
            "causal_id": "causal-1",
            "effect_id": None,
            "decision": {"text": "ok"},
            "outcome": None,
        }


class _PeerConn:
    def __init__(self, pid, uid=None, gid=0):
        self.pid = pid
        self.uid = os.geteuid() if uid is None else uid
        self.gid = gid

    def getsockopt(self, level, option, size):
        return struct.pack("3i", self.pid, self.uid, self.gid)


def _broker(tmp_path):
    return ProviderTerminalBroker(
        tmp_path / "provider.sock",
        engine=_FakeEngine(),
        clerk_map={"clerk-g": "gabriel", "clerk-a": "andreas"},
    )


def test_exact_registered_pane_pid_is_required_even_for_same_uid(tmp_path):
    broker = _broker(tmp_path)
    broker.register_peer(user_id="gabriel", session_id="session:gabriel", pid=4242)

    assert broker._peer_identity(_PeerConn(4242)) == ("gabriel", "session:gabriel")

    with pytest.raises(PermissionError, match="PID"):
        broker._peer_identity(_PeerConn(4243))


def test_different_uid_is_rejected_before_pid_authority(tmp_path):
    broker = _broker(tmp_path)
    broker.register_peer(user_id="gabriel", session_id="session:gabriel", pid=4242)

    with pytest.raises(PermissionError, match="UID"):
        broker._peer_identity(_PeerConn(4242, uid=os.geteuid() + 1))


def test_provider_secret_cannot_be_serialized_back_to_terminal(tmp_path, monkeypatch):
    broker = _broker(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "super-secret-provider-token")

    with pytest.raises(ProviderTerminalBrokerError, match="credential"):
        broker._assert_no_provider_secret(b'{"text":"super-secret-provider-token"}\n')
