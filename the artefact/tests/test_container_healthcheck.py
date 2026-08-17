from pathlib import Path

from clayverse.identity import IdentityRouter
from clayverse.service import _state_probe_payload
from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import _runtime_ready


class _TerminalProbe:
    def __init__(self, live=None):
        self.live = live or {"gabriel": True, "andreas": True}
        self.checked = []

    def binding(self, user_id):
        return user_id

    def _has_session(self, binding):
        self.checked.append(binding)
        return bool(self.live.get(binding, False))


def test_container_healthcheck_is_read_only_runtime_readiness_probe():
    dockerfile=(Path(__file__).resolve().parents[1]/'Dockerfile').read_text()
    health=next(line for line in dockerfile.splitlines() if line.startswith('HEALTHCHECK '))
    assert '--once' not in health
    assert '/readyz' in health
    assert '/healthz' not in health
    assert 'urllib.request' in health
    assert 'clayverse.service' not in health


def test_runtime_readiness_tracks_canonical_state_and_live_product_terminals(tmp_path):
    db = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(db, {})
    terminals = _TerminalProbe()
    assert _runtime_ready(db, terminals) is True
    assert terminals.checked == ['gabriel', 'andreas']
    db.close()
    assert _runtime_ready(db, _TerminalProbe()) is False


def test_runtime_readiness_rejects_missing_product_terminal(tmp_path):
    db = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(db, {})
    try:
        terminals = _TerminalProbe({"gabriel": True, "andreas": False})
        assert _runtime_ready(db, terminals) is False
        assert terminals.checked == ['gabriel', 'andreas']
    finally:
        db.close()


def test_runtime_readiness_rejects_wrong_schema_without_mutation(tmp_path):
    db = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(db, {})
    try:
        db.db.execute("UPDATE meta SET value='999' WHERE key='schema_version'")
        terminals = _TerminalProbe()
        assert _runtime_ready(db, terminals) is False
        assert terminals.checked == []
    finally:
        db.close()


def test_once_probe_is_explicitly_state_only_and_never_ready():
    payload = _state_probe_payload(7, 'abc123')
    assert payload == {
        'service': 'clayverse',
        'status': 'probe_ok',
        'scope': 'state_only',
        'ready': False,
        'checkpoint': 7,
        'state_hash': 'abc123',
    }
