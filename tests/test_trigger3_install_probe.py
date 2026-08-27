import importlib.util
import json
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "AI_START_HERE_DO_NOT_SCAN_REPO" / "install_probe.py"
spec = importlib.util.spec_from_file_location("install_probe", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def _parsed(capsys):
    return json.loads(capsys.readouterr().out)


def test_missing_authority_fails_closed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(probe, "repo_root", lambda: tmp_path)
    rc = probe.main()
    out = _parsed(capsys)
    assert rc == 2
    assert out["result"] == "BLOCKED"
    assert out["provider_calls"] == 0
    assert out["secret_lookups"] == 0


def test_malformed_inbox_fails_closed(tmp_path, monkeypatch, capsys):
    (tmp_path / "CLAY_EXECUTION_AUTHORITY.md").write_text("x")
    inbox = tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox.parent.mkdir(parents=True)
    inbox.write_text("{")
    monkeypatch.setattr(probe, "repo_root", lambda: tmp_path)
    rc = probe.main()
    out = _parsed(capsys)
    assert rc == 2
    assert out["result"] == "BLOCKED"
    assert any("failed to parse supervisor inbox" in error for error in out["errors"])


def test_hardoff_is_detected_and_no_cli_stays_degraded(tmp_path, monkeypatch, capsys):
    (tmp_path / "CLAY_EXECUTION_AUTHORITY.md").write_text("x")
    inbox = tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(json.dumps({
        "schema_version": "9.13",
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": False,
            "together_forbidden": True,
            "no_paid_fallback": True,
        },
    }))
    monkeypatch.setattr(probe, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "command", lambda name: None)
    rc = probe.main()
    out = _parsed(capsys)
    assert rc == 0
    assert out["result"] == "DEGRADED"
    assert out["provider_hard_off_detected"] is True


def test_cli_presence_never_promotes_precheck_to_native(tmp_path, monkeypatch, capsys):
    (tmp_path / "CLAY_EXECUTION_AUTHORITY.md").write_text("x")
    inbox = tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(json.dumps({
        "schema_version": "9.13",
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": False,
            "together_forbidden": True,
            "no_paid_fallback": True,
        },
    }))
    monkeypatch.setattr(probe, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "command", lambda name: "/bin/claude" if name == "claude" else None)
    rc = probe.main()
    out = _parsed(capsys)
    assert rc == 0
    assert out["result"] == "ADAPTED"
    assert out["result"] != "NATIVE"
    assert out["capabilities"]["detected_cli_hosts"] == ["claude"]


def test_probe_source_has_no_provider_or_network_client_imports():
    source = MODULE.read_text()
    for forbidden in ("import requests", "import httpx", "import socket", "import urllib", "import subprocess"):
        assert forbidden not in source
