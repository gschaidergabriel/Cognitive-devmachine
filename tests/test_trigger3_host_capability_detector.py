import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "AI_START_HERE_DO_NOT_SCAN_REPO" / "detect_host_capabilities.py"
spec = importlib.util.spec_from_file_location("trigger3_host_caps", MODULE)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


def test_marker_fallback_finds_repo(tmp_path):
    (tmp_path / "research_entity/continuity").mkdir(parents=True)
    (tmp_path / "research_entity/claycode/autonomous").mkdir(parents=True)
    (tmp_path / "CLAY_EXECUTION_AUTHORITY.md").write_text("x")
    (tmp_path / "research_entity/continuity/BOOTSTRAP_MINIMAL.json").write_text("{}")
    (tmp_path / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").write_text("{}")
    assert host.find_repo_root(tmp_path / "research_entity" / "continuity") == tmp_path


def test_missing_repo_is_fail_closed(tmp_path):
    snap = host.snapshot(tmp_path)
    assert snap["repo"]["root"] is None
    assert snap["routes"]["claude_code"] == "BLOCKED"
    assert snap["routes"]["codex_cli"] == "BLOCKED"
    assert snap["routes"]["hermes_agent"] == "BLOCKED"


def test_snapshot_never_claims_execution_evidence(tmp_path):
    snap = host.snapshot(tmp_path)
    assert snap["network_checked"] is False
    assert snap["provider_credentials_checked"] is False
    assert snap["hooks_verified"] is False
    assert snap["durable_write_verified"] is False
    assert snap["effect_receipt_verified"] is False
    assert snap["installation_result"] == "UNVERIFIED_CAPABILITY_SNAPSHOT_ONLY"


def test_cli_routes_are_candidate_only(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(host, "command_paths", lambda: {
        "git": "/usr/bin/git", "python": "/usr/bin/python3",
        "claude_code": "/bin/claude", "codex_cli": "/bin/codex", "hermes_agent": "/bin/hermes",
    })
    snap = host.snapshot(tmp_path)
    assert snap["routes"]["claude_code"] == "NATIVE_CANDIDATE"
    assert snap["routes"]["codex_cli"] == "NATIVE_CANDIDATE"
    assert snap["routes"]["hermes_agent"] == "ADAPTED_CANDIDATE"


def test_source_has_no_network_or_subprocess_imports():
    source = MODULE.read_text()
    for forbidden in ("import requests", "import socket", "import urllib", "import subprocess"):
        assert forbidden not in source
