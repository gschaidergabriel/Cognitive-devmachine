from pathlib import Path

from clayverse.service import _state_probe_payload


def test_container_healthcheck_is_read_only_http_probe():
    dockerfile=(Path(__file__).resolve().parents[1]/'Dockerfile').read_text()
    health=next(line for line in dockerfile.splitlines() if line.startswith('HEALTHCHECK '))
    assert '--once' not in health
    assert '/healthz' in health
    assert 'urllib.request' in health
    assert 'clayverse.service' not in health


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
