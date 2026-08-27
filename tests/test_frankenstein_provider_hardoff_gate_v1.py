import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_authority_gate_v1 as gate
import frankenstein_orchestrator_v1 as orch
import frankenstein_bugfix_v1 as bugfix


def test_current_inbox_blocks_provider_routes_and_together():
    state = gate.provider_authority_state()
    assert state["authority_readable"] is True
    assert state["provider_routes_admitted"] is False
    assert state["together_admitted"] is False


def test_gate_fails_closed_when_authority_is_missing(tmp_path):
    state = gate.provider_authority_state(tmp_path)
    assert state["provider_routes_admitted"] is False
    assert state["authority_readable"] is False


def test_require_provider_routes_raises_before_provider_boundary():
    try:
        gate.require_provider_routes("test")
        assert False, "HARD_OFF must block provider route"
    except gate.ProviderAuthorityBlocked as exc:
        assert "blocked before provider import/secret lookup/network" in str(exc)


def test_canonical_entrypoints_have_no_eager_provider_imports():
    for module in (orch, bugfix):
        source = Path(module.__file__).read_text()
        assert "import requests" not in source
        assert "import llm" not in source
    assert orch.authority_status()["provider_calls_performed"] == 0
    assert bugfix.authority_status()["secret_lookups_performed"] == 0


def test_orchestrator_main_never_executes_quarantined_donor_under_hardoff(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_orchestrator_v1.py"])
    monkeypatch.setattr(orch.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        orch.main()
        assert False, "HARD_OFF must raise"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []


def test_bugfix_main_never_executes_quarantined_donor_under_hardoff(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_bugfix_v1.py"])
    monkeypatch.setattr(bugfix.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        bugfix.main()
        assert False, "HARD_OFF must raise"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []
