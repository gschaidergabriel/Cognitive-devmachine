import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ARTEFACT = Path(__file__).resolve().parents[1]
HELPER = ARTEFACT / "build" / "install_locked_xterm.py"
SOURCE_LOCK = ARTEFACT / "SOURCE_LOCK.json"
DOCKERFILE = ARTEFACT / "Dockerfile"


def _load_helper():
    spec = importlib.util.spec_from_file_location("install_locked_xterm", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sri(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode("ascii")


def test_repository_lock_binds_xterm_version_and_sha512_integrity():
    data = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    entry = data["xterm"]
    assert entry["package"] == "@xterm/xterm"
    assert entry["version"] == "6.0.0"
    assert entry["registry"] == "https://registry.npmjs.org"
    integrity = entry["tarball_integrity"]
    assert integrity.startswith("sha512-")
    assert len(base64.b64decode(integrity.removeprefix("sha512-"), validate=True)) == 64


def test_dockerfile_uses_locked_helper_instead_of_direct_registry_install():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY SOURCE_LOCK.json /opt/clayverse-build/SOURCE_LOCK.json" in dockerfile
    assert "COPY build/install_locked_xterm.py /opt/clayverse-build/install_locked_xterm.py" in dockerfile
    assert "python /opt/clayverse-build/install_locked_xterm.py" in dockerfile
    assert 'npm install --global "${XTERM_SPEC}"' not in dockerfile


def test_archive_integrity_regression_rejects_modified_bytes(tmp_path):
    helper = _load_helper()
    archive = tmp_path / "xterm.tgz"
    baseline = b"bounded-xterm-regression-archive"
    archive.write_bytes(baseline)
    expected = _sri(baseline)
    helper.verify_archive(archive, expected)

    # Replay-only regression of the already-consumed GO byte-tamper intervention.
    archive.write_bytes(baseline + b"!")
    with pytest.raises(helper.XtermLockError, match="integrity mismatch"):
        helper.verify_archive(archive, expected)
