from pathlib import Path

from clayverse.identity import IdentityRouter
from clayverse.service import _state_probe_payload
from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import _runtime_ready


def test_container_healthcheck_is_read_only_runtime_readiness_probe():
    dockerfile=(Path(__file__).resolve().parents[1]/'Dockerfile').read_text()
    health=next(line for line in dockerfile.splitlines() if line.startswith('HEALTHCHECK '))
    assert '--once' not in health
    assert '/readyz' in health
    assert '/healthz' not in health
    assert 'urllib.request' in health
    assert 'clayverse.service' not in health


def test_runtime_readiness_tracks_minimum_canonical_state_and_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(db, {})
    assert _runtime_ready(db) is True
    db.close()
    assert _runtime_ready(db) is False


def test_runtime_readiness_rejects_wrong_schema_without_mutation(tmp_path):
    db = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(db, {})
    try:
        db.db.execute("UPDATE meta SET value='999' WHERE key='schema_version'")
        assert _runtime_ready(db) is False
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
