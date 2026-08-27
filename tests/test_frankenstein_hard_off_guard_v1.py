from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_hard_off_guard_v1.py"
)
SPEC = importlib.util.spec_from_file_location("frankenstein_hard_off_guard_v1", MODULE_PATH)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write_inbox(tmp_path: Path, payload: object) -> Path:
    repo = tmp_path / "repo"
    inbox = repo / "research_entity" / "claycode" / "autonomous" / "SUPERVISOR_INBOX.json"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(json.dumps(payload), encoding="utf-8")
    return repo


def _hard_off_payload() -> dict:
    return {
        "schema_version": "9.13",
        "current_frontier": {
            "runtime_provider_authority": "CURRENT_EXPLICIT_HARD_OFF_9_13_ALL_PROVIDERS_FALSE_TOGETHER_FORBIDDEN_NO_PAID_FALLBACK"
        },
        "free_only": {
            "provider_routes_admitted": False,
            "together_forbidden": True,
            "remaining_together_paid_runs_authorized": 0,
        },
    }


def test_current_hard_off_is_blocked_with_zero_boundary_counts(tmp_path: Path) -> None:
    receipt = GUARD.check(_write_inbox(tmp_path, _hard_off_payload()))
    assert receipt["decision"] == "BLOCK"
    assert receipt["reason"] == "CURRENT_SUPERVISOR_HARD_OFF"
    assert receipt["execution_authority_granted"] is False
    assert receipt["provider_calls"] == 0
    assert receipt["secret_lookups"] == 0
    assert receipt["network_calls"] == 0
    assert receipt["aider_calls"] == 0


def test_future_or_non_hardoff_shape_does_not_become_permission(tmp_path: Path) -> None:
    payload = _hard_off_payload()
    payload["free_only"]["provider_routes_admitted"] = True
    receipt = GUARD.check(_write_inbox(tmp_path, payload))
    assert receipt["decision"] == "BLOCK"
    assert receipt["reason"] == "UNKNOWN_OR_NON_HARD_OFF_AUTHORITY_REQUIRES_SUCCESSOR_REVIEW"
    assert receipt["execution_authority_granted"] is False


def test_malformed_or_missing_authority_fails_closed(tmp_path: Path) -> None:
    repo = _write_inbox(tmp_path, ["not", "an", "object"])
    receipt = GUARD.check(repo)
    assert receipt["decision"] == "BLOCK"
    assert receipt["reason"] == "AUTHORITY_READ_OR_PARSE_FAILED"
    assert receipt["provider_calls"] == 0
    assert receipt["secret_lookups"] == 0


def test_guard_source_does_not_import_provider_network_or_process_clients() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_imports = (
        "import requests",
        "import urllib",
        "import socket",
        "import subprocess",
        "import llm",
        "harness_aider",
        "fallback-start",
    )
    for token in forbidden_imports:
        assert token not in source


def test_cli_block_returns_nonzero_and_zero_call_receipt(tmp_path: Path) -> None:
    repo = _write_inbox(tmp_path, _hard_off_payload())
    proc = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 78
    receipt = json.loads(proc.stdout)
    assert receipt["decision"] == "BLOCK"
    assert receipt["provider_calls"] == 0
    assert receipt["secret_lookups"] == 0
    assert receipt["network_calls"] == 0
    assert receipt["aider_calls"] == 0
