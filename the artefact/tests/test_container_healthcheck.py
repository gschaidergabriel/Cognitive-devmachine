from pathlib import Path


def test_container_healthcheck_is_read_only_http_probe():
    dockerfile=(Path(__file__).resolve().parents[1]/'Dockerfile').read_text()
    health=next(line for line in dockerfile.splitlines() if line.startswith('HEALTHCHECK '))
    assert '--once' not in health
    assert '/healthz' in health
    assert 'urllib.request' in health
    assert 'clayverse.service' not in health
