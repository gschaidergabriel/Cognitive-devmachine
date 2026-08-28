import hashlib
import subprocess
from types import SimpleNamespace

from clayverse.entityos_bridge import EntityOSBridge


def test_entityos_exec_does_not_inherit_parent_path(monkeypatch, tmp_path):
    entityos = tmp_path / "EntityOS"
    payload = b"#!/bin/sh\nexit 0\n"
    entityos.write_bytes(payload)
    entityos.chmod(0o700)

    observed = {}

    def fake_run(*args, **kwargs):
        observed["env"] = dict(kwargs["env"])
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setenv("PATH", f"{tmp_path}/attacker-bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin")
    monkeypatch.setenv("PYTHONPATH", f"{tmp_path}/attacker-python")
    monkeypatch.setattr(subprocess, "run", fake_run)

    bridge = EntityOSBridge(
        path=str(entityos),
        sha256=hashlib.sha256(payload).hexdigest(),
        timeout=3,
    )
    result = bridge.run(["--probe"])

    assert result["ok"] is True
    assert observed["env"] == {"PATH": "/usr/bin:/bin"}
    assert str(tmp_path) not in observed["env"]["PATH"]
    assert "PYTHONPATH" not in observed["env"]


def test_entityos_exec_path_contract_is_fixed():
    assert EntityOSBridge._EXEC_PATH == "/usr/bin:/bin"
