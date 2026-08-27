"""Tests for the Frankenstein provider authority gate
(frankenstein_authority_gate_v1.py). Originally written by the project's
autonomous supervisor process (trigger3, 2026-08-27) against the LIVE,
shared, concurrently-modified SUPERVISOR_INBOX.json -- fixed here (Gabriel's
direct 2026-08-28 instruction adjusted that live file's free_only block to
re-admit provider routes for this task) to use INJECTED tmp repo_root
fixtures for both the blocked and admitted states, so this suite tests the
gate FUNCTION's real behavior and never goes stale just because the
project's live authority state legitimately changes over time. The two
state-independent tests (missing authority file, no eager provider imports)
are unchanged from the original.
"""
import json
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_authority_gate_v1 as gate
import frankenstein_orchestrator_v1 as orch
import frankenstein_bugfix_v1 as bugfix


def _write_inbox(repo_root: Path, *, provider_routes_admitted: bool, together_forbidden: bool = True,
                  remaining_together_paid_runs_authorized: int = 0) -> None:
    inbox_path = repo_root / gate.INBOX_RELATIVE_PATH
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    inbox_path.write_text(json.dumps({
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": provider_routes_admitted,
            "free_swarm_owner_emergency_stop": not provider_routes_admitted,
            "together_forbidden": together_forbidden,
            "remaining_together_paid_runs_authorized": remaining_together_paid_runs_authorized,
        }
    }))


def test_gate_fails_closed_when_authority_is_missing(tmp_path):
    state = gate.provider_authority_state(tmp_path)
    assert state["provider_routes_admitted"] is False
    assert state["authority_readable"] is False


def test_gate_blocks_when_inbox_denies_provider_routes(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=False)
    state = gate.provider_authority_state(tmp_path)
    assert state["authority_readable"] is True
    assert state["provider_routes_admitted"] is False
    assert state["together_admitted"] is False


def test_gate_admits_when_inbox_explicitly_admits_provider_routes(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=True, together_forbidden=True,
                 remaining_together_paid_runs_authorized=0)
    state = gate.provider_authority_state(tmp_path)
    assert state["provider_routes_admitted"] is True
    # together_forbidden=True keeps the training-run allowance separately
    # closed even though general provider routes (free-pool helper dispatch)
    # are admitted -- these are two independently gated concerns.
    assert state["together_admitted"] is False


def test_gate_admits_together_only_when_all_three_conditions_hold(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=True, together_forbidden=False,
                 remaining_together_paid_runs_authorized=1)
    state = gate.provider_authority_state(tmp_path)
    assert state["together_admitted"] is True

    _write_inbox(tmp_path, provider_routes_admitted=True, together_forbidden=False,
                 remaining_together_paid_runs_authorized=0)
    assert gate.provider_authority_state(tmp_path)["together_admitted"] is False


def test_require_provider_routes_raises_when_denied(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=False)
    try:
        gate.require_provider_routes("test", tmp_path)
        assert False, "must raise when authority denies provider routes"
    except gate.ProviderAuthorityBlocked as exc:
        assert "blocked before provider import/secret lookup/network" in str(exc)


def test_require_provider_routes_passes_when_admitted(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=True)
    state = gate.require_provider_routes("test", tmp_path)
    assert state["provider_routes_admitted"] is True


def test_canonical_entrypoints_have_no_eager_provider_imports():
    for module in (orch, bugfix):
        source = Path(module.__file__).read_text()
        assert "import requests" not in source
        assert "import llm" not in source
    assert orch.authority_status()["provider_calls_performed"] == 0
    assert bugfix.authority_status()["secret_lookups_performed"] == 0


def test_orchestrator_main_never_executes_quarantined_donor_when_denied(tmp_path, monkeypatch):
    _write_inbox(tmp_path, provider_routes_admitted=False)
    monkeypatch.setattr(orch, "REPO_ROOT", tmp_path)
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_orchestrator_v1.py"])
    monkeypatch.setattr(orch.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        orch.main()
        assert False, "denied authority must raise"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []


def test_bugfix_main_never_executes_quarantined_donor_when_denied(tmp_path, monkeypatch):
    _write_inbox(tmp_path, provider_routes_admitted=False)
    monkeypatch.setattr(bugfix, "REPO_ROOT", tmp_path)
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_bugfix_v1.py"])
    monkeypatch.setattr(bugfix.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        bugfix.main()
        assert False, "denied authority must raise"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []
